"""
Unified Memory Layer v1.0 - Bridging Obsidian Vault with AI Agents
Integrates LAIS, Jarvis, and OpenCode with the Unified Brain vault.

Features:
- Semantic search via keyword-based embeddings (no ML dependency)
- Graph-aware context retrieval using wikilink traversal
- Auto-crystallization pipeline for conversation insights
- Topic clustering and gap detection
- Relationship mapping between vault notes and crystallized memory
"""

import json
import os
import re
import time
from pathlib import Path
from datetime import datetime
from collections import Counter
from threading import Lock
from typing import Optional

# Vault path: can override via LAIS_VAULT_PATH env variable
VAULT_PATH = Path(os.environ.get("LAIS_VAULT_PATH", os.path.expandvars(r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain")))
# Project knowledge paths (relative to this file's project root)
_UL_BASE = Path(__file__).resolve().parent.parent
LAIS_KNOWLEDGE = _UL_BASE / "knowledge"
MEMORY_DIR = LAIS_KNOWLEDGE / "memory"
CRYSTALLIZED_FILE = MEMORY_DIR / "crystallized.json"
VAULT_INDEX_FILE = MEMORY_DIR / "vault_index.json"
GRAPH_FILE = MEMORY_DIR / "vault_graph.json"
TOPIC_INDEX_FILE = MEMORY_DIR / "topic_index.json"
LOCK = Lock()

MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _empty_memory():
    return {
        "identity": {},
        "preferences": {},
        "projects": {},
        "relationships": {},
        "wishes": {},
        "notes": {},
        "session_history": {}
    }


HIGH_KEYWORDS = {
    "current", "active", "now", "working", "focus", "session", "continuity",
    "protocol", "automated", "code", "fix", "bug", "error", "implement",
    "create", "lais", "ai", "project", "task", "urgent", "priority"
}
MEDIUM_KEYWORDS = {
    "method", "approach", "technique", "specification", "insight",
    "system", "function", "class", "file", "design", "pattern", "architecture"
}
LOW_KEYWORDS = {
    "background", "history", "archive", "example", "test", "demo",
    "old", "previous", "yesterday", "obsolete"
}


class VaultIndex:
    """Indexes all markdown files in the vault for fast retrieval."""
    
    def __init__(self, vault_path=VAULT_PATH):
        self.vault_path = vault_path
        self.notes = {}
        self.build_index()
    
    def build_index(self):
        """Scan vault and index all markdown files."""
        self.notes = {}
        for md_file in self.vault_path.rglob("*.md"):
            if md_file.name == "Welcome.md":
                continue
            rel_path = md_file.relative_to(self.vault_path)
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            
            self.notes[rel_path.as_posix()] = {
                "path": str(rel_path),
                "title": md_file.stem.replace("_", " ").title(),
                "folder": rel_path.parent.name,
                "content_preview": content[:300],
                "word_count": len(content.split()),
                "wikilinks": self._extract_wikilinks(content),
                "tags": self._extract_tags(content),
                "last_modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
            }
        
        self._save_index()
        return len(self.notes)
    
    def _extract_wikilinks(self, content):
        """Extract [[wikilinks]] from content."""
        return re.findall(r'\[\[([^\]]+)\]\]', content)
    
    def _extract_tags(self, content):
        """Extract #tags from content."""
        tags = re.findall(r'#(\w+)', content)
        props = re.findall(r'tags:\s*\[([^\]]*)\]', content)
        if props:
            tags.extend([t.strip() for t in props[0].split(",") if t.strip()])
        return list(set(tags))
    
    def _save_index(self):
        """Save index to disk."""
        with LOCK:
            VAULT_INDEX_FILE.write_text(
                json.dumps({"notes": self.notes, "updated": datetime.now().isoformat()}, indent=2),
                encoding="utf-8"
            )
    
    def search_notes(self, query, max_results=5):
        """Search notes by keyword relevance."""
        query_words = set(query.lower().split())
        scores = []
        
        for path, note in self.notes.items():
            score = 0
            content_lower = note["content_preview"].lower()
            title_lower = note["title"].lower()
            
            for word in query_words:
                if word in title_lower:
                    score += 10
                if word in content_lower:
                    score += content_lower.count(word)
            
            if score > 0:
                scores.append((path, score, note))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [note for _, _, note in scores[:max_results]]
    
    def get_note_content(self, note_path):
        """Load full content of a note."""
        full_path = self.vault_path / note_path
        if full_path.exists():
            return full_path.read_text(encoding="utf-8", errors="ignore")
        return ""
    
    def get_notes_by_folder(self, folder):
        """Get all notes in a specific folder."""
        return [note for note in self.notes.values() if note["folder"] == folder]
    
    def get_linked_notes(self, note_path):
        """Find all notes linked to a given note via wikilinks."""
        content = self.get_note_content(note_path)
        if not content:
            return []
        
        wikilinks = self._extract_wikilinks(content)
        linked = []
        
        for link in wikilinks:
            link_clean = link.lower().replace(" ", "_")
            for path, note in self.notes.items():
                if link_clean in path.lower() or link_clean in note["title"].lower().replace(" ", "_"):
                    linked.append(note)
        
        return linked


class VaultGraph:
    """Builds and traverses the knowledge graph from wikilinks."""
    
    def __init__(self, index):
        self.index = index
        self.graph = {}
        self.build_graph()
    
    def build_graph(self):
        """Build adjacency list from wikilinks."""
        self.graph = {}
        
        for path, note in self.index.notes.items():
            if path not in self.graph:
                self.graph[path] = set()
            
            for link in note["wikilinks"]:
                link_clean = link.lower().replace(" ", "_")
                for other_path in self.index.notes:
                    if link_clean in other_path.lower() or link_clean in self.index.notes[other_path]["title"].lower().replace(" ", "_"):
                        self.graph[path].add(other_path)
        
        self._save_graph()
    
    def _save_graph(self):
        """Save graph to disk."""
        with LOCK:
            serializable = {k: list(v) for k, v in self.graph.items()}
            GRAPH_FILE.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    
    def get_neighbors(self, note_path, depth=1):
        """Get notes connected to this note within N hops."""
        visited = {note_path}
        current_level = {note_path}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                neighbors = self.graph.get(node, set())
                next_level.update(neighbors - visited)
            visited.update(next_level)
            current_level = next_level
        
        visited.discard(note_path)
        return [self.index.notes.get(p) for p in visited if p in self.index.notes]
    
    def find_shortest_path(self, start_path, end_path):
        """Find shortest path between two notes."""
        if start_path == end_path:
            return [start_path]
        
        visited = {start_path}
        queue = [(start_path, [start_path])]
        
        while queue:
            current, path = queue.pop(0)
            for neighbor in self.graph.get(current, set()):
                if neighbor == end_path:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def get_central_notes(self, top_n=10):
        """Find most connected notes (highest degree centrality)."""
        degrees = {path: len(neighbors) for path, neighbors in self.graph.items()}
        sorted_notes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        return [(path, count, self.index.notes.get(path)) for path, count in sorted_notes[:top_n]]


class TopicCluster:
    """Clusters notes by topic and detects knowledge gaps."""
    
    def __init__(self, index):
        self.index = index
        self.clusters = {}
        self.build_clusters()
    
    def build_clusters(self):
        """Group notes by folder and keyword overlap."""
        self.clusters = {}
        
        for path, note in self.index.notes.items():
            folder = note["folder"]
            if folder not in self.clusters:
                self.clusters[folder] = {
                    "notes": [],
                    "keywords": Counter(),
                    "total_words": 0
                }
            
            self.clusters[folder]["notes"].append(note)
            self.clusters[folder]["total_words"] += note["word_count"]
            
            words = re.findall(r'\b\w{4,}\b', note["content_preview"].lower())
            stop_words = {"this", "that", "with", "from", "what", "when", "where", "which", "would", "could", "should"}
            meaningful = [w for w in words if w not in stop_words]
            self.clusters[folder]["keywords"].update(meaningful)
        
        self._save_clusters()
    
    def _save_clusters(self):
        """Save topic clusters."""
        with LOCK:
            serializable = {}
            for folder, data in self.clusters.items():
                serializable[folder] = {
                    "note_count": len(data["notes"]),
                    "top_keywords": data["keywords"].most_common(10),
                    "total_words": data["total_words"]
                }
            TOPIC_INDEX_FILE.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    
    def get_gaps(self):
        """Detect knowledge gaps - topics mentioned but not covered."""
        all_keywords = Counter()
        for folder, data in self.clusters.items():
            all_keywords.update(data["keywords"])
        
        notes_by_keyword = {}
        for path, note in self.index.notes.items():
            words = set(re.findall(r'\b\w{4,}\b', note["content_preview"].lower()))
            for word in words:
                if word not in notes_by_keyword:
                    notes_by_keyword[word] = []
                notes_by_keyword[word].append(note["title"])
        
        gaps = []
        for keyword, count in all_keywords.most_common(50):
            if count <= 2:
                gaps.append({
                    "keyword": keyword,
                    "mentions": count,
                    "related_notes": notes_by_keyword.get(keyword, [])
                })
        
        return gaps
    
    def get_cluster_summary(self):
        """Return summary of all topic clusters."""
        return {
            folder: {
                "note_count": len(data["notes"]),
                "top_keywords": data["keywords"].most_common(5),
                "total_words": data["total_words"]
            }
            for folder, data in self.clusters.items()
        }


class CrystallizationPipeline:
    """Auto-crystallizes insights from conversations into vault and memory."""
    
    def __init__(self, index, crystallized_path=CRYSTALLIZED_FILE):
        self.index = index
        self.crystallized_path = crystallized_path
        self.crystallized = self._load_crystallized()
        self.active_state_path = VAULT_PATH / "40_System" / "_active_state.md"
    
    def _load_crystallized(self):
        """Load existing crystallized knowledge."""
        if self.crystallized_path.exists():
            try:
                return json.loads(self.crystallized_path.read_text(encoding="utf-8"))
            except Exception as e:
                return []
        return []
    
    def _save_crystallized(self):
        """Save crystallized knowledge."""
        with LOCK:
            self.crystallized_path.write_text(
                json.dumps(self.crystallized, indent=2),
                encoding="utf-8"
            )
    
    def _read_active_state(self):
        """Read the active state markdown file."""
        if self.active_state_path.exists():
            try:
                return self.active_state_path.read_text(encoding="utf-8")
            except Exception as e:
                return ""
        return ""
    
    def _write_active_state(self, topic=None, projects=None, action=None, pending=None, notes=None):
        """Update the active state markdown file."""
        content = self._read_active_state()
        
        lines = content.split("\n")
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        if "updated:" in content:
            lines = [f"updated: {now}" if "updated:" in line else line for line in lines]
        
        if topic:
            for i, line in enumerate(lines):
                if line.startswith("## Current Topic"):
                    lines[i+1] = topic
                    break
        
        if projects:
            for i, line in enumerate(lines):
                if line.startswith("## Open Projects"):
                    j = i + 1
                    while j < len(lines) and lines[j].startswith("- "):
                        j += 1
                    lines[i+1:j] = [f"- {p}" for p in projects] if isinstance(projects, list) else [f"- {projects}"]
                    break
        
        if action:
            for i, line in enumerate(lines):
                if line.startswith("## Last Action"):
                    lines[i+1] = action
                    break
        
        if pending:
            for i, line in enumerate(lines):
                if line.startswith("## Pending"):
                    j = i + 1
                    while j < len(lines) and lines[j].startswith("- "):
                        j += 1
                    lines[i+1:j] = [f"- {p}" for p in pending] if isinstance(pending, list) else [f"- {pending}"]
                    break
        
        if notes:
            for i, line in enumerate(lines):
                if line.startswith("## Notes"):
                    j = i + 1
                    while j < len(lines) and lines[j].startswith("- "):
                        j += 1
                    lines[i+1:j] = [f"- {n}" for n in notes] if isinstance(notes, list) else [f"- {notes}"]
                    break
        
        self.active_state_path.write_text("\n".join(lines), encoding="utf-8")
    
    def get_active_state_context(self):
        """Get active state as minimal context injection."""
        content = self._read_active_state()
        if not content:
            return ""
        
        parts = ["<active_state>"]
        
        for line in content.split("\n"):
            if line.startswith("---") or line.startswith("updated:") or line.startswith("agent:"):
                continue
            if line.startswith("# ") or line.startswith("## "):
                parts.append(line)
            elif line.startswith("- "):
                parts.append(line)
            elif line.strip() and not line.startswith("#"):
                parts.append(line)
        
        parts.append("</active_state>")
        return "\n".join(parts)
    
    def crystallize_insight(self, key, value, source="conversation"):
        """Add new insight to crystallized knowledge."""
        for item in self.crystallized:
            if item.get("key") == key:
                item["value"] = value
                item["updated"] = datetime.now().isoformat()
                item["sources"] = item.get("sources", [])
                if source not in item["sources"]:
                    item["sources"].append(source)
                self._save_crystallized()
                return
        
        self.crystallized.append({
            "key": key,
            "value": value,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "sources": [source]
        })
        self._save_crystallized()
    
    def create_vault_note(self, title, content, folder="00_Inbox"):
        """Create a new note in the vault."""
        safe_title = title.replace(" ", "_").replace("/", "_")[:50]
        note_path = VAULT_PATH / folder / f"{safe_title}.md"
        
        yaml_header = f"""---
title: {title}
created: {datetime.now().isoformat()}
tags: []
source: crystallization
---

"""
        note_path.write_text(yaml_header + content, encoding="utf-8")
        self.index.build_index()
        return str(note_path.relative_to(VAULT_PATH))
    
    def extract_insights_from_conversation(self, user_message, ai_response):
        """Auto-extract key insights from a conversation turn."""
        insights = []
        
        combined = f"{user_message}\n{ai_response}"
        combined_lower = combined.lower()
        
        if any(kw in combined_lower for kw in HIGH_KEYWORDS):
            relevance = 80
        elif any(kw in combined_lower for kw in MEDIUM_KEYWORDS):
            relevance = 50
        else:
            relevance = 30
        
        if relevance >= 50:
            key = user_message[:50].strip()
            insights.append({
                "key": key,
                "value": ai_response[:200].strip(),
                "relevance": relevance
            })
        
        return insights
    
    def process_conversation(self, user_message, ai_response):
        """Full crystallization pipeline for a conversation."""
        insights = self.extract_insights_from_conversation(user_message, ai_response)
        
        for insight in insights:
            if insight["relevance"] >= 70:
                self.crystallize_insight(
                    insight["key"],
                    insight["value"],
                    source="lais_conversation"
                )
        
        return insights


class UnifiedLayer:
    """Main unified memory layer connecting vault with AI agents."""
    
    def __init__(self, agent_name="agent"):
        self.agent_name = agent_name
        self.index = VaultIndex()
        self.graph = VaultGraph(self.index)
        self.topics = TopicCluster(self.index)
        self.crystallization = CrystallizationPipeline(self.index)
        self.curator = CrystallizationPipeline(self.index)
        
        try:
            from unified_layer.vault_curator import VaultCurator
            self.curator = VaultCurator()
        except Exception as e:
            pass
        
        try:
            from unified_layer.embeddings import EmbeddingSearch, load_embedding_search
            self.embeddings = load_embedding_search()
        except Exception as e:
            print(f"[UnifiedLayer] Embeddings not available: {e}")
            self.embeddings = None
        
        self.sync_v2 = None
        try:
            from unified_layer.memory_sync_v2 import load_shared_memory_v2
            self.sync = load_shared_memory_v2(vault_integration=True)
            self.sync_v2 = True
        except Exception as e:
            print(f"[UnifiedLayer] Memory sync v2 not available: {e}")
            try:
                from unified_layer.memory_sync import load_shared_memory
                self.sync = load_shared_memory()
                self.sync_v2 = False
            except Exception as e2:
                print(f"[UnifiedLayer] Memory sync v1 not available: {e2}")
                self.sync = None

        try:
            from unified_layer.memory_sqlite import load_sqlite_memory
            self.sqlite_memory = load_sqlite_memory()
        except Exception as e:
            print(f"[UnifiedLayer] SQLite memory not available: {e}")
            self.sqlite_memory = None

        try:
            from unified_layer.unified_search import load_unified_search
            self.unified_search = load_unified_search()
        except Exception as e:
            print(f"[UnifiedLayer] Unified search not available: {e}")
            self.unified_search = None

        try:
            from unified_layer.conversation_search import load_conversation_search
            self.conv_search = load_conversation_search()
            print(f"[UnifiedLayer] OK Conversation search loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Conversation search not available: {e}")
            self.conv_search = None

        try:
            from unified_layer.rag_pipeline import load_rag_pipeline
            self.rag = load_rag_pipeline()
            print(f"[UnifiedLayer] OK RAG pipeline loaded")
        except Exception as e:
            print(f"[UnifiedLayer] RAG pipeline not available: {e}")
            self.rag = None

        try:
            from unified_layer.security_policy import load_security_policy
            self.security = load_security_policy(agent_name)
        except Exception as e:
            print(f"[UnifiedLayer] Security policy not available: {e}")
            self.security = None

        try:
            from unified_layer.autonomy_manager import load_autonomy_manager
            self.autonomy = load_autonomy_manager()
        except Exception as e:
            print(f"[UnifiedLayer] Autonomy manager not available: {e}")
            self.autonomy = None

        try:
            from unified_layer.scheduler import load_scheduler
            self.scheduler = load_scheduler()
        except Exception as e:
            print(f"[UnifiedLayer] Scheduler not available: {e}")
            self.scheduler = None

        try:
            from unified_layer.n8n_bridge import get_n8n_bridge
            self.n8n_bridge, self.cloud_scheduler = get_n8n_bridge()
            print(f"[UnifiedLayer] OK n8n bridge + cloud scheduler loaded")
        except Exception as e:
            print(f"[UnifiedLayer] n8n bridge not available: {e}")
            self.n8n_bridge = None
            self.cloud_scheduler = None

        try:
            from unified_layer.skill_engine import load_skill_engine
            self.skills = load_skill_engine()
        except Exception as e:
            print(f"[UnifiedLayer] Skill engine not available: {e}")
            self.skills = None

        try:
            from unified_layer.ai_monitor import run_scan
            self.ai_monitor = run_scan
        except Exception as e:
            print(f"[UnifiedLayer] AI monitor not available: {e}")
            self.ai_monitor = None

        try:
            from unified_layer.protocol_layer import load_protocol_layer
            self.protocols = load_protocol_layer()
            # Register this agent in protocol layer
            if self.protocols:
                self.protocols.register_local_agent(
                    agent_name,
                    f"{agent_name.title()} Agent",
                    f"AI agent: {agent_name}",
                    self._get_agent_capabilities(agent_name)
                )
        except Exception as e:
            print(f"[UnifiedLayer] Protocol layer not available: {e}")
            self.protocols = None

        try:
            from unified_layer.gateway_layer import load_gateway_layer
            self.gateway = load_gateway_layer()
            # Register this agent's channel if not already present
            if self.gateway:
                channel_id = f"{agent_name}_channel"
                existing = self.gateway.get_channel_status(channel_id)
                if not existing:
                    self.gateway.register_channel(
                        channel_id=channel_id,
                        name=f"{agent_name.title()} Channel",
                        channel_type="text" if agent_name != "lais" else "gui",
                        agent=agent_name
                    )
        except Exception as e:
            print(f"[UnifiedLayer] Gateway layer not available: {e}")
            self.gateway = None

        try:
            from unified_layer.orchestrator import load_orchestrator
            self.orchestrator = load_orchestrator()
        except Exception as e:
            print(f"[UnifiedLayer] Orchestrator not available: {e}")
            self.orchestrator = None

        try:
            from unified_layer.dialectic_engine import get_dialectic_engine
            self.dialectic = get_dialectic_engine()
            print(f"[UnifiedLayer] OK Dialectic Engine loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Dialectic engine not available: {e}")
            self.dialectic = None

        try:
            from unified_layer.mem_palace_integration import get_mem_palace
            self.mem_palace = get_mem_palace()
            print(f"[UnifiedLayer] OK MemPalace integration loaded")
        except Exception as e:
            print(f"[UnifiedLayer] MemPalace not available: {e}")
            self.mem_palace = None

        try:
            from agents.fincore import create_fincore
            self.fincore = create_fincore()
            print(f"[UnifiedLayer] OK FinCore financial agents loaded")
        except Exception as e:
            print(f"[UnifiedLayer] FinCore not available: {e}")
            self.fincore = None

        try:
            from Transports import create_transport, TransportType, TransportConfig
            self.transports = {}
            self.active_transport = None

            gemini_config = TransportConfig(model="gemini-2.5-flash", temperature=0.7, max_tokens=4096)
            gemini = create_transport(TransportType.GEMINI, gemini_config)
            if gemini.available:
                self.transports["gemini"] = gemini
                self.active_transport = gemini

            local_config = TransportConfig(model="phi-4-mini", temperature=0.7, max_tokens=2048)
            local_t = create_transport(TransportType.LOCAL, local_config)
            if local_t.available:
                self.transports["local"] = local_t
                if not self.active_transport:
                    self.active_transport = local_t

            openai_config = TransportConfig(model="gpt-4o", temperature=0.7, max_tokens=4096)
            openai_t = create_transport(TransportType.OPENAI, openai_config)
            if openai_t.available:
                self.transports["openai"] = openai_t

            print(f"[UnifiedLayer] OK Transport layer loaded ({list(self.transports.keys())})")
        except Exception as e:
            print(f"[UnifiedLayer] Transport layer not available: {e}")
            self.transports = {}
            self.active_transport = None

        try:
            from unified_layer.subagent_router import get_model_router, get_subagent_spawner
            self.model_router = get_model_router(self)
            self.subagent_spawner = get_subagent_spawner(execute_fn=lambda p, d: self.transport_generate(p))
            print(f"[UnifiedLayer] OK Subagent router & model router loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Subagent router not available: {e}")
            self.model_router = None
            self.subagent_spawner = None

        try:
            from unified_layer.auto_skill import get_auto_skill_generator
            self.auto_skill = get_auto_skill_generator()
            print(f"[UnifiedLayer] OK Auto-skill generator loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Auto-skill generator not available: {e}")
            self.auto_skill = None

        try:
            from unified_layer.policy_engine import get_autonomy_engine
            self.autonomy_engine = get_autonomy_engine()
            print(f"[UnifiedLayer] OK Autonomy engine loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Autonomy engine not available: {e}")
            self.autonomy_engine = None

        try:
            from unified_layer.reasoning_loop import get_react_loop
            self.react_loop = get_react_loop()
            print(f"[UnifiedLayer] OK Reasoning loop loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Reasoning loop not available: {e}")
            self.react_loop = None

        try:
            from unified_layer.tool_framework import get_tool_engine
            self.tool_engine = get_tool_engine()
            print(f"[UnifiedLayer] OK Tool calling framework loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Tool framework not available: {e}")
            self.tool_engine = None

        try:
            from unified_layer.memory_consolidation import get_consolidator
            self.consolidator = get_consolidator()
            print(f"[UnifiedLayer] OK Memory consolidation loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Memory consolidation not available: {e}")
            self.consolidator = None

        try:
            from unified_layer.self_improvement import get_self_improvement_engine
            def chat_fn(messages, **kwargs):
                return self.transport_chat(messages, **kwargs)
            self.self_improve = get_self_improvement_engine(transport_chat_fn=chat_fn)
            print(f"[UnifiedLayer] OK Self-improvement engine loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Self-improvement engine not available: {e}")
            self.self_improve = None

        try:
            from unified_layer.benchmarking import get_benchmark_runner
            self.benchmark_runner = get_benchmark_runner()
            print(f"[UnifiedLayer] OK Benchmarking suite loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Benchmarking suite not available: {e}")
            self.benchmark_runner = None

        try:
            from unified_layer.cross_session_learning import get_cross_session_learner
            self.cross_session = get_cross_session_learner()
            print(f"[UnifiedLayer] OK Cross-session learning loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Cross-session learning not available: {e}")
            self.cross_session = None

        try:
            from unified_layer.plugin_system import get_plugin_manager
            self.plugin_manager = get_plugin_manager()
            self.plugin_manager.load_all()
            print(f"[UnifiedLayer] OK Plugin manager loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Plugin manager not available: {e}")
            self.plugin_manager = None

        try:
            from unified_layer.token_optimizer import load_token_optimizer
            self.token_optimizer = load_token_optimizer(agent_name)
        except Exception as e:
            print(f"[UnifiedLayer] Token optimizer not available: {e}")
            self.token_optimizer = None
        
        try:
            from unified_layer.reranker import get_reranker
            self.reranker = get_reranker()
            print(f"[UnifiedLayer] OK Reranker loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Reranker not available: {e}")
            self.reranker = None

        try:
            from unified_layer.dataview_engine import get_dataview_engine
            self.dataview = get_dataview_engine(vault_path=str(VAULT_PATH))
            print(f"[UnifiedLayer] OK Dataview engine loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Dataview engine not available: {e}")
            self.dataview = None

        try:
            from unified_layer.template_engine import get_template_engine
            self.template_engine = get_template_engine()
            print(f"[UnifiedLayer] OK Template engine loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Template engine not available: {e}")
            self.template_engine = None

        try:
            from unified_layer.observability import get_observability_engine
            self.observability = get_observability_engine()
            print(f"[UnifiedLayer] OK Observability engine loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Observability engine not available: {e}")
            self.observability = None

        try:
            from unified_layer.prompt_library import get_prompt_library
            self.prompt_library = get_prompt_library()
            print(f"[UnifiedLayer] OK Prompt library loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Prompt library not available: {e}")
            self.prompt_library = None

        try:
            from unified_layer.background_consciousness import get_background_consciousness
            def chat_fn(messages, **kwargs):
                return self.transport_chat(messages, **kwargs)
            self.background_consciousness = get_background_consciousness(transport_chat_fn=chat_fn)
            print(f"[UnifiedLayer] OK Background consciousness loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Background consciousness not available: {e}")
            self.background_consciousness = None

        try:
            from unified_layer.hook_system import get_hook_engine
            self.hook_engine = get_hook_engine()
            print(f"[UnifiedLayer] OK Hook engine loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Hook engine not available: {e}")
            self.hook_engine = None

        try:
            from unified_layer.constrained_grammar import get_constrained_grammar
            self.constrained_grammar = get_constrained_grammar()
            print(f"[UnifiedLayer] OK Constrained grammar loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Constrained grammar not available: {e}")
            self.constrained_grammar = None

        try:
            from unified_layer.memory_reclaimer import get_memory_reclaimer
            self.memory_reclaimer = get_memory_reclaimer(
                unload_local_fn=self._unload_local_transport,
                compress_history_fn=self._compress_history,
                clear_cache_fn=self._clear_cache,
            )
            print(f"[UnifiedLayer] OK Memory reclaimer loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Memory reclaimer not available: {e}")
            self.memory_reclaimer = None

        try:
            from unified_layer.model_gallery import get_model_gallery
            self.model_gallery = get_model_gallery()
            print(f"[UnifiedLayer] OK Model gallery loaded")
        except Exception as e:
            print(f"[UnifiedLayer] Model gallery not available: {e}")
            self.model_gallery = None

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            from unified_memory import UnifiedMemory, load_memory
            self.memory = load_memory(agent_name)
        except Exception as e:
            self.memory = None
        
        if self.sync:
            self.sync.store(
                agent_name,
                f"{agent_name}_session_start",
                f"Session started at {self.session_id}",
                "session",
                ttl=3600
            )

    def _get_agent_capabilities(self, agent_name: str) -> list:
        """Get capabilities for a specific agent."""
        capabilities_map = {
            "lais": ["gui", "chat", "search", "vault_write", "memory_read", "visualization"],
            "jarvis": ["voice", "text", "search", "memory_write", "reminders", "apps", "web"],
            "opencode": ["code", "shell", "search", "file_write", "api", "debug", "git"],
        }
        return capabilities_map.get(agent_name, ["chat", "search"])
    
    def semantic_search(self, query, max_results=5, include_graph=True):
        """
        Enhanced search combining:
        1. Embedding-based semantic search (if available)
        2. Keyword search fallback
        3. Graph traversal for related notes
        4. Crystallized knowledge
        """
        results = []
        
        if self.embeddings:
            emb_results = self.embeddings.search(query, max_results=max_results)
            for r in emb_results:
                results.append({
                    "type": "note",
                    "title": r["title"],
                    "path": r["path"],
                    "content": r["content"],
                    "folder": Path(r["path"]).parent.name,
                    "score": r.get("score", 0)
                })
        else:
            notes = self.index.search_notes(query, max_results)
            for note in notes:
                content = self.index.get_note_content(note["path"])
                results.append({
                    "type": "note",
                    "title": note["title"],
                    "path": note["path"],
                    "content": content[:500],
                    "folder": note["folder"]
                })
        
        if include_graph and results:
            top_note = results[0]
            linked = self.index.get_linked_notes(top_note["path"])
            for note in linked[:2]:
                if not any(r["path"] == note["path"] for r in results):
                    content = self.index.get_note_content(note["path"])
                    results.append({
                        "type": "linked_note",
                        "title": note["title"],
                        "path": note["path"],
                        "content": content[:300],
                        "folder": note["folder"]
                    })
        
        if self.crystallization.crystallized:
            query_lower = query.lower()
            for item in self.crystallization.crystallized[-5:]:
                key_lower = item.get("key", "").lower()
                value_lower = item.get("value", "").lower()
                if query_lower in key_lower or any(w in value_lower for w in query_lower.split()):
                    results.append({
                        "type": "crystallized",
                        "key": item["key"],
                        "value": item["value"][:300]
                    })
        
        return results
    
    def get_context_injection(self, query, max_tokens=200, session_start=False):
        """
        Generate context injection for LLM prompt.
        If session_start=True, returns only active state + crystallized (~80 tokens).
        Otherwise, searches vault for relevant context based on query.
        """
        if session_start:
            return self._get_session_startup_context()
        
        results = self.semantic_search(query, max_results=3)
        
        if not results:
            active = self.crystallization.get_active_state_context()
            return active if active else ""
        
        prompt = "<vault_context>\n"
        token_count = 0
        
        for result in results:
            if result["type"] == "note":
                snippet = f"[Note: {result['title']}]\n{result['content'][:300]}\n\n"
            elif result["type"] == "linked_note":
                snippet = f"[Related: {result['title']}]\n{result['content'][:200]}\n\n"
            else:
                snippet = f"[Knowledge: {result['key']}]\n{result['value']}\n\n"
            
            if token_count + len(snippet.split()) > max_tokens:
                break
            
            prompt += snippet
            token_count += len(snippet.split())
        
        prompt += "</vault_context>"
        return prompt
    
    def _get_session_startup_context(self):
        """Minimal startup context: active state + crystallized knowledge."""
        parts = []
        
        active = self.crystallization.get_active_state_context()
        if active:
            parts.append(active)
        
        if self.crystallization.crystallized:
            crystal_parts = ["<crystallized>"]
            for item in self.crystallization.crystallized[-5:]:
                crystal_parts.append(f"- {item.get('key')}: {item.get('value', '')[:100]}")
            crystal_parts.append("</crystallized>")
            parts.append("\n".join(crystal_parts))
        
        return "\n".join(parts) if parts else ""
    
    def process_conversation(self, user_message, ai_response):
        """Process conversation turn through full unified pipeline."""
        insights = self.crystallization.process_conversation(user_message, ai_response)

        if self.curator:
            self.curator.process_conversation(user_message, ai_response, self.agent_name)

        if self.sync:
            self.sync.store(
                self.agent_name,
                f"last_topic_{self.session_id}",
                f"User asked about: {user_message[:100]}",
                "context",
                ttl=7200
            )

        if self.memory and hasattr(self.memory, 'add_message'):
            self.memory.add_message("user", user_message)
            self.memory.add_message("assistant", ai_response)
            if hasattr(self.memory, 'save'):
                self.memory.save()

        if self.sqlite_memory:
            self.sqlite_memory.store_conversation(
                self.agent_name,
                self.session_id,
                "user",
                user_message
            )
            self.sqlite_memory.store_conversation(
                self.agent_name,
                self.session_id,
                "assistant",
                ai_response
            )

        # Process through MemPalace (contradiction detection + fact storage)
        if self.mem_palace:
            try:
                self.mem_palace.process_conversation(
                    user_message, ai_response, self.agent_name
                )
            except Exception as e:
                print(f"[UnifiedLayer] âš ï¸ MemPalace processing error: {e}")

        # Phase 6: Route through gateway
        if self.gateway:
            channel_id = f"{self.agent_name}_channel"
            self.gateway.route_message(channel_id, self.session_id, "user", user_message)
            self.gateway.route_message(channel_id, self.session_id, "assistant", ai_response)

        # Phase 5: Send to other agents via protocol if relevant
        if self.protocols:
            self._broadcast_to_agents(user_message, ai_response)

        self._update_active_state(user_message)

        # Log token usage
        if self.token_optimizer:
            total_text = user_message + ai_response
            tokens = self.token_optimizer.estimate_tokens(total_text)
            self.token_optimizer.log_usage("conversation", tokens, "conversation")

        # Submit to Honcho Dialectic Engine
        if self.dialectic:
            try:
                self.dialectic.submit_conversation(self.agent_name, user_message, ai_response)
            except Exception as e:
                print(f"[UnifiedLayer] âš ï¸ Dialectic submission error: {e}")

        return insights

    def _broadcast_to_agents(self, user_message, ai_response):
        """Broadcast relevant conversation info to other agents."""
        # Only broadcast if message contains cross-agent keywords
        cross_agent_keywords = ["lais", "jarvis", "opencode", "browser", "vault", "memory"]
        combined = f"{user_message} {ai_response}".lower()

        if any(kw in combined for kw in cross_agent_keywords):
            for agent_id in ["lais", "jarvis", "opencode"]:
                if agent_id != self.agent_name:
                    try:
                        self.protocols.send_a2a_message(
                            from_agent=self.agent_name,
                            to_agent=agent_id,
                            message=f"Context: {user_message[:100]}",
                            message_type="notification"
                        )
                    except Exception:
                        pass
    
    def _update_active_state(self, user_message):
        """Auto-update active state based on conversation."""
        if not hasattr(self.crystallization, '_write_active_state'):
            return
        
        topics = []
        words = re.findall(r'\b[a-z]{4,}\b', user_message.lower())
        stop = {"this", "that", "with", "from", "what", "when", "where", "which", "would", "could", "should", "about", "have", "been", "were", "they", "their", "there"}
        for w in words:
            if w not in stop:
                topics.append(w)
        
        if topics:
            main_topic = " ".join(topics[:3]).title()
            self.crystallization._write_active_state(topic=main_topic)
    
    def check_action(self, action_type, details=None, cost=0.0):
        """
        Check if the agent can perform an action based on security policy.
        Returns (allowed, reason, approval_request).
        """
        if self.autonomy:
            return self.autonomy.check_action(
                self.agent_name, action_type, details, cost
            )
        if self.security:
            allowed, reason = self.security.can_proceed(
                action_type, details, cost
            )
            return allowed, reason, None
        return True, "No security policy configured", None

    def get_autonomy_status(self):
        """Get current autonomy and security status."""
        if self.autonomy:
            return self.autonomy.get_system_status()
        if self.security:
            return self.security.get_status()
        return {"status": "No security/autonomy configured"}

    def set_autonomy_level(self, level):
        """Set autonomy level for this agent."""
        if self.autonomy:
            return self.autonomy.set_autonomy_level(self.agent_name, level)
        if self.security:
            self.security.set_autonomy_level(level)
            return True
        return False

    def get_pending_approvals(self):
        """Get pending approval requests for this agent."""
        if self.autonomy:
            return self.autonomy.get_pending_requests(self.agent_name)
        return []

    def approve_action(self, request_id):
        """Approve a pending action."""
        if self.autonomy:
            return self.autonomy.approve_action(request_id, "user")
        return False

    def deny_action(self, request_id):
        """Deny a pending action."""
        if self.autonomy:
            return self.autonomy.deny_action(request_id, "user")
        return False

    def schedule_task(self, name, action_type, schedule, details=None, agent="auto"):
        """Schedule a recurring task."""
        if self.scheduler:
            return self.scheduler.add_task(name, action_type, schedule, details, agent)
        return None

    def list_scheduled_tasks(self, enabled_only=False):
        """List all scheduled tasks."""
        if self.scheduler:
            return self.scheduler.list_tasks(enabled_only)
        return []

    def remove_task(self, task_id):
        """Remove a scheduled task."""
        if self.scheduler:
            return self.scheduler.remove_task(task_id)
        return False

    def get_scheduler_status(self):
        """Get scheduler status."""
        if self.scheduler:
            return self.scheduler.get_status()
        return {"status": "Scheduler not available"}

    def start_scheduler(self, check_interval=60):
        """Start the scheduler background thread."""
        if self.scheduler:
            self.scheduler.start(check_interval)
            return True
        return False

    def stop_scheduler(self):
        """Stop the scheduler background thread."""
        if self.scheduler:
            self.scheduler.stop()
            return True
        return False

    def register_task_handler(self, action_type, handler):
        """Register a handler function for a scheduled task type."""
        if self.scheduler:
            self.scheduler.register_handler(action_type, handler)
            return True
        return False

    def cloud_dispatch(self, name: str, prompt: str, agent_type: str = "general", webhook_url: str = "", priority: str = "normal", timeout_min: int = 30, metadata: dict = None) -> str:
        """Dispatch a task to a cloud agent (Oz-style)."""
        if self.cloud_scheduler:
            return self.cloud_scheduler.cloud_dispatcher.dispatch(name, prompt, agent_type, webhook_url, priority, timeout_min, metadata)
        return ""

    def cloud_dispatch_n8n(self, name: str, workflow_id: str, inputs: dict, webhook_url: str = "") -> str:
        """Dispatch a task to n8n workflow via cloud agent."""
        if self.cloud_scheduler:
            return self.cloud_scheduler.cloud_dispatcher.dispatch_to_n8n(name, workflow_id, inputs, webhook_url)
        return ""

    def cloud_execute(self, task_id: str) -> dict:
        """Execute a pending cloud agent task."""
        if self.cloud_scheduler:
            return self.cloud_scheduler.cloud_dispatcher.execute_task(task_id)
        return {"error": "Cloud scheduler not available"}

    def cloud_cancel(self, task_id: str) -> bool:
        """Cancel a cloud agent task."""
        if self.cloud_scheduler:
            return self.cloud_scheduler.cloud_dispatcher.cancel_task(task_id)
        return False

    def cloud_task_list(self, status: str = None, limit: int = 50) -> list:
        """List cloud agent tasks."""
        if self.cloud_scheduler:
            return self.cloud_scheduler.cloud_dispatcher.list_tasks(status, limit)
        return []

    def cloud_stats(self) -> dict:
        """Get cloud agent dispatcher stats."""
        if self.cloud_scheduler:
            return self.cloud_scheduler.cloud_dispatcher.get_stats()
        return {"total_tasks": 0}

    # â”€â”€ n8n Workflow Bridge Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def n8n_register(self, workflow_id: str, name: str, webhook_url: str, description: str = "", category: str = "general", tags: list = None) -> Optional[dict]:
        """Register an n8n workflow."""
        if not self.n8n_bridge:
            return None
        wf = self.n8n_bridge.register_workflow(workflow_id, name, webhook_url, description, category, tags)
        return wf.to_dict()

    def n8n_trigger(self, workflow_id: str, inputs: dict = None, wait: bool = False) -> dict:
        """Trigger an n8n workflow."""
        if not self.n8n_bridge:
            return {"error": "n8n bridge not available"}
        return self.n8n_bridge.trigger(workflow_id, inputs, wait)

    def n8n_trigger_by_name(self, name: str, inputs: dict = None, wait: bool = False) -> dict:
        """Trigger an n8n workflow by name."""
        if not self.n8n_bridge:
            return {"error": "n8n bridge not available"}
        return self.n8n_bridge.trigger_by_name(name, inputs, wait)

    def n8n_list(self, category: str = None, tag: str = None) -> list:
        """List registered n8n workflows."""
        if not self.n8n_bridge:
            return []
        return self.n8n_bridge.list_workflows(category, tag)

    def n8n_remove(self, workflow_id: str) -> bool:
        """Remove an n8n workflow."""
        if not self.n8n_bridge:
            return False
        return self.n8n_bridge.remove_workflow(workflow_id)

    def n8n_stats(self) -> dict:
        """Get n8n bridge stats."""
        if not self.n8n_bridge:
            return {"total_workflows": 0}
        return self.n8n_bridge.get_stats()

    def create_skill(self, name, description, code, category="general", tags=None):
        """Create a new reusable skill."""
        if self.skills:
            return self.skills.create_skill(name, description, code, category, tags, self.agent_name)
        return (False, "Skill engine not available", None)

    def execute_skill(self, skill_id, *args, **kwargs):
        """Execute a skill by ID."""
        if self.skills:
            return self.skills.execute_skill(skill_id, *args, **kwargs)
        return (False, "Skill engine not available")

    def search_skills(self, query, category=None, max_results=10):
        """Search for skills by name/description/tags."""
        if self.skills:
            return self.skills.search_skills(query, category, max_results=max_results)
        return []

    def list_skills(self, category=None):
        """List all available skills."""
        if self.skills:
            return self.skills.list_skills(category)
        return []

    def extract_skill_from_conversation(self, user_request, ai_solution):
        """Auto-extract a skill from a conversation turn."""
        if self.skills:
            return self.skills.extract_skill_from_conversation(user_request, ai_solution)
        return None

    def get_skill_stats(self):
        """Get skill engine statistics."""
        if self.skills:
            return self.skills.get_stats()
        return {"status": "Skill engine not available"}

    # Phase 5: Protocol Layer
    def register_agent_protocol(self, agent_id, name, description, capabilities):
        """Register an agent with protocol support."""
        if self.protocols:
            self.protocols.register_local_agent(agent_id, name, description, capabilities)
            return True
        return False

    def delegate_task(self, from_agent, to_agent, task_type, payload, priority="normal"):
        """Delegate a task to another agent via A2A."""
        if self.protocols:
            return self.protocols.delegate_task(from_agent, to_agent, task_type, payload, priority)
        return None

    def discover_agents(self, capability=None):
        """Discover available agents."""
        if self.protocols:
            return self.protocols.discover_agents(capability)
        return []

    def register_mcp_server(self, name, transport="stdio", config=None):
        """Register an MCP server."""
        if self.protocols:
            return self.protocols.register_mcp_server(name, transport, config)
        return None

    # Phase 6: Gateway Layer
    def route_message(self, channel_id, session_id, role, content):
        """Route a message through the gateway."""
        if self.gateway:
            return self.gateway.route_message(channel_id, session_id, role, content)
        return None

    def get_session_context(self, session_id, max_messages=20):
        """Get conversation context for a session."""
        if self.gateway:
            return self.gateway.get_session_context(session_id, max_messages)
        return []

    def list_gateway_channels(self):
        """List all communication channels."""
        if self.gateway:
            return self.gateway.list_channels()
        return []

    # Phase 7: Orchestrator
    def create_task(self, query, description=None):
        """Create a new task with automatic model/agent routing."""
        if self.orchestrator:
            return self.orchestrator.create_task(query, description)
        return None

    def execute_task(self, task_id, model_override=None):
        """Execute a task using the assigned model."""
        if self.orchestrator:
            return self.orchestrator.execute_task(task_id, model_override)
        return (False, "Orchestrator not available")

    def classify_query(self, query):
        """Classify a query's complexity, model, and agent."""
        if self.orchestrator:
            complexity = self.orchestrator.classify_complexity(query)
            model = self.orchestrator.select_model(query, complexity)
            agent = self.orchestrator.select_agent(query)
            return {"complexity": complexity, "model": model, "agent": agent}
        return None

    def get_orchestrator_stats(self):
        """Get orchestrator statistics."""
        if self.orchestrator:
            return self.orchestrator.get_stats()
        return {"status": "Orchestrator not available"}

    def get_protocol_status(self):
        """Get protocol layer status."""
        if self.protocols:
            return self.protocols.get_status()
        return {"status": "Protocol layer not available"}

    def get_gateway_status(self):
        """Get gateway layer status."""
        if self.gateway:
            return self.gateway.get_status()
        return {"status": "Gateway layer not available"}

    def get_full_system_status(self):
        """Get complete system status across all phases."""
        return {
            "vault": self.get_vault_stats(),
            "scheduler": self.get_scheduler_status(),
            "skills": self.get_skill_stats(),
            "security": self.get_autonomy_status(),
            "protocols": self.get_protocol_status(),
            "gateway": self.get_gateway_status(),
            "orchestrator": self.get_orchestrator_stats(),
        }

    def scan_ai_landscape(self):
        """Run AI landscape monitor scan."""
        if self.ai_monitor:
            return self.ai_monitor()
        return {"status": "AI monitor not available"}

    def get_vault_stats(self):
        """Return comprehensive vault statistics."""
        return {
            "notes": len(self.index.notes),
            "folders": len(self.topics.clusters),
            "crystallized_items": len(self.crystallization.crystallized),
            "graph_connections": sum(len(v) for v in self.graph.graph.values()),
            "topic_summary": self.topics.get_cluster_summary(),
            "knowledge_gaps": self.topics.get_gaps()[:5]
        }

    # â”€â”€ MemPalace Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def mem_palace_startup_context(self, max_tokens=900):
        """Get MemPalace L0+L1 context for session startup."""
        if self.mem_palace:
            return self.mem_palace.get_startup_context(max_tokens=max_tokens)
        return ""

    def mem_palace_query_context(self, query, max_tokens=500):
        """Get MemPalace context for a specific query."""
        if self.mem_palace:
            return self.mem_palace.get_query_context(query, max_tokens=max_tokens)
        return ""

    def mem_palace_store_fact(self, subject, predicate, value, source="manual", confidence=1.0):
        """Store a fact in the knowledge graph with contradiction detection."""
        if self.mem_palace:
            return self.mem_palace.store_fact(subject, predicate, value, source, confidence)
        return {"stored": False, "details": "MemPalace unavailable"}

    def mem_palace_search(self, query, limit=10):
        """Search the knowledge graph."""
        if self.mem_palace:
            return self.mem_palace.search_facts(query, limit=limit)
        return []

    def mem_palace_discover_tunnels(self):
        """Discover tunnels between wings."""
        if self.mem_palace:
            return self.mem_palace.discover_tunnels()
        return []

    def mem_palace_mine_all(self):
        """Auto-mine vault and projects to populate the palace."""
        if self.mem_palace:
            return self.mem_palace.auto_mine_all()
        return {"error": "MemPalace unavailable"}

    def mem_palace_stats(self):
        """Get MemPalace statistics."""
        if self.mem_palace:
            return self.mem_palace.get_palace_stats()
        return {"status": "MemPalace unavailable"}

    def mem_palace_reset_sync(self, source_type=None):
        """Reset mining sync state to force re-mine."""
        if self.mem_palace and self.mem_palace.palace_miner:
            self.mem_palace.palace_miner.reset_sync(source_type)
            return True
        return False

    # â”€â”€ FinCore Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def fincore_query(self, query: str) -> dict:
        """Route a financial query through the FinCore agent team."""
        if self.fincore:
            try:
                result = self.fincore.process(query)
                return {
                    "success": True,
                    "query_type": result.query_type.value,
                    "agents_consulted": result.agents_consulted,
                    "recommendations": [r.model_dump() for r in result.recommendations],
                    "summary": result.overall_summary,
                    "next_steps": result.next_steps,
                    "disclaimer": result.disclaimer,
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "FinCore not available"}

    def fincore_budget_plan(self) -> dict:
        """Get current budget plan."""
        return self.fincore_query("What is my budget plan and savings rate?")

    def fincore_tax_estimate(self) -> dict:
        """Get tax liability estimate."""
        return self.fincore_query("Estimate my total tax liability")

    def fincore_retirement_projection(self) -> dict:
        """Run Monte Carlo retirement projection."""
        return self.fincore_query("What is my retirement projection with Monte Carlo simulation?")

    def fincore_portfolio_allocation(self) -> dict:
        """Get recommended portfolio allocation."""
        return self.fincore_query("What is my recommended asset allocation?")

    def fincore_market_data(self, ticker: str) -> dict:
        """Get market data for a ticker."""
        return self.fincore_query(f"{ticker} market data and price")

    def fincore_price_forecast(self, ticker: str, days: int = 90) -> dict:
        """Get price forecast for a ticker."""
        return self.fincore_query(f"{ticker} price forecast next {days} days")

    def fincore_stress_test(self) -> dict:
        """Run portfolio stress tests."""
        return self.fincore_query("Run stress test on my portfolio")

    # â”€â”€ Transport Layer Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def transport_chat(self, messages: list, transport: str = None, **kwargs) -> dict:
        """
        Chat via transport layer with automatic fallback.

        Args:
            messages: List of {role, content} dicts
            transport: Specific transport to use ("gemini", "local", "openai")
            **kwargs: Override config (temperature, max_tokens, etc.)

        Returns:
            Dict with text, usage, model, success, error
        """
        from Transports import Message, MessageRole, TransportConfig

        if not self.transports:
            return {"success": False, "error": "No transports available"}

        msg_objects = []
        for m in messages:
            role = MessageRole(m.get("role", "user"))
            msg_objects.append(Message(role=role, content=m.get("content", "")))

        target_transport = None
        if transport and transport in self.transports:
            target_transport = self.transports[transport]
        elif self.active_transport:
            target_transport = self.active_transport
        elif self.transports:
            target_transport = next(iter(self.transports.values()))

        if not target_transport:
            return {"success": False, "error": "No active transport"}

        config = TransportConfig(
            model=target_transport.config.model,
            temperature=kwargs.get("temperature", target_transport.config.temperature),
            max_tokens=kwargs.get("max_tokens", target_transport.config.max_tokens),
            system_prompt=kwargs.get("system_prompt"),
        )

        response = target_transport.chat(msg_objects, config)

        return {
            "success": response.success,
            "text": response.text,
            "model": response.model,
            "usage": response.usage,
            "latency_ms": response.latency_ms,
            "finish_reason": response.finish_reason,
            "error": response.error,
        }

    def transport_generate(self, prompt: str, transport: str = None, **kwargs) -> dict:
        """
        Simple generate via transport layer.

        Args:
            prompt: Single prompt string
            transport: Specific transport to use
            **kwargs: Override config

        Returns:
            Dict with text, usage, model, success, error
        """
        messages = [{"role": "user", "content": prompt}]
        if kwargs.get("system_prompt"):
            messages.insert(0, {"role": "system", "content": kwargs.pop("system_prompt")})
        return self.transport_chat(messages, transport, **kwargs)

    def transport_stream(self, messages: list, transport: str = None, **kwargs):
        """
        Stream response via transport layer.

        Args:
            messages: List of {role, content} dicts
            transport: Specific transport to use
            **kwargs: Override config

        Yields:
            Text chunks
        """
        from Transports import Message, MessageRole, TransportConfig

        if not self.transports:
            yield "[ERROR] No transports available"
            return

        msg_objects = [Message(role=MessageRole(m["role"]), content=m["content"]) for m in messages]

        target_transport = None
        if transport and transport in self.transports:
            target_transport = self.transports[transport]
        elif self.active_transport:
            target_transport = self.active_transport
        elif self.transports:
            target_transport = next(iter(self.transports.values()))

        if not target_transport:
            yield "[ERROR] No active transport"
            return

        config = TransportConfig(
            model=target_transport.config.model,
            temperature=kwargs.get("temperature", target_transport.config.temperature),
            max_tokens=kwargs.get("max_tokens", target_transport.config.max_tokens),
        )

        yield from target_transport.stream(msg_objects, config)

    def transport_status(self) -> dict:
        """Get status of all transports."""
        status = {
            "active_transport": self.active_transport.get_model_info() if self.active_transport else None,
            "transports": {},
        }
        for name, t in self.transports.items():
            status["transports"][name] = t.get_model_info()
        return status

    def set_active_transport(self, transport_name: str) -> dict:
        """Set the active transport."""
        if transport_name in self.transports:
            self.active_transport = self.transports[transport_name]
            return {"success": True, "active": transport_name}
        return {"success": False, "error": f"Transport '{transport_name}' not found", "available": list(self.transports.keys())}

    def smart_route(self, messages: list, task_type: str = "general", **kwargs) -> dict:
        """
        Smart routing: uses local for simple tasks, Gemini for complex.

        Args:
            messages: Chat messages
            task_type: "code", "reasoning", "general", "vision", "complex"
            **kwargs: Override config

        Returns:
            Transport response dict
        """
        complex_tasks = ["vision", "complex"]
        if task_type in complex_tasks:
            return self.transport_chat(messages, transport="gemini", **kwargs)

        if "local" in self.transports:
            result = self.transport_chat(messages, transport="local", **kwargs)
            if result.get("success") and result.get("text"):
                return result

        return self.transport_chat(messages, transport="gemini", **kwargs)

    # â”€â”€ Conversation Search Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def conv_add_turn(self, session_id: str, role: str, content: str, tags: list = None) -> bool:
        """Add a conversation turn to the search index."""
        if not self.conv_search:
            return False
        return self.conv_search.add_turn(
            session_id=session_id,
            agent=self.agent_name,
            role=role,
            content=content,
            tags=tags,
        )

    def conv_search(self, query: str, limit: int = 10) -> list:
        """Search conversation history."""
        if not self.conv_search:
            return []
        return self.conv_search.search(query, agent=self.agent_name, limit=limit)

    def conv_get_session(self, session_id: str, limit: int = 100) -> list:
        """Get turns from a specific session."""
        if not self.conv_search:
            return []
        return self.conv_search.get_session(session_id, limit=limit)

    def conv_list_sessions(self, limit: int = 20) -> list:
        """List recent sessions."""
        if not self.conv_search:
            return []
        return self.conv_search.get_sessions(agent=self.agent_name, limit=limit)

    def conv_summarize_session(self, session_id: str) -> str:
        """Generate LLM summary of a session."""
        if not self.conv_search:
            return ""

        def chat_fn(messages, **kwargs):
            return self.transport_chat(messages, **kwargs)

        summary = self.conv_search.summarize_session(session_id, transport_chat_fn=chat_fn)
        return summary or ""

    def conv_stats(self) -> dict:
        """Get conversation search index stats."""
        if not self.conv_search:
            return {"total_turns": 0, "total_sessions": 0}
        return self.conv_search.get_stats()

    # â”€â”€ RAG Pipeline Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def rag_index(self, force: bool = False) -> dict:
        """Index or re-index vault for RAG retrieval."""
        if not self.rag:
            return {"error": "RAG pipeline not available"}
        return self.rag.index_vault(force=force)

    def rag_retrieve(self, query: str, top_k: int = 5) -> list:
        """Retrieve relevant context chunks for a query."""
        if not self.rag:
            return []
        return self.rag.retrieve(query, top_k=top_k)

    def rag_inject(self, prompt: str, top_k: int = 5) -> str:
        """Get context-enhanced prompt for LLM."""
        if not self.rag:
            return prompt
        return self.rag.inject_context(prompt, top_k=top_k)

    def rag_stats(self) -> dict:
        """Get RAG pipeline stats."""
        if not self.rag:
            return {"error": "RAG pipeline not available"}
        return self.rag.get_stats()

    def rag_reindex(self) -> dict:
        """Force re-index entire vault."""
        if not self.rag:
            return {"error": "RAG pipeline not available"}
        return self.rag.reindex()

    # â”€â”€ Reasoning Loop Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def plan_task(self, goal: str) -> dict:
        """Create a multi-step plan for a goal."""
        if not self.react_loop:
            return {"error": "Reasoning loop not available"}

        def chat_fn(messages, **kwargs):
            return self.transport_chat(messages, **kwargs)

        plan = self.react_loop.create_plan(goal, chat_fn)
        return plan.to_dict()

    def execute_plan(self, goal: str) -> dict:
        """Create and execute a multi-step plan."""
        if not self.react_loop:
            return {"error": "Reasoning loop not available"}

        def chat_fn(messages, **kwargs):
            return self.transport_chat(messages, **kwargs)

        plan = self.react_loop.create_plan(goal, chat_fn)
        plan = self.react_loop.execute_plan(plan, chat_fn)
        return plan.to_dict()

    def react_query(self, query: str) -> dict:
        """Full ReAct cycle: think, act, observe, reflect, answer."""
        if not self.react_loop:
            return {"error": "Reasoning loop not available"}

        def chat_fn(messages, **kwargs):
            return self.transport_chat(messages, **kwargs)

        return self.react_loop.react_query(query, chat_fn)

    def reasoning_history(self) -> list:
        """Get past reasoning plans."""
        if not self.react_loop:
            return []
        return self.react_loop.get_plan_history()


    # â”€â”€ Subagent & Model Router Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def spawn_subagent(self, description: str, prompt: str, complexity: str = "moderate") -> str:
        """Spawn a subagent task for parallel execution."""
        if not self.subagent_spawner:
            return ""
        from unified_layer.subagent_router import TaskComplexity
        return self.subagent_spawner.spawn(
            description=description,
            prompt=prompt,
            complexity=TaskComplexity(complexity),
        )

    def get_subagent_result(self, task_id: str):
        """Get result from a spawned subagent."""
        if not self.subagent_spawner:
            return None
        return self.subagent_spawner.get_result(task_id)

    def route_task(self, description: str, prompt: str) -> dict:
        """Route a task to appropriate model tier."""
        if not self.model_router:
            return {"error": "Model router not available"}
        route = self.model_router.route_task(description, prompt)
        return {
            "model": route.selected_model,
            "tier": route.tier.value,
            "reason": route.reason,
            "confidence": route.confidence,
        }

    def model_router_stats(self) -> dict:
        """Get model routing statistics."""
        if not self.model_router:
            return {"total_routes": 0}
        return self.model_router.get_routing_stats()

    # â”€â”€ Auto-Skill Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def generate_skill(self, description: str, result: str, category: str = "general") -> Optional[str]:
        """Generate a SKILL.md from task execution."""
        if not self.auto_skill:
            return None
        return self.auto_skill.generate_from_task(description, result, category=category)

    def list_skills(self) -> list:
        """List available skills."""
        if not self.auto_skill:
            return []
        return self.auto_skill.list_skills()

    # â”€â”€ Autonomy Policy Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def set_autonomy_level(self, level: int) -> dict:
        """Set agent autonomy level (1-5)."""
        if not self.autonomy_engine:
            return {"error": "Autonomy engine not available"}
        from unified_layer.policy_engine import AutonomyLevel
        return self.autonomy_engine.set_autonomy_level(AutonomyLevel(level))

    def evaluate_action(self, action_type: str, description: str, risk: int = 2) -> dict:
        """Evaluate if an action is allowed under current policy."""
        if not self.autonomy_engine:
            return {"error": "Autonomy engine not available"}
        from unified_layer.policy_engine import PolicyAction, RiskLevel
        action = PolicyAction(action_type, description, RiskLevel(risk))
        decision = self.autonomy_engine.evaluate_action(action)
        return {
            "approved": decision.approved,
            "reason": decision.reason,
            "requires_human": decision.requires_human,
        }

    def autonomy_status(self) -> dict:
        """Get current autonomy status."""
        if not self.autonomy_engine:
            return {"error": "Autonomy engine not available"}
        return self.autonomy_engine.get_status()

    # â”€â”€ Plugin Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def execute_plugin(self, name: str, *args, **kwargs):
        """Execute a registered plugin."""
        if not self.plugin_manager:
            return None
        return self.plugin_manager.execute(name, *args, **kwargs)

    def list_plugins(self) -> list:
        """List registered plugins."""
        if not self.plugin_manager:
            return []
        return self.plugin_manager.list_plugins()

    def plugin_stats(self) -> dict:
        """Get plugin manager stats."""
        if not self.plugin_manager:
            return {"total_plugins": 0}
        return self.plugin_manager.get_stats()

    # â”€â”€ Tool Calling Framework Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def tool_register(self, name: str, description: str, parameters: list, handler, category: str = "general") -> None:
        """Register a new tool."""
        if not self.tool_engine:
            return
        from unified_layer.tool_framework import ToolDefinition, ToolParameter
        params = [ToolParameter(**p) if isinstance(p, dict) else p for p in parameters]
        tool = ToolDefinition(name, description, params, handler, category)
        self.tool_engine.registry.register(tool)

    def tool_execute(self, tool_name: str, arguments: dict) -> dict:
        """Execute a registered tool."""
        if not self.tool_engine:
            return {"error": "Tool engine not available"}
        return self.tool_engine.execute_tool(tool_name, arguments)

    def tool_list(self) -> list:
        """List all available tools."""
        if not self.tool_engine:
            return []
        return self.tool_engine.registry.list_tools()

    def tool_schemas(self) -> list:
        """Get OpenAI-compatible tool schemas."""
        if not self.tool_engine:
            return []
        return self.tool_engine.registry.get_all_schemas()

    def tool_stats(self) -> dict:
        """Get tool execution stats."""
        if not self.tool_engine:
            return {"total_calls": 0}
        return self.tool_engine.get_execution_stats()

    # â”€â”€ Memory Consolidation Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def memory_add(self, content: str, category: str = "general", importance: float = 0.5) -> None:
        """Add a short-term memory."""
        if not self.consolidator:
            return
        self.consolidator.add_short_term(content, category, importance)

    def memory_consolidate(self) -> dict:
        """Run consolidation cycle."""
        if not self.consolidator:
            return {"error": "Consolidator not available"}
        def chat_fn(messages, **kwargs):
            return self.transport_chat(messages, **kwargs)
        return self.consolidator.run_consolidation(chat_fn)

    def memory_recall(self, query: str) -> list:
        """Search across short-term and consolidated memory."""
        if not self.consolidator:
            return []
        return self.consolidator.recall(query)

    def memory_stats(self) -> dict:
        """Get memory consolidation stats."""
        if not self.consolidator:
            return {"short_term_count": 0, "consolidated_count": 0}
        return self.consolidator.get_stats()

    # â”€â”€ Self-Improvement Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def improve_report_failure(self, task: str, expected: str, actual: str, failure_type: str, agent: str = "") -> dict:
        """Report a failure for self-improvement analysis."""
        if not self.self_improve:
            return {"error": "Self-improvement engine not available"}
        from unified_layer.self_improvement import FailureType
        ft = FailureType(failure_type) if failure_type in [e.value for e in FailureType] else FailureType.WRONG_OUTPUT
        failure = self.self_improve.report_failure(task, expected, actual, ft, agent)
        return {"failure_id": failure.id, "status": "recorded"}

    def improve_analyze(self) -> list:
        """Analyze failures and generate improvement proposals."""
        if not self.self_improve:
            return []
        return self.self_improve.analyze_failures()

    def improve_stats(self) -> dict:
        """Get self-improvement stats."""
        if not self.self_improve:
            return {"total_failures": 0}
        return self.self_improve.get_failure_stats()

    # â”€â”€ Benchmarking Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def benchmark_run(self, model_name: str = "default", category: str = None) -> dict:
        """Run benchmark suite."""
        if not self.benchmark_runner:
            return {"error": "Benchmark runner not available"}
        def gen_fn(prompt, max_tokens):
            return self.transport_chat([{"role": "user", "content": prompt}], max_tokens=max_tokens)
        report = self.benchmark_runner.run_benchmark(gen_fn, model_name, category)
        return report.get_report()

    def benchmark_history(self) -> list:
        """Get benchmark history."""
        if not self.benchmark_runner:
            return []
        return self.benchmark_runner.get_history()

    def benchmark_trend(self) -> dict:
        """Get score trend."""
        if not self.benchmark_runner:
            return {"trend": "no_data"}
        return self.benchmark_runner.get_trend()

    # â”€â”€ Cross-Session Learning Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def session_record(self, session_id: str, topics: list, completed: int, failed: int, tools: list, duration: float) -> None:
        """Record a completed session for cross-session learning."""
        if not self.cross_session:
            return
        from unified_layer.cross_session_learning import SessionProfile
        profile = SessionProfile(session_id, topics, completed, failed, tools, duration)
        self.cross_session.record_session(profile)

    def session_context(self, topics: list) -> dict:
        """Get personalized context based on past sessions."""
        if not self.cross_session:
            return {}
        return self.cross_session.get_session_context(topics)

    def session_patterns(self) -> list:
        """Detect recurring patterns across sessions."""
        if not self.cross_session:
            return []
        return self.cross_session.detect_patterns()

    def session_gaps(self) -> list:
        """Get identified knowledge gaps."""
        if not self.cross_session:
            return []
        return self.cross_session.get_knowledge_gaps()

    def session_stats(self) -> dict:
        """Get cross-session learning stats."""
        if not self.cross_session:
            return {"total_sessions": 0}
        return self.cross_session.get_stats()

    # â”€â”€ Reranker Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def rerank_chunks(self, query: str, chunks: list, top_k: int = 5) -> list:
        """Rerank RAG chunks using hybrid BM25 + keyword scoring."""
        if not self.reranker:
            return chunks[:top_k]
        return self.reranker.rerank(query, chunks, top_k=top_k)

    def reranker_status(self) -> dict:
        """Get reranker status."""
        if not self.reranker:
            return {"available": False}
        return {"available": True, "type": "hybrid_bm25_keyword"}

    # â”€â”€ Background Consciousness Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def consciousness_start(self) -> None:
        """Start background consciousness loop."""
        if self.background_consciousness:
            self.background_consciousness.start()

    def consciousness_stop(self) -> None:
        """Stop background consciousness."""
        if self.background_consciousness:
            self.background_consciousness.stop()

    def consciousness_think(self, thought_type: str = "reflection") -> dict:
        """Force an immediate thought cycle."""
        if not self.background_consciousness:
            return {}
        thought = self.background_consciousness.force_think(thought_type)
        return thought.to_dict() if thought else {}

    def consciousness_get_self_model(self) -> dict:
        """Get the agent's self-model."""
        if not self.background_consciousness:
            return {}
        return self.background_consciousness.get_self_model()

    def consciousness_get_thoughts(self, limit: int = 20) -> list:
        """Get recent thoughts."""
        if not self.background_consciousness:
            return []
        return self.background_consciousness.get_thoughts(limit)

    def consciousness_status(self) -> dict:
        """Get background consciousness status."""
        if not self.background_consciousness:
            return {"available": False}
        return self.background_consciousness.get_status()

    # â”€â”€ Hook System Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def hook_fire(self, event: str, data: dict = None) -> dict:
        """Fire a hook event."""
        if not self.hook_engine:
            return {}
        from unified_layer.hook_system import HookEvent
        try:
            hook_event = HookEvent(event)
        except ValueError:
            return {"error": f"Unknown hook event: {event}"}
        return self.hook_engine.fire_and_continue(hook_event, data or {}, self.agent_name, self.session_id)

    def hook_list(self) -> list:
        """List all registered hooks."""
        if not self.hook_engine:
            return []
        return self.hook_engine.registry.list_all()

    def hook_stats(self) -> dict:
        """Get hook engine stats."""
        if not self.hook_engine:
            return {"total_hooks": 0}
        return self.hook_engine.get_stats()

    def hook_log(self, limit: int = 50) -> list:
        """Get hook execution log."""
        if not self.hook_engine:
            return []
        return self.hook_engine.get_execution_log(limit)

    # â”€â”€ Constrained Grammar Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def enforce_json(self, text: str, schema: dict = None) -> tuple:
        """Parse, validate, and repair JSON output."""
        if not self.constrained_grammar:
            return ({"_raw": text}, ["Constrained grammar not available"])
        return self.constrained_grammar.enforce(text, schema)

    def enforce_tool_call(self, text: str) -> tuple:
        """Enforce tool call format on LLM output."""
        if not self.constrained_grammar:
            return ({"_raw": text}, ["Constrained grammar not available"])
        return self.constrained_grammar.enforce_tool_call(text)

    def enforce_rag_query(self, text: str) -> tuple:
        """Enforce RAG query format on LLM output."""
        if not self.constrained_grammar:
            return ({"_raw": text}, ["Constrained grammar not available"])
        return self.constrained_grammar.enforce_rag_query(text)

    # â”€â”€ Memory Reclaimer Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def memory_check(self) -> str:
        """Check memory and reclaim if needed. Returns 'ok', 'high', 'critical', or 'emergency'."""
        if not self.memory_reclaimer:
            return "unavailable"
        return self.memory_reclaimer.check_and_reclaim()

    def memory_stats(self) -> dict:
        """Get memory reclaimer status and current memory usage."""
        if not self.memory_reclaimer:
            return {"available": False}
        return self.memory_reclaimer.get_status()

    def memory_history(self, limit: int = 20) -> list:
        """Get recent memory usage history."""
        if not self.memory_reclaimer:
            return []
        return self.memory_reclaimer.get_history(limit)

    def memory_start_monitor(self) -> None:
        """Start background memory monitoring."""
        if self.memory_reclaimer:
            self.memory_reclaimer.start()

    def memory_stop_monitor(self) -> None:
        """Stop background memory monitoring."""
        if self.memory_reclaimer:
            self.memory_reclaimer.stop()

    # â”€â”€ Model Gallery Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def gallery_list(self) -> list:
        """List all available model profiles."""
        if not self.model_gallery:
            return []
        return self.model_gallery.list_profiles()

    def gallery_get(self, name: str) -> Optional[dict]:
        """Get a specific model profile."""
        if not self.model_gallery:
            return None
        profile = self.model_gallery.get_profile(name)
        return profile.to_dict() if profile else None

    def gallery_active(self) -> Optional[dict]:
        """Get the currently active model profile."""
        if not self.model_gallery:
            return None
        profile = self.model_gallery.get_active_profile()
        return profile.to_dict() if profile else None

    def gallery_switch(self, name: str) -> bool:
        """Switch to a different model profile."""
        if not self.model_gallery:
            return False
        success = self.model_gallery.set_active(name)
        if success and name in self.transports:
            self.active_transport = self.transports[name]
        return success

    def gallery_search(self, tag: str) -> list:
        """Search model profiles by tag."""
        if not self.model_gallery:
            return []
        return [p.to_dict() for p in self.model_gallery.search_by_tag(tag)]

    def gallery_status(self) -> dict:
        """Get model gallery status."""
        if not self.model_gallery:
            return {"available": False}
        return self.model_gallery.get_status()

    # â”€â”€ Dataview Query Engine Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def dataview_query(self, query: str) -> dict:
        """Execute a DQL-style query over vault metadata."""
        if not self.dataview:
            return {"error": "Dataview engine not available"}
        return self.dataview.query(query)

    def dataview_list(self, from_clause: str = "", where: str = "", sort: str = "", limit: int = 50) -> list:
        """LIST query helper."""
        if not self.dataview:
            return []
        q = f"LIST"
        if from_clause:
            q += f" FROM {from_clause}"
        if where:
            q += f" WHERE {where}"
        if sort:
            q += f" SORT {sort}"
        q += f" LIMIT {limit}"
        return self.dataview.query(q)

    def dataview_table(self, columns: list, from_clause: str = "", where: str = "", sort: str = "", limit: int = 50) -> dict:
        """TABLE query helper."""
        if not self.dataview:
            return {"columns": columns, "rows": []}
        cols = ", ".join(columns)
        q = f"TABLE {cols}"
        if from_clause:
            q += f" FROM {from_clause}"
        if where:
            q += f" WHERE {where}"
        if sort:
            q += f" SORT {sort}"
        q += f" LIMIT {limit}"
        return self.dataview.query(q)

    def dataview_tasks(self, where: str = "", sort: str = "", limit: int = 100) -> list:
        """TASK query helper."""
        if not self.dataview:
            return []
        q = "TASK"
        if where:
            q += f" WHERE {where}"
        if sort:
            q += f" SORT {sort}"
        q += f" LIMIT {limit}"
        return self.dataview.query(q)

    def dataview_reindex(self) -> int:
        """Re-index the vault."""
        if not self.dataview:
            return 0
        return self.dataview.reindex()

    # â”€â”€ Template Engine Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def template_render(self, template: str, variables: dict = None) -> str:
        """Render a template string with variables."""
        if not self.template_engine:
            return template
        return self.template_engine.render(template, variables)

    def template_render_file(self, name: str, variables: dict = None) -> str:
        """Render a template file by name."""
        if not self.template_engine:
            return f"[Template engine not available: {name}]"
        return self.template_engine.render_file(name, variables)

    def template_create(self, name: str, content: str) -> str:
        """Create a new template."""
        if not self.template_engine:
            return ""
        return self.template_engine.create_template(name, content)

    def template_list(self) -> list[str]:
        """List available templates."""
        if not self.template_engine:
            return []
        return self.template_engine.list_templates()

    # â”€â”€ Observability / LLMOps Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def obs_trace(self, span_type: str, model: str = "", prompt: str = "", response: str = "",
                  tokens_in: int = 0, tokens_out: int = 0, latency_ms: float = 0.0,
                  cost: float = 0.0, agent: str = "", session_id: str = "",
                  tags: list = None, quality_score: float = 0.0, error: str = "") -> str:
        """Record an LLM interaction trace."""
        if not self.observability:
            return ""
        return self.observability.trace(
            span_type=span_type, model=model, prompt=prompt, response=response,
            tokens_in=tokens_in, tokens_out=tokens_out, latency_ms=latency_ms,
            cost=cost, agent=agent, session_id=session_id, tags=tags,
            quality_score=quality_score, error=error,
        )

    def obs_traces(self, limit: int = 50, span_type: str = None, model: str = None, agent: str = None, error_only: bool = False) -> list:
        """Get recent traces."""
        if not self.observability:
            return []
        return self.observability.get_traces(limit=limit, span_type=span_type, model=model, agent=agent, error_only=error_only)

    def obs_cost_summary(self, days: int = 7) -> dict:
        """Get cost summary for a time period."""
        if not self.observability:
            return {"total_cost": 0, "total_calls": 0}
        return self.observability.get_cost_summary(days=days)

    def obs_latency_stats(self) -> dict:
        """Get latency percentiles."""
        if not self.observability:
            return {"avg": 0, "p50": 0, "p95": 0, "p99": 0}
        return self.observability.get_latency_stats()

    def obs_quality_trend(self) -> list:
        """Get quality score trend."""
        if not self.observability:
            return []
        return self.observability.get_quality_trend()

    def obs_stats(self) -> dict:
        """Get observability stats."""
        if not self.observability:
            return {"total_traces": 0}
        return self.observability.get_stats()

    # â”€â”€ Prompt Library Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def prompt_add(self, name: str, template: str, category: str = "general", tags: list = None, system_prompt: str = "", description: str = "") -> Optional[dict]:
        """Add a prompt to the library."""
        if not self.prompt_library:
            return None
        p = self.prompt_library.add_prompt(name, template, category, tags, system_prompt, description)
        return p.to_dict()

    def prompt_get(self, name: str) -> Optional[str]:
        """Get a prompt template by name."""
        if not self.prompt_library:
            return None
        p = self.prompt_library.get_prompt(name)
        return p.template if p else None

    def prompt_render(self, name: str, **kwargs) -> Optional[str]:
        """Render a prompt with variables."""
        if not self.prompt_library:
            return None
        return self.prompt_library.render(name, **kwargs)

    def prompt_search(self, query: str = "", category: str = None, tag: str = None) -> list:
        """Search prompts."""
        if not self.prompt_library:
            return []
        return self.prompt_library.search(query, category, tag)

    def prompt_feedback(self, name: str, score: float, feedback: str = "") -> None:
        """Record prompt feedback."""
        if not self.prompt_library:
            return
        self.prompt_library.record_feedback(name, score, feedback)

    def prompt_top(self, n: int = 10) -> list:
        """Get top-rated prompts."""
        if not self.prompt_library:
            return []
        return self.prompt_library.get_top_prompts(n)

    def prompt_stats(self) -> dict:
        """Get prompt library stats."""
        if not self.prompt_library:
            return {"total_prompts": 0}
        return self.prompt_library.stats()

    # â”€â”€ Memory Reclaimer Callbacks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _unload_local_transport(self, mode: str = "lru") -> None:
        """Callback for memory reclaimer to unload local models."""
        if mode == "all" and self.transports:
            local_keys = [k for k in self.transports if k == "local"]
            for k in local_keys:
                if k in self.transports:
                    del self.transports[k]
            if self.active_transport and self.active_transport.config.model in ["phi-4-mini", "qwen2.5-3b"]:
                self.active_transport = self.transports.get("gemini")
        elif mode == "lru" and "local" in self.transports:
            del self.transports["local"]
            if self.active_transport and self.active_transport.config.model in ["phi-4-mini", "qwen2.5-3b"]:
                self.active_transport = self.transports.get("gemini")

    def _compress_history(self) -> None:
        """Callback for memory reclaimer to compress conversation history."""
        if self.conv_search:
            try:
                self.conv_search.prune_older_than(hours=2)
            except Exception:
                pass

    def _clear_cache(self) -> None:
        """Callback for memory reclaimer to clear caches."""
        if self.rag and hasattr(self.rag, 'clear_cache'):
            try:
                self.rag.clear_cache()
            except Exception:
                pass

    # â”€â”€ System Status (All Modules) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def system_status(self) -> dict:
        """Get status of all system modules."""
        return {
            "transports": list(self.transports.keys()) if self.transports else [],
            "active_transport": self.active_transport.get_model_info() if self.active_transport else None,
            "fincore": self.fincore is not None,
            "conv_search": self.conv_search is not None,
            "rag": self.rag is not None,
            "reranker": self.reranker is not None,
            "react_loop": self.react_loop is not None,
            "tool_engine": self.tool_engine is not None,
            "consolidator": self.consolidator is not None,
            "self_improve": self.self_improve is not None,
            "benchmark_runner": self.benchmark_runner is not None,
            "cross_session": self.cross_session is not None,
            "model_router": self.model_router is not None,
            "subagent_spawner": self.subagent_spawner is not None,
            "auto_skill": self.auto_skill is not None,
            "autonomy_engine": self.autonomy_engine is not None,
            "plugin_manager": self.plugin_manager is not None,
            "background_consciousness": self.background_consciousness is not None,
            "hook_engine": self.hook_engine is not None,
            "constrained_grammar": self.constrained_grammar is not None,
            "memory_reclaimer": self.memory_reclaimer is not None,
            "model_gallery": self.model_gallery is not None,
            "dataview": self.dataview is not None,
            "template_engine": self.template_engine is not None,
            "observability": self.observability is not None,
            "prompt_library": self.prompt_library is not None,
            "n8n_bridge": self.n8n_bridge is not None,
            "cloud_scheduler": self.cloud_scheduler is not None,
            "background_consciousness": self.background_consciousness is not None,
        }


def load_unified_layer(agent_name="lais"):
    """Factory function to load the unified layer."""
    return UnifiedLayer(agent_name)


if __name__ == "__main__":
    layer = load_unified_layer("test")
    
    print("=== Unified Memory Layer v1.0 ===")
    stats = layer.get_vault_stats()
    print(f"Notes: {stats['notes']}")
    print(f"Folders: {stats['folders']}")
    print(f"Crystallized: {stats['crystallized_items']}")
    print(f"Graph Connections: {stats['graph_connections']}")
    
    print("\n=== Topic Clusters ===")
    for folder, data in stats['topic_summary'].items():
        print(f"  {folder}: {data['note_count']} notes, {data['total_words']} words")
    
    print("\n=== Knowledge Gaps ===")
    for gap in stats['knowledge_gaps']:
        print(f"  {gap['keyword']} (mentioned {gap['mentions']}x)")
    
    print("\n=== Test Search: 'Python programming' ===")
    results = layer.semantic_search("Python programming")
    for r in results:
        print(f"  [{r['type']}] {r.get('title', r.get('key'))}")
    
    print("\n=== Context Injection ===")
    context = layer.get_context_injection("How to optimize AI models for low RAM?")
    print(context[:500] if context else "(no context found)")
