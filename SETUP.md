# Kaustav's GitHub Profile Kit

This kit is designed for the special profile repository `Kaustav-coder-hub/Kaustav-coder-hub`.

## Install it

1. Open https://github.com/Kaustav-coder-hub.
2. Create a repository named **exactly** `Kaustav-coder-hub` if it does not already exist. GitHub uses a repository with the same name as your username for the profile README.
3. If that repository already has a README or files, download/clone it and **back it up first**. Do not overwrite existing work blindly.
4. Copy `README.md`, `.gitignore`, `scripts/`, and `.github/` from this kit into the root of the profile repository.
5. Commit and push to the repository's default branch (the workflow currently expects `main`; adjust the branch filters if yours differs).
6. Open the repository's **Actions** tab. Enable Actions if prompted, then run **Profile maintenance** with **Run workflow**.
7. Check the workflow run and the rendered profile page.

## What the workflows do

- **Profile maintenance** runs weekly, on demand, and after relevant changes to the default branch. It uses GitHub's public API to populate the Projects and Recent GitHub activity sections with public repository/event data. It commits only if README changes.
- **README quality checks** validates the README markers and Python syntax on pushes and pull requests.
- GitHub statistics cards are embedded in the README and render dynamically from the external `github-readme-stats` service. They are not copied into your repository and may occasionally be rate-limited or unavailable.
- Project discovery is automatic: it selects up to six non-forked, non-archived public repositories owned by the account, sorted by stars and last push. Add accurate descriptions to repositories so the cards read well.

## Important notes

- The automation does not invent repository URLs, stars, languages, or activity. It reads the public GitHub API.
- The activity API only exposes recent **public** events; private work will not appear.
- GitHub scheduled workflows can be delayed during high load and are not guaranteed to run at the exact minute.
- `GITHUB_TOKEN` is supplied automatically by GitHub Actions; no personal access token or secret is required for this kit.
- The workflow needs repository **contents: write** permission to commit refreshed README sections. If organization or repository policies block this permission, the update step will fail.
- The workflow uses major-version action tags for readability. For a hardened supply-chain setup, pin each action to a reviewed full commit SHA.
- The README's skills section is a starter list. Remove anything you cannot confidently demonstrate in your own work.

## Troubleshooting

- If the scheduled workflow cannot push, go to **Settings → Actions → General → Workflow permissions** and allow read/write permissions if your account policy permits it.
- If the default branch is `master`, update `branches: [main]` in both workflow files.
- If a repository has no description, add one in that repository's About panel.
- If the profile README does not appear, confirm the repository name matches your username exactly and that `README.md` is at the repository root.
