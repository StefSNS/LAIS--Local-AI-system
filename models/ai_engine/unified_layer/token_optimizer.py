"""
Token Optimization Protocol - Manages token budgets and context compaction.
Ensures efficient token usage across all agents.
"""

import sys
from pathlib import Path

# Add project root to path
LAIS_PATH = Path(r"str(Path(__file__).resolve().parent.parent)")
if str(LAIS_PATH) not in sys.path:
    sys.path.insert(0, str(LAIS_PATH))

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

TOKEN_LOG_FILE = Path(
    r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\token_log.json"
)
TOKEN_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Token budgets per agent/session type
TOKEN_BUDGETS = {
    "session_start": 180,   # Context injection at session start
    "context_injection": 300, # Vault context for queries
    "conversation": 2000,    # Total conversation context
    "compaction_target": 1000, # Target after compaction
}

# Approximate tokens per word (conservative estimate)
TOKENS_PER_WORD = 1.3


def estimate_tokens(text: str) -> int:
    """Estimate token count from text."""
    if not text:
        return 0
    words = len(text.split())
    return int(words * TOKENS_PER_WORD)


def truncate_to_budget(text: str, max_tokens: int) -> str:
    """Truncate text to fit within token budget."""
    if estimate_tokens(text) <= max_tokens:
        return text
    
    words = text.split()
    budget_words = int(max_tokens / TOKENS_PER_WORD)
    
    # Keep first 70% and last 30% for context
    keep_start = int(budget_words * 0.7)
    keep_end = budget_words - keep_start
    
    if keep_end <= 0:
        return " ".join(words[:budget_words])
    
    start_text = " ".join(words[:keep_start])
    end_text = " ".join(words[-keep_end:])
    
    return f"{start_text}\n...[truncated]...\n{end_text}"


