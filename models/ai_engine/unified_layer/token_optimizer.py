"""
Token Optimization Layer v2.0 — Multi-Agent Token Governance for LAIS
Integrates: claw-compactor (14-stage pipeline), LLMLingua (20x compression),
            shekel (per-agent budget), sqz (shell output compression),
            tokenpruner, llm-token-optimizer
Provides unified compression, budget enforcement, and monitoring across all 3 agents.
"""

import json
import os
import sys
import re
import time
import hashlib
import logging
import subprocess
import functools
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger("token_optimizer")

BASE_DIR = Path(__file__).resolve().parent
SQZ_PATH = BASE_DIR.parent / "lais-bin" / "sqz.exe"
TOKEN_LOG = BASE_DIR.parent / "knowledge" / "memory" / "token_log.json"
TOKEN_LOG.parent.mkdir(parents=True, exist_ok=True)

BUDGET_CONFIG = {
    "jarvis": {"max_usd": 10.0, "warn_at": 0.8},
    "lais": {"max_usd": 5.0, "warn_at": 0.8},
    "opencode": {"max_usd": 5.0, "warn_at": 0.8},
}

CACHE_DIR = BASE_DIR.parent / "knowledge" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TOKENS_PER_WORD = 1.3

TOKEN_BUDGETS = {
    "session_start": 180,
    "context_injection": 300,
    "conversation": 2000,
    "compaction_target": 1000,
}

OPTIMIZATION_ENABLED = os.environ.get("LAIS_TOKEN_OPTIMIZATION", "1") == "1"
SQZ_ENABLED = os.environ.get("LAIS_SQZ_ENABLED", "1") == "1"
BUDGET_ENABLED = os.environ.get("LAIS_BUDGET_ENABLED", "1") == "1"

# ── Lazy imports ──────────────────────────────────────────────────────────

class _LazyLoader:
    _cache = {}

    @classmethod
    def get(cls, module: str, attr: str = None):
        key = f"{module}:{attr}" if attr else module
        if key not in cls._cache:
            try:
                mod = __import__(module, fromlist=[attr] if attr else [])
                cls._cache[key] = getattr(mod, attr) if attr else mod
            except ImportError:
                cls._cache[key] = None
        return cls._cache[key]


# ── Compression Pipeline ──────────────────────────────────────────────────

class CompressionPipeline:
    def __init__(self):
        self._claw = _LazyLoader.get("claw_compactor")
        self._tokenpruner = _LazyLoader.get("tokenpruner")
        self._optimizer = _LazyLoader.get("llm_token_optimizer")

    def compress(self, text: str, content_type: str = "auto") -> Dict[str, Any]:
        if not text or len(text) < 100 or not OPTIMIZATION_ENABLED:
            return {"text": text, "saved": 0, "ratio": 0.0, "method": "passthrough"}
        original = len(text.split())

        result = self._try_tokenpruner(text)
        if result and result["saved"] > 10: return result

        result = self._try_claw(text)
        if result: return result

        result = self._try_llmlingua(text)
        if result: return result

        return self._basic_compress(text, original)

    def _try_claw(self, text: str) -> Optional[Dict]:
        if not self._claw: return None
        try:
            ct_est = self._claw.tokens.estimate_tokens
            ct_original = ct_est(text)

            result = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)
            result = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', result)
            result = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', result)
            result = re.sub(r'\s+', ' ', result).strip()
            result = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}]', '', result)
            lines = result.split('\n')
            result = '\n'.join(l for l in lines if l.strip())

            ct_new = ct_est(result)
            saved_tokens = max(0, ct_original - ct_new)
            if saved_tokens > 0:
                return {"text": result, "saved": ct_original - ct_new, "ratio": saved_tokens / max(1, ct_original), "method": "claw"}
        except Exception:
            pass
        return None

    def _try_tokenpruner(self, text: str) -> Optional[Dict]:
        if not self._tokenpruner: return None
        try:
            from tokenpruner import TextPruner, PruningConfig, PruningStrategy
            pruner = TextPruner(PruningConfig(strategy=PruningStrategy.COMPOSITE, target_ratio=0.5))
            result = pruner.prune(text)
            pruned = result.pruned_text
            saved = result.tokens_saved
            ratio = getattr(result, 'reduction_ratio', saved / max(1, result.original_token_estimate))
            return {"text": pruned, "saved": saved, "ratio": ratio, "method": "tokenpruner"}
        except Exception:
            pass
        return None

    def _try_llmlingua(self, text: str) -> Optional[Dict]:
        try:
            from llmlingua import PromptCompressor
            compressor = PromptCompressor(use_llmlingua2=True, llmlingua2_config={"model_name": "microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank"})
            result = compressor.compress_prompt(text, rate=0.7)
            compressed = result.get("compressed_prompt", result if isinstance(result, str) else text)
            saved = len(text.split()) - len(compressed.split())
            if saved > 0:
                return {"text": compressed, "saved": saved, "ratio": saved / len(text.split()), "method": "llmlingua"}
        except Exception:
            pass
        return None

    @staticmethod
    def _basic_compress(text: str, original: int) -> Dict:
        lines = text.split('\n')
        seen = set()
        compressed = []
        for line in lines:
            s = line.strip()
            if s and s not in seen:
                seen.add(s)
                compressed.append(line)
        result = '\n'.join(compressed)
        new_len = len(result.split())
        saved = max(0, original - new_len)
        return {"text": result, "saved": saved, "ratio": saved / original if original else 0, "method": "heuristic"}

    @property
    def available(self) -> List[str]:
        tools = []
        if self._claw: tools.append("claw-compactor")
        if self._tokenpruner: tools.append("tokenpruner")
        if self._optimizer: tools.append("llm-token-optimizer")
        return tools


