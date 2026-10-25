#!/usr/bin/env python3
"""Refresh the profile README's project cards and recent public activity."""
import html
import json
import os
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

# Repositories to prefer when they exist. Remaining slots are filled using
# actual public repository metadata (stars, then most recently pushed).
FEATURED_FIRST = [
    "agent-reach",
    "veriframe",
    "preclick",
    "dixy",
    "vocalemotion",
    "deepfakedetection",
    "waste-management-system",
    "autocv--resume-scoring-system",
    "chatbot-history-analyzer",
    "gemmaforge",
]


def get_json(path):
    request = urllib.request.Request(API + path, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def replace_section(readme, name, content):
    start = f"<!-- {name}:START -->"
    end = f"<!-- {name}:END -->"
    if readme.count(start) != 1 or readme.count(end) != 1:
        raise ValueError(f"Expected exactly one START and END marker for {name} in README.md")
    before, remainder = readme.split(start, 1)
    _, after = remainder.split(end, 1)
    return before + start + "\n" + content.rstrip() + "\n" + end + after


def clean(text):
    return (text or "").replace("\r", " ").replace("\n", " ").strip()


def esc(value):
    return html.escape(str(value or ""), quote=True)


def repo_key(repo):
    return repo.get("name", "").lower().replace("_", "-").replace(" ", "-")


def project_cards():
    repos = get_json(
        f"/users/{urllib.parse.quote(USERNAME)}/repos?sort=updated&per_page=100&type=owner"
    )
    repos = [
        repo for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and not repo.get("private")
        and repo.get("name", "").lower() != USERNAME.lower()
    ]
    by_key = {repo_key(repo): repo for repo in repos}
    selected = []
    seen = set()

    for preferred in FEATURED_FIRST:
        candidate = by_key.get(preferred.lower().replace("_", "-"))
        if candidate and candidate["name"] not in seen:
            selected.append(candidate)
            seen.add(candidate["name"])

    remaining = [repo for repo in repos if repo["name"] not in seen]
    remaining.sort(
        key=lambda repo: (repo.get("stargazers_count", 0), repo.get("pushed_at") or ""),
        reverse=True,
    )
    selected.extend(remaining[:max(0, 6 - len(selected))])
    selected = selected[:6]

    if not selected:
        return "<p><em>No eligible public repositories were found yet.</em></p>"

    cells = []
    for repo in selected:
        name = esc(repo.get("name"))
        url = esc(repo.get("html_url"))
        description = esc(clean(repo.get("description")) or "Description coming soon.")
        language = esc(repo.get("language") or "Repository")
        stars = int(repo.get("stargazers_count") or 0)
        forks = int(repo.get("forks_count") or 0)
        updated = (repo.get("pushed_at") or "")[:10]
        metadata = f"<sub>{language} &nbsp;·&nbsp; ★ {stars} &nbsp;·&nbsp; Forks {forks}</sub>"
        if updated:
            metadata += f"<br/><sub>Last push: {esc(updated)}</sub>"
        cells.append(
            "<td width=\"50%\" valign=\"top\">"
            f"<h3>🔹 <a href=\"{url}\">{name}</a></h3>"
            f"<p>{description}</p>"
            f"<p>{metadata}</p>"
            "</td>"
        )

    rows = []
    for index in range(0, len(cells), 2):
        row_cells = cells[index:index + 2]
        if len(row_cells) == 1:
            row_cells.append("<td width=\"50%\" valign=\"top\"></td>")
        rows.append("<tr>\n" + "\n".join(row_cells) + "\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def recent_activity():
    events = get_json(
        f"/users/{urllib.parse.quote(USERNAME)}/events/public?per_page=100"
    )
    lines = []
    for event in events:
        event_type = event.get("type", "")
        repo = event.get("repo", {}).get("name", "")
        created = event.get("created_at", "")
        if not repo or not created:
            continue
        repo_url = "https://github.com/" + repo
        date = created[:10]
        payload = event.get("payload", {})
        if event_type == "PushEvent":
            count = len(payload.get("commits", []))
            action = f"pushed {count} commit(s) to"
        elif event_type == "PullRequestEvent":
            action = clean(payload.get("action") or "updated") + " a pull request in"
        elif event_type == "IssuesEvent":
            action = clean(payload.get("action") or "updated") + " an issue in"
        elif event_type == "CreateEvent":
            action = "created " + clean(payload.get("ref_type") or "resource") + " in"
        elif event_type == "WatchEvent":
            action = "starred"
        elif event_type == "ForkEvent":
            action = "forked"
        elif event_type == "ReleaseEvent":
            action = "published a release in"
        else:
            continue
        lines.append(f"- `{date}` — {action} [{repo}]({repo_url})")
        if len(lines) >= 6:
            break
    if not lines:
        return "_No recent public events were returned by GitHub. Private activity is not shown._"
    return "\n".join(lines)


def main():
    with open(README_PATH, "r", encoding="utf-8") as file:
        readme = file.read()
    readme = replace_section(readme, "PROJECTS", project_cards())
    readme = replace_section(readme, "ACTIVITY", recent_activity())
    with open(README_PATH, "w", encoding="utf-8", newline="\n") as file:
        file.write(readme)
    print(f"Updated profile for {USERNAME} at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
