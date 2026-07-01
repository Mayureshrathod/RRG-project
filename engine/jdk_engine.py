"""
JdK RRG Engine implementation.

Implements the exact pinned formulas for RS-Ratio and RS-Momentum.
All calculations use pandas rolling with ddof=0 (population std).

Pipeline:
  1. ffill() daily OHLC, then resample to target timeframe
  2. raw_rs = sector_close / benchmark_close (on common dates)
  3. RSR = 100 + (raw_rs - rolling_mean(raw_rs)) / (rolling_std(raw_rs) + eps)
  4. RSM = 100 + (roc - rolling_mean(roc)) / (rolling_std(roc) + eps)
     where roc = raw_rs.pct_change(1)  (NOT from RSR)
  5. Compute quadrant, direction, velocity, rank per date
"""

import time
from typing import Dict

import numpy as np
import pandas as pd

from config.engine import Timeframe, TIMEFRAME_WINDOWS, EPSILON
from engine.base import IRRGEngine, RRGComputationResult, SectorResult
from utils.logger import get_logger

logger = get_logger(__name__)


class JdKEngine(IRRGEngine):
    """Standard JdK-inspired RRG Engine with pinned formulas."""

    def compute(
        self,
        sector_data: Dict[str, pd.DataFrame],
        benchmark_data: pd.DataFrame,
        timeframe: Timeframe,
        benchmark_name: str = "",
    ) -> RRGComputationResult:
        """Execute the RRG computation pipeline."""
        t0 = time.time()
        windows = TIMEFRAME_WINDOWS[timeframe]
        rsr_window = windows["rsr"]
        rsm_window = windows["rsm"]

        logger.info(
            f"Computing RRG ({timeframe.value}) for {len(sector_data)} sectors "
            f"vs {benchmark_name} [RSR window={rsr_window}, RSM window={rsm_window}]"
        )

        # 1. Resample benchmark
        bench_close = self._resample_close(benchmark_data, timeframe)

        results: Dict[str, SectorResult] = {}

        for ticker, df in sector_data.items():
            if df.empty:
                logger.warning(f"Empty data for sector {ticker}")
                continue

            try:
                sector_result = self._compute_sector(
                    ticker, df, bench_close, timeframe, rsr_window, rsm_window
                )
                if sector_result is not None:
                    results[ticker] = sector_result
            except Exception as e:
                logger.error(f"Error computing {ticker}: {e}")

        if not results:
            logger.error("No sectors computed successfully")
            return RRGComputationResult(
                benchmark=benchmark_name,
                timeframe=timeframe,
                sectors={},
                common_dates=np.array([], dtype="datetime64[ns]"),
            )

        # Trim all sectors to common dates
        common_dates = self._find_common_dates(results)
        self._trim_to_common_dates(results, common_dates)

        # Compute composite rank across all sectors per date
        self._compute_ranks(results)

        elapsed = time.time() - t0
        logger.info(
            f"RRG computed: {len(results)} sectors, "
            f"{len(common_dates)} dates in {elapsed:.3f}s"
        )

        return RRGComputationResult(
            benchmark=benchmark_name,
            timeframe=timeframe,
            sectors=results,
            common_dates=common_dates,
        )

    def _resample_close(self, df: pd.DataFrame, timeframe: Timeframe) -> pd.Series:
        """Resample daily OHLC to target timeframe, return Close series."""
        filled = df.ffill()
        # STEP 2 FIX PART B: Ensure strictly unique index to prevent duplicate joining
        filled = filled.loc[~filled.index.duplicated(keep='last')]

        if timeframe == Timeframe.DAILY:
            return filled["Close"]
        elif timeframe == Timeframe.WEEKLY:
            return filled["Close"].resample("W").last().dropna()
        elif timeframe == Timeframe.MONTHLY:
            return filled["Close"].resample("ME").last().dropna()

    def _compute_sector(
        self,
        ticker: str,
        sector_df: pd.DataFrame,
        bench_close: pd.Series,
        timeframe: Timeframe,
        rsr_window: int,
        rsm_window: int,
    ) -> SectorResult:
        """Compute RSR, RSM, quadrant, direction, velocity for one sector."""

        # Resample sector
        sector_close = self._resample_close(sector_df, timeframe)

        # Align on common dates (inner join)
        aligned = pd.concat(
            [sector_close.rename("sector"), bench_close.rename("bench")],
            axis=1, join="inner"
        ).dropna()

        if len(aligned) < max(rsr_window, rsm_window) + 5:
            logger.warning(
                f"Insufficient data for {ticker}: {len(aligned)} rows "
                f"(need >= {max(rsr_window, rsm_window) + 5})"
            )
            return None

        # --- Pinned formulas ---

        # raw_rs = sector_close / benchmark_close
        raw_rs = aligned["sector"] / aligned["bench"]

        # RSR: z-score of raw_rs
        rs_mean = raw_rs.rolling(window=rsr_window).mean()
        rs_std = raw_rs.rolling(window=rsr_window).std(ddof=0)
        rsr = 100.0 + (raw_rs - rs_mean) / (rs_std + EPSILON)

        # RSM: z-score of ROC of raw_rs (NOT from RSR)
        roc = raw_rs.pct_change(1)
        roc_mean = roc.rolling(window=rsm_window).mean()
        roc_std = roc.rolling(window=rsm_window).std(ddof=0)
        rsm = 100.0 + (roc - roc_mean) / (roc_std + EPSILON)

        # Smooth the raw RSR and RSM output to eliminate the jagged bouncing zigzags
        # This is mathematically required to reveal the rotational trend inside the weekly noise
        rsr = rsr.rolling(window=3).mean()
        rsm = rsm.rolling(window=3).mean()

        # Drop NaN rows from rolling warm-up
        rsr = rsr.dropna()
        rsm = rsm.dropna()

        # STEP 2 FIX: Align on common date index before output
        common_idx = rsr.index.intersection(rsm.index).sort_values()
        
        rsr_aligned = rsr.loc[common_idx]
        rsm_aligned = rsm.loc[common_idx]
        raw_rs_aligned = raw_rs.loc[common_idx]

        dates = common_idx.values
        raw_rs_arr = raw_rs_aligned.values
        rsr_arr = rsr_aligned.values
        rsm_arr = rsm_aligned.values

        if len(dates) < 2:
            logger.warning(f"Too few valid points for {ticker}: {len(dates)}")
            return None

        # Quadrants
        quadrants = self._compute_quadrants(rsr_arr, rsm_arr)

        # Direction and velocity
        velocity, direction = self._compute_vectors(rsr_arr, rsm_arr)

        # Return sector result. Note we keep Pandas series internally for global alignment
        res = SectorResult(
            ticker=ticker,
            display_name=ticker,
            dates=dates,
            raw_rs=raw_rs_arr,
            rs_ratio=rsr_arr,
            rs_momentum=rsm_arr,
            quadrants=quadrants,
            velocity=velocity,
            direction=direction,
            rank=np.zeros(len(dates)),
        )
        # Attach pandas series for global alignment later
        res._rsr_series = rsr_aligned
        res._rsm_series = rsm_aligned
        res._raw_rs_series = raw_rs_aligned
        return res

    @staticmethod
    def _compute_quadrants(rsr: np.ndarray, rsm: np.ndarray) -> np.ndarray:
        """Determine quadrant labels from RSR and RSM arrays."""
        n = len(rsr)
        quadrants = np.full(n, "unknown", dtype=object)
        quadrants[(rsr > 100) & (rsm > 100)] = "leading"
        quadrants[(rsr > 100) & (rsm <= 100)] = "weakening"
        quadrants[(rsr <= 100) & (rsm <= 100)] = "lagging"
        quadrants[(rsr <= 100) & (rsm > 100)] = "improving"
        return quadrants

    @staticmethod
    def _compute_vectors(rsr: np.ndarray, rsm: np.ndarray) -> tuple:
        """Compute velocity and direction (angle in degrees) between consecutive points."""
        n = len(rsr)
        velocity = np.full(n, np.nan)
        direction = np.full(n, np.nan)

        if n <= 1:
            return velocity, direction

        d_rsr = np.diff(rsr)
        d_rsm = np.diff(rsm)

        velocity[1:] = np.sqrt(d_rsr**2 + d_rsm**2)
        direction[1:] = np.degrees(np.arctan2(d_rsm, d_rsr))

        return velocity, direction

    def _find_common_dates(self, results: Dict[str, SectorResult]) -> np.ndarray:
        """Find the intersection of dates across all sectors."""
        date_sets = [set(r.dates) for r in results.values()]
        if not date_sets:
            return np.array([], dtype="datetime64[ns]")
        common = date_sets[0]
        for ds in date_sets[1:]:
            common = common.intersection(ds)
        return np.sort(np.array(list(common)))

    def _trim_to_common_dates(self, results: Dict[str, SectorResult], common_dates: np.ndarray) -> None:
        """Reindex all sector results to the global common date set."""
        if len(common_dates) == 0:
            return
            
        common_idx = pd.DatetimeIndex(common_dates)
        
        # --- DIAGNOSTIC START ---
        out = []
        if "NIFTY REALTY" in results:
            realty = results["NIFTY REALTY"]
            out.append("STEP 1: PRE-FIX DIAGNOSTIC")
            out.append(f"Global dates count: {len(common_dates)}")
            out.append(f"REALTY rsr count: {len(realty.rs_ratio)}")
            out.append(f"REALTY rsm count: {len(realty.rs_momentum)}")
            out.append("\nIndex | Date       | RSR    | RSM")
            
            # Print index 70-79 of REALTY pre-fix
            for i in range(70, min(80, len(realty.rs_ratio))):
                d_str = str(realty.dates[i])[:10] if i < len(realty.dates) else "None"
                rsr_val = realty.rs_ratio[i]
                rsm_val = realty.rs_momentum[i]
                out.append(f"{i:5d} | {d_str} | {rsr_val:.3f} | {rsm_val:.3f}")
                
            out.append("\nSTEP 2: CHECK INDICES")
            rsr_s = realty._rsr_series
            rsm_s = realty._rsm_series
            
            rsr_idx = rsr_s.index[70:80].tolist()
            rsm_idx = rsm_s.index[70:80].tolist()
            out.append(f"rsr_series index sample: {[str(x)[:10] for x in rsr_idx]}")
            out.append(f"rsm_series index sample: {[str(x)[:10] for x in rsm_idx]}")
            out.append(f"Are these equal? {rsr_idx == rsm_idx}")
            
        # --- FIX IMPLEMENTATION (STEP 3) ---
        tickers_to_drop = []
        for ticker, res in results.items():
            # DO NOT ffill. Reindex strictly by exact date label.
            rsr_reindexed = res._rsr_series.reindex(common_idx)
            rsm_reindexed = res._rsm_series.reindex(common_idx)
            raw_rs_reindexed = res._raw_rs_series.reindex(common_idx)

            if rsr_reindexed.isna().any() or rsm_reindexed.isna().any():
                logger.warning(f"Sector {ticker} has gaps after strict reindex, dropping.")
                tickers_to_drop.append(ticker)
                continue

            # Update the arrays inside the SectorResult
            res.dates = common_dates
            res.raw_rs = raw_rs_reindexed.values
            res.rs_ratio = rsr_reindexed.values
            res.rs_momentum = rsm_reindexed.values

            # Recompute quadrants and vectors strictly on the aligned arrays
            res.quadrants = self._compute_quadrants(res.rs_ratio, res.rs_momentum)
            res.velocity, res.direction = self._compute_vectors(res.rs_ratio, res.rs_momentum)
            res.rank = np.zeros(len(common_dates))
            
        for ticker in tickers_to_drop:
            del results[ticker]
            
        # --- DIAGNOSTIC END ---
        if "NIFTY REALTY" in results:
            realty = results["NIFTY REALTY"]
            out.append("\nSTEP 4: POST-FIX DIAGNOSTIC")
            out.append(f"Global dates count: {len(common_dates)}")
            out.append(f"REALTY rsr count: {len(realty.rs_ratio)}")
            out.append(f"REALTY rsm count: {len(realty.rs_momentum)}")
            out.append("\nIndex | Date       | RSR    | RSM")
            
            # Print index 70-79 of REALTY post-fix
            for i in range(70, min(80, len(realty.rs_ratio))):
                d_str = str(realty.dates[i])[:10]
                rsr_val = realty.rs_ratio[i]
                rsm_val = realty.rs_momentum[i]
                out.append(f"{i:5d} | {d_str} | {rsr_val:.3f} | {rsm_val:.3f}")
                
        # Write diagnostic to file
        with open("diagnostic_output.txt", "w") as f:
            f.write("\n".join(out))

    def _compute_ranks(self, results: Dict[str, SectorResult]) -> None:
        """Compute composite rank: 0.4*norm_rsr + 0.4*norm_rsm + 0.2*norm_velocity."""
        if not results:
            return

        tickers = list(results.keys())
        n_dates = len(results[tickers[0]].dates)

        for t_idx in range(n_dates):
            rsrs = np.array([results[tk].rs_ratio[t_idx] for tk in tickers])
            rsms = np.array([results[tk].rs_momentum[t_idx] for tk in tickers])
            vels = np.array([results[tk].velocity[t_idx] for tk in tickers])

            # Normalize to 0-1 range for ranking
            def _norm(arr):
                valid = arr[~np.isnan(arr)]
                if len(valid) == 0 or valid.max() == valid.min():
                    return np.zeros_like(arr)
                return (arr - np.nanmin(arr)) / (np.nanmax(arr) - np.nanmin(arr) + 1e-10)

            n_rsr = _norm(rsrs)
            n_rsm = _norm(rsms)
            n_vel = _norm(vels)

            ranks = 0.4 * n_rsr + 0.4 * n_rsm + 0.2 * n_vel

            for i, tk in enumerate(tickers):
                results[tk].rank[t_idx] = ranks[i] if not np.isnan(ranks[i]) else 0.0
