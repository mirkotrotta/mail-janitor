from __future__ import annotations

import os

from playwright.sync_api import expect, sync_playwright


def run() -> None:
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8088")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{base_url}/")
        expect(page.locator("h1")).to_have_text("mail-janitor")
        expect(page.locator("form[action='/accounts/save']").first).to_be_visible()

        page.locator("form[action='/accounts/save'] input[name='label']").first.fill(
            "   "
        )
        page.locator(
            "form[action='/accounts/save'] select[name='provider']"
        ).first.select_option("gmail")
        page.locator("form[action='/accounts/save'] input[name='host']").first.fill(
            "imap.gmail.com"
        )
        page.locator("form[action='/accounts/save'] input[name='port']").first.fill(
            "993"
        )
        page.locator("form[action='/accounts/save'] input[name='username']").first.fill(
            "demo@example.com"
        )
        page.locator("form[action='/accounts/save'] input[name='password']").first.fill(
            "not-real"
        )
        page.locator(
            "form[action='/accounts/save'] button[type='submit']"
        ).first.click()

        expect(page.locator(".alert.error")).to_contain_text("Label is required")

        browser.close()


if __name__ == "__main__":
    run()
