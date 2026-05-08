"""
Orchestrator - Phase 7 of Architecture Evolution
LLM-based task routing, model selection, and task decomposition.
Coordinates all agents, routes tasks to the right model, and aggregates results.
"""

import sys
from pathlib import Path

lais_root = Path(__file__).resolve().parent.parent
if str(lais_root) not in sys.path:
    sys.path.insert(0, str(lais_root))

import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple
from threading import Lock

ANALYTICS_AVAILABLE = False
SEMANTIC_AVAILABLE = False
try:
    from ..plugins.analytics_engine import AnalyticsEngine, load_analytics_engine
    ANALYTICS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    try:
        from plugins.analytics_engine import AnalyticsEngine, load_analytics_engine
        ANALYTICS_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        pass

try:
    from ..plugins.semantic_search import TxtaiSearch, load_txtai_search
    SEMANTIC_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    try:
        from plugins.semantic_search import TxtaiSearch, load_txtai_search
        SEMANTIC_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        pass

MODEL_ENDPOINTS = {
    "smol3": "http://localhost:8100/v1/chat/completions",
    "qwen4": "http://localhost:8101/v1/chat/completions",
    "rwkv7": "http://localhost:8102/v1/chat/completions",
}

ORCHESTRATOR_LOG_FILE = Path(
    r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\orchestrator_log.json"
)
ORCHESTRATOR_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
LOCK = Lock()

# Model capabilities matrix
MODEL_CAPABILITIES = {
    "smol3": {
        "label": "SmolLM3-3B",
        "params": "3B",
        "strengths": ["reasoning", "creative_writing", "general_chat", "summarization", "analysis"],
        "weaknesses": ["complex_code", "math", "long_context"],
        "speed": "slow",
        "quality": "good",
    },
    "qwen4": {
        "label": "Qwen3.5-4B",
        "params": "4B",
        "strengths": ["quick_responses", "code_snippets", "classification", "formatting", "simple_chat", "multimodal", "instruction_following"],
        "weaknesses": ["complex_reasoning", "creative_writing", "long_responses"],
        "speed": "fast",
        "quality": "basic",
    },
    "rwkv7": {
        "label": "RWKV-7-Goose-3B",
        "params": "3B",
        "strengths": ["constant_memory", "infinite_context", "streaming", "long_conversations", "low_ram"],
        "weaknesses": ["math", "code_generation", "creative_writing"],
        "speed": "fast",
        "quality": "good",
        "ram_usage_mb": 1500,
        "architecture": "RNN",
    },
}

# Task complexity levels
TASK_COMPLEXITY = {
    "simple": {
        "description": "Quick answer, formatting, classification, short code",
        "recommended_model": "qwen4",
        "examples": ["what time is it", "format this data", "is X a prime number", "list files"],
    },
    "medium": {
        "description": "Multi-step reasoning, analysis, medium code tasks",
        "recommended_model": "smol3",
        "examples": ["explain how X works", "debug this function", "summarize this article"],
    },
    "complex": {
        "description": "Deep reasoning, architecture design, complex code, creative work",
        "recommended_model": "smol3",
        "examples": ["design a system for X", "write a full module", "analyze this codebase"],
    },
}


