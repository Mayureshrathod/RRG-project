"""
Phase 0 — Real-World Validation Script

Fetches NIFTY BANK and NIFTY 50 data, computes RSR/RSM,
and validates quadrant classification + rotation direction
against expected behavior.

Run: python tests/validate_real_world.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from datetime import date, timedelta

from engine.rs_calculator import compute_raw_rs
from engine.normalization import normalize_zscore_vectorized
from engine.momentum import compute_rs_momentum
from engine.timeframe import resample_close_series, get_windows
from config.engine import Timeframe, EPSILON


def classify_quadrant(rsr: float, rsm: float) -> str:
    """Classify a point into one of the four RRG quadrants."""
    if rsr > 100 and rsm > 100:
        return "Leading"
    elif rsr > 100 and rsm <= 100:
        return "Weakening"
    elif rsr <= 100 and rsm <= 100:
        return "Lagging"
    else:
        return "Improving"


def run_validation():
    """Run the full validation pipeline."""
    print("=" * 70)
    print("RRG Phase 0 — Real-World Validation")
    print("NIFTY BANK vs NIFTY 50 (Weekly Timeframe)")
    print("=" * 70)
    print()

    # ── Step 1: Fetch Data ──────────────────────────────────────
    print("[1/6] Fetching data...")

    try:
        from providers.yfinance_provider import YFinanceProvider
        provider = YFinanceProvider()

        end_date = date.today()
        start_date = end_date - timedelta(days=730)

        print(f"  Fetching NIFTY 50 ({start_date} → {end_date})...")
        benchmark_df = provider.fetch_index_history("NIFTY 50", start_date, end_date)

        print(f"  Fetching NIFTY BANK ({start_date} → {end_date})...")
        import time
        time.sleep(1)  # Avoid rate limiting
        sector_df = provider.fetch_index_history("NIFTY BANK", start_date, end_date)

        if benchmark_df is None or sector_df is None:
            print("  ❌ FAILED: Could not fetch from yfinance.")
            print("  Cannot proceed with real-world validation.")
            return False

    except Exception as e:
        print(f"\n  ❌ FAILED: {e}")
        return False

    print(f"  ✅ Benchmark: {len(benchmark_df)} daily rows")
    print(f"  ✅ Sector:    {len(sector_df)} daily rows")

    # ── Step 2: Resample to Weekly ──────────────────────────────
    print("\n[2/6] Resampling to weekly...")

    bench_weekly = resample_close_series(benchmark_df["Close"], Timeframe.WEEKLY)
    sector_weekly = resample_close_series(sector_df["Close"], Timeframe.WEEKLY)

    # Align to common dates
    common = bench_weekly.index.intersection(sector_weekly.index)
    bench_close = bench_weekly.loc[common].values
    sector_close = sector_weekly.loc[common].values
    dates = common

    print(f"  ✅ {len(common)} common weekly dates")

    # ── Step 3: Compute Raw RS ──────────────────────────────────
    print("\n[3/6] Computing raw RS...")

    raw_rs = compute_raw_rs(sector_close, bench_close)
    print(f"  First RS:  {raw_rs[0]:.6f}")
    print(f"  Last RS:   {raw_rs[-1]:.6f}")
    print(f"  Min RS:    {np.nanmin(raw_rs):.6f}")
    print(f"  Max RS:    {np.nanmax(raw_rs):.6f}")

    # ── Step 4: Compute RSR and RSM ─────────────────────────────
    print("\n[4/6] Computing RSR and RSM (weekly, canonical JdK windows)...")

    windows = get_windows(Timeframe.WEEKLY)
    rsr_window = windows["rsr"]  # 10
    rsm_window = windows["rsm"]  # 14

    # RSR = normalized raw RS
    rsr = normalize_zscore_vectorized(raw_rs, window=rsr_window, epsilon=EPSILON)

    # RSM = normalized ROC of raw RS
    rsm = compute_rs_momentum(raw_rs, window=rsm_window, smoothing=1, epsilon=EPSILON)

    # Find valid range (both non-NaN)
    valid_mask = ~(np.isnan(rsr) | np.isnan(rsm))
    valid_indices = np.where(valid_mask)[0]

    if len(valid_indices) == 0:
        print("  ❌ FAILED: No valid RSR/RSM values computed.")
        return False

    valid_rsr = rsr[valid_mask]
    valid_rsm = rsm[valid_mask]
    valid_dates = dates[valid_mask]

    print(f"  ✅ {len(valid_rsr)} valid data points")
    print(f"  RSR range: [{np.min(valid_rsr):.2f}, {np.max(valid_rsr):.2f}]")
    print(f"  RSM range: [{np.min(valid_rsm):.2f}, {np.max(valid_rsm):.2f}]")

    # ── Step 5: Quadrant Classification ─────────────────────────
    print("\n[5/6] Quadrant analysis...")

    current_rsr = valid_rsr[-1]
    current_rsm = valid_rsm[-1]
    current_quadrant = classify_quadrant(current_rsr, current_rsm)

    print(f"  Current RSR:      {current_rsr:.4f}")
    print(f"  Current RSM:      {current_rsm:.4f}")
    print(f"  Current Quadrant: {current_quadrant}")
    print(f"  Current Date:     {valid_dates[-1].strftime('%Y-%m-%d')}")

    # Count quadrant distribution over the valid period
    quadrant_counts = {"Leading": 0, "Weakening": 0, "Lagging": 0, "Improving": 0}
    for r, m in zip(valid_rsr, valid_rsm):
        q = classify_quadrant(r, m)
        quadrant_counts[q] += 1

    print(f"\n  Quadrant Distribution (over {len(valid_rsr)} weeks):")
    for q, count in quadrant_counts.items():
        pct = count / len(valid_rsr) * 100
        print(f"    {q:12s}: {count:3d} weeks ({pct:.1f}%)")

    # ── Step 6: Rotation Direction ──────────────────────────────
    print("\n[6/6] Rotation analysis (last 10 data points)...")

    trail = min(10, len(valid_rsr))
    trail_rsr = valid_rsr[-trail:]
    trail_rsm = valid_rsm[-trail:]
    trail_dates = valid_dates[-trail:]

    print(f"\n  {'Date':>12s}  {'RSR':>8s}  {'RSM':>8s}  {'Quadrant':>12s}")
    print(f"  {'─' * 12}  {'─' * 8}  {'─' * 8}  {'─' * 12}")
    for i in range(trail):
        d = trail_dates[i].strftime('%Y-%m-%d')
        q = classify_quadrant(trail_rsr[i], trail_rsm[i])
        print(f"  {d}  {trail_rsr[i]:8.4f}  {trail_rsm[i]:8.4f}  {q:>12s}")

    # Compute direction of last movement
    if len(trail_rsr) >= 2:
        delta_rsr = trail_rsr[-1] - trail_rsr[-2]
        delta_rsm = trail_rsm[-1] - trail_rsm[-2]
        angle = np.degrees(np.arctan2(delta_rsm, delta_rsr))
        velocity = np.sqrt(delta_rsr**2 + delta_rsm**2)
        print(f"\n  Last movement:")
        print(f"    ΔRSR:      {delta_rsr:+.4f}")
        print(f"    ΔRSM:      {delta_rsm:+.4f}")
        print(f"    Direction: {angle:.1f}°")
        print(f"    Velocity:  {velocity:.4f}")

    # ── Validation Summary ──────────────────────────────────────
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    checks = []

    # Check 1: RSR values are finite and in reasonable range
    rsr_ok = np.all(np.isfinite(valid_rsr)) and np.all(np.abs(valid_rsr - 100) < 20)
    checks.append(("RSR values finite & in range [80, 120]", rsr_ok))

    # Check 2: RSM values are finite and in reasonable range
    rsm_ok = np.all(np.isfinite(valid_rsm)) and np.all(np.abs(valid_rsm - 100) < 20)
    checks.append(("RSM values finite & in range [80, 120]", rsm_ok))

    # Check 3: Multiple quadrants visited (rotation occurs)
    active_quadrants = sum(1 for v in quadrant_counts.values() if v > 0)
    rotation_ok = active_quadrants >= 2
    checks.append((f"Multiple quadrants visited ({active_quadrants}/4)", rotation_ok))

    # Check 4: No NaN/Inf in output
    nan_ok = not np.any(np.isnan(valid_rsr)) and not np.any(np.isnan(valid_rsm))
    checks.append(("No NaN in final output", nan_ok))

    # Check 5: Centered near 100
    mean_rsr = np.mean(valid_rsr)
    mean_rsm = np.mean(valid_rsm)
    centered_ok = abs(mean_rsr - 100) < 5 and abs(mean_rsm - 100) < 5
    checks.append((f"RSR mean={mean_rsr:.2f}, RSM mean={mean_rsm:.2f} (near 100)", centered_ok))

    all_passed = True
    for desc, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {desc}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("  ✅ ALL CHECKS PASSED — Engine validated for real-world data.")
        print()
        print("  NOTE: This validates mathematical behavior (finite values,")
        print("  centered at 100, rotation present). For directional comparison")
        print("  with StockCharts/Optuma, visually inspect the trail above.")
    else:
        print("  ❌ VALIDATION FAILED — Do NOT proceed to dashboard.")
        print("  Investigate and fix engine before continuing.")

    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
