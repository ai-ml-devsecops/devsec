"""Create a GitLab group and project through the GitLab web interface."""

import argparse
import os
import re
from dataclasses import dataclass
from urllib.parse import urljoin

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


DEFAULT_URL = "http://192.168.26.128"


@dataclass(frozen=True)
class Settings:
    base_url: str
    username: str
    password: str
    group_name: str
    project_name: str
    headless: bool


def parse_args() -> Settings:
    parser = argparse.ArgumentParser(
        description="Create a GitLab group and project using an authenticated browser session."
    )
    parser.add_argument("--url", default=os.getenv("GITLAB_URL", DEFAULT_URL))
    parser.add_argument("--username", default=os.getenv("GITLAB_USERNAME"))
    parser.add_argument("--password", default=os.getenv("GITLAB_PASSWORD"))
    parser.add_argument("--group", default=os.getenv("GITLAB_GROUP_NAME"))
    parser.add_argument("--project", default=os.getenv("GITLAB_PROJECT_NAME"))
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Show the browser while the automation runs.",
    )
    args = parser.parse_args()

    missing = [
        name
        for name, value in (
            ("--username/GITLAB_USERNAME", args.username),
            ("--password/GITLAB_PASSWORD", args.password),
            ("--group/GITLAB_GROUP_NAME", args.group),
            ("--project/GITLAB_PROJECT_NAME", args.project),
        )
        if not value
    ]
    if missing:
        parser.error("Missing required values: " + ", ".join(missing))

    return Settings(
        base_url=args.url.rstrip("/") + "/",
        username=args.username,
        password=args.password,
        group_name=args.group,
        project_name=args.project,
        headless=not args.headed,
    )


def login(page: Page, settings: Settings) -> None:
    page.goto(urljoin(settings.base_url, "users/sign_in"), wait_until="domcontentloaded")
    page.get_by_label("Username or primary email").fill(settings.username)
    page.get_by_label("Password").fill(settings.password)
    page.get_by_role("button", name=re.compile("Sign in", re.IGNORECASE)).click()
    page.wait_for_load_state("domcontentloaded")
    if "/users/sign_in" in page.url:
        raise RuntimeError("GitLab sign-in failed; check the username and password.")


def create_group(page: Page, settings: Settings) -> str:
    page.goto(
        urljoin(settings.base_url, "admin/registrations/groups/new"),
        wait_until="domcontentloaded",
    )
    page.get_by_label("Group name").fill(settings.group_name)
    page.get_by_role("button", name=re.compile("Create group", re.IGNORECASE)).click()
    page.wait_for_load_state("domcontentloaded")

    if page.get_by_text(re.compile("already exists", re.IGNORECASE)).count():
        raise RuntimeError(f"GitLab group '{settings.group_name}' already exists.")
    if "/admin/registrations/groups/new" in page.url or "/users/sign_in" in page.url:
        raise RuntimeError(f"GitLab did not create the group (current URL: {page.url}).")
    group_link = page.get_by_role("link", name=settings.group_name, exact=True)
    if group_link.count():
        href = group_link.first.get_attribute("href")
        if href:
            return urljoin(settings.base_url, href)
    return page.url


def create_project(page: Page, settings: Settings, group_url: str) -> None:
    page.goto(group_url, wait_until="domcontentloaded")
    new_project = page.get_by_role("link", name=re.compile("New project", re.IGNORECASE))
    if not new_project.count():
        new_project = page.get_by_role(
            "button", name=re.compile("New project", re.IGNORECASE)
        )
    if not new_project.count():
        raise RuntimeError("Could not find the New project control on the new group.")
    new_project.first.click()
    page.wait_for_load_state("domcontentloaded")
    page.get_by_label("Project name").fill(settings.project_name)
    page.get_by_role("button", name=re.compile("Create project", re.IGNORECASE)).click()
    page.wait_for_load_state("domcontentloaded")

    if page.get_by_text(re.compile("already exists", re.IGNORECASE)).count():
        raise RuntimeError(f"GitLab project '{settings.project_name}' already exists.")
    if "/projects/new" in page.url or not page.get_by_text(
        settings.project_name, exact=True
    ).count():
        raise RuntimeError(f"GitLab did not create the project (current URL: {page.url}).")


def main() -> None:
    settings = parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=settings.headless)
        page = browser.new_page()
        try:
            login(page, settings)
            group_url = create_group(page, settings)
            create_project(page, settings, group_url)
        except PlaywrightTimeoutError as error:
            raise RuntimeError(
                "GitLab page did not contain the expected control. "
                "Check the GitLab version and supplied values."
            ) from error
        finally:
            browser.close()

    print(f"Created GitLab group '{settings.group_name}' and project '{settings.project_name}'.")


if __name__ == "__main__":
    main()
