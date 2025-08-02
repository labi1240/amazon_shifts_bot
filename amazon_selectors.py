"""Amazon-specific selectors for reliable element detection."""

AMAZON_SELECTORS = {
    'job_cards': [
        '[data-test-id="job-card"]',
        '.job-tile',
        '[data-testid="job-tile"]',
        '.JobTile'
    ],
    'filters_panel': [
        '[data-test-id="filters-panel"]',
        '.filters-panel',
        '[data-testid="filters-panel"]'
    ],
    'loading_indicators': [
        '[data-testid="loading-spinner"]',
        '.loading-spinner',
        '[aria-label="Loading"]',
        '.spinner-border'
    ],
    'no_jobs_message': [
        '[data-testid="no-jobs-message"]',
        '.no-results',
        '.empty-state'
    ]
}