"""
Skill Engine v2 — Progressive 3-level loading with description-based triggering.
Inspired by Anthropic Agent Skills (Apache 2.0) + everything-claude-code.
"""

import json
import re
import ast
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple
from threading import Lock

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

SKILL_REGISTRY_FILE = SKILLS_DIR / "skill_registry.json"
SKILL_LOG_FILE = SKILLS_DIR / "skill_log.json"
TRIGGER_EVAL_FILE = SKILLS_DIR / "trigger_evals.json"
LOCK = Lock()


class Skill:
    """Represents a reusable agent skill with progressive disclosure."""

    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        code: str = "",
        category: str = "general",
        tags: Optional[List[str]] = None,
        created_by: str = "system",
        trigger_keywords: Optional[List[str]] = None,
        reference_files: Optional[List[str]] = None,
        allowed_tools: Optional[List[str]] = None,
        eval_queries: Optional[List[str]] = None,
    ):
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.code = code
        self.category = category
        self.tags = tags or []
        self.created_by = created_by
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.usage_count = 0
        self.last_used = None
        self.success_rate = 0.0
        self.successes = 0
        self.failures = 0
        self.enabled = True
        self.trigger_keywords = trigger_keywords or []
        self.reference_files = reference_files or []
        self.allowed_tools = allowed_tools or []
        self.eval_queries = eval_queries or []
        self.eval_results: Optional[Dict[str, Any]] = None

    def record_usage(self, success: bool):
        self.usage_count += 1
        self.last_used = datetime.now().isoformat()
        if success:
            self.successes += 1
        else:
            self.failures += 1
        total = self.successes + self.failures
        self.success_rate = self.successes / total if total > 0 else 0.0
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "category": self.category,
            "tags": self.tags,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "success_rate": round(self.success_rate, 2),
            "enabled": self.enabled,
            "trigger_keywords": self.trigger_keywords,
            "reference_files": self.reference_files,
            "allowed_tools": self.allowed_tools,
            "eval_queries": self.eval_queries,
            "eval_results": self.eval_results,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        skill = cls(
            skill_id=data["skill_id"],
            name=data["name"],
            description=data["description"],
            code=data.get("code", ""),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            created_by=data.get("created_by", "system"),
            trigger_keywords=data.get("trigger_keywords", []),
            reference_files=data.get("reference_files", []),
            allowed_tools=data.get("allowed_tools", []),
            eval_queries=data.get("eval_queries", []),
        )
        skill.created_at = data.get("created_at", datetime.now().isoformat())
        skill.updated_at = data.get("updated_at", skill.created_at)
        skill.usage_count = data.get("usage_count", 0)
        skill.last_used = data.get("last_used")
        skill.success_rate = data.get("success_rate", 0.0)
        skill.successes = data.get("successes", 0)
        skill.failures = data.get("failures", 0)
        skill.enabled = data.get("enabled", True)
        skill.eval_results = data.get("eval_results")
        return skill

    def to_metadata(self) -> Dict[str, Any]:
        """Level 1: Metadata only — always in context (~100 tokens)."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.trigger_keywords or self.tags[:3],
            "success_rate": round(self.success_rate, 2),
            "usage_count": self.usage_count,
            "allowed_tools": self.allowed_tools,
        }

    def to_instructions(self) -> Dict[str, Any]:
        """Level 2: Full instructions — loaded on trigger."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "category": self.category,
            "tags": self.tags,
            "trigger_keywords": self.trigger_keywords,
            "reference_files": self.reference_files,
            "allowed_tools": self.allowed_tools,
            "eval_queries": self.eval_queries,
            "usage_count": self.usage_count,
            "success_rate": round(self.success_rate, 2),
        }


