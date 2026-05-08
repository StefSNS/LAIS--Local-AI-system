---
name: plan-mode
description: Create execution plans with steps and undo capability. Use when user asks for plan mode, wants to see steps before execution, or asks to undo/redo.
---

# Plan Mode Skill

## When to Use

- User says "plan mode" or "enter plan mode"
- User asks "what would you do" before execution
- User asks to "show plan" or "show steps"
- User asks to "undo" or "redo"

## Plan Flow

1. **Create**: Describe task → System proposes steps
2. **Review**: User sees all steps before execution
3. **Execute**: User approves → Steps run
4. **Undo**: If issues → Rollback available
5. **Redo**: Re-execute rolled-back plan

## Commands

| Input | Action |
|-------|--------|
| `plan: <task>` | Create plan for task |
| `plan show` | Display current plan |
| `plan do` | Execute plan |
| `plan undo` | Undo last plan |
| `plan redo` | Redo undone plan |

## Format Displayed

```
Plan: [Task Description]

Steps:
[ ] 1. Step one
[ ] 2. Step two
[ ] 3. Step three

Rollback (if undo needed):
1. Reverse step 3
2. Reverse step 2
3. Reverse step 1
```

## Undo/Redo Behavior
- **Undo**: Reverts all changes from last plan
- **Redo**: Re-applies last undone plan
- Plans stack: Can undo multiple plans in sequence
- Redo clears if new plan created after undo

## Planning Best Practices (from roadmap.sh/System Design)

### Plan Structure
```
1. Understand Requirements
   - Clarify scope, constraints, success criteria
2. Research & Design
   - Check existing patterns in codebase
   - Identify dependencies, risks
3. Break Down Tasks
   - List atomic, ordered steps
   - Note which files/tools affected
4. Review & Approve
   - Present plan to user
   - Await approval before execution
5. Execute Incrementally
   - Complete one step → verify → next step
6. Rollback Plan
   - Document how to undo each step
```

### System Design Planning Questions
- What are the read/write ratios?
- What are the latency requirements?
- How will it scale?
- What's the failure tolerance?
- What's the data growth rate?
- Which components can fail independently?

### Plan Mode Workflow
```
User: "I want to add feature X"
→ Enter plan mode (Tab)
→ Research codebase (grep, read files)
→ Present plan with steps
→ User reviews / iterates
→ User: "Go ahead" → Execute
→ If issues: /undo → Modify plan → Re-execute
```