class LLMClient:
    """HTTP client for local llama.cpp OpenAI-compatible API."""

    def __init__(self, timeout: int = 120):
        self.timeout = timeout

    def _rwkv_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Tuple[bool, str]:
        """RWKV-7 uses completions endpoint with User/Assistant format."""
        base = MODEL_ENDPOINTS.get("rwkv7", "").replace("/v1/chat/completions", "/v1/completions")
        if not base:
            return False, "RWKV-7 endpoint not configured"
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "").replace("\n\n", "\n")
            if role == "system":
                prompt_parts.append(f"User: {content}\n\nAssistant: Understood. I will follow these instructions.\n\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n\nAssistant:")
            elif role == "assistant":
                prompt_parts.append(f"{content}\n\n")

        prompt = "\n".join(prompt_parts)
        payload = {"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature, "stop": ["\nUser:"]}

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            base,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result.get("choices", [{}])[0].get("text", "").strip()
                return (True, content) if content else (False, "Empty response from RWKV-7")
        except urllib.error.URLError as e:
            reason = str(e.reason) if hasattr(e, "reason") else str(e)
            return False, f"Connection failed to RWKV-7 ({base}): {reason}"
        except Exception as e:
            return False, f"RWKV-7 error: {str(e)}"

    def chat_completion(
        self,
        model_key: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Tuple[bool, str]:
        if model_key == "rwkv7":
            return self._rwkv_completion(messages, max_tokens, temperature)

        endpoint = MODEL_ENDPOINTS.get(model_key)
        if not endpoint:
            return False, f"No endpoint configured for model: {model_key}"

        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "reasoning": False,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                msg = result.get("choices", [{}])[0].get("message", {})
                content = msg.get("content", "")
                if not content:
                    content = msg.get("reasoning_content", "")
                if content:
                    return True, content.strip()
                return False, "Empty response from model"
        except urllib.error.URLError as e:
            reason = str(e.reason) if hasattr(e, "reason") else str(e)
            return False, f"Connection failed to {MODEL_CAPABILITIES.get(model_key, {}).get('label', model_key)} ({endpoint}): {reason}"
        except Exception as e:
            return False, f"Model error: {str(e)}"


class Task:
    """Represents a task in the orchestrator."""

    def __init__(
        self,
        task_id: str,
        description: str,
        original_query: str,
        complexity: str = "medium",
        assigned_model: str = "smol3",
        assigned_agent: str = "auto",
        subtasks: Optional[List[Dict]] = None,
    ):
        self.task_id = task_id
        self.description = description
        self.original_query = original_query
        self.complexity = complexity
        self.assigned_model = assigned_model
        self.assigned_agent = assigned_agent
        self.subtasks = subtasks or []
        self.status = "pending"
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.result = None
        self.model_used = None
        self.agent_used = None

    def complete(self, result: Any, model_used: str, agent_used: str):
        self.status = "completed"
        self.result = result
        self.model_used = model_used
        self.agent_used = agent_used
        self.completed_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "original_query": self.original_query,
            "complexity": self.complexity,
            "assigned_model": self.assigned_model,
            "assigned_agent": self.assigned_agent,
            "subtasks": self.subtasks,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": str(self.result)[:500] if self.result else None,
            "model_used": self.model_used,
            "agent_used": self.agent_used,
        }


class Orchestrator:
    """
    LLM-based task orchestrator.
    - Classifies task complexity
    - Routes to the right model and agent
    - Decomposes complex tasks into subtasks
    - Aggregates results from parallel execution
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.model_executor: Optional[Callable] = None
        self.llm_client = LLMClient()
        self.analytics = load_analytics_engine() if ANALYTICS_AVAILABLE else None
        self.semantic = load_txtai_search() if SEMANTIC_AVAILABLE else None
        if self.analytics:
            print("[Orchestrator] Analytics engine enabled (DuckDB)")
        if self.semantic:
            print("[Orchestrator] Semantic search enabled (txtai)")
        self._load_log()
        self._delegation_chain: Dict[str, int] = {}
        self._timeout_seconds: int = 120
        self._max_retries: int = 3
        self._max_delegation_hops: int = 5
        self._budget_tracker: Dict[str, float] = {"total_tokens": 0, "daily_tokens": 0, "last_reset": datetime.now().isoformat()}
        self._budget_limits: Dict[str, int] = {"daily_tokens": 1000000, "max_tokens_per_task": 50000, "max_tasks_per_hour": 50}
        self._checkpoints: Dict[str, dict] = {}
        self._task_hourly_counts: Dict[str, int] = {}

    def _load_log(self):
        """Load orchestrator log."""
        if ORCHESTRATOR_LOG_FILE.exists():
            try:
                data = json.loads(ORCHESTRATOR_LOG_FILE.read_text(encoding="utf-8"))
                for task_data in data:
                    task = Task(
                        task_id=task_data["task_id"],
                        description=task_data.get("description", ""),
                        original_query=task_data.get("original_query", ""),
                        complexity=task_data.get("complexity", "medium"),
                        assigned_model=task_data.get("assigned_model", "smol3"),
                        assigned_agent=task_data.get("assigned_agent", "auto"),
                        subtasks=task_data.get("subtasks", []),
                    )
                    task.status = task_data.get("status", "pending")
                    task.created_at = task_data.get("created_at", datetime.now().isoformat())
                    task.completed_at = task_data.get("completed_at")
                    task.result = task_data.get("result")
                    self.tasks[task.task_id] = task
            except Exception:
                pass

    def _save_log(self):
        """Save orchestrator log."""
        with LOCK:
            data = [task.to_dict() for task in self.tasks.values()]
            ORCHESTRATOR_LOG_FILE.write_text(
                json.dumps(data[-100:], indent=2), encoding="utf-8"
            )

    def _log_event(self, event: str, detail: str):
        """Log an orchestrator event."""
        log_entry = {
            "event": event,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            if ORCHESTRATOR_LOG_FILE.exists():
                log = json.loads(ORCHESTRATOR_LOG_FILE.read_text(encoding="utf-8"))
            else:
                log = []
            log.append(log_entry)
            ORCHESTRATOR_LOG_FILE.write_text(
                json.dumps(log[-200:], indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def classify_complexity(self, query: str) -> str:
        """
        Classify task complexity from the query.
        Uses keyword matching as a fast approximation of LLM classification.
        Returns: 'simple', 'medium', or 'complex'
        """
        q = query.lower()

        # Complex signals
        complex_signals = [
            "design", "architecture", "build a system", "create a framework",
            "refactor", "optimize", "multi-step", "pipeline",
            "write a full", "implement a complete", "deep analysis",
            "compare and contrast", "evaluate alternatives",
            "long-term strategy", "comprehensive",
        ]
        if any(s in q for s in complex_signals):
            return "complex"

        # Simple signals
        simple_signals = [
            "what is", "what are", "who is", "when did",
            "list", "show me", "format", "convert",
            "is it", "does it", "can you", "quick",
            "check", "count", "find", "sort",
        ]
        if any(s in q for s in simple_signals):
            # Only simple if also short
            if len(q.split()) < 15:
                return "simple"

        # Medium: everything else
        return "medium"

    def select_model(self, query: str, complexity: Optional[str] = None) -> str:
        """
        Select the best model for a query.
        Returns model key ('smol3', 'qwen4', or 'rwkv7').
        """
        if complexity is None:
            complexity = self.classify_complexity(query)

        q = query.lower()

        # RWKV-7: long conversations, memory-heavy tasks, constant context
        long_context_signals = ["long conversation", "remember", "context", "history",
                                "summary of", "everything we discussed", "full thread"]
        if any(s in q for s in long_context_signals):
            return "rwkv7"

        # Override: code-heavy queries go to Qwen3 for speed
        code_keywords = ["def ", "import ", "function", "class ", "return ",
                         "pip install", "npm install", "git", "regex", "json"]
        if complexity == "simple" and any(kw in q for kw in code_keywords):
            return "qwen4"

        # Override: creative writing goes to SmolLM3
        creative_keywords = ["write a story", "creative", "poem", "essay",
                             "imagine", "describe in detail", "explain like"]
        if any(kw in q for kw in creative_keywords):
            return "smol3"

        return TASK_COMPLEXITY[complexity]["recommended_model"]

    def select_agent(self, query: str) -> str:
        """
        Select the best agent for a query.
        Returns: 'lais', 'jarvis', 'opencode', 'browser', or 'auto'
        """
        q = query.lower()

        # Browser tasks → browser_agent (browsegrab) - CHECK FIRST
        import re
        browser_patterns = [
            r"browse",
            r"browser",
            r"navigate\s+to\s+",
            r"go\s+to\s+",
            r"open\s+(google|youtube|github|twitter|reddit|amazon|facebook|instagram|wikipedia|bing|duckduckgo|yahoo|browser|web)",
            r"visit\s+(google|youtube|github|twitter|reddit|amazon|facebook|instagram|wikipedia|bing|duckduckgo|yahoo)",
            r"website",
            r"webpage",
            r"fill\s+form",
            r"log\s+in",
            r"login",
            r"scrape",
            r"extract\s+from",
            r"screenshot",
            r"scroll",
            r"search\s+on\s+",
            r"find\s+on\s+",
            r"get\s+content\s+from",
        ]
        for pattern in browser_patterns:
            if re.search(pattern, q):
                return "browser"

        # Code/CLI tasks → OpenCode
        code_signals = ["code", "script", "file", "debug", "run", "execute",
                         "install", "build", "test", "deploy", "git", "python",
                         "powershell", "terminal", "command"]
        if any(s in q for s in code_signals):
            return "opencode"

        # GUI/visual tasks → LAIS
        gui_signals = ["show", "display", "visualize", "chart", "graph",
                       "dashboard", "gui", "interface", "ui", "draw"]
        if any(s in q for s in gui_signals):
            return "lais"

        # Default: LAIS (general chat)
        return "lais"

    def decompose_task(self, query: str, complexity: str) -> List[Dict]:
        """
        Decompose a complex task into subtasks.
        Uses rule-based decomposition as a placeholder for LLM-based decomposition.
        """
        if complexity != "complex":
            return []

        subtasks = []
        q = query.lower()

        # Common decomposition patterns
        if any(w in q for w in ["build", "create", "implement", "design", "develop"]):
            subtasks = [
                {"name": "Research and plan", "type": "analysis", "model": "smol3"},
                {"name": "Write core code", "type": "code", "model": "smol3"},
                {"name": "Test and validate", "type": "testing", "model": "qwen4"},
            ]

        elif any(w in q for w in ["analyze", "evaluate", "review", "assess"]):
            subtasks = [
                {"name": "Gather context", "type": "research", "model": "qwen4"},
                {"name": "Analyze findings", "type": "analysis", "model": "smol3"},
                {"name": "Write summary", "type": "writing", "model": "smol3"},
            ]

        elif any(w in q for w in ["optimize", "improve", "refactor", "enhance"]):
            subtasks = [
                {"name": "Profile current state", "type": "analysis", "model": "qwen4"},
                {"name": "Identify bottlenecks", "type": "analysis", "model": "smol3"},
                {"name": "Implement improvements", "type": "code", "model": "smol3"},
            ]

        elif any(w in q for w in ["automate", "automation", "pipeline", "workflow"]):
            subtasks = [
                {"name": "Analyze requirements", "type": "analysis", "model": "smol3"},
                {"name": "Design automation flow", "type": "design", "model": "smol3"},
                {"name": "Implement automation", "type": "code", "model": "smol3"},
                {"name": "Test automation", "type": "testing", "model": "qwen4"},
            ]

        return subtasks

    def create_task(
        self,
        query: str,
        description: Optional[str] = None,
        complexity: Optional[str] = None,
    ) -> Task:
        """
        Create a new task with automatic model/agent routing.
        """
        if complexity is None:
            complexity = self.classify_complexity(query)

        model = self.select_model(query, complexity)
        agent = self.select_agent(query)
        subtasks = self.decompose_task(query, complexity)

        task_id = f"task_{int(datetime.now().timestamp())}_{hash(query) % 10000:04d}"

        task = Task(
            task_id=task_id,
            description=description or query[:100],
            original_query=query,
            complexity=complexity,
            assigned_model=model,
            assigned_agent=agent,
            subtasks=subtasks,
        )

        self.tasks[task_id] = task
        self._save_log()

        self._log_event(
            "task_created",
            f"{task_id}: {query[:50]} (complexity={complexity}, model={model}, agent={agent})",
        )

        return task

    def _check_delegation_hop(self, task_id: str) -> Tuple[bool, str]:
        if task_id not in self._delegation_chain:
            self._delegation_chain[task_id] = 0
        self._delegation_chain[task_id] += 1
        if self._delegation_chain[task_id] > self._max_delegation_hops:
            return False, f"Max delegation hops ({self._max_delegation_hops}) exceeded for {task_id}"
        return True, "OK"

    def execute_task(
        self,
        task_id: str,
        model_override: Optional[str] = None,
    ) -> Tuple[bool, Any]:
        task = self.tasks.get(task_id)
        if not task:
            return False, "Task not found"

        hop_ok, hop_msg = self._check_delegation_hop(task_id)
        if not hop_ok:
            return False, hop_msg

        budget_ok, budget_msg = self._check_budget(task.original_query, max_tokens=2048)
        if not budget_ok:
            return False, budget_msg

        self._save_checkpoint(task_id, "pre_execute", {"model": model_override or task.assigned_model, "agent": task.assigned_agent})

        if task.assigned_agent == "browser":
            return self._execute_browser_task(task)

        model = model_override or task.assigned_model
        if model not in MODEL_CAPABILITIES:
            return False, f"Unknown model: {model}"

        max_tokens = {"simple": 512, "medium": 1024, "complex": 2048}.get(task.complexity, 1024)

        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, direct answers."},
            {"role": "user", "content": task.original_query},
        ]

        success, result = self.llm_client.chat_completion(
            model_key=model,
            messages=messages,
            max_tokens=max_tokens,
        )

        if success:
            task.complete(result=result, model_used=model, agent_used=task.assigned_agent)
            self._save_log()
            self._log_event(
                "task_executed",
                f"{task_id}: model={model}, agent={task.assigned_agent}, tokens={len(result)}",
            )
        else:
            self._log_event(
                "task_failed",
                f"{task_id}: model={model}, error={result[:200]}",
            )

        return success, result

    def _execute_browser_task(self, task) -> Tuple[bool, Any]:
        """Execute a browser automation task using browsegrab."""
        try:
            from plugins.browser_agent import BrowserAgent, run_browser_async

            agent = BrowserAgent(headless=True)
            query = task.original_query.lower()

            # Parse intent from query to determine browser actions
            result_text = []
            
            # Extract URL from query
            url = self._extract_url(query)
            if url:
                print(f"[Browser] Navigating to: {url}")
                nav_result = run_browser_async(agent.navigate(url))
                result_text.append(f"Navigated to {url}")
                
                if "error" in nav_result:
                    return False, f"Navigation failed: {nav_result['error']}"
                
                # Get snapshot after navigation
                snap_result = run_browser_async(agent.snapshot())
                if "tree" in snap_result:
                    elements = snap_result.get("interactive_elements", 0)
                    result_text.append(f"Found {elements} interactive elements")
                
                # If query includes extraction, get content
                if "extract" in query or "content" in query or "get" in query:
                    content_result = run_browser_async(agent.extract_content())
                    if "content" in content_result:
                        result_text.append(f"\nContent:\n{content_result['content'][:500]}")
            else:
                return False, "No URL found in query. Please provide a URL to browse."

            run_browser_async(agent.stop())
            
            result = "\n".join(result_text)
            task.complete(result=result, model_used="browsegrab", agent_used="browser")
            self._save_log()
            self._log_event(
                "task_executed",
                f"{task.task_id}: browser task completed, agent=browser",
            )
            return True, result

        except ImportError:
            return False, "browsegrab not installed. Run: pip install browsegrab playwright"
        except Exception as e:
            return False, f"Browser task failed: {e}"

    def _extract_url(self, query: str) -> Optional[str]:
        """Extract URL from a natural language query."""
        import re
        
        # Direct URL match
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        match = re.search(url_pattern, query)
        if match:
            url = match.group(0)
            if url.startswith("www."):
                url = "https://" + url
            return url
        
        # Common site patterns
        site_patterns = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "twitter": "https://twitter.com",
            "x.com": "https://x.com",
            "wikipedia": "https://www.wikipedia.org",
            "reddit": "https://www.reddit.com",
            "amazon": "https://www.amazon.com",
        }
        
        q = query.lower()
        for pattern, url in site_patterns.items():
            if f"go to {pattern}" in q or f"open {pattern}" in q or f"visit {pattern}" in q:
                return url
        
        return None

    def search_context(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search semantic + memory context before executing a task.
        Used to inject relevant knowledge into the LLM prompt.
        """
        results = []

        if self.semantic:
            semantic_results = self.semantic.search(query, max_results=max_results)
            for r in semantic_results:
                results.append({
                    "source": "semantic",
                    "title": r.get("title", ""),
                    "text": r.get("text", "")[:300],
                    "score": r.get("score", 0),
                })

        return results[:max_results]

    def get_analytics(self, query: str) -> Dict[str, Any]:
        """
        Run analytical query against the analytics engine.
        Falls back gracefully if DuckDB is unavailable.
        """
        if not self.analytics:
            return {"error": "Analytics engine not available"}

        analytical_patterns = [
            "summary", "statistics", "stats", "count", "how many",
            "distribution", "trend", "compare", "report", "activity",
            "top", "most", "least", "average", "total",
        ]

        q = query.lower()
        if any(p in q for p in analytical_patterns):
            if "activity" in q or "summary" in q or "stats" in q:
                agent_match = re.search(r"(opencode|lais|jarvis|browser)", q)
                if agent_match:
                    return self.analytics.agent_activity_summary(agent_match.group(1))
                return self.analytics.agent_comparison()

            if "category" in q or "distribution" in q:
                return {"category_distribution": self.analytics.category_distribution()}

            if "trend" in q or "conversation" in q:
                return {"conversation_trends": self.analytics.conversation_trends()}

            if "report" in q:
                report_path = self.analytics.export_report()
                return {"report_generated": report_path}

        return {"note": "Query not recognized as analytical, use keywords like: summary, stats, trend, report"}

    def enrich_prompt(self, query: str) -> str:
        """
        Enrich a user query with relevant context from memory + semantic search.
        Returns the original query with injected context.
        """
        context = self.search_context(query, max_results=3)
        if not context:
            return query

        context_block = "\n### Relevant Context\n"
        for c in context:
            context_block += f"- [{c['source']}] {c.get('title', '')}: {c['text'][:150]}\n"

        return f"{context_block}\n\n### User Query\n{query}"

    def get_model_info(self, model_key: str) -> Optional[Dict]:
        """Get information about a model."""
        return MODEL_CAPABILITIES.get(model_key)

    def get_available_models(self) -> List[Dict]:
        """List all available models."""
        return [
            {"key": k, **v}
            for k, v in MODEL_CAPABILITIES.items()
        ]

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a task by ID."""
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None

    def list_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """List tasks, optionally filtered by status."""
        tasks = []
        for t in self.tasks.values():
            if status and t.status != status:
                continue
            tasks.append(t.to_dict())
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        return tasks

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        tasks = list(self.tasks.values())
        completed = [t for t in tasks if t.status == "completed"]

        model_usage = {}
        for t in completed:
            if t.model_used:
                model_usage[t.model_used] = model_usage.get(t.model_used, 0) + 1

        complexity_distribution = {}
        for t in tasks:
            complexity_distribution[t.complexity] = complexity_distribution.get(t.complexity, 0) + 1

        stats = {
            "total_tasks": len(tasks),
            "completed": len(completed),
            "pending": len([t for t in tasks if t.status == "pending"]),
            "model_usage": model_usage,
            "complexity_distribution": complexity_distribution,
            "analytics_enabled": self.analytics is not None,
            "semantic_search_enabled": self.semantic is not None,
        }

        if self.analytics:
            try:
                stats["analytics"] = self.analytics.agent_comparison()
            except Exception:
                pass

        if self.semantic:
            try:
                stats["semantic_index"] = self.semantic.get_stats()
            except Exception:
                pass

        return stats

    def _check_budget(self, query: str, max_tokens: int = 1024) -> Tuple[bool, str]:
        now = datetime.now()
        last_reset = datetime.fromisoformat(self._budget_tracker["last_reset"])
        if (now - last_reset).total_seconds() > 86400:
            self._budget_tracker["daily_tokens"] = 0
            self._budget_tracker["last_reset"] = now.isoformat()
            self._task_hourly_counts = {}

        hour_key = now.strftime("%Y-%m-%d-%H")
        self._task_hourly_counts[hour_key] = self._task_hourly_counts.get(hour_key, 0) + 1
        if self._task_hourly_counts[hour_key] > self._budget_limits["max_tasks_per_hour"]:
            return False, f"Hourly task limit ({self._budget_limits['max_tasks_per_hour']}) exceeded"

        if max_tokens > self._budget_limits["max_tokens_per_task"]:
            return False, f"Task token limit ({self._budget_limits['max_tokens_per_task']}) exceeded"

        projected = self._budget_tracker["daily_tokens"] + max_tokens
        if projected > self._budget_limits["daily_tokens"]:
            return False, f"Daily token budget ({self._budget_limits['daily_tokens']}) would be exceeded"

        return True, "OK"

    def _record_token_usage(self, tokens: int):
        self._budget_tracker["total_tokens"] += tokens
        self._budget_tracker["daily_tokens"] += tokens

    def _save_checkpoint(self, task_id: str, stage: str, state: dict):
        self._checkpoints[task_id] = {
            "stage": stage,
            "state": state,
            "timestamp": datetime.now().isoformat()
        }

    def _load_checkpoint(self, task_id: str) -> Optional[dict]:
        return self._checkpoints.get(task_id)

    def resume_task(self, task_id: str) -> Tuple[bool, Any]:
        checkpoint = self._load_checkpoint(task_id)
        if not checkpoint:
            return False, "No checkpoint found for task"
        return True, checkpoint

    def get_budget_status(self) -> dict:
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d-%H")
        return {
            "daily_tokens_used": self._budget_tracker["daily_tokens"],
            "daily_token_limit": self._budget_limits["daily_tokens"],
            "daily_remaining": self._budget_limits["daily_tokens"] - self._budget_tracker["daily_tokens"],
            "total_tokens_all_time": self._budget_tracker["total_tokens"],
            "tasks_this_hour": self._task_hourly_counts.get(hour_key, 0),
            "hourly_limit": self._budget_limits["max_tasks_per_hour"],
            "max_tokens_per_task": self._budget_limits["max_tokens_per_task"],
        }


def load_orchestrator() -> Orchestrator:
    """Factory function."""
    return Orchestrator()


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0, r"str(Path(__file__).resolve().parent.parent)"
    )

    print("=== Orchestrator - Phase 7 ===\n")

    orch = load_orchestrator()

    # Test model connectivity
    print("--- Model Connectivity ---")
    client = orch.llm_client
    for key, url in MODEL_ENDPOINTS.items():
        success, result = client.chat_completion(key, [{"role": "user", "content": "Hello, respond with a short greeting"}], max_tokens=20)
        status = "ONLINE" if success else f"OFFLINE ({result[:80]})"
        print(f"  {MODEL_CAPABILITIES[key]['label']}: {status}")

    # Test complexity classification
    print("--- Complexity Classification ---")
    test_queries = [
        "What time is it?",
        "List all files in the directory",
        "Explain how the memory system works",
        "Design a complete e-commerce automation pipeline",
        "Write a story about robots",
        "Debug this Python function that crashes",
        "Optimize the SQLite query performance",
        "Quick, what's 2+2?",
        "Build a full REST API with authentication",
    ]

    for q in test_queries:
        complexity = orch.classify_complexity(q)
        model = orch.select_model(q, complexity)
        agent = orch.select_agent(q)
        print(f"  '{q[:50]}...'")
        print(f"    complexity={complexity}, model={model}, agent={agent}")

    # Create and execute tasks
    print("\n--- Task Creation & Execution ---")
    task1 = orch.create_task("What models are currently running?")
    print(f"  Created: {task1.task_id} (model={task1.assigned_model})")
    success, result = orch.execute_task(task1.task_id)
    print(f"  Success: {success}")
    print(f"  Result: {result[:200]}..." if result else "  No result")

    task2 = orch.create_task("Design a complete e-commerce automation system with price monitoring and inventory management")
    print(f"\n  Created: {task2.task_id} (complexity={task2.complexity})")
    print(f"  Subtasks: {len(task2.subtasks)}")
    for st in task2.subtasks:
        print(f"    - {st['name']} ({st['type']}, model={st['model']})")

    # Model info
    print("\n--- Available Models ---")
    for m in orch.get_available_models():
        print(f"  {m['label']} ({m['params']})")
        print(f"    Speed: {m['speed']}, Quality: {m['quality']}")
        print(f"    Strengths: {', '.join(m['strengths'][:3])}")

    print("\n--- Stats ---")
    stats = orch.get_stats()
    print(json.dumps(stats, indent=2))

    print("\nPhase 7 orchestrator test complete.")
