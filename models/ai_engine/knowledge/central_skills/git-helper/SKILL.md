---
name: git-helper
description: Git workflows, commits, branches, merging, and GitHub operations. Use when user asks about git, commits, branches, merges, or GitHub.
---

# Git Helper Skill

## When to Use
- User says "commit", "push", "pull", "merge"
- User asks about branches, tags, releases
- User has merge conflicts
- User wants to undo git changes
- User mentions GitHub, PRs, issues

## Essential Git Commands

### Daily Workflow
```bash
# Check status
git status
git diff

# Stage and commit
git add <file>
git add .                    # Stage all
git commit -m "feat: add login"

# Push/pull
git push origin main
git pull origin main
```

### Branching
```bash
git branch feature-x           # Create branch
git checkout feature-x         # Switch to branch
git checkout -b hotfix        # Create + switch
git branch -d old-branch      # Delete local branch
git push origin --delete branch # Delete remote
```

### Undoing Changes
| Command | Effect |
|---------|--------|
| `git restore <file>` | Discard unstaged changes |
| `git restore --staged <file>` | Unstage file |
| `git revert <commit>` | Revert commit (safe) |
| `git reset --soft HEAD~1` | Undo commit, keep changes |
| `git reset --hard HEAD~1` | Undo commit + changes (dangerous) |

## GitHub Operations

### Pull Request Process
1. Push branch → Go to GitHub → Create PR
2. Add description, link issues
3. Request review
4. Address feedback
5. Merge (merge/rebase/squash)

### GitHub CLI (gh)
```bash
gh pr create --title "Fix bug" --body "Description"
gh pr list
gh issue create --title "Bug" --body "Details"
gh release create v1.0
```

## Merge Conflict Resolution
1. `git status` → see conflicted files
2. Edit files (remove `<<<<<<`, `======`, `>>>>>>>`)
3. `git add <fixed-file>`
4. `git commit` (or `git rebase --continue` if rebasing)

## Commit Message Convention
```
feat: add user login
fix: resolve null pointer
docs: update README
refactor: simplify auth logic
test: add unit tests for API
chore: update dependencies
```

## Common Scenarios

### Fix Failed Push
```bash
git pull --rebase origin main
git push origin feature-x
```

### Stash Changes
```bash
git stash              # Stash changes
git stash list          # List stashes
git stash pop          # Apply + remove stash
```

### Sync with Remote
```bash
git fetch origin
git rebase origin/main
```

## Best Practices
- Write meaningful commit messages
- Keep commits atomic (one concern)
- Pull before pushing
- Use `.gitignore` for unnecessary files
- Protect main branch (require PR reviews)
- Sign commits with GPG (security)
