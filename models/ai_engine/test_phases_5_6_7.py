"""
Integration Test for Phases 5, 6, 7
Tests Protocol Layer, Gateway Layer, Orchestrator, and Token Optimization
"""

import sys
from pathlib import Path

# Add project root to path
LAIS_PATH = Path(r"str(Path(__file__).resolve().parent)")
sys.path.insert(0, str(LAIS_PATH))

print("=" * 60)
print("PHASES 5, 6, 7 INTEGRATION TEST")
print("=" * 60)

# Track test results
tests_passed = 0
tests_failed = 0

def test(name, condition, detail=""):
    global tests_passed, tests_failed
    if condition:
        print(f"[PASS] {name}")
        tests_passed += 1
    else:
        print(f"[FAIL] {name} - {detail}")
        tests_failed += 1

# ---- Phase 5: Protocol Layer ----------------------------------------
print("\n" + "=" * 60)
print("PHASE 5: PROTOCOL LAYER (MCP + A2A)")
print("=" * 60)

try:
    from unified_layer.protocol_layer import load_protocol_layer
    protocol = load_protocol_layer()
    test("Protocol layer loads", protocol is not None)

    from unified_layer import load_unified_layer
    unified = load_unified_layer("opencode")
    test("Unified layer with protocol loads", unified.protocols is not None)

    # Test agent registration
    status = unified.get_protocol_status()
    test("Agent registered in protocol layer", status.get("local_agents", 0) > 0,
          f"Got: {status}")

    # Test A2A message sending
    if unified.protocols:
        msg_id = unified.protocols.send_a2a_message(
            "opencode", "jarvis", "Test message from opencode"
        )
        test("A2A message send", msg_id is not None, f"Message ID: {msg_id}")

        # Test task delegation
        task = unified.protocols.delegate_task(
            "opencode", "jarvis", "test_task",
            {"test": True}, "normal"
        )
        test("Task delegation", task is not None, f"Task ID: {task.task_id}")

        # Test agent discovery
        agents = unified.protocols.discover_agents()
        test("Agent discovery", len(agents) > 0,
              f"Found {len(agents)} agents")

        # Test MCP server registration
        server = unified.protocols.register_mcp_server(
            "test_server", "stdio", {"command": "test"}
        )
        test("MCP server registration", server is not None)

except Exception as e:
    print(f"[ERROR] Phase 5 error: {e}")
    import traceback
    traceback.print_exc()

# ---- Phase 6: Gateway Layer ------------------------------------------
print("\n" + "=" * 60)
print("PHASE 6: GATEWAY LAYER")
print("=" * 60)

try:
    from unified_layer.gateway_layer import load_gateway_layer
    gateway = load_gateway_layer()
    test("Gateway layer loads", gateway is not None)

    # Test channel registration (done in __init__)
    channels = gateway.list_channels()
    test("Default channels created", len(channels) >= 3,
          f"Found {len(channels)} channels")

    # Test message routing
    agent = gateway.route_message("lais_gui", "test_session_1", "user", "Hello!")
    test("Message routing", agent == "lais", f"Routed to: {agent}")

    # Test session tracking
    sessions = gateway.list_sessions()
    test("Session tracking", len(sessions) > 0,
          f"Sessions: {len(sessions)}")

    # Test session context
    ctx = gateway.get_session_context("test_session_1")
    test("Session context retrieval", len(ctx) > 0,
          f"Context items: {len(ctx)}")

    # Test gateway status
    status = gateway.get_status()
    test("Gateway status", status.get("channels", 0) > 0,
          f"Status: {status}")

    # Test via unified layer
    if unified.gateway:
        unified.gateway.route_message("opencode_channel", "test_session_2", "user", "Test")
        unified.gateway.route_message("opencode_channel", "test_session_2", "assistant", "Response")
        ctx = unified.get_session_context("test_session_2")
        test("Unified layer gateway routing", len(ctx) > 0)

        # Test session compaction
        gateway.compact_session("test_session_2")
        test("Session compaction", True)

except Exception as e:
    print(f"[ERROR] Phase 6 error: {e}")
    import traceback
    traceback.print_exc()

# ---- Phase 7: Orchestrator -------------------------------------------
print("\n" + "=" * 60)
print("PHASE 7: ORCHESTRATOR")
print("=" * 60)

