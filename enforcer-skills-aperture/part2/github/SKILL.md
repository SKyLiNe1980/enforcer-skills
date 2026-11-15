---
name: github
description: Complete GitHub workflow — auth setup, repo management, PR lifecycle, code review, and issue triage via gh CLI or git+curl fallback.
version: 2.0.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Git, Pull-Requests, Issues, Code-Review, CI/CD, Repositories]
    consolidates: [github-auth, github-code-review, github-issues, github-pr-workflow, github-repo-management]
---

# GitHub Workflow

Complete GitHub operations from authentication through pull request lifecycle, code review, issue management, and repository administration. Every section supports two paths: **`gh` CLI** (preferred, richer) and **`git` + `curl`** (universal fallback, no installation needed).

## Quick Auth Detection

Run this at the start of any GitHub workflow to determine which path to use:

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

A convenience script is at `scripts/gh-env.sh` — source it for a one-step setup.

---

## 1. Authentication

### HTTPS with Personal Access Token (Recommended)

Works everywhere, no sudo needed. The user generates a token at https://github.com/settings/tokens with `repo` + `workflow` scopes.

```bash
git config --global credential.helper store
git config --global user.name "Name"
git config --global user.email "email@example.com"
# First git operation triggers credential prompt — use token as password
git ls-remote https://github.com/<user>/<repo>.git
```

### SSH Key Authentication

```bash
ssh-keygen -t ed25519 -C "email@example.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub  # Add to https://github.com/settings/keys
ssh -T git@github.com
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### gh CLI Authentication

```bash
# Browser (desktop)
gh auth login

# Token (headless)
echo "<TOKEN>" | gh auth login --with-token
gh auth setup-git
```

### Token Extraction from Git Credentials

```bash
grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | Use personal access token as password |
| `Permission to X denied` | Token may lack `repo` scope |
| `Authentication failed` | Run `git credential reject` then re-auth |
| Credentials not persisting | Check `git config --global credential.helper` |
| Multiple GitHub accounts | Per-repo credential URLs or SSH host aliases |

---

## 2. Repository Management

### Clone

```bash
# Pure git
git clone https://github.com/owner/repo.git
git clone --depth 1 https://github.com/owner/repo.git  # shallow

# gh shorthand
gh repo clone owner/repo
```

### Create

```bash
# gh
gh repo create my-project --public --clone
gh repo create my-project --private --description "desc" --license MIT --clone

# curl
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name": "my-project", "private": false, "auto_init": true}'
```

Push existing directory:
```bash
cd /path/to/project && git init && git add . && git commit -m "Initial commit"
git remote add origin https://github.com/$GH_USER/my-project.git
git push -u origin main
```

### Fork

```bash
# gh
gh repo fork owner/repo --clone

# curl + git
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/forks
sleep 3 && git clone https://github.com/$GH_USER/repo.git
cd repo && git remote add upstream https://github.com/owner/repo.git
```

Keep in sync: `git fetch upstream && git checkout main && git merge upstream/main && git push origin main`

### Repo Info

```bash
gh repo view owner/repo
# curl: GET /repos/$OWNER/$REPO
```

### Releases

```bash
# gh
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release list

# curl: POST /repos/$OWNER/$REPO/releases
```

### Secrets (GitHub Actions)

```bash
gh secret set API_KEY --body "value"
gh secret list
gh secret delete API_KEY
# curl: requires encryption with repo's public key (PyNaCl)
```

### Branch Protection

```bash
curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{"required_status_checks": {"strict": true, "contexts": ["ci/test"]},
       "required_pull_request_reviews": {"required_approving_review_count": 1}}'
```

### Gists

```bash
gh gist create script.py --public --desc "Useful script"
# curl: POST /gists
```

---

## 3. Pull Request Workflow

### Branch

```bash
git fetch origin && git checkout main && git pull origin main
git checkout -b feat/description
```

Naming: `feat/`, `fix/`, `refactor/`, `docs/`, `ci/`

### Commit (Conventional Commits)

