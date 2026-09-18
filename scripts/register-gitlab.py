"""Interactively register a GitLab account in a browser."""

import json
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright


DEFAULT_URL = "http://192.168.56.7"
MAX_FIELDS = 5
REPORT_PATH = Path(__file__).resolve().parent.parent / "gitlab-registration.json"


def field_label(field: Locator) -> str:
    label = field.get_attribute("aria-label") or field.get_attribute("placeholder")
    if label:
        return label.strip()

    field_id = field.get_attribute("id")
    if field_id:
        associated = field.locator(f"xpath=//label[@for='{field_id}']")
        if associated.count():
            return associated.first.inner_text().strip()

    name = field.get_attribute("name") or field.get_attribute("type")
    return (name or "field").replace("_", " ").strip().title()


def visible_editable_fields(page: Page) -> list[Locator]:
    fields = page.locator("input:not([type='hidden']):not([type='submit']):not([type='button']), textarea, select")
    return [fields.nth(index) for index in range(fields.count()) if fields.nth(index).is_visible()]


def main() -> None:
    url = input(f"GitLab URL [{DEFAULT_URL}]: ").strip() or DEFAULT_URL
    entries: dict[str, str] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")

        register = page.get_by_role("link", name="Register")
        if register.count():
            register.first.click()
            page.wait_for_load_state("domcontentloaded")

        fields = visible_editable_fields(page)[:MAX_FIELDS]
        if not fields:
            browser.close()
            raise RuntimeError("No visible registration fields were found.")

        for field in fields:
            label = field_label(field)
            input_type = (field.get_attribute("type") or "text").lower()
            field.click()
            print(f"\n{label}")
            value = input("Enter value: ")
            if input_type == "checkbox":
                if value.lower() in {"y", "yes", "true", "1"}:
                    field.check()
            elif field.evaluate("element => element.tagName") == "SELECT":
                field.select_option(value)
            else:
                field.fill(value)
            entries[label] = "[REDACTED]" if input_type == "password" else value

        submit = page.get_by_role("button", name="Continue")
        if not submit.count():
            submit = page.get_by_role("button", name="Register")
        if not submit.count():
            submit = page.get_by_role("link", name="Continue")
        if not submit.count():
            browser.close()
            raise RuntimeError("Could not find a Continue or Register control.")

        submit.first.click()
        page.wait_for_timeout(1500)
        browser.close()

    with REPORT_PATH.open("w", encoding="utf-8") as report:
        json.dump(entries, report, indent=2)
        report.write("\n")

    print(f"\nRegistration submitted. Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()