import sys
import os
import importlib.util

sys.path.insert(0, 'plugins')

def run_goal(goal_message, llm_chat_func, progress_callback=None):
    """Simple goal loop (stable version)."""

    steps = goal_message.replace(" then ", "|").split("|")
    results = []

    results.append(f"🎯 GOAL: {goal_message}")
    results.append("─" * 40)

    for i, step in enumerate(steps, 1):
        step = step.strip()
        if not step:
            continue

        results.append(f"\n⚙️ Step {i}: {step}")

        try:
            lower = step.lower()

            if "define" in lower:
                word = step.replace("define", "").strip()
                spec = importlib.util.spec_from_file_location("dictionary", "plugins/dictionary.py")
                d = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(d)
                output = d.define(word)

            elif "research" in lower:
                topic = step.replace("research", "").strip()
                spec = importlib.util.spec_from_file_location("researcher", "plugins/researcher.py")
                rmod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(rmod)
                output = rmod.research_and_save(topic)

            elif "open" in lower or "launch" in lower:
                app = step.replace("open", "").replace("launch", "").strip()
                spec = importlib.util.spec_from_file_location("system_control", "plugins/system_control.py")
                sc = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(sc)
                output = sc.launch(app)

            elif "code" in lower:
                spec = importlib.util.spec_from_file_location("agent_dispatcher", "plugins/agent_dispatcher.py")
                ad = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(ad)
                output = ad.dispatch(step, "coder")

            else:
                output = llm_chat_func(step)

            results.append(f"✅ {str(output)[:300]}")

        except Exception as e:
            results.append(f"❌ Error: {e}")

    results.append("\n🏁 Goal Finished")
    return "\n".join(results)


def get_status():
    return "Goal system ready."