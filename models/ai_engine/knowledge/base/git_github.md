# Git and GitHub (from roadmap.sh)

Source: https://roadmap.sh/git-github

## Git Basics

### Essential Commands
| Command | Purpose |
|---------|----------|
| `git init` | Initialize repo |
| `git clone <url>` | Clone remote repo |
| `git add <file>` | Stage changes |
| `git commit -m "msg"` | Commit staged changes |
| `git status` | Check working tree |
| `git log --oneline` | View commit history |
| `git diff` | Show unstaged changes |

### Branching
```bash
git branch feature-x        # Create branch
git checkout feature-x      # Switch to branch
git checkout -b hotfix    # Create + switch
git merge feature-x         # Merge into current
git rebase main            # Rebase onto main
```

### Undoing Changes
| Command | Effect |
|---------|--------|
| `git restore <file>` | Discard unstaged changes |
| `git restore --staged <file>` | Unstage file |
| `git revert <commit>` | Revert commit (safe) |
| `git reset --soft HEAD~1` | Undo commit, keep changes |
| `git reset --hard HEAD~1` | Undo commit + changes (dangerous) |

## GitHub Workflow

### Pull Request (PR) Process
1. Create branch → commit → push
2. Open PR on GitHub
3. Code review → address feedback
4. Merge (merge/rebase/squash)

### GitHub Features
- **Actions**: CI/CD pipelines
- **Issues**: Bug tracking, feature requests
- **Projects**: Kanban boards
- **Releases**: Tagged versions
- **Wiki**: Documentation
- **Pages**: Static site hosting

## Best Practices
- Write meaningful commit messages
- Keep commits atomic (one concern)
- Pull before pushing (avoid conflicts)
- Use `.gitignore` for unnecessary files
- Sign commits with GPG (security)
- Protect main branch (require PR reviews)

## Common Git Scenarios

### Fix Failed Push
```bash
git pull --rebase origin main
git push origin feature-x
```

### Resolve Merge Conflict
1. `git status` → see conflicted files
2. Edit files (remove `<<<<<<`, `======`, `>>>>>>>`)
3. `git add <fixed-file>`
4. `git commit` (or `git rebase --continue` if rebasing)

### Stash Changes
```bash
git stash              # Stash uncommitted changes
git stash list          # List stashes
git stash pop          # Apply + remove stash
git stash drop         # Delete stash
```

## Collaboration Patterns
- **Fork & PR**: External contributors fork → PR to upstream
- **Feature branches**: Each feature in its own branch
- **GitFlow**: main → develop → feature/hotfix/release
- **Trunk-based**: Short-lived branches, merge to main frequently