class SkillEngine:
    """
    Self-improving skill engine with progressive 3-level disclosure.
    Level 1: Metadata always in context
    Level 2: Full instructions loaded on trigger match
    Level 3: Reference files loaded on demand
    """

    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.runtime_handlers: Dict[str, Callable] = {}
        self._load_registry()

    def _load_registry(self):
        if SKILL_REGISTRY_FILE.exists():
            try:
                data = json.loads(SKILL_REGISTRY_FILE.read_text(encoding="utf-8"))
                for skill_data in data:
                    skill = Skill.from_dict(skill_data)
                    if skill.enabled:
                        self.skills[skill.skill_id] = skill
            except Exception:
                pass

    def _save_registry(self):
        with LOCK:
            all_skills = [skill.to_dict() for skill in self.skills.values()]
            SKILL_REGISTRY_FILE.write_text(json.dumps(all_skills, indent=2), encoding="utf-8")

    def get_metadata_index(self) -> List[Dict[str, Any]]:
        """Level 1: Return lightweight metadata for all enabled skills."""
        return [s.to_metadata() for s in self.skills.values() if s.enabled]

    def get_instructions(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Level 2: Return full instructions for a specific skill."""
        skill = self.skills.get(skill_id)
        return skill.to_instructions() if skill and skill.enabled else None

    def get_reference(self, skill_id: str, ref_name: str) -> Optional[str]:
        """Level 3: Load a reference file on demand."""
        skill = self.skills.get(skill_id)
        if not skill or not skill.enabled:
            return None
        ref_path = SKILLS_DIR / skill_id.replace("skill_", "") / ref_name
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8")
        return None

    def detect_trigger(self, query: str, min_score: int = 5) -> Optional[Dict[str, Any]]:
        """Description-based triggering: find best matching skill."""
        query_lower = query.lower()
        best_match = None
        best_score = 0

        for skill in self.skills.values():
            if not skill.enabled:
                continue

            score = 0
            # Description match (primary signal)
            desc_words = skill.description.lower().split()
            for word in desc_words:
                if len(word) > 3 and word in query_lower:
                    score += 3

            # Trigger keywords match
            for kw in skill.trigger_keywords:
                if kw.lower() in query_lower:
                    score += 5

            # Tag match
            for tag in skill.tags:
                if tag.lower() in query_lower:
                    score += 3

            # Name match
            name_words = skill.name.lower().split()
            for word in name_words:
                if len(word) > 3 and word in query_lower:
                    score += 2

            # Boost for well-performing skills
            if skill.success_rate > 0.8 and skill.usage_count > 5:
                score += 2

            if score > best_score:
                best_score = score
                best_match = skill.to_instructions()
                best_match["trigger_score"] = score

        if best_match and best_score >= min_score:
            return best_match
        return None

    def compute_trigger_accuracy(self, eval_queries: List[str]) -> float:
        """
        Evaluate trigger accuracy: given a list of (query, should_trigger_skill_id) pairs,
        return accuracy score.
        """
        if not eval_queries:
            return 0.0
        correct = 0
        for q_item in eval_queries:
            if isinstance(q_item, dict):
                query = q_item.get("query", "")
                expected = q_item.get("expected_skill", "")
                result = self.detect_trigger(query, min_score=3)
                triggered = result["skill_id"] if result else None
                if triggered == expected:
                    correct += 1
        return correct / len(eval_queries)

    def optimize_description(self, skill_id: str, eval_data: List[Dict]) -> Tuple[bool, str]:
        """
        Optimize skill description using trigger eval data.
        eval_data: list of {"query": str, "should_trigger": bool}
        """
        skill = self.skills.get(skill_id)
        if not skill:
            return False, "Skill not found"

        if len(eval_data) < 4:
            return False, "Need at least 4 eval queries"

        split = max(2, int(len(eval_data) * 0.6))
        train = eval_data[:split]
        test = eval_data[split:]

        triggers_found = 0
        for item in train:
            result = self.detect_trigger(item["query"], min_score=3)
            triggered = result is not None
            if triggered == item["should_trigger"]:
                triggers_found += 1

        accuracy = triggers_found / len(train) if train else 0
        return True, f"Trigger accuracy: {accuracy:.0%} (train={len(train)}, test={len(test)})"

    def search_skills(self, query: str, category: Optional[str] = None, min_success_rate: float = 0.0, max_results: int = 10) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        for skill in self.skills.values():
            if not skill.enabled:
                continue
            if category and skill.category != category:
                continue
            if skill.success_rate < min_success_rate:
                continue
            score = 0
            if query_lower in skill.name.lower():
                score += 10
            if query_lower in skill.description.lower():
                score += 5
            if any(query_lower in tag.lower() for tag in skill.tags):
                score += 3
            if any(query_lower in kw.lower() for kw in skill.trigger_keywords):
                score += 4
            if score > 0:
                results.append((score, skill.to_dict()))
        results.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in results[:max_results]]

    def get_skill(self, skill_id: str) -> Optional[Dict]:
        skill = self.skills.get(skill_id)
        return skill.to_dict() if skill else None

    def list_skills(self, category: Optional[str] = None) -> List[Dict]:
        results = []
        for skill in self.skills.values():
            if not skill.enabled:
                continue
            if category and skill.category != category:
                continue
            results.append(skill.to_dict())
        results.sort(key=lambda x: x["usage_count"], reverse=True)
        return results

    def create_skill(self, name, description, code="", category="general", tags=None, created_by="system", trigger_keywords=None, eval_queries=None):
        skill_id = f"skill_{int(datetime.now().timestamp() * 1000)}"
        skill = Skill(
            skill_id=skill_id, name=name, description=description, code=code,
            category=category, tags=tags or [], created_by=created_by,
            trigger_keywords=trigger_keywords or [], eval_queries=eval_queries or [],
        )
        self.skills[skill_id] = skill
        self._save_registry()
        self._log("created", skill_id, f"Created by {created_by}")
        return True, f"Skill '{name}' created", skill

    def execute_skill(self, skill_id, *args, **kwargs):
        skill = self.skills.get(skill_id)
        if not skill:
            return False, f"Skill {skill_id} not found"
        try:
            local_ns = {"__builtins__": __builtins__}
            exec(skill.code, local_ns)
            if "execute" in local_ns:
                result = local_ns["execute"](*args, **kwargs)
                skill.record_usage(success=True)
                self._save_registry()
                return True, result
            else:
                skill.record_usage(success=False)
                self._save_registry()
                return False, "Skill code has no execute() function"
        except Exception as e:
            skill.record_usage(success=False)
            self._save_registry()
            return False, str(e)

    def disable_skill(self, skill_id: str) -> bool:
        if skill_id in self.skills:
            self.skills[skill_id].enabled = False
            self.skills[skill_id].updated_at = datetime.now().isoformat()
            self._save_registry()
            return True
        return False

    def enable_skill(self, skill_id: str) -> bool:
        if skill_id in self.skills:
            self.skills[skill_id].enabled = True
            self.skills[skill_id].updated_at = datetime.now().isoformat()
            self._save_registry()
            return True
        return False

    def _log(self, event: str, skill_id: str, detail: str):
        entry = {"event": event, "skill_id": skill_id, "detail": detail, "timestamp": datetime.now().isoformat()}
        try:
            log = json.loads(SKILL_LOG_FILE.read_text(encoding="utf-8")) if SKILL_LOG_FILE.exists() else []
            log.append(entry)
            SKILL_LOG_FILE.write_text(json.dumps(log[-100:], indent=2), encoding="utf-8")
        except Exception:
            pass

    def extract_skill_from_conversation(self, user_request: str, ai_solution: str) -> Optional[Dict]:
        combined = f"{user_request} {ai_solution}".lower()
        signals = ["def ", "function", "here's how", "here is how", "to do this", "you can use", "reusable", "utility", "helper", "script"]
        signal_score = sum(1 for s in signals if s in combined)
        if signal_score < 2:
            return None
        code_blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", ai_solution, re.DOTALL)
        if not code_blocks or len(code_blocks[0].strip()) < 10:
            return None
        return {
            "name": user_request.strip()[:50],
            "description": f"Auto-generated from: {user_request[:80]}",
            "code": code_blocks[0].strip(),
            "category": "auto-generated",
            "tags": ["auto"],
        }

    def get_stats(self) -> Dict[str, Any]:
        skills = list(self.skills.values())
        total_usage = sum(s.usage_count for s in skills)
        avg_success = sum(s.success_rate for s in skills if s.usage_count > 0) / max(1, sum(1 for s in skills if s.usage_count > 0))
        categories = {}
        for s in skills:
            categories[s.category] = categories.get(s.category, 0) + 1
        return {
            "total_skills": len(skills),
            "enabled_skills": sum(1 for s in skills if s.enabled),
            "total_usage": total_usage,
            "avg_success_rate": round(avg_success, 2),
            "categories": categories,
            "trigger_enabled": True,
            "progressive_loading": "3-level",
        }

    def create_meta_skill_creator(self):
        """Create the skill-creator meta-skill inline."""
        code = '''
import json
from pathlib import Path

def execute(task, description=None, trigger_keywords=None, eval_queries=None):
    """Create or optimize a skill. This meta-skill helps build other skills."""
    return {
        "status": "skill_ready",
        "task": task,
        "suggested_name": task.strip()[:40].replace(" ", "_"),
        "suggested_description": description or f"Skill for: {task[:60]}",
        "suggested_keywords": trigger_keywords or [w.lower() for w in task.split() if len(w) > 3][:5],
        "auto_eval": True,
    }
'''
        ok, msg, skill = self.create_skill(
            name="Skill Creator Meta-Skill",
            description="Create new skills, modify existing skills, and measure skill performance via trigger evals. Use when users want to create a skill from scratch, edit, or optimize trigger descriptions.",
            code=code,
            category="meta",
            tags=["meta", "skill-creation", "trigger-optimization", "eval"],
            created_by="system",
            trigger_keywords=["create skill", "new skill", "optimize skill", "skill creator", "meta skill", "trigger eval", "improve description"],
            eval_queries=[
                {"query": "create a skill for formatting tables", "expected_skill": "skill_creator", "should_trigger": True},
                {"query": "how do I make a new reusable skill", "expected_skill": "skill_creator", "should_trigger": True},
                {"query": "what skills do we have", "expected_skill": "", "should_trigger": False},
            ],
        )
        if ok and skill:
            eval_ok, eval_msg = self.auto_eval_trigger(skill.skill_id, optimize=True)
            msg = f"{msg}. {eval_msg}"
        return ok, msg, skill

    def auto_eval_trigger(self, skill_id: str, optimize: bool = True, f1_threshold: float = 0.7, use_llm: bool = False):
        """
        Auto-run trigger evaluation on a skill using engine's detect_trigger() for consistency.
        Optionally uses LLM-graded eval (use_llm=True) if a capable model is available.
        Stores results in skill.eval_results.
        """
        skill = self.skills.get(skill_id)
        if not skill:
            return False, "Skill not found"

        try:
            should_queries, should_not_queries = [], []

            # Try to import trigger_eval for query templates
            trigger_path = SKILLS_DIR / "skill_creator" / "trigger_eval.py"
            te = None
            if trigger_path.exists():
                spec = importlib.util.spec_from_file_location("trigger_eval_module", str(trigger_path))
                te = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(te)
                should_queries, should_not_queries = te.get_queries(skill.name, skill.description)
            else:
                # Fallback: generate simple queries
                lower = skill.description.lower()
                keywords = [w for w in lower.split() if len(w) > 3][:5] or [skill.name.lower()[:20]]
                should_queries = [{"q": k, "reason": "keyword"} for k in keywords]
                should_not_queries = [
                    {"q": "weather", "reason": "unrelated"},
                    {"q": "email", "reason": "unrelated"},
                ]

            tp = fn = fp = tn = 0
            results = []

            # Evaluate should-match queries
            for item in should_queries:
                q = item["q"] if isinstance(item, dict) else item
                if use_llm and te:
                    triggered = te.evaluate_single(skill.description, q)
                else:
                    result = self.detect_trigger(q, min_score=2)
                    triggered = (result is not None and result.get("skill_id") == skill_id)
                if triggered:
                    tp += 1
                else:
                    fn += 1
                results.append({"query": q, "expected": True, "got": triggered,
                                "status": "TP" if triggered else "FN", "reason": item.get("reason", "")})

            # Evaluate should-NOT-match queries
            for item in should_not_queries:
                q = item["q"] if isinstance(item, dict) else item
                if use_llm and te:
                    triggered = te.evaluate_single(skill.description, q)
                else:
                    result = self.detect_trigger(q, min_score=3)
                    triggered = (result is not None and result.get("skill_id") == skill_id)
                if not triggered:
                    tn += 1
                else:
                    fp += 1
                results.append({"query": q, "expected": False, "got": triggered,
                                "status": "TN" if not triggered else "FP", "reason": item.get("reason", "")})

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            skill.eval_results = {
                "f1": f1, "precision": precision, "recall": recall,
                "tp": tp, "fn": fn, "fp": fp, "tn": tn,
                "query_count": len(results),
                "eval_date": datetime.now().isoformat(),
                "eval_mode": "llm" if use_llm else "engine",
            }

            if optimize and f1 < f1_threshold and te:
                best_desc = te.optimize_description(skill.description, skill.name,
                    {"f1": f1, "results": results}, iterations=2)
                if best_desc and best_desc != skill.description:
                    skill.description = best_desc
                    skill.eval_results["optimized_description"] = best_desc

            self._save_registry()
            return True, f"Trigger eval complete: F1={skill.eval_results['f1']:.1%} (mode={'llm' if use_llm else 'engine'})"

        except Exception as e:
            return False, f"Trigger eval failed: {e}"


def load_skill_engine() -> SkillEngine:
    return SkillEngine()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    engine = load_skill_engine()

    print("=== Skill Engine v2 — Progressive 3-Level Loading ===\n")

    ok, msg, skill = engine.create_skill(
        "Format Table",
        "Format a list of dicts as an aligned text table for terminal output",
        code='''def execute(data, format_type="markdown"):
    if not data: return "No data"
    headers = list(data[0].keys())
    widths = {h: len(h) for h in headers}
    for row in data:
        for h in headers:
            widths[h] = max(widths[h], len(str(row.get(h, ""))))
    header_line = " | ".join(h.ljust(widths[h]) for h in headers)
    sep = "-+-".join("-" * widths[h] for h in headers)
    lines = [header_line, sep]
    for row in data:
        line = " | ".join(str(row.get(h, "")).ljust(widths[h]) for h in headers)
        lines.append(line)
    return "\\n".join(lines)
''',
        category="formatting", tags=["table", "format", "output"],
        created_by="system", trigger_keywords=["format table", "align text", "output table", "markdown table"],
    )
    print(f"  1. {skill.name}: {msg}")

    ok, msg, skill = engine.create_skill(
        "Search Vault Notes",
        "Search the Obsidian vault by keyword matching note titles and content",
        code='''def execute(query, max_results=5):
    import os
    results = []
    vault = os.path.expanduser("~/Desktop/AI projects/Obsidian/Unified Brain")
    for root, dirs, files in os.walk(vault):
        for f in files:
            if f.endswith(".md"):
                path = os.path.join(root, f)
                try:
                    content = open(path, encoding="utf-8").read()
                    if query.lower() in content.lower():
                        results.append({"file": f, "path": path})
                        if len(results) >= max_results:
                            return results
                except: pass
    return results
''',
        category="vault", tags=["search", "vault", "notes"],
        created_by="system", trigger_keywords=["search vault", "find note", "vault search", "obsidian search"],
    )
    print(f"  2. {skill.name}: {msg}")

    # Create meta-skill
    ok, msg, meta_skill = engine.create_meta_skill_creator()
    print(f"  3. {meta_skill.name}: {msg}")

    # Progressive disclosure demo
    print("\n--- Progressive Disclosure Demo ---")
    metadata = engine.get_metadata_index()
    print(f"  Level 1 (metadata): {len(metadata)} skills, ~{len(metadata) * 80} tokens")
    for m in metadata:
        print(f"    [{m['category']}] {m['name']} — {m['description'][:50]}...")

    print(f"\n  Level 2 (trigger match):")
    result = engine.detect_trigger("can you format this table for me")
    if result:
        print(f"    Triggered: {result['name']} (score={result['trigger_score']})")

    result = engine.detect_trigger("search for project notes in vault")
    if result:
        print(f"    Triggered: {result['name']} (score={result['trigger_score']})")

    result = engine.detect_trigger("I need to create a new skill")
    if result:
        print(f"    Triggered: {result['name']} (score={result['trigger_score']})")

    print("\n--- Stats ---")
    stats = engine.get_stats()
    print(json.dumps(stats, indent=2))
    print("\nSkill Engine v2 ready.")
