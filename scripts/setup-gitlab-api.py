"""Bootstrap the local GitLab training project through the REST API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin
from urllib.request import Request, urlopen


DEFAULT_URL = "http://192.168.26.128"
DEFAULT_GROUP = "pdso"
DEFAULT_PROJECT = "django.nv"
DEFAULT_SOURCE = ""
https://gitlab.practical-devsecops.training/pdso/django.nv.git

class GitLabError(RuntimeError):
    """An actionable GitLab API error."""


@dataclass(frozen=True)
class Settings:
    base_url: str
    token: str
    username: str | None
    name: str | None
    email: str | None
    password: str | None
    group_name: str
    project_name: str
    source_url: str
    timeout: int
    poll_interval: int
    ensure_runner: bool
    runner_description: str
    runner_tags: str
    trigger_pipeline: bool


class GitLabApi:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.api_url = urljoin(settings.base_url, "/api/v4/")

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> Any:
        url = urljoin(self.api_url, path.lstrip("/"))
        if query:
            url += "?" + urlencode(query)
        payload = None
        headers = {"PRIVATE-TOKEN": self.settings.token, "Accept": "application/json"}
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.settings.timeout) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code not in expected:
                raise GitLabError(f"{method} {path} returned HTTP {error.code}: {detail}") from error
            if error.code == 404:
                return None
            return json.loads(detail) if detail else None
        except (URLError, TimeoutError) as error:
            raise GitLabError(f"Could not reach GitLab at {self.settings.base_url}: {error}") from error

    def wait_until_ready(self, attempts: int = 60) -> None:
        for attempt in range(1, attempts + 1):
            try:
                self.request("GET", "version", expected=(200, 401))
                return
            except GitLabError:
                if attempt == attempts:
                    break
                time.sleep(self.settings.poll_interval)
        raise GitLabError("GitLab did not become ready before the timeout expired.")

    def find_user(self, username: str) -> dict[str, Any] | None:
        users = self.request("GET", "users", query={"username": username})
        return next((user for user in users if user.get("username") == username), None)

    def ensure_user(self) -> dict[str, Any] | None:
        if not self.settings.username:
            return None
        user = self.find_user(self.settings.username)
        if user:
            return user
        required = {
            "name": self.settings.name,
            "email": self.settings.email,
            "password": self.settings.password,
            "username": self.settings.username,
            "admin": False,
            "skip_confirmation": True,
        }
        missing = [key for key in ("name", "email", "password") if not required[key]]
        if missing:
            raise GitLabError("User creation requires: " + ", ".join(missing))
        return self.request("POST", "users", body=required, expected=(201,))

    def find_group(self, name: str) -> dict[str, Any] | None:
        groups = self.request("GET", "groups", query={"search": name, "top_level_only": "true"})
        return next((group for group in groups if group.get("name") == name or group.get("path") == name), None)

    def ensure_group(self) -> dict[str, Any]:
        group = self.find_group(self.settings.group_name)
        if not group:
            path = self.settings.group_name.lower().replace(" ", "-")
            group = self.request(
                "POST",
                "groups",
                body={
                    "name": self.settings.group_name,
                    "path": path,
                    "visibility": "public",
                    "auto_devops_enabled": True,
                },
                expected=(201,),
            )
        return group

    def ensure_group_member(self, group_id: int, user_id: int) -> None:
        member_path = f"groups/{group_id}/members/{user_id}"
        try:
            member = self.request("GET", member_path, expected=(200, 404))
        except GitLabError:
            member = None
        if member:
            if member.get("access_level", 0) < 50:
                self.request("PUT", member_path, body={"access_level": 50}, expected=(200,))
            return
        self.request(
            "POST",
            f"groups/{group_id}/members",
            body={"user_id": user_id, "access_level": 50},
            expected=(201,),
        )

    def find_project(self, full_path: str) -> dict[str, Any] | None:
        encoded = quote(full_path, safe="")
        try:
            return self.request("GET", f"projects/{encoded}", expected=(200, 404))
        except GitLabError:
            return None

    def ensure_project(self, group: dict[str, Any]) -> dict[str, Any]:
        full_path = f"{group['full_path']}/{self.settings.project_name}"
        project = self.find_project(full_path)
        if not project:
            project = self.request(
                "POST",
                "projects",
                body={
                    "name": self.settings.project_name,
                    "path": self.settings.project_name,
                    "namespace_id": group["id"],
                    "visibility": "public",
                    "import_url": self.settings.source_url,
                    "auto_devops_enabled": True,
                },
                expected=(201,),
            )
        elif not project.get("auto_devops_enabled"):
            project = self.request(
                "PUT",
                f"projects/{project['id']}",
                body={"auto_devops_enabled": True},
                expected=(200,),
            )
        return project

    def wait_for_import(self, project: dict[str, Any]) -> dict[str, Any]:
        if not project.get("import_url") and project.get("import_status") in (None, "none"):
            return project
        for _ in range(120):
            current = self.request("GET", f"projects/{project['id']}/import")
            status = current.get("import_status")
            if status == "finished":
                return current
            if status == "failed":
                raise GitLabError(f"Project import failed: {current.get('import_error') or current}")
            time.sleep(self.settings.poll_interval)
        raise GitLabError("Project import did not finish before the timeout expired.")

    def ensure_runner(self, project: dict[str, Any]) -> dict[str, Any]:
        tag_list = [tag for tag in self.settings.runner_tags.split(",") if tag]
        return self.request(
            "POST",
            "user/runners",
            body={
                "runner_type": "project_type",
                "project_id": project["id"],
                "description": self.settings.runner_description,
                "tag_list": tag_list,
                "run_untagged": True,
                "locked": False,
            },
            expected=(201,),
        )

    def wait_for_runner_online(self, project: dict[str, Any], attempts: int = 60) -> dict[str, Any]:
        for attempt in range(1, attempts + 1):
            runners = self.request("GET", f"projects/{project['id']}/runners")
            online = [r for r in runners if r.get("status") in ("online", "active")]
            if online:
                return online[0]
            if attempt == attempts:
                break
            time.sleep(self.settings.poll_interval)
        raise GitLabError("No online runner was found for the project before the timeout expired.")

    def trigger_pipeline(self, project: dict[str, Any]) -> dict[str, Any]:
        ref = project.get("default_branch") or "main"
        return self.request(
            "POST",
            f"projects/{project['id']}/pipeline",
            body={"ref": ref},
            expected=(201,),
        )

    def wait_for_pipeline(self, project: dict[str, Any], pipeline: dict[str, Any]) -> dict[str, Any]:
        for _ in range(120):
            current = self.request("GET", f"projects/{project['id']}/pipelines/{pipeline['id']}")
            status = current.get("status")
            if status in ("success", "failed", "canceled", "skipped"):
                return current
            time.sleep(self.settings.poll_interval)
        raise GitLabError("Pipeline did not finish before the timeout expired.")


def parse_args() -> Settings:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.getenv("GITLAB_URL", DEFAULT_URL))
    parser.add_argument("--token", default=os.getenv("GITLAB_TOKEN"))
    parser.add_argument("--username", default=os.getenv("GITLAB_USERNAME"))
    parser.add_argument("--name", default=os.getenv("GITLAB_NAME"))
    parser.add_argument("--email", default=os.getenv("GITLAB_EMAIL"))
    parser.add_argument("--password", default=os.getenv("GITLAB_PASSWORD"))
    parser.add_argument("--group", default=os.getenv("GITLAB_GROUP_NAME", DEFAULT_GROUP))
    parser.add_argument("--project", default=os.getenv("GITLAB_PROJECT_NAME", DEFAULT_PROJECT))
    parser.add_argument("--source-url", default=os.getenv("GITLAB_SOURCE_URL", DEFAULT_SOURCE))
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--poll-interval", type=int, default=5)
    parser.add_argument("--ensure-runner", action="store_true")
    parser.add_argument("--runner-description", default=os.getenv("GITLAB_RUNNER_DESCRIPTION", "devsecops-lab-runner"))
    parser.add_argument("--runner-tags", default=os.getenv("GITLAB_RUNNER_TAGS", "docker,lab"))
    parser.add_argument("--trigger-pipeline", action="store_true")
    args = parser.parse_args()
    if not args.token:
        parser.error("--token/GITLAB_TOKEN is required")
    if args.username and not all((args.name, args.email, args.password)):
        parser.error("--name, --email, and --password are required when creating a user")
    return Settings(
        base_url=args.url.rstrip("/") + "/",
        token=args.token,
        username=args.username,
        name=args.name,
        email=args.email,
        password=args.password,
        group_name=args.group,
        project_name=args.project,
        source_url=args.source_url,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
        ensure_runner=args.ensure_runner,
        runner_description=args.runner_description,
        runner_tags=args.runner_tags,
        trigger_pipeline=args.trigger_pipeline,
    )


def main() -> int:
    settings = parse_args()
    api = GitLabApi(settings)
    api.wait_until_ready()
    user = api.ensure_user()
    group = api.ensure_group()
    if user:
        api.ensure_group_member(group["id"], user["id"])
    project = api.ensure_project(group)
    imported = api.wait_for_import(project)
    print(f"GitLab URL: {project.get('web_url')}")
    print(f"Group: {group['full_path']}")
    print(f"Project: {project['path_with_namespace']}")
    print(f"Import status: {imported.get('import_status', 'none')}")
    print(f"Auto DevOps: {'enabled' if project.get('auto_devops_enabled', True) else 'disabled'}")

    if settings.ensure_runner:
        runner = api.ensure_runner(project)
        print(f"RUNNER_TOKEN={runner['token']}")

    if settings.trigger_pipeline:
        api.wait_for_runner_online(project)
        pipeline = api.trigger_pipeline(project)
        finished = api.wait_for_pipeline(project, pipeline)
        print(f"Pipeline: {finished.get('web_url')}")
        print(f"Pipeline status: {finished.get('status')}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GitLabError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
