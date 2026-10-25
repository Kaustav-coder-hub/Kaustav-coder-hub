#!/usr/bin/env python3
"""Update marked project and activity sections in the profile README using GitHub's public API."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

USERNAME = os.environ.get("GITHUB_USERNAME", "Kaustav-coder-hub")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
README_PATH = "README.md"
API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": f"{USERNAME}-profile-maintenance",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def get_json(path):
    request = urllib.request.Request(API + path, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def replace_section(readme, name, content):
    start = f"<!-- {name}:START -->"
    end = f"<!-- {name}:END -->"
    if start not in readme or end not in readme:
        raise ValueError(f"Missing markers for {name} section in README.md")
    before, remainder = readme.split(start, 1)
    _, after = remainder.split(end, 1)
    return before + start + "\n" + content.rstrip() + "\n" + end + after


def clean(text):
    return (text or "").replace("\r", " ").replace("\n", " ").strip()


def update_projects():
    repos = get_json(f"/users/{urllib.parse.quote(USERNAME)}/repos?sort=updated&per_page=100&type=owner")
    repos = [
        r for r in repos
        if not r.get("fork") and not r.get("archived") and not r.get("private")
        and r.get("name", "").lower() != USERNAME.lower()
    ]
    repos.sort(key=lambda r: (r.get("stargazers_count", 0), r.get("pushed_at") or ""), reverse=True)
    selected = repos[:6]
    if not selected:
        return "_No eligible public repositories were found yet. Add public repositories with useful descriptions to populate this section._"
    lines = []
    for repo in selected:
        name = clean(repo.get("name"))
        url = repo.get("html_url", "")
        description = clean(repo.get("description")) or "Public repository; description not added yet."
        language = clean(repo.get("language"))
        meta = f" · `{language}`" if language else ""
        lines.append(f"- **[{name}]({url})**{meta} — {description}")
    return "\n".join(lines)


def update_activity():
    events = get_json(f"/users/{urllib.parse.quote(USERNAME)}/events/public?per_page=100")
    lines = []
    for event in events:
        event_type = event.get("type", "")
        repo = event.get("repo", {}).get("name", "")
        created = event.get("created_at", "")
        if not repo or not created:
            continue
        date = created[:10]
        repo_url = f"https://github.com/{repo}"
        if event_type == "PushEvent":
            count = len(event.get("payload", {}).get("commits", []))
            action = f"pushed {count} commit(s) to"
        elif event_type == "PullRequestEvent":
            action = event.get("payload", {}).get("action", "updated") + " a pull request in"
        elif event_type == "IssuesEvent":
            action = event.get("payload", {}).get("action", "updated") + " an issue in"
        elif event_type == "CreateEvent":
            ref_type = event.get("payload", {}).get("ref_type", "resource")
            action = f"created {ref_type} in"
        elif event_type == "WatchEvent":
            action = "starred"
        elif event_type == "ForkEvent":
            action = "forked"
        elif event_type == "ReleaseEvent":
            action = "published a release in"
        else:
            continue
        lines.append(f"- `{date}` — {action} [{repo}]({repo_url})")
        if len(lines) == 8:
            break
    if not lines:
        return "_No recent public events were returned by GitHub. This is normal if you have been working privately or have been inactive._"
    return "\n".join(lines)


def main():
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()
    readme = replace_section(readme, "PROJECTS", update_projects())
    readme = replace_section(readme, "ACTIVITY", update_activity())
    with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(readme)
    print(f"Updated profile sections for {USERNAME} at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
