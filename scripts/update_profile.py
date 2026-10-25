
import os
import json
import html
import urllib.request
from datetime import datetime, timezone

USERNAME = "Kaustav-coder-hub"
README = "README.md"
MAX_PROJECTS = 6

API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Kaustav-GitHub-Profile",
}

token = os.environ.get("GITHUB_TOKEN")
if token:
    HEADERS["Authorization"] = f"Bearer {token}"

# Order matters: projects that match these repository names
# are shown first, regardless of stars or last-push date.
PREFERRED_REPOS = [
    "Agent-Reach-Jisu-winner-opensource",
    "VeriFrame",
    "DIXY",
    "VocalEmotion",
    "PreClick",
    "DeepfakeDetection",
]

# Fill remaining slots using this fallback order:
# more stars first, then more recently pushed.
def github_api(endpoint):
    request = urllib.request.Request(
        f"{API}{endpoint}",
        headers=HEADERS,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def escape(value):
    return html.escape(str(value or ""), quote=True)


def replace_section(content, section, replacement):
    start = f"<!-- {section}:START -->"
    end = f"<!-- {section}:END -->"

    if content.count(start) != 1 or content.count(end) != 1:
        raise ValueError(
            f"Expected exactly one pair of {section} markers in README.md"
        )

    before, rest = content.split(start, 1)
    _, after = rest.split(end, 1)

    # Replace EVERYTHING between the markers.
    # This prevents duplicate cards/tables on subsequent runs.
    return f"{before}{start}\n{replacement}\n{end}{after}"


def fetch_repositories():
    repositories = github_api(
        f"/users/{USERNAME}/repos?type=owner&sort=updated&per_page=100"
    )

    # Only public, original, active repositories.
    repositories = [
        repo for repo in repositories
        if not repo.get("fork", False)
        and not repo.get("archived", False)
        and not repo.get("private", False)
        and repo.get("name", "").lower() != USERNAME.lower()
    ]

    # Prevent duplicates even if the API data contains repeated entries.
    unique = {}
    for repo in repositories:
        unique.setdefault(repo["name"].lower(), repo)

    return list(unique.values())


def select_projects(repositories):
    by_name = {
        repo["name"].lower(): repo
        for repo in repositories
    }

    selected = []
    used = set()

    # First: explicitly prioritized projects, in the exact order above.
    for name in PREFERRED_REPOS:
        repo = by_name.get(name.lower())
        if repo and repo["name"].lower() not in used:
            selected.append(repo)
            used.add(repo["name"].lower())

    # Second: fill remaining places using stars, then recent activity.
    remaining = [
        repo for repo in repositories
        if repo["name"].lower() not in used
    ]

    remaining.sort(
        key=lambda repo: (
            repo.get("stargazers_count", 0),
            repo.get("pushed_at") or "",
        ),
        reverse=True,
    )

    selected.extend(remaining[:max(0, MAX_PROJECTS - len(selected))])
    return selected[:MAX_PROJECTS]


def render_project(repo):
    name = escape(repo.get("name"))
    url = escape(repo.get("html_url"))
    description = escape(
        repo.get("description") or "Project description coming soon."
    )
    language = escape(repo.get("language") or "Multiple technologies")
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    pushed = escape((repo.get("pushed_at") or "")[:10])

    last_push = (
        f"<br/><sub>Last push: {pushed}</sub>"
        if pushed else ""
    )

    return f"""
<td width="50%" valign="top">
  <h3>🚀 <a href="{url}">{name}</a></h3>
  <p>{description}</p>
  <p><sub>{language} · ⭐ {stars} · 🍴 {forks}{last_push}</sub></p>
</td>
""".strip()


def generate_projects():
    repositories = fetch_repositories()
    selected = select_projects(repositories)

    if not selected:
        return "<p>No eligible public repositories were found.</p>"

    rows = []

    for index in range(0, len(selected), 2):
        pair = selected[index:index + 2]
        cells = [render_project(repo) for repo in pair]

        if len(cells) == 1:
            cells.append('<td width="50%"></td>')

        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")

    return "<table>\n" + "\n".join(rows) + "\n</table>"


def generate_activity():
    events = github_api(
        f"/users/{USERNAME}/events/public?per_page=100"
    )

    lines = []

    for event in events:
        kind = event.get("type")
        repo = event.get("repo", {}).get("name")
        date = (event.get("created_at") or "")[:10]

        if not repo or not date:
            continue

        if kind == "PushEvent":
            count = len(event.get("payload", {}).get("commits", []))
            action = f"pushed {count} commit(s) to"
        elif kind == "PullRequestEvent":
            action = "updated a pull request in"
        elif kind == "IssuesEvent":
            action = "updated an issue in"
        elif kind == "CreateEvent":
            action = "created a resource in"
        elif kind == "ReleaseEvent":
            action = "published a release in"
        else:
            continue

        url = f"https://github.com/{repo}"
        lines.append(
            f'- `{date}` — {action} '
            f'[{escape(repo)}]({url})'
        )

        if len(lines) >= 6:
            break

    return "\n".join(lines) if lines else (
        "_No recent public activity is available._"
    )


def main():
    with open(README, encoding="utf-8") as file:
        readme = file.read()

    projects = generate_projects()
    activity = generate_activity()

    readme = replace_section(readme, "PROJECTS", projects)
    readme = replace_section(readme, "ACTIVITY", activity)

    with open(README, "w", encoding="utf-8", newline="\n") as file:
        file.write(readme)

    print(
        "Profile updated successfully:",
        datetime.now(timezone.utc).isoformat(),
    )


if __name__ == "__main__":
    main()
