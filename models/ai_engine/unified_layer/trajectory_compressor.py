"""
Trajectory Compressor - Compresses conversation history for storage and training.
Based on Hermes Agent's trajectory compression system.
"""

import json
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class TrajectoryCompressor:
    """
    Compresses agent trajectories for:
    - Efficient storage (40-60% reduction)
    - Training data preparation
    - Long-term memory offloading
    """

    def __init__(self):
        self.compression_cache: Dict[str, str] = {}

    def compress_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress a single message by:
        - Removing redundant whitespace
        - Truncating long code blocks
        - Normalizing tool call formats
        """
        role = message.get("role", "")
        content = message.get("content", "")

        if role == "assistant" and "tool_calls" in message:
            compressed = self._compress_tool_calls(message)
        elif content:
            compressed = self._compress_content(content)
        else:
            compressed = {}

        compressed["role"] = role
        if "name" in message:
            compressed["name"] = message["name"]

        return compressed

    def _compress_content(self, content: str) -> Dict[str, Any]:
        """Compress text content."""
        content = re.sub(r'\n\n+', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        content = content.strip()

        code_blocks = re.findall(r'```[\s\S]*?```', content)
        for i, block in enumerate(code_blocks):
            if len(block) > 500:
                lines = block.split('\n')
                if len(lines) > 20:
                    compressed_block = '\n'.join(lines[:10] + [f"... [{len(lines) - 20} lines truncated] ..."] + lines[-5:])
                    content = content.replace(block, compressed_block)

        return {"content": content[:8000]} if len(content) > 8000 else {"content": content}

    def _compress_tool_calls(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Compress tool calls."""
        tool_calls = message.get("tool_calls", [])
        compressed_calls = []

        for tc in tool_calls:
            compressed = {
                "type": "tool_call",
                "name": tc.get("name", tc.get("function", {}).get("name", "")),
            }

            args = tc.get("arguments") or tc.get("function", {}).get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass

            if isinstance(args, dict):
                simplified = {}
                for k, v in args.items():
                    if isinstance(v, str) and len(v) > 200:
                        simplified[k] = v[:200] + "..."
                    else:
                        simplified[k] = v
                compressed["arguments"] = simplified

            compressed_calls.append(compressed)

        return {"tool_calls": compressed_calls}

    def compress_trajectory(
        self,
        messages: List[Dict[str, Any]],
        strategy: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Compress an entire trajectory.

        Strategies:
        - "aggressive": Maximum compression, loses detail
        - "balanced": Good compression, maintains key info
        - "hybrid": Combines multiple techniques
        """
        if strategy == "aggressive":
            return self._aggressive_compress(messages)
        elif strategy == "balanced":
            return self._balanced_compress(messages)
        else:
            return self._hybrid_compress(messages)

    def _aggressive_compress(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Maximum compression - removes most details."""
        compressed_messages = []
        tool_call_count = 0

        for msg in messages:
            compressed = self.compress_message(msg)

            if msg.get("role") == "assistant":
                if "tool_calls" in msg:
                    tool_call_count += len(msg["tool_calls"])

            if compressed.get("content"):
                if len(compressed["content"]) > 500:
                    compressed["content"] = compressed["content"][:500] + "..."

            compressed_messages.append(compressed)

        return {
            "strategy": "aggressive",
            "original_count": len(messages),
            "compressed_count": len(compressed_messages),
            "tool_calls": tool_call_count,
            "messages": compressed_messages,
            "compressed_at": datetime.now().isoformat(),
        }

    def _balanced_compress(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Balanced compression - keeps key information."""
        compressed_messages = []
        summary_messages = []
        tool_call_count = 0

        prev_role = None
        for msg in messages:
            compressed = self.compress_message(msg)

            if msg.get("role") == "assistant":
                if "tool_calls" in msg:
                    tool_call_count += len(msg["tool_calls"])

            if prev_role == msg.get("role") and msg.get("role") == "user":
                if summary_messages:
                    combined = summary_messages[-1]["content"] + "\n" + (compressed.get("content") or "")
                    summary_messages[-1]["content"] = combined[:2000]
                    continue

            compressed_messages.append(compressed)
            summary_messages.append(compressed)
            prev_role = msg.get("role")

        return {
            "strategy": "balanced",
            "original_count": len(messages),
            "compressed_count": len(compressed_messages),
            "tool_calls": tool_call_count,
            "messages": compressed_messages,
            "compressed_at": datetime.now().isoformat(),
        }

    def _hybrid_compress(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Hybrid compression - best of both worlds."""
        compressed_messages = []
        tool_calls = []
        summary_tokens = []

        for msg in messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                tc = msg["tool_calls"]
                for t in tc:
                    tool_calls.append({
                        "tool": t.get("name", t.get("function", {}).get("name", "")),
                        "timestamp": msg.get("timestamp", ""),
                    })
                continue

            compressed = self.compress_message(msg)
            if compressed.get("content"):
                compressed_messages.append(compressed)
                tokens = len(compressed["content"].split())
                summary_tokens.append(tokens)

        return {
            "strategy": "hybrid",
            "original_count": len(messages),
            "compressed_count": len(compressed_messages),
            "tool_calls_extracted": len(tool_calls),
            "total_tokens": sum(summary_tokens),
            "messages": compressed_messages,
            "tool_calls": tool_calls[:50],
            "compressed_at": datetime.now().isoformat(),
        }

    def decompress_trajectory(self, compressed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompress a compressed trajectory."""
        return compressed.get("messages", [])

    def calculate_compression_ratio(self, original: List[Dict[str, Any]], compressed: Dict[str, Any]) -> float:
        """Calculate compression ratio."""
        orig_size = sum(len(json.dumps(m)) for m in original)
        comp_size = len(json.dumps(compressed))
        if orig_size == 0:
            return 0.0
        return (1 - comp_size / orig_size) * 100

    def batch_compress(
        self,
        trajectories: List[List[Dict[str, Any]]],
        strategy: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """Compress multiple trajectories."""
        return [
            self.compress_trajectory(traj, strategy)
            for traj in trajectories
        ]


_trajectory_compressor_instance: Optional[TrajectoryCompressor] = None


def get_trajectory_compressor() -> TrajectoryCompressor:
    """Get or create the trajectory compressor instance."""
    global _trajectory_compressor_instance
    if _trajectory_compressor_instance is None:
        _trajectory_compressor_instance = TrajectoryCompressor()
    return _trajectory_compressor_instance


if __name__ == "__main__":
    tc = get_trajectory_compressor()

    sample_trajectory = [
        {"role": "user", "content": "Can you help me build a new feature for my agent?"},
        {"role": "assistant", "content": "Absolutely! Let me start by using the brainstorming skill to explore the requirements.", "tool_calls": [{"name": "skill", "arguments": {"name": "brainstorming"}}]},
        {"role": "assistant", "content": "Great, I've loaded the brainstorming skill. Let's discuss your idea. What problem does this feature solve?"},
        {"role": "user", "content": "It's for better memory management across sessions."},
        {"role": "assistant", "content": "Excellent. Memory management is crucial. Let me think about the key aspects...", "tool_calls": [{"name": "memory_search", "arguments": {"query": "memory architecture"}}]},
    ]

    print("=== Trajectory Compression ===")
    print(f"Original messages: {len(sample_trajectory)}")

    for strategy in ["aggressive", "balanced", "hybrid"]:
        compressed = tc.compress_trajectory(sample_trajectory, strategy)
        ratio = tc.calculate_compression_ratio(sample_trajectory, compressed)
        print(f"\n{strategy}:")
        print(f"  Compressed to: {compressed['compressed_count']} messages")
        print(f"  Compression ratio: {ratio:.1f}%")

    print("\n=== Decompress Test ===")
    compressed = tc.compress_trajectory(sample_trajectory, "hybrid")
    decompressed = tc.decompress_trajectory(compressed)
    print(f"Decompressed messages: {len(decompressed)}")