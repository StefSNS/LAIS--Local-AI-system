# Skills System for Omnis AI

## Overview

Skills are reusable task templates that extend Omnis capabilities. Each skill is a folder with `SKILL.md` containing instructions.

## Skills Directory

**Location:** `knowledge/skills/`

## Creating a Skill

Create a folder with the skill name and add `SKILL.md`:

```
knowledge/skills/
├── code_review/
│   └── SKILL.md
├── test_generator/
│   └── SKILL.md
├── documentation/
│   └── SKILL.md
└── security_audit/
    └── SKILL.md
```

## Skill Format (SKILL.md)

```markdown
---
name: code_review
description: Performs code review with security and best practices checks
---

# Code Review Skill

You are a code reviewer. When activated:

1. Read the code files to review
2. Check for:
   - Security vulnerabilities
   - Code smells
   - Performance issues
   - Best practices violations
3. Provide constructive feedback
4. Suggest improvements

Output format:
- Issues found (severity: high/medium/low)
- Recommendations
- Code snippets for fixes
```

## Using Skills in Omnis

**Commands:**
- `skills:list` - Show all available skills
- `skills:use <name>` - Activate a skill
- `skills:create <name>` - Create new skill

## Available Skills

| Skill | Description |
|-------|-------------|
| code_review | Code review with security checks |
| test_gen | Generate unit tests |
| docs | Generate documentation |
| refactor | Refactor code suggestions |
| debug | Debug and fix issues |

## OpenCode Integration

Skills work with OpenCode when working on this project:
- Read: `knowledge/skills/<name>/SKILL.md`
- Automatically discovered from this directory