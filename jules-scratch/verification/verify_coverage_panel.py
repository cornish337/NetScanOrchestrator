from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    try:
        # 1. Navigate directly to the dashboard for a mock scan.
        page.goto("http://localhost:5173/dashboard?scan=scan_running")

        # 2. Wait for the dashboard to load and the panel to be visible
        coverage_panel_heading = page.get_by_role("heading", name="Scan Coverage")
        expect(coverage_panel_heading).to_be_visible(timeout=10000)

        # 3. Take a screenshot of the coverage panel
        coverage_panel = coverage_panel_heading.locator("..")
        coverage_panel.screenshot(path="jules-scratch/verification/verification.png")

    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
