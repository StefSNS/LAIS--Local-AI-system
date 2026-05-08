---
name: multi-modal-workflow
description: Generate and execute cross-modality multi-step workflows from natural language
---

# Multi-Modal Workflow Orchestrator

## Overview
Decomposes natural language tasks into sub-tasks mapped to available CLI/GUI/Voice tools. Works across OpenCode (CLI), Omnis (GUI), and Jarvis (Voice).

## Usage
```
workflow: <describe your multi-step task>
```

## Capabilities
- Decomposes tasks into interface-appropriate sub-tasks
- Validates workflow compatibility before execution
- Auto-retries failed steps with fallback tool mappings
- Supports CLI, GUI, and Voice output modes

## Workflow Format
```
Workflow: [task description]
Mode: [CLI/GUI/Voice/Auto]
Steps:
1. [step description] → [tool_name]
2. [step description] → [tool_name]
3. [step description] → [tool_name]

Fallback mapping:
- CLI: [alternative tool]
- GUI: [alternative tool]
- Voice: [alternative tool]
```

## Implementation
Leverages:
- Omnis plan-mode skill (knowledge/skills/plan_mode.py)
- Jarvis agent/task_queue.py and agent/planner.py
- OpenCode task tool for sub-task execution

## Example
```
workflow: Find the weather in Paris, then open a browser and search for hotels
Mode: Auto
Steps:
1. Get weather for Paris → weather_report
2. Open Chrome browser → open_app
3. Search for Paris hotels → browser_control
```
