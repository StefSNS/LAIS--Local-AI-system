"""
MemPalace Integration â€” Bridges Knowledge Graph, Memory Stack, Contradiction Detection,
Tunnels, and Palace Miner into a unified memory palace for JARVIS/LAIS.

Provides:
- Smart context injection (uses Memory Stack L0-L3)
- Contradiction-aware fact storage
- Cross-entity tunnel discovery
- Auto-mining from vault and projects
- Natural language palace queries
"""

import os
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Paths
UNIFIED_LAYER = Path(__file__).parent
VAULT_PATH = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
PROJECTS_PATH = Path(r"%USERPROFILE%\Desktop\AI projects\Projects")
DATA_DIR = UNIFIED_LAYER / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class MemPalace:
    """Unified interface to all MemPalace modules."""

    def __init__(self):
        self.kg = None
        self.memory_stack = None
        self.contradiction_detector = None
        self.tunnel_manager = None
        self.palace_miner = None
        self.gemini = None
        self._lock = threading.Lock()
        self._initialized = False

    def initialize(self):
        """Lazy-load all modules. Safe to call multiple times."""
        if self._initialized:
            return

        try:
            from knowledge_graph import KnowledgeGraph
            self.kg = KnowledgeGraph()
        except Exception as e:
            print(f"[MemPalace] âš ï¸ KnowledgeGraph unavailable: {e}")

        try:
            from memory_stack import MemoryStack
            mem_sqlite = DATA_DIR / "memory.db"
            self.memory_stack = MemoryStack(
                memory_sqlite_path=str(mem_sqlite) if mem_sqlite.exists() else None,
                vault_path=str(VAULT_PATH) if VAULT_PATH.exists() else None
            )
        except Exception as e:
            print(f"[MemPalace] âš ï¸ MemoryStack unavailable: {e}")

        try:
            from contradiction_detection import ContradictionDetector
            kg_path = DATA_DIR / "knowledge_graph.db"
            mem_path = DATA_DIR / "memory.db"
            self.contradiction_detector = ContradictionDetector(
                knowledge_graph_path=str(kg_path) if kg_path.exists() else None,
                memory_sqlite_path=str(mem_path) if mem_path.exists() else None
            )
        except Exception as e:
            print(f"[MemPalace] âš ï¸ ContradictionDetector unavailable: {e}")

        try:
            from tunnels import TunnelManager
            self.tunnel_manager = TunnelManager()
        except Exception as e:
            print(f"[MemPalace] âš ï¸ TunnelManager unavailable: {e}")

        try:
            from palace_miner import PalaceMiner
            self.palace_miner = PalaceMiner(
                vault_path=str(VAULT_PATH),
                project_paths=[str(PROJECTS_PATH)]
            )
        except Exception as e:
            print(f"[MemPalace] âš ï¸ PalaceMiner unavailable: {e}")

        self._init_gemini()
        self._initialized = True

    def _init_gemini(self):
        try:
            config_path = Path(r"%USERPROFILE%\Desktop\AI projects\Projects\models\Mark-XXXIX\config\api_keys.json")
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    api_key = json.load(f).get("gemini_api_key")
                if api_key:
                    from google import genai
                    self.gemini = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
        except Exception as e:
            print(f"[MemPalace] âš ï¸ Gemini init failed: {e}")

    # â”€â”€ Wake-up / Context â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def get_startup_context(self, max_tokens=900) -> str:
        """Get L0+L1 context for session startup."""
        self.initialize()
        if self.memory_stack:
            return self.memory_stack.wake_up(max_tokens=max_tokens)
        return ""

    def get_query_context(self, query: str, max_tokens=500) -> str:
        """Get relevant context for a specific query."""
        self.initialize()
        if self.memory_stack:
            return self.memory_stack.recall(query=query, max_tokens=max_tokens)
        return ""

    # â”€â”€ Fact Storage (with contradiction detection) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def store_fact(self, subject: str, predicate: str, value: str,
                   source: str = "conversation", confidence: float = 1.0) -> Dict[str, Any]:
        """Store a fact, checking for contradictions first."""
        self.initialize()
        result = {"stored": False, "contradiction": False, "details": ""}

        if not self.kg:
            result["details"] = "KnowledgeGraph unavailable"
            return result

        # Check for contradictions
        if self.contradiction_detector:
            check = self.contradiction_detector.check_contradiction(subject, predicate, value)
            if check.get("has_contradiction"):
                result["contradiction"] = True
                result["details"] = check.get("explanation", "Contradiction detected")
                result["conflicting"] = check.get("conflicting", [])

                # Auto-resolve
                if len(check.get("conflicting", [])) > 0:
                    old_value = check["conflicting"][0].get("value", "")
                    strategy = self.contradiction_detector.auto_resolve(
                        subject, predicate, value, old_value
                    )
                    result["resolution_strategy"] = strategy

        # Store the fact
        try:
            rowid = self.kg.add_triple(
                subject=subject,
                predicate=predicate,
                obj=value,
                confidence=confidence,
                source=source
            )
            result["stored"] = True
            result["rowid"] = rowid
            if not result["details"]:
                result["details"] = f"Stored fact #{rowid}"
        except Exception as e:
            result["details"] = f"Storage failed: {e}"

        return result

    # â”€â”€ Knowledge Graph Queries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def query(self, subject: str = None, predicate: str = None,
              obj: str = None, limit: int = 20) -> List[Dict]:
        """Query the knowledge graph with optional filters."""
        self.initialize()
        if not self.kg:
            return []

        try:
            return self.kg.query_triples(
                subject=subject, predicate=predicate, obj=obj, limit=limit
            )
        except Exception:
            return []

    def search_facts(self, query: str, limit: int = 10) -> List[Dict]:
        """Full-text search across all triples."""
        self.initialize()
        if not self.kg:
            return []

        try:
            return self.kg.search_triples(query, limit=limit)
        except Exception:
            return []

    def get_entity_info(self, entity_name: str) -> Dict[str, Any]:
        """Get all facts about an entity."""
        self.initialize()
        if not self.kg:
            return {}

        try:
            return self.kg.get_entity(entity_name)
        except Exception:
            return {}

    # â”€â”€ Tunnels (Cross-Wing Connections) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def discover_tunnels(self) -> List[Dict]:
        """Discover new tunnels between wings."""
        self.initialize()
        if not self.tunnel_manager:
            return []

        try:
            return self.tunnel_manager.discover_tunnels()
        except Exception:
            return []

    def find_tunnels_for_topic(self, topic: str) -> List[Dict]:
        """Find all tunnels involving a specific topic/room."""
        self.initialize()
        if not self.tunnel_manager:
            return []

        try:
            return self.tunnel_manager.find_tunnels_for_room(topic)
        except Exception:
            return []

    def get_tunnel_map(self) -> Dict:
        """Get full tunnel adjacency list."""
        self.initialize()
        if not self.tunnel_manager:
            return {}

        try:
            return self.tunnel_manager.get_tunnel_map()
        except Exception:
            return {}

    def traverse_memory(self, start_topic: str) -> Dict:
        """Starting from a topic, discover all connected wings via tunnels."""
        self.initialize()
        if not self.tunnel_manager:
            return {"wings": [], "rooms": [], "paths": []}

        try:
            return self.tunnel_manager.traverse_from(
                start_wing="auto", start_room=start_topic
            )
        except Exception:
            return {"wings": [], "rooms": [], "paths": []}

    # â”€â”€ Palace Mining â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def mine_vault(self) -> Dict[str, Any]:
        """Mine the Obsidian vault to populate the palace."""
        self.initialize()
        if not self.palace_miner:
            return {"error": "PalaceMiner unavailable"}

        try:
            return self.palace_miner.mine_vault(str(VAULT_PATH))
        except Exception as e:
            return {"error": str(e)}

    def mine_projects(self) -> Dict[str, Any]:
        """Mine project directories to populate the palace."""
        self.initialize()
        if not self.palace_miner:
            return {"error": "PalaceMiner unavailable"}

        project_list = []
        if PROJECTS_PATH.exists():
            for p in PROJECTS_PATH.iterdir():
                if p.is_dir():
                    project_list.append(str(p))

        try:
            return self.palace_miner.mine_projects(project_list)
        except Exception as e:
            return {"error": str(e)}

    def auto_mine_all(self) -> Dict[str, Any]:
        """Run all miners."""
        self.initialize()
        if not self.palace_miner:
            return {"error": "PalaceMiner unavailable"}

        try:
            return self.palace_miner.auto_mine_all()
        except Exception as e:
            return {"error": str(e)}

    def get_mining_status(self) -> Dict[str, Any]:
        """Get current mining statistics."""
        self.initialize()
        if not self.palace_miner:
            return {"error": "PalaceMiner unavailable"}

        try:
            return self.palace_miner.get_mining_status()
        except Exception as e:
            return {"error": str(e)}

    # â”€â”€ Stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def get_palace_stats(self) -> Dict[str, Any]:
        """Get comprehensive palace statistics."""
        self.initialize()
        stats = {
            "knowledge_graph": {"status": "unavailable"},
            "memory_stack": {"status": "unavailable"},
            "tunnels": {"status": "unavailable"},
            "mining": {"status": "unavailable"},
        }

        if self.kg:
            try:
                kg_stats = self.kg.get_stats()
                stats["knowledge_graph"] = kg_stats
            except Exception:
                pass

        if self.memory_stack:
            try:
                stats["memory_stack"] = {"status": "available"}
            except Exception:
                pass

        if self.tunnel_manager:
            try:
                tunnel_stats = self.tunnel_manager.stats()
                stats["tunnels"] = tunnel_stats
            except Exception:
                pass

        if self.palace_miner:
            try:
                stats["mining"] = self.palace_miner.get_mining_status()
            except Exception:
                pass

        return stats

    # â”€â”€ Conversation Processing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def process_conversation(self, user_message: str, ai_response: str,
                             agent_name: str = "jarvis") -> Dict[str, Any]:
        """Process a conversation turn through the full palace pipeline."""
        self.initialize()
        results = {
            "facts_stored": 0,
            "contradictions_found": 0,
            "tunnels_discovered": 0,
        }

        # Extract facts via LLM (or heuristics if LLM unavailable)
        facts = self._extract_facts(user_message, ai_response)
        for fact in facts:
            result = self.store_fact(
                subject=fact["subject"],
                predicate=fact["predicate"],
                value=fact["value"],
                source=f"conversation_{agent_name}"
            )
            if result.get("stored"):
                results["facts_stored"] += 1
            if result.get("contradiction"):
                results["contradictions_found"] += 1

        # Periodically discover tunnels (every 10 conversations would be ideal,
        # but we'll do it here for simplicity)
        if self.tunnel_manager and results["facts_stored"] > 0:
            try:
                tunnels = self.tunnel_manager.discover_tunnels()
                results["tunnels_discovered"] = len(tunnels) if tunnels else 0
            except Exception:
                pass

        return results

    def _extract_facts(self, user_message: str, ai_response: str) -> List[Dict]:
        """Extract facts from conversation using LLM or heuristics fallback."""
        if self.gemini:
            return self._extract_facts_llm(user_message, ai_response)
        return self._extract_facts_heuristic(user_message, ai_response)

    def _extract_facts_llm(self, user_message: str, ai_response: str) -> List[Dict]:
        """Use Gemini to extract structured facts (Graphiti-inspired pipeline)."""
        facts = []
        try:
            combined = f"User: {user_message}\nAssistant: {ai_response}"
            prompt = (
                "Extract all factual claims, preferences, project details, and relationships "
                "from this conversation. Return ONLY a JSON array of objects with keys: "
                '"subject", "predicate", "value". Examples:\n'
                '[{"subject": "user", "predicate": "name", "value": "User"},\n'
                ' {"subject": "project_x", "predicate": "uses_language", "value": "Python"},\n'
                ' {"subject": "kai", "predicate": "works_on", "value": "memory system"}]\n\n'
                f"Conversation:\n{combined}\n\nReturn only the JSON array, no other text."
            )
            response = self.gemini.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            if response.text:
                text = response.text.strip()
                # Strip markdown code fences if present
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    for item in parsed:
                        if all(k in item for k in ("subject", "predicate", "value")):
                            facts.append({
                                "subject": item["subject"].lower().replace(" ", "_")[:50],
                                "predicate": item["predicate"].lower().replace(" ", "_")[:50],
                                "value": str(item["value"])[:200],
                            })
        except Exception as e:
            print(f"[MemPalace] âš ï¸ LLM fact extraction failed: {e}")
            facts = self._extract_facts_heuristic(user_message, ai_response)
        return facts

    def _extract_facts_heuristic(self, user_message: str, ai_response: str) -> List[Dict]:
        """Heuristic-based fact extraction (fallback when LLM unavailable)."""
        facts = []
        combined = f"{user_message}\n{ai_response}".lower()

        fact_patterns = [
            {
                "pattern": ["my name is", "i am called", "call me"],
                "predicate": "name",
                "subject": "user"
            },
            {
                "pattern": ["my favorite", "i prefer", "i like"],
                "predicate": "preference",
                "subject": "user"
            },
            {
                "pattern": ["i work on", "i'm building", "i am working on"],
                "predicate": "working_on",
                "subject": "user"
            },
        ]

        for pattern_info in fact_patterns:
            for pattern in pattern_info["pattern"]:
                if pattern in combined:
                    idx = combined.find(pattern)
                    value = combined[idx + len(pattern):].split("\n")[0].strip()[:100]
                    if value and len(value) > 2:
                        facts.append({
                            "subject": pattern_info["subject"],
                            "predicate": pattern_info["predicate"],
                            "value": value
                        })

        return facts


# â”€â”€ Singleton â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_palace_instance = None
_palace_lock = threading.Lock()


def get_mem_palace() -> MemPalace:
    """Get or create the singleton MemPalace instance."""
    global _palace_instance
    if _palace_instance is None:
        with _palace_lock:
            if _palace_instance is None:
                _palace_instance = MemPalace()
    return _palace_instance