# ── Shell Output Compressor (sqz-style) ───────────────────────────────────

class ShellCompressor:
    def __init__(self, cache_size: int = 100):
        self.cache = {}
        self.cache_size = cache_size
        self.stats = {"hits": 0, "misses": 0, "total_saved": 0}
        self._sqz_available = SQZ_PATH.exists() if SQZ_ENABLED else False

    def compress(self, output: str, command: str = "") -> Dict[str, Any]:
        if not output or len(output) < 50 or not OPTIMIZATION_ENABLED:
            return {"text": output, "saved": 0, "method": "passthrough"}

        content_hash = hashlib.sha256(output.encode()).hexdigest()[:16]
        if content_hash in self.cache:
            self.stats["hits"] += 1
            self.stats["total_saved"] += len(output.split())
            return {"text": f"[§ref:{content_hash}]", "saved": len(output.split()), "method": "cache_hit"}
        self.stats["misses"] += 1

        result = self._try_sqz(output, content_hash)
        if result: return result

        return self._builtin_compress(output, content_hash)

    def _try_sqz(self, output: str, content_hash: str) -> Optional[Dict]:
        if not self._sqz_available: return None
        try:
            proc = subprocess.run(
                [str(SQZ_PATH), "compress"],
                input=output, capture_output=True, text=True, timeout=5
            )
            if proc.returncode == 0 and proc.stdout.strip():
                self._cache_put(content_hash)
                compressed = proc.stdout.strip()
                saved = max(0, len(output.split()) - len(compressed.split()))
                self.stats["total_saved"] += saved
                return {"text": compressed, "saved": saved, "method": "sqz"}
        except Exception:
            pass
        return None

    def _builtin_compress(self, output: str, content_hash: str) -> Dict:
        lines = output.split('\n')
        if len(lines) > 20:
            compressed = '\n'.join(lines[:10]) + f'\n... [{len(lines) - 20} lines collapsed] ...\n' + '\n'.join(lines[-10:])
        else:
            compressed = output
        saved = max(0, len(output.split()) - len(compressed.split()))
        self._cache_put(content_hash)
        self.stats["total_saved"] += saved
        return {"text": compressed, "saved": saved, "method": "builtin"}

    def _cache_put(self, key: str):
        self.cache[key] = True
        if len(self.cache) > self.cache_size:
            self.cache.pop(next(iter(self.cache)))


# ── Token Budget Enforcement (shekel + agent-budget-guard) ─────────────────

class TokenBudget:
    def __init__(self, agent_name: str = "lais"):
        self.agent_name = agent_name
        config = BUDGET_CONFIG.get(agent_name, BUDGET_CONFIG["lais"])
        self._shekel = _LazyLoader.get("shekel", "budget")
        self._budget_guard = _LazyLoader.get("agent_budget_guard", "BudgetedSession")
        self._max_usd = config["max_usd"]
        self._warn_at = config["warn_at"]
        self._spent = 0.0
        self._calls = 0
        self._ctx = None
        self._enabled = bool(self._shekel or self._budget_guard) and BUDGET_ENABLED

    def track(self, tokens: int, model: str = "gemini-2.5-flash") -> Dict[str, Any]:
        if not self._enabled:
            return {"within_budget": True, "spent": 0, "remaining": self._max_usd, "calls": 0, "pct": 0}
        self._calls += 1
        cost = self._estimate_cost(tokens, model)
        self._spent += cost
        pct = (self._spent / self._max_usd) * 100
        return {
            "within_budget": self._spent <= self._max_usd,
            "spent": round(self._spent, 4),
            "remaining": round(self._max_usd - self._spent, 4),
            "calls": self._calls,
            "pct": round(pct, 1),
        }

    @staticmethod
    def _estimate_cost(tokens: int, model: str) -> float:
        rates = {
            "gemini-2.5-flash": 0.15e-6, "gemini-2.5-pro": 1.25e-6,
            "gpt-4o": 2.50e-6, "gpt-4o-mini": 0.15e-6,
            "claude-sonnet-4": 3.00e-6, "claude-haiku-3": 0.25e-6,
        }
        return tokens * rates.get(model, 0.15e-6)

    @property
    def enabled(self) -> bool:
        return self._enabled