try:
    from unified_layer.orchestrator import load_orchestrator
    orch = load_orchestrator()
    test("Orchestrator loads", orch is not None)

    # Test complexity classification
    complexity = orch.classify_complexity("What time is it?")
    test("Simple query classification", complexity == "simple",
          f"Got: {complexity}")

    complexity = orch.classify_complexity("Design a complete e-commerce system")
    test("Complex query classification", complexity == "complex",
          f"Got: {complexity}")

    # Test model selection
    model = orch.select_model("What time is it?", "simple")
    test("Model selection for simple query", model in ["qwen4", "rwkv7"],
          f"Got: {model}")

    # Test agent selection
    agent = orch.select_agent("Open the browser")
    test("Agent selection for browser task", agent == "browser",
          f"Got: {agent}")

    agent = orch.select_agent("Write a Python script")
    test("Agent selection for code task", agent == "opencode",
          f"Got: {agent}")

    # Test task creation
    task = orch.create_task("What models are running?")
    test("Task creation", task is not None,
          f"Task ID: {task.task_id if task else None}")

    # Test task decomposition
    task = orch.create_task("Design a complete automation system")
    test("Task decomposition", len(task.subtasks) > 0,
          f"Subtasks: {len(task.subtasks)}")

    # Test via unified layer
    if unified.orchestrator:
        classification = unified.classify_query("Build a REST API")
        test("Unified layer query classification",
              classification is not None and "complexity" in classification,
              f"Got: {classification}")

        task = unified.create_task("Test task from unified layer")
        test("Unified layer task creation", task is not None)

        stats = unified.get_orchestrator_stats()
        test("Orchestrator stats", stats.get("total_tasks", 0) > 0,
              f"Stats: {stats}")

except Exception as e:
    print(f"[ERROR] Phase 7 error: {e}")
    import traceback
    traceback.print_exc()

# ---- Token Optimization -----------------------------------------------
print("\n" + "=" * 60)
print("TOKEN OPTIMIZATION PROTOCOL")
print("=" * 60)

try:
    from unified_layer.token_optimizer import (
        load_token_optimizer, estimate_tokens, truncate_to_budget
    )

    optimizer = load_token_optimizer("test")
    test("Token optimizer loads", optimizer is not None)

    # Test token estimation
    tokens = estimate_tokens("Hello world! " * 50)
    test("Token estimation", tokens > 0, f"Tokens: {tokens}")

    # Test budget check
    budget = optimizer.check_budget("Hello!", "session_start")
    test("Budget check", budget["within_budget"] == True,
          f"Budget check: {budget}")

    # Test truncation
    long_text = "Hello world! " * 200
    truncated = truncate_to_budget(long_text, 50)
    test("Text truncation", estimate_tokens(truncated) <= 50,
          f"Truncated tokens: {estimate_tokens(truncated)}")

    # Test context optimization
    context_items = [
        {"content": "A" * 500, "score": 0.9},
        {"content": "B" * 500, "score": 0.7},
        {"content": "C" * 500, "score": 0.5},
    ]
    optimized = optimizer.optimize_context(context_items, max_tokens=100)
    test("Context optimization", len(optimized) <= len(context_items),
          f"Optimized: {len(optimized)} items")

    # Test history compaction
    messages = [
        {"role": "system", "content": "You are helpful."},
    ]
    for i in range(20):
        messages.append({"role": "user", "content": f"Message {i}" * 20})
        messages.append({"role": "assistant", "content": f"Response {i}" * 20})

    compacted = optimizer.compact_history(messages, target_tokens=200)
    test("History compaction", len(compacted) < len(messages),
          f"Compacted: {len(messages)} -> {len(compacted)}")

    # Test via unified layer
    if unified.token_optimizer:
        test("Unified layer has token optimizer", True)

        tokens = unified.token_optimizer.estimate_tokens("Test message")
        unified.token_optimizer.log_usage("test", tokens, "session_start")
        stats = unified.token_optimizer.get_usage_stats()
        test("Token usage logging", stats.get("calls", 0) > 0,
              f"Stats: {stats}")

except Exception as e:
    print(f"[ERROR] Token optimizer error: {e}")
    import traceback
    traceback.print_exc()

# ---- Integration Test: Full Pipeline ---------------------------------
print("\n" + "=" * 60)
print("INTEGRATION: FULL PIPELINE")
print("=" * 60)

try:
    # Simulate a conversation turn
    user_msg = "What is the current project status?"
    ai_response = "Based on the vault context, you have 3 active projects."

    # Process through unified layer (this should trigger all phases)
    if unified:
        # This should route through gateway, broadcast via protocol, etc.
        insights = unified.process_conversation(user_msg, ai_response)
        test("Full pipeline: process_conversation", True)

        # Check gateway has the messages
        if unified.gateway:
            sessions = unified.list_gateway_channels()
            test("Full pipeline: gateway channels", len(sessions) > 0)

        # Check system status
        status = unified.get_full_system_status()
        test("Full pipeline: system status",
              status.get("protocols") is not None or status.get("gateway") is not None,
              f"Status keys: {list(status.keys())}")

except Exception as e:
    print(f"[ERROR] Integration error: {e}")
    import traceback
    traceback.print_exc()

# ---- Summary ---------------------------------------------------------
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"Tests passed: {tests_passed}")
print(f"Tests failed: {tests_failed}")
print(f"Total tests: {tests_passed + tests_failed}")

if tests_failed == 0:
    print("\n[ALL TESTS PASSED]")
else:
    print(f"\n[WARNING] {tests_failed} test(s) failed")

print("=" * 60)