```bash
git add <files>
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes"
```

Format: `type(scope): short description` followed by body. Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`. See `references/conventional-commits.md`.

### Push & Create PR

```bash
git push -u origin HEAD

# gh
gh pr create --title "feat: ..." --body "## Summary..." [--draft] [--reviewer user]

# curl
BRANCH=$(git branch --show-current)
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{\"title\": \"...\", \"body\": \"...\", \"head\": \"$BRANCH\", \"base\": \"main\"}"
```

PR body templates: `templates/pr-body-bugfix.md`, `templates/pr-body-feature.md`.

### Monitor CI

```bash
# gh
gh pr checks [--watch]

# curl: GET /repos/$OWNER/$REPO/commits/$SHA/status
# curl: GET /repos/$OWNER/$REPO/commits/$SHA/check-runs
```

### Auto-Fix CI Failures

1. Check CI status → identify failures
2. Get failure logs (gh: `gh run view <ID> --log-failed`, curl: download logs zip)
3. Fix with `patch`/`write_file`
4. `git add . && git commit -m "fix: ..." && git push`
5. Re-check status; repeat up to 3 attempts

See `references/ci-troubleshooting.md` for detailed CI debugging.

### Merge

```bash
# gh
gh pr merge --squash --delete-branch
gh pr merge --auto --squash --delete-branch

# curl: PUT /repos/$OWNER/$REPO/pulls/$PR/merge
# Methods: "merge", "squash", "rebase"

# Clean up
git checkout main && git pull origin main && git branch -d $BRANCH
```

### Quick Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List PRs | `gh pr list --author @me` | GET `/repos/o/r/pulls` |
| View diff | `gh pr diff` | `git diff main...HEAD` (local) |
| Add comment | `gh pr comment N --body "..."` | POST `/issues/N/comments` |
| Request review | `gh pr edit N --add-reviewer user` | POST `/pulls/N/requested_reviewers` |
| Close PR | `gh pr close N` | PATCH `/pulls/N` |
| Check out PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |

---

## 4. Code Review

### Local (Pre-Push)

```bash
# Scope
git diff main...HEAD --stat
git log main..HEAD --oneline

# Full diff
git diff main...HEAD

# Quick checks
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|debugger"
git diff main...HEAD | grep -in "password\|secret\|api_key\|token.*="
git diff main...HEAD | grep -n "<<<<<<\|>>>>>>\|======="
```

### PR Review

```bash
# gh
gh pr view 123
gh pr diff 123 [--name-only]
gh pr checks 123

# Check out locally
git fetch origin pull/123/head:pr-123 && git checkout pr-123
# Now use read_file, search_files, run tests
```

### Review Checklist

- **Correctness**: Does the code do what it claims? Edge cases handled?
- **Security**: No hardcoded secrets, input validation, no SQL injection/XSS
- **Code Quality**: Clear naming, no unnecessary complexity, DRY
- **Testing**: New code paths tested? Happy + error paths covered?
- **Performance**: No N+1 queries, appropriate caching
- **Documentation**: Public APIs documented, README updated

### Output Format

Use the review output template at `references/review-output-template.md`. Structure: Critical → Warnings → Suggestions → Looks Good.

### Posting Reviews

```bash
# Approve
gh pr review 123 --approve --body "LGTM!"

# Request changes
gh pr review 123 --request-changes --body "See inline comments."

# Comment
gh pr review 123 --comment --body "Suggestions, nothing blocking."
```

**Inline comments (curl — atomic review with multiple inline comments):**

```bash
HEAD_SHA=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")

curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER/reviews \
  -d "{\"commit_id\": \"$HEAD_SHA\", \"event\": \"REQUEST_CHANGES\",
    \"body\": \"## Review\\n\\nFound 2 issues.\",
    \"comments\": [
      {\"path\": \"src/auth.py\", \"line\": 45, \"body\": \"🔴 **Critical:** SQL injection.\"},
      {\"path\": \"src/models.py\", \"line\": 23, \"body\": \"⚠️ Hash passwords.\"}
    ]}"
```

### Complete PR Review Workflow

1. Set up environment (auth detection)
2. `gh pr view N` or curl to get PR metadata + changed files
3. `git fetch origin pull/N/head:pr-N && git checkout pr-N`
4. `git diff main...HEAD` — full diff review
5. Run tests if available: `python -m pytest` or equivalent
6. Apply review checklist
7. Post review with inline comments
8. Also post a top-level summary comment
9. `git checkout main && git branch -D pr-N`

---

## 5. Issue Management

### View

```bash
# gh
gh issue list [--state open] [--label "bug"] [--assignee @me]
gh issue view 42

# curl
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open&per_page=20"
```

### Create

```bash
# gh
gh issue create --title "Login redirect ignores ?next=" \
  --body "## Description..." --label "bug,backend" --assignee "username"

# curl: POST /repos/$OWNER/$REPO/issues
```

Templates: `templates/bug-report.md`, `templates/feature-request.md`.

### Manage

```bash
# Labels
gh issue edit 42 --add-label "priority:high,bug"
gh issue edit 42 --remove-label "needs-triage"

# Assign
gh issue edit 42 --add-assignee username

# Comment
gh issue comment 42 --body "Investigated — root cause in auth middleware."

# Close/Reopen
gh issue close 42 [--reason "not planned"]
gh issue reopen 42
```

Linking to PRs: include `Closes #42` / `Fixes #42` / `Resolves #42` in PR body.

### Triage Workflow

1. List untriaged: `gh issue list --label "needs-triage" --state open`
2. Read and categorize each issue
3. Apply labels + priority
4. Assign if clear
5. Comment with triage notes

### Bulk Operations

```bash
# Close all with a label
gh issue list --label "wontfix" --json number --jq '.[].number' | \
  xargs -I {} gh issue close {} --reason "not planned"
```

### Quick Reference

| Action | gh | curl endpoint |
|--------|-----|--------------|
| List | `gh issue list` | GET `/repos/{o}/{r}/issues` |
| View | `gh issue view N` | GET `/repos/{o}/{r}/issues/N` |
| Create | `gh issue create ...` | POST `/repos/{o}/{r}/issues` |
| Add labels | `gh issue edit N --add-label ...` | POST `/repos/{o}/{r}/issues/N/labels` |
| Assign | `gh issue edit N --add-assignee ...` | POST `/repos/{o}/{r}/issues/N/assignees` |
| Comment | `gh issue comment N --body ...` | POST `/repos/{o}/{r}/issues/N/comments` |
| Close | `gh issue close N` | PATCH `/repos/{o}/{r}/issues/N` |
| Search | `gh issue list --search "..."` | GET `/search/issues?q=...` |

---

## Common Pitfalls

- **`gh: command not found` + no sudo** — use git + curl fallbacks throughout; no installation needed
- **Token scope missing** — needs `repo` (full access) + `workflow` (Actions) scopes
- **Stale cached credentials** — run `git credential reject` then re-authenticate
- **PR auto-merge requires repo settings** — enable in repo settings before using `gh pr merge --auto`
- **GitHub API returns PRs in `/issues` endpoint** — filter with `'pull_request' not in item`
- **Secrets via curl require encryption** — `gh secret set` is dramatically simpler; if unavailable, install gh for just secrets ops
- **Branch naming matters** — CI workflows may trigger on branch patterns; use conventional prefixes

## Supporting Files

- `scripts/gh-env.sh` — One-step auth environment detection
- `references/review-output-template.md` — Code review output format
- `references/ci-troubleshooting.md` — CI failure diagnosis patterns
- `references/conventional-commits.md` — Conventional commit format reference
- `references/github-api-cheatsheet.md` — Full GitHub API endpoint reference
- `templates/pr-body-bugfix.md` — Bugfix PR body template
- `templates/pr-body-feature.md` — Feature PR body template
- `templates/bug-report.md` — Bug report issue template
- `templates/feature-request.md` — Feature request issue template