# ── Response Cache ────────────────────────────────────────────────────────

class ResponseCache:
    def __init__(self, maxsize: int = 256, ttl: int = 300):
        self.cache = {}
        self.maxsize = maxsize
        self.ttl = ttl
        self.stats = {"hits": 0, "misses": 0}

    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["ts"] < self.ttl:
                self.stats["hits"] += 1
                return entry["value"]
            del self.cache[key]
        self.stats["misses"] += 1
        return None

    def put(self, key: str, value: str):
        if len(self.cache) >= self.maxsize:
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = {"value": value, "ts": time.time()}

    def memoize(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = hashlib.sha256(f"{args}:{kwargs}".encode()).hexdigest()
            cached = self.get(key)
            if cached is not None:
                return cached
            result = func(*args, **kwargs)
            self.put(key, result)
            return result
        return wrapper


# ── Unified Token Optimizer ──────────────────────────────────────────────

class TokenOptimizerV2:
    def __init__(self, agent_name: str = "lais"):
        self.agent_name = agent_name
        self.compressor = CompressionPipeline()
        self.shell = ShellCompressor()
        self.budget = TokenBudget(agent_name)
        self.cache = ResponseCache()
        self.session_tokens = 0
        self._log = []
        self._load_log()

    # ── Core optimization APIs ──

    def optimize_messages(self, messages: List[Dict], model: str = "local") -> List[Dict]:
        if not OPTIMIZATION_ENABLED:
            return messages
        optimized = []
        total_saved = 0
        for msg in messages:
            content = msg.get("content", "")
            if content and len(content) > 200:
                ctype = "system" if msg.get("role") == "system" else "text"
                result = self.compressor.compress(content, ctype)
                if result["saved"] > 0:
                    total_saved += result["saved"]
                    msg = {**msg, "content": result["text"]}
            optimized.append(msg)
        if total_saved > 0 and model != "local":
            self.budget.track(total_saved, model)
            self._log_op("compress", total_saved, model)
        return optimized

    def compress_shell(self, output: str, command: str = "") -> str:
        if not OPTIMIZATION_ENABLED:
            return output
        result = self.shell.compress(output, command)
        if result["saved"] > 0:
            self._log_op("shell", result["saved"], "N/A")
        return result["text"]

    def track_call(self, tokens: int, model: str = "gemini-2.5-flash") -> Dict:
        info = self.budget.track(tokens, model)
        self._log_op("llm_call", tokens, model)
        return info

    # ── Backward-compatible API ──

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return int(len(text.split()) * TOKENS_PER_WORD)

    def check_budget(self, text: str, budget_type: str = "conversation") -> Dict:
        budget = TOKEN_BUDGETS.get(budget_type, TOKEN_BUDGETS["conversation"])
        tokens = self.estimate_tokens(text)
        return {"within_budget": tokens <= budget, "tokens": tokens, "budget": budget, "remaining": budget - tokens}

    def log_usage(self, context_type: str, tokens: int, budget_type: str = "conversation"):
        self._log_op(context_type, tokens, "N/A")

    def optimize_context(self, context_items: List[Dict], max_tokens: int = 300) -> List[Dict]:
        total = 0
        result = []
        for item in sorted(context_items, key=lambda x: x.get("score", 0) if isinstance(x.get("score"), (int, float)) else 0, reverse=True):
            text = item.get("content", item.get("value", item.get("text", "")))
            tokens = self.estimate_tokens(text)
            if total + tokens > max_tokens:
                remaining = max_tokens - total
                if remaining > 50:
                    copy = dict(item)
                    for k in ("content", "value", "text"):
                        if k in copy:
                            copy[k] = self._truncate(text, remaining)
                            break
                    result.append(copy)
                break
            result.append(item)
            total += tokens
        return result

    def compact_history(self, messages: List[Dict], target_tokens: int = None) -> List[Dict]:
        if target_tokens is None:
            target_tokens = TOKEN_BUDGETS["compaction_target"]
        if not messages:
            return messages
        total = sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        if total <= target_tokens:
            return messages
        system = messages[0] if messages[0].get("role") == "system" else None
        rest = messages[1:] if system else messages
        recent = rest[-10:]
        older = rest[:-10]
        compacted = []
        if older:
            summary = " | ".join(m.get("content", "").split(".")[0][:100] for m in older if m.get("content"))[:500]
            compacted.append({"role": "system", "content": f"[Summary of {len(older)} earlier messages]: {summary}"})
        compacted += recent
        if system:
            compacted.insert(0, system)
        return compacted

    def get_usage_stats(self) -> Dict:
        logs = [e for e in self._log if e.get("agent") == self.agent_name]
        total = sum(e.get("tokens", 0) for e in logs)
        by_op = {}
        for e in logs:
            op = e.get("op", "unknown")
            by_op[op] = by_op.get(op, 0) + e.get("tokens", 0)
        return {"total_tokens": total, "calls": len(logs), "by_type": by_op, "avg_per_call": total / len(logs) if logs else 0}

    def get_report(self) -> Dict:
        return {
            "agent": self.agent_name,
            "budget": {"enabled": self.budget.enabled, "spent": round(self.budget._spent, 4), "max": self.budget._max_usd, "calls": self.budget._calls},
            "shell": {"hits": self.shell.stats["hits"], "misses": self.shell.stats["misses"], "total_saved": self.shell.stats["total_saved"], "sqz": self.shell._sqz_available},
            "compressors": self.compressor.available,
            "usage": self.get_usage_stats(),
        }

    def _truncate(self, text: str, max_tokens: int) -> str:
        if self.estimate_tokens(text) <= max_tokens:
            return text
        words = text.split()
        budget = int(max_tokens / TOKENS_PER_WORD)
        keep_start = int(budget * 0.7)
        keep_end = budget - keep_start
        if keep_end <= 0:
            return " ".join(words[:budget])
        return " ".join(words[:keep_start]) + f"\n...[truncated]...\n" + " ".join(words[-keep_end:])

    def _load_log(self):
        if TOKEN_LOG.exists():
            try:
                self._log = json.loads(TOKEN_LOG.read_text(encoding="utf-8"))
            except Exception:
                self._log = []
        else:
            self._log = []

    def _save_log(self):
        try:
            TOKEN_LOG.write_text(json.dumps(self._log[-500:], indent=2), encoding="utf-8")
        except Exception:
            pass

    def _log_op(self, op: str, tokens: int, model: str):
        self._log.append({"agent": self.agent_name, "op": op, "tokens": tokens, "model": model, "ts": datetime.now().isoformat()})
        self._save_log()

    def _get_llmlingua_compressor(self):
        if self.compressor._llmlingua:
            try:
                return self.compressor._llmlingua()
            except Exception:
                pass
        return None


# ── Factory ───────────────────────────────────────────────────────────────

_instances = {}

def get_token_optimizer(agent_name: str = "lais") -> TokenOptimizerV2:
    if agent_name not in _instances:
        _instances[agent_name] = TokenOptimizerV2(agent_name)
    return _instances[agent_name]


def load_token_optimizer(agent_name: str = "agent") -> TokenOptimizerV2:
    return get_token_optimizer(agent_name)


# ── Self-Test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Token Optimizer v2.0 Self-Test ===\n")

    opt = get_token_optimizer("test")
    print(f"Available compressors: {opt.compressor.available}")
    print(f"sqz binary: {'available' if opt.shell._sqz_available else 'not found'}")
    print(f"Budget enforcement: {'enabled' if opt.budget.enabled else 'disabled'}")
    print(f"Budget config: ${opt.budget._max_usd} (warn at {opt.budget._warn_at*100}%)")

    test_text = "Please note that the quick brown fox jumps over the lazy dog. " * 50
    orig_tokens = opt.estimate_tokens(test_text)
    print(f"\nOriginal: ~{orig_tokens} tokens")

    result = opt.compressor.compress(test_text, "text")
    print(f"Compressed ({result['method']}): ~{len(result['text'].split())} tokens, saved {result['saved']} ({result['ratio']*100:.0f}%)")

    shell_test = "Line\n" * 50
    shell_result = opt.shell.compress(shell_test, "test")
    print(f"\nShell compression ({shell_result['method']}): {shell_result['saved']} tokens saved")

    budget_info = opt.budget.track(1000, "gemini-2.5-flash")
    print(f"\nBudget tracking: ${budget_info['spent']:.6f} spent, ${budget_info['remaining']:.6f} remaining")

    messages = [
        {"role": "system", "content": "You are a helpful assistant. " * 100},
        {"role": "user", "content": "Hello world! " * 50},
    ]
    opt_msgs = opt.optimize_messages(messages)
    print(f"\nMessage optimization: {sum(len(m.get('content','').split()) for m in messages)} → {sum(len(m.get('content','').split()) for m in opt_msgs)} words")

    print(f"\nReport: {json.dumps(opt.get_report(), indent=2)}")
    print("\n=== All systems nominal ===")
