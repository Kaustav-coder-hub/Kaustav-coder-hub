
import os
import json
import html
import urllib.request
from datetime import datetime, timezone

USERNAME = "Kaustav-coder-hub"
README = "README.md"
API = "https://api.github.com"
MAX_ACTIVITY = 6

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Kaustav-GitHub-Profile",
}

token = os.environ.get("GITHUB_TOKEN")
if token:
    HEADERS["Authorization"] = f"Bearer {token}"


# Fixed project order. Repository names must match GitHub exactly.
# Note: Thermal and SamudraNet currently share the same URLs
# because those are the links supplied for both projects.
FEATURED_PROJECTS = [
    {
        "title": "Agent Reach — Self-Healing Internet Router",
        "description": (
            "An open-source AI routing system with semantic evaluation "
            "and adaptive fallback routing."
        ),
        "repos": ["Agent-Reach-Jisu-winner-opensource"],
    },
    {
        "title": "Thermal Satellite Image Super-Resolution",
        "description": (
            "Optical-guided super-resolution for thermal infrared "
            "satellite imagery, with separate frontend and backend."
        ),
        "repos": [
            "SIH-ISRO_Frontend_Hosting",
            "SIH-ISRO_BackEnd_Hosting",
        ],
    },
    {
        "title": "SamudraNet",
        "description": (
            "A project with separate frontend and backend repositories."
        ),
        "repos": [
            "SIH-ISRO_Frontend_Hosting",
            "SIH-ISRO_BackEnd_Hosting",
        ],
    },
    {
        "title": "VeriFrame",
        "description": (
            "Digital media provenance and verification using "
            "cryptographic fingerprints and related technologies."
        ),
        "repos": ["VeriFrame"],
    },
    {
        "title": "VocalEmotion",
        "description": (
            "Deep-learning-based speech emotion recognition."
        ),
        "repos": ["VocalEmotion"],
    },
    {
        "title": "ChatBot-History-Analyzer-2",
        "description": (
            "A chatbot project for general queries and browser-history "
            "analysis."
        ),
        "repos": ["ChatBot-Histroy-Annalyzer-2"],
    },
]


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
            f"README.md must contain exactly one pair of "
            f"{section} markers."
        )

    before, rest = content.split(start, 1)
    _, after = rest.split(end, 1)

    # Replace the entire section, never append to old generated cards.
    return f"{before}{start}\n{replacement}\n{end}{after}"


def fetch_repo(name):
    endpoint = f"/repos/{USERNAME}/{name}"

    try:
        return github_api(endpoint)
    except Exception as exc:
        print(f"Warning: could not fetch {name}: {exc}")
        return None


def render_project(project):
    repos = [
        repo
        for name in project["repos"]
        if (repo := fetch_repo(name)) is not None
    ]

    if not repos:
        print(f"Skipping unavailable project: {project['title']}")
        return None

    title = escape(project["title"])
    description = escape(project["description"])

    links = []
    languages = set()
    stars = 0
    forks = 0
    dates = []

    for repo in repos:
        repo_name = escape(repo["name"])
        repo_url = escape(repo["html_url"])

        links.append(
            f'<a href="{repo_url}">{repo_name}</a>'
        )

        language = repo.get("language")
        if language:
            languages.add(language)

        stars += repo.get("stargazers_count", 0)
        forks += repo.get("forks_count", 0)

        pushed = (repo.get("pushed_at") or "")[:10]
        if pushed:
            dates.append(pushed)

    language_text = escape(
        " / ".join(sorted(languages)) or "Multiple technologies"
    )
    repo_links = " · ".join(links)
    last_push = max(dates) if dates else "N/A"

    return f"""
<td width="50%" valign="top">
  <h3>🚀 {title}</h3>
  <p>{description}</p>
  <p><sub>{repo_links}</sub></p>
  <p><sub>{language_text} · ⭐ {stars} · 🍴 {forks}</sub>
  <br/><sub>Last push: {escape(last_push)}</sub></p>
</td>
""".strip()


def generate_projects():
    cards = []

    for project in FEATURED_PROJECTS:
        card = render_project(project)
        if card:
            cards.append(card)

    if not cards:
        return "<p>Featured project metadata is temporarily unavailable.</p>"

    rows = []

    for index in range(0, len(cards), 2):
        pair = cards[index:index + 2]

        if len(pair) == 1:
            pair.append('<td width="50%"></td>')

        rows.append("<tr>\n" + "\n".join(pair) + "\n</tr>")

    return "<table>\n" + "\n".join(rows) + "\n</table>"


def generate_activity():
    try:
        events = github_api(
            f"/users/{USERNAME}/events/public?per_page=100"
        )
    except Exception as exc:
        print(f"Warning: could not fetch public activity: {exc}")
        return "_Recent activity is temporarily unavailable._"

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

        if len(lines) >= MAX_ACTIVITY:
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
