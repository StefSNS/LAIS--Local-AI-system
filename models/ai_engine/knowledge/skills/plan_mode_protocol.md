# Plan Mode with Undo/Redo

## Overview
Plan Mode allows Omnis to propose a multi-step plan before execution, with full undo/redo capability.

## Usage

| Command | Action |
|---------|--------|
| `plan:` | Enter plan mode, describe what you want |
| `plan do` | Execute the proposed plan |
| `plan undo` | Undo the last plan |
| `plan redo` | Redo the last undone plan |
| `plan show` | Show current plan |

## Plan Format

```
Plan: [task description]
Steps:
1. [step 1]
2. [step 2]
3. [step 3]

Rollback (if undo needed):
1. [reverse step 1]
2. [reverse step 2]
```

## State Tracking

The system tracks:
- `current_plan` - Active plan
- `plan_history` - Completed plans
- `undo_stack` - Plans available for undo
- `redo_stack` - Plans available for redo

## Implementation

```python
from knowledge.skills.plan_mode import PlanMode

pm = PlanMode()

# Create plan
pm.create_plan("Add user authentication", steps=[
    "Create auth.py with login/register",
    "Add Flask routes for auth",
    "Create login.html template"
])

# Show plan
pm.show_plan()

# Execute
pm.execute_plan()

# Undo if needed
pm.undo()

# Redo if needed  
pm.redo()
```