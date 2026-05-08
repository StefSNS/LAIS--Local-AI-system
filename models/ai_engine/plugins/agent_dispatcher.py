"""
LAIS Agent Dispatcher
Routes tasks to the correct plugin agent.
"""

import os
import sys
import importlib.util

PLUGINS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(PLUGINS_DIR, os.pardir))


def _load_plugin(module_name):
    path = os.path.join(PLUGINS_DIR, f"{module_name}.py")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plugin not found: {path}")

    sys.modules.pop(module_name, None)
    sys.modules.pop(f"plugins.{module_name}", None)

    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _get_chat():
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
    from llm_engine import chat
    return chat


def dispatch(task, agent="general", llm_chat=None):
    task = (task or "").strip()
    agent = (agent or "general").strip().lower()

    if not task:
        return "No task provided."

    if llm_chat is None:
        try:
            llm_chat = _get_chat()
        except Exception:
            llm_chat = None

    try:
        if agent in ("coder", "code"):
            mod = _load_plugin("code_editor")
            if hasattr(mod, "run"):
                try:
                    return mod.run(task, llm_chat)
                except TypeError:
                    return mod.run(task)
            return "Coder plugin is missing a compatible entry point."

        if agent in ("research", "researcher"):
            mod = _load_plugin("researcher")
            if hasattr(mod, "research"):
                try:
                    return mod.research(task, llm_chat)
                except TypeError:
                    return mod.research(task)
            if hasattr(mod, "research_and_save"):
                return mod.research_and_save(task)
            return "Researcher plugin is missing a compatible entry point."

        if agent in ("direct", "executor"):
            mod = _load_plugin("direct_executor")
            if hasattr(mod, "run"):
                return mod.run(task)
            if hasattr(mod, "execute"):
                return mod.execute(task)
            return "Direct executor plugin is missing a compatible entry point."

        if agent in ("file", "files"):
            mod = _load_plugin("file_manager")
            if hasattr(mod, "run"):
                return mod.run(task)
            return "File manager plugin is missing a compatible entry point."

        if llm_chat:
            return llm_chat(task)

        return "No dispatcher route available."

    except Exception as e:
        return f"Dispatcher error ({agent}): {e}"


def route(task, agent="general", llm_chat=None):
    return dispatch(task, agent, llm_chat)
