/**
 * RRG Dashboard — Search & Filter Module (Phase 6)
 *
 * Responsibilities:
 * - Provide logic to determine if a sector matches the active search term.
 * - This centralizes partial matching, ensuring Graph, Table, and Legend behave uniformly.
 */

window.rrgSearch = {
    /**
     * Checks if a sector should be highlighted based on the current search filter.
     * @param {string} sector - The sector name to check.
     * @returns {boolean} True if the sector matches the search string, or if search is empty.
     */
    isHighlighted: function(sector) {
        var term = window.uiState.searchFilter;
        if (!term) return true; // No filter means everything is highlighted
        return sector.toLowerCase().includes(term.toLowerCase());
    }
};