class TokenOptimizer:
    """
    Manages token budgets and context compaction for all agents.
    Tracks usage and provides optimization suggestions.
    """
    
    def __init__(self, agent_name: str = "agent"):
        self.agent_name = agent_name
        self.session_tokens = 0
        self.max_session_tokens = TOKEN_BUDGETS["conversation"]
        self._load_log()
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        return estimate_tokens(text)
    
    def _load_log(self):
        """Load token usage log."""
        if TOKEN_LOG_FILE.exists():
            try:
                data = json.loads(TOKEN_LOG_FILE.read_text(encoding="utf-8"))
                self.log = data
            except Exception:
                self.log = []
        else:
            self.log = []
    
    def _save_log(self):
        """Save token usage log."""
        try:
            TOKEN_LOG_FILE.write_text(
                json.dumps(self.log[-500:], indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass
    
    def check_budget(self, text: str, budget_type: str = "conversation") -> Dict[str, Any]:
        """
        Check if text fits within budget.
        Returns: {"within_budget": bool, "tokens": int, "budget": int, "remaining": int}
        """
        budget = TOKEN_BUDGETS.get(budget_type, TOKEN_BUDGETS["conversation"])
        tokens = estimate_tokens(text)
        
        return {
            "within_budget": tokens <= budget,
            "tokens": tokens,
            "budget": budget,
            "remaining": budget - tokens,
        }
    
    def optimize_context(self, context_items: List[Dict], max_tokens: int = 300) -> List[Dict]:
        """
        Optimize a list of context items to fit within token budget.
        Prioritizes items by relevance score.
        """
        total_tokens = 0
        optimized = []
        
        # Sort by relevance (if available) or recency
        sorted_items = sorted(
            context_items,
            key=lambda x: x.get("score", 0) if isinstance(x.get("score"), (int, float)) else 0,
            reverse=True
        )
        
        for item in sorted_items:
            text = ""
            if "content" in item:
                text = item["content"]
            elif "value" in item:
                text = item["value"]
            elif "text" in item:
                text = item["text"]
            
            item_tokens = estimate_tokens(text)
            
            if total_tokens + item_tokens > max_tokens:
                # Try truncating
                available = max_tokens - total_tokens
                if available > 50:  # Only include if meaningful
                    item_copy = item.copy()
                    if "content" in item_copy:
                        item_copy["content"] = truncate_to_budget(text, available)
                    elif "value" in item_copy:
                        item_copy["value"] = truncate_to_budget(text, available)
                    optimized.append(item_copy)
                break
            
            optimized.append(item)
            total_tokens += item_tokens
        
        return optimized
    
    def compact_history(self, messages: List[Dict], target_tokens: int = None) -> List[Dict]:
        """
        Compact conversation history to fit within target token count.
        Keeps first message (system prompt) and last N messages.
        Summarizes middle messages.
        """
        if target_tokens is None:
            target_tokens = TOKEN_BUDGETS["compaction_target"]
        
        if not messages:
            return messages
        
        # Calculate current tokens
        total_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)
        
        if total_tokens <= target_tokens:
            return messages
        
        # Keep system message (first) and recent messages
        system_msg = messages[0] if messages[0].get("role") == "system" else None
        other_msgs = messages[1:] if system_msg else messages
        
        # Keep last 10 messages intact
        recent_count = min(10, len(other_msgs))
        recent = other_msgs[-recent_count:]
        older = other_msgs[:-recent_count]
        
        # Summarize older messages
        if older:
            summary = self._summarize_messages(older)
            summary_msg = {
                "role": "system",
                "content": f"[Summary of {len(older)} earlier messages]: {summary}"
            }
            compacted = [summary_msg] + recent
        else:
            compacted = recent
        
        if system_msg:
            compacted.insert(0, system_msg)
        
        return compacted
    
    def _summarize_messages(self, messages: List[Dict]) -> str:
        """Create a brief summary of messages."""
        if not messages:
            return ""
        
        # Extract key info
        topics = []
        for msg in messages:
            content = msg.get("content", "")
            if content:
                # Extract first sentence or first 100 chars
                first_part = content.split(".")[0][:100]
                if first_part:
                    topics.append(first_part)
        
        return " | ".join(topics[:5])
    
    def log_usage(self, context_type: str, tokens: int, budget_type: str = "conversation"):
        """Log token usage for analytics."""
        entry = {
            "agent": self.agent_name,
            "type": context_type,
            "tokens": tokens,
            "budget": TOKEN_BUDGETS.get(budget_type, 0),
            "timestamp": datetime.now().isoformat(),
        }
        self.log.append(entry)
        self._save_log()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics for this agent."""
        agent_logs = [l for l in self.log if l.get("agent") == self.agent_name]
        
        if not agent_logs:
            return {"total_tokens": 0, "calls": 0}
        
        total = sum(l.get("tokens", 0) for l in agent_logs)
        
        by_type = {}
        for log in agent_logs:
            t = log.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + log.get("tokens", 0)
        
        return {
            "total_tokens": total,
            "calls": len(agent_logs),
            "by_type": by_type,
            "avg_per_call": total / len(agent_logs) if agent_logs else 0,
        }


def load_token_optimizer(agent_name: str = "agent") -> TokenOptimizer:
    """Factory function."""
    return TokenOptimizer(agent_name)


if __name__ == "__main__":
    print("=== Token Optimizer Test ===\n")
    
    optimizer = TokenOptimizer("test")
    
    # Test token estimation
    test_text = "Hello world! " * 50
    tokens = estimate_tokens(test_text)
    print(f"Estimated tokens for 50x 'Hello world!': {tokens}")
    
    # Test budget check
    budget_check = optimizer.check_budget(test_text, "session_start")
    print(f"\nBudget check (session_start):")
    print(f"  Tokens: {budget_check['tokens']}")
    print(f"  Budget: {budget_check['budget']}")
    print(f"  Within budget: {budget_check['within_budget']}")
    
    # Test truncation
    truncated = truncate_to_budget(test_text, 50)
    print(f"\nTruncated to 50 tokens: {truncated[:100]}...")
    
    # Test context optimization
    context_items = [
        {"content": "A" * 200, "score": 0.9},
        {"content": "B" * 200, "score": 0.7},
        {"content": "C" * 200, "score": 0.5},
        {"content": "D" * 200, "score": 0.3},
    ]
    optimized = optimizer.optimize_context(context_items, max_tokens=100)
    print(f"\nContext optimization: {len(context_items)} -> {len(optimized)} items")
    
    # Test history compaction
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ]
    # Add 20 message pairs
    for i in range(20):
        messages.append({"role": "user", "content": f"Message {i}"})
        messages.append({"role": "assistant", "content": f"Response {i}"})
    
    compacted = optimizer.compact_history(messages, target_tokens=200)
    print(f"\nHistory compaction: {len(messages)} -> {len(compacted)} messages")
    
    # Print stats
    optimizer.log_usage("test", tokens, "session_start")
    stats = optimizer.get_usage_stats()
    print(f"\nUsage stats: {stats}")
    
    print("\nToken optimizer test complete.")
