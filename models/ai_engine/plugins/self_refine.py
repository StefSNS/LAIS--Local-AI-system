import os
import json
import time
import importlib.util
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_DIR = os.path.join(PROJECT_ROOT, "knowledge")
PLUGINS_DIR = os.path.join(PROJECT_ROOT, "plugins")
REFINE_LOG = os.path.join(KNOWLEDGE_DIR, "refinement_log.json")
REFINE_STATE = os.path.join(KNOWLEDGE_DIR, "refine_state.json")

def get_state():
    """Load the refinement state."""
    try:
        with open(REFINE_STATE, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {
            "install_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "last_refine": None,
            "refine_count": 0,
            "next_refine": "2026-04-23 00:00"
        }

def save_state(state):
    """Save the refinement state."""
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    with open(REFINE_STATE, 'w') as f:
        json.dump(state, f, indent=2)

def should_refine():
    """Check if a refinement cycle is due."""
    state = get_state()
    now = datetime.now()
    
    # Parse next refine time
    try:
        next_refine = datetime.strptime(state["next_refine"], "%Y-%m-%d %H:%M")
    except Exception as e:
        next_refine = datetime(2026, 4, 23, 0, 0)
    
    # Check if we are past the scheduled time
    if now >= next_refine:
        # Check if we already refined today
        if state["last_refine"]:
            try:
                last = datetime.strptime(state["last_refine"], "%Y-%m-%d %H:%M")
                if last.date() == now.date():
                    return False  # Already refined today
            except Exception as e:
                pass
        return True
    
    return False

def run_refinement(progress_callback=None):
    """Execute the daily refinement cycle."""
    state = get_state()
    now = datetime.now()
    results = []
    
    results.append(f"[REFINE] DAILY REFINEMENT CYCLE #{state['refine_count'] + 1}")
    results.append(f"[DATE] Date: {now.strftime('%A, %d %B %Y %H:%M')}")
    results.append("-" * 50)
    
    if progress_callback:
        progress_callback("Starting daily refinement...")
    
    # =========== PHASE 1: KNOWLEDGE AUDIT ===========
    results.append("\n[PHASE 1] Knowledge Audit")
    try:
        knowledge_files = os.listdir(KNOWLEDGE_DIR)
        md_files = [f for f in knowledge_files if f.endswith('.md')]
        json_files = [f for f in knowledge_files if f.endswith('.json')]
        
        total_size = 0
        for f in knowledge_files:
            total_size += os.path.getsize(os.path.join(KNOWLEDGE_DIR, f))
        
        results.append(f"   Markdown files: {len(md_files)}")
        results.append(f"   Data files: {len(json_files)}")
        results.append(f"   Total size: {total_size / 1024:.1f} KB")
        results.append("   [OK] Knowledge audit complete")
    except Exception as e:
        results.append(f"   [ERROR] Audit failed: {e}")
    
    # =========== PHASE 2: PLUGIN HEALTH CHECK ===========
    results.append("\n[PHASE 2] Plugin Health Check")
    try:
        plugin_files = [f for f in os.listdir(PLUGINS_DIR) if f.endswith('.py') and f != '__init__.py']
        healthy = 0
        broken = 0
        
        for pf in plugin_files:
            try:
                spec = importlib.util.spec_from_file_location(pf[:-3], os.path.join(PLUGINS_DIR, pf))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                healthy += 1
                results.append(f"   [OK] {pf}")
            except Exception as e:
                broken += 1
                results.append(f"   [ERROR] {pf}: {e}")
        
        results.append(f"   Healthy: {healthy} | Broken: {broken}")
    except Exception as e:
        results.append(f"   [ERROR] Plugin check failed: {e}")
    
    # =========== PHASE 3: AUTO-RESEARCH ===========
    results.append("\n[PHASE 3] Auto-Research (Expanding Knowledge)")
    
    research_topics = [
        "Python programming best practices",
        "AI model optimization",
        "Windows 11 automation",
        "RAM management",
        "intent classification NLP"
    ]
    
    # Pick one topic per day (rotate through the list)
    topic_index = state['refine_count'] % len(research_topics)
    today_topic = research_topics[topic_index]
    
    try:
        if progress_callback:
            progress_callback(f"Researching: {today_topic}")
        
        import sys
        sys.modules.pop('researcher', None)
        sys.modules.pop('plugins.researcher', None)
        
        researcher_path = os.path.join(PLUGINS_DIR, "researcher.py")
        spec = importlib.util.spec_from_file_location("researcher", researcher_path)
        researcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(researcher)
        
        research_result = researcher.research_and_save(today_topic)
        results.append(f"   Topic: {today_topic}")
        results.append(f"   Result: {research_result}")
    except Exception as e:
        results.append(f"   [ERROR] Research failed: {e}")
    
    # =========== PHASE 4: SELF-CODE REVIEW ===========
    results.append("\n[PHASE 4] Self-Code Review")
    try:
        core_files = ['main.py', 'llm_engine.py', 'memory_lais.py', 'plugin_manager.py', 'config.json']
        for cf in core_files:
            cf_path = os.path.join(PROJECT_ROOT, cf)
            if os.path.exists(cf_path):
                size = os.path.getsize(cf_path) / 1024
                results.append(f"   [OK] {cf} ({size:.1f} KB)")
            else:
                results.append(f"   [WARN] {cf} MISSING")
    except Exception as e:
        results.append(f"   [ERROR] Code review failed: {e}")
    
    # =========== PHASE 5: DICTIONARY HEALTH ===========
    results.append("\n[PHASE 5] Dictionary Status")
    try:
        dict_path = os.path.join(KNOWLEDGE_DIR, "webster_dictionary.json")
        if os.path.exists(dict_path):
            dict_size = os.path.getsize(dict_path) / (1024 * 1024)
            with open(dict_path, 'r') as f:
                d = json.load(f)
            results.append(f"   [OK] Webster Dictionary: {len(d)} words ({dict_size:.1f} MB)")
        else:
            results.append("   [WARN] Dictionary not found")
    except Exception as e:
        results.append(f"   [ERROR] Dictionary check failed: {e}")
    
    # =========== SUMMARY ===========
    results.append("\n" + "-" * 50)
    results.append("[DONE] REFINEMENT COMPLETE")
    
    # Update state
    state["last_refine"] = now.strftime("%Y-%m-%d %H:%M")
    state["refine_count"] += 1
    state["next_refine"] = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0
    ).strftime("%Y-%m-%d %H:%M")
    save_state(state)
    
    results.append(f"   Next refinement: {state['next_refine']}")
    
    # Save refinement log
    log_entry = {
        "date": now.strftime("%Y-%m-%d %H:%M"),
        "cycle": state["refine_count"],
        "summary": "\n".join(results)
    }
    
    try:
        if os.path.exists(REFINE_LOG):
            with open(REFINE_LOG, 'r') as f:
                log = json.load(f)
        else:
            log = []

        log.append(log_entry)

        with open(REFINE_LOG, 'w') as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        pass

    return "\n".join(results)

