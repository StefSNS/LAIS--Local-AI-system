import json
import re
from pathlib import Path

def multi_modal_workflow(task_description, mode="auto"):
    """
    Execute multi-modal workflow across CLI, GUI, and Voice interfaces.
    
    Args:
        task_description: Natural language description of the task
        mode: Target interface (auto, cli, gui, voice)
    
    Returns:
        dict with workflow execution results
    """
    try:
        # Parse workflow steps from task description
        steps = _parse_workflow(task_description)
        
        results = {
            "workflow": task_description,
            "mode": mode,
            "steps_executed": 0,
            "results": []
        }
        
        for step in steps:
            tool_name = step.get("tool", "unknown")
            step_desc = step.get("description", "")
            
            # Map to appropriate interface
            if mode == "auto":
                target_interface = _detect_best_interface(tool_name)
            else:
                target_interface = mode
            
            results["results"].append({
                "step": step_desc,
                "tool": tool_name,
                "interface": target_interface,
                "status": "planned"
            })
            results["steps_executed"] += 1
        
        return {
            "status": "success",
            "message": f"Workflow planned with {results['steps_executed']} steps",
            "data": results
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Workflow planning failed: {str(e)}"
        }


def _parse_workflow(description):
    """Parse natural language into workflow steps."""
    steps = []
    
    # Simple parser - looks for numbered items or bullet points
    patterns = [
        r'(\d+)[\.\)]\s*(.+)',  # 1. Step or 1) Step
        r'[-*]\s*(.+)',           # - Step or * Step
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description)
        for match in matches:
            step_text = match if isinstance(match, str) else match[1]
            tool = _infer_tool(step_text)
            steps.append({
                "description": step_text.strip(),
                "tool": tool
            })
    
    if not steps:
        # Single task - create one step
        steps.append({
            "description": description,
            "tool": _infer_tool(description)
        })
    
    return steps


def _infer_tool(text):
    """Infer appropriate tool from step description."""
    text_lower = text.lower()
    
    tool_mapping = {
        "weather": "weather_report",
        "browser": "browser_control",
        "open": "open_app",
        "search": "web_search",
        "file": "file_controller",
        "code": "code_helper",
        "reminder": "reminder",
        "youtube": "youtube_video",
        "screen": "screen_process",
        "computer": "computer_settings",
        "message": "send_message",
        "game": "game_updater",
        "flight": "flight_finder",
    }
    
    for keyword, tool in tool_mapping.items():
        if keyword in text_lower:
            return tool
    
    return "agent_task"  # Default to multi-step agent


def _detect_best_interface(tool_name):
    """Detect best interface for a given tool."""
    voice_tools = ["weather_report", "reminder", "youtube_video", "computer_settings"]
    gui_tools = ["browser_control", "screen_process", "file_controller"]
    cli_tools = ["code_helper", "dev_agent", "web_search", "cmd_control"]
    
    if tool_name in voice_tools:
        return "voice"
    elif tool_name in gui_tools:
        return "gui"
    elif tool_name in cli_tools:
        return "cli"
    else:
        return "cli"  # Default


if __name__ == "__main__":
    # Test
    result = multi_modal_workflow("1. Get weather in Paris 2. Open browser 3. Search for hotels")
    print(json.dumps(result, indent=2))
