import os
import json
import html
import urllib.request
from datetime import datetime, timezone

USERNAME = "Kaustav-coder-hub"
README = "README.md"

API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Kaustav-GitHub-Profile"
}

token = os.environ.get("GITHUB_TOKEN")
if token:
    HEADERS["Authorization"] = f"Bearer {token}"


def github_api(endpoint):
    request = urllib.request.Request(
        f"{API}{endpoint}",
        headers=HEADERS
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

    return (
        before + start + "\n"
        + replacement + "\n"
        + end + after
    )


def generate_projects():
    repositories = github_api(
        f"/users/{USERNAME}/repos?type=owner&sort=updated&per_page=100"
    )

    # Keep public, original repositories.
    repositories = [
        repo for repo in repositories
        if not repo["fork"]
        and not repo["archived"]
        and not repo["private"]
        and repo["name"].lower() != USERNAME.lower()
    ]

    # Put preferred projects first if their actual repository names match.
    preferred = [
        "Agent-Reach",
        "VeriFrame",
        "DIXY",
        "VocalEmotion",
        "DeepfakeDetection",
        "PreClick",
    ]

    by_name = {
        repo["name"].lower(): repo
        for repo in repositories
    }

    selected = []
    used = set()

    for name in preferred:
        repo = by_name.get(name.lower())
        if repo and repo["name"] not in used:
            selected.append(repo)
            used.add(repo["name"])

    remaining = [
        repo for repo in repositories
        if repo["name"] not in used
    ]

    remaining.sort(
        key=lambda repo: (
            repo.get("stargazers_count", 0),
            repo.get("pushed_at") or ""
        ),
        reverse=True
    )

    selected.extend(remaining[:max(0, 6 - len(selected))])
    selected = selected[:6]

    if not selected:
        return "<p>No eligible public repositories were found.</p>"

    cards = []

    for repo in selected:
        name = escape(repo["name"])
        url = escape(repo["html_url"])
        description = escape(
            repo.get("description") or
            "Add a repository description on GitHub."
        )
        language = escape(repo.get("language") or "Multiple technologies")
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)

        pushed = (repo.get("pushed_at") or "")[:10]
        updated = (
            f"<br/><sub>Last push: {escape(pushed)}</sub>"
            if pushed else ""
        )

        cards.append(f"""
<td width="50%" valign="top">
  <h3>🚀 <a href="{url}">{name}</a></h3>
  <p>{description}</p>
  <p>
    <sub>{language} · ⭐ {stars} · 🍴 {forks}</sub>
    {updated}
  </p>
</td>
""".strip())

    rows = []

    for index in range(0, len(cards), 2):
        pair = cards[index:index + 2]

        if len(pair) == 1:
            pair.append('<td width="50%"></td>')

        rows.append(
            "<tr>\n" + "\n".join(pair) + "\n</tr>"
        )

    return (
        '<table>\n'
        + "\n".join(rows)
        + '\n</table>'
    )


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
        datetime.now(timezone.utc).isoformat()
    )


if __name__ == "__main__":
    main()