"""
Honcho Dialectic Memory Engine
Vault-level hybrid system that performs dialectic reasoning about the user.

Operates across all three agents (lais, jarvis, opencode):
1. Collects conversation turns
2. After N turns (cadence), calls Gemini for dialectic reasoning
3. Writes conclusions to SQLite (conclusions category) and Vault Notes (Markdown)

The dialectic prompt asks Gemini to derive deep insights about the user
that go beyond explicit statements.
"""

import os
import sys
import json
import threading
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque

# Add paths for imports
LAIS_PATH = Path(r"str(Path(__file__).resolve().parent.parent)")
JARVIS_XXXIX_PATH = Path(r"%USERPROFILE%\Desktop\AI projects\Mark-XXXIX")

for p in [LAIS_PATH, JARVIS_XXXIX_PATH]:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Vault path
VAULT_BASE = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
HONCHO_DIR = VAULT_BASE / "30_Honcho"
CONCLUSIONS_DIR = HONCHO_DIR / "Conclusions"
USER_PROFILE_PATH = HONCHO_DIR / "User Profile.md"

# SQLite path (JARVIS memory)
JARVIS_DB_PATH = JARVIS_XXXIX_PATH / "memory" / "jarvis_memory.db"

# Configuration
DEFAULT_CADENCE = 5  # Run dialectic every N turns
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"


class DialecticEngine:
    """
    Honcho Dialectic Engine - derives deep user insights through Gemini reasoning.

    Collects conversation turns from all agents, and periodically runs
    dialectic analysis to update the user profile and conclusions.
    """

    def __init__(
        self,
        cadence: int = DEFAULT_CADENCE,
        gemini_model: str = DEFAULT_GEMINI_MODEL,
        vault_base: Optional[Path] = None,
        jarvis_db_path: Optional[Path] = None,
    ):
        self.cadence = cadence
        self.gemini_model = gemini_model
        self.vault_base = vault_base or VAULT_BASE
        self.honcho_dir = self.vault_base / "30_Honcho"
        self.conclusions_dir = self.honcho_dir / "Conclusions"
        self.user_profile_path = self.honcho_dir / "User Profile.md"
        self.jarvis_db_path = jarvis_db_path or JARVIS_DB_PATH

        self.turn_buffer: deque = deque(maxlen=cadence * 2)
        self.turn_count = 0
        self._lock = threading.Lock()
        self._gemini_client = None
        self._gemini_api_key = None

        # Ensure directories exist
        self.conclusions_dir.mkdir(parents=True, exist_ok=True)

        print(f"[Honcho] Dialectic Engine initialized (cadence={cadence})")

    def _get_gemini_client(self):
        """Lazy-load Gemini client."""
        if self._gemini_client is None:
            try:
                from google import genai
                if self._gemini_api_key is None:
                    from utils.api_keys import get_gemini_api_key
                    self._gemini_api_key = get_gemini_api_key()
                self._gemini_client = genai.Client(api_key=self._gemini_api_key)
                print("[Honcho] Gemini client initialized")
            except Exception as e:
                print(f"[Honcho] âš ï¸ Gemini client init failed: {e}")
                return None
        return self._gemini_client

    def _read_jarvis_memory(self) -> Dict[str, Any]:
        """Read existing memory from JARVIS SQLite."""
        try:
            import sqlite3
            if not self.jarvis_db_path.exists():
                return {}
            conn = sqlite3.connect(str(self.jarvis_db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            memory = {}
            categories = ["identity", "preferences", "projects", "relationships", "wishes", "notes", "conclusions"]
            for cat in categories:
                cur.execute(
                    "SELECT key, value, updated FROM memory_entries WHERE category = ? ORDER BY updated DESC LIMIT 20",
                    (cat,)
                )
                rows = cur.fetchall()
                if rows:
                    memory[cat] = {row["key"]: {"value": row["value"], "updated": row["updated"]} for row in rows}
            conn.close()
            return memory
        except Exception as e:
            print(f"[Honcho] âš ï¸ Failed to read JARVIS memory: {e}")
            return {}

    def _read_user_profile(self) -> str:
        """Read existing User Profile.md from vault."""
        try:
            if self.user_profile_path.exists():
                return self.user_profile_path.read_text(encoding="utf-8")
            return ""
        except Exception as e:
            print(f"[Honcho] âš ï¸ Failed to read User Profile: {e}")
            return ""

    def _write_conclusion_to_sqlite(self, conclusion: str, date_str: str) -> None:
        """Write conclusion to JARVIS SQLite (conclusions category)."""
        try:
            import sqlite3
            from datetime import datetime as dt
            conn = sqlite3.connect(str(self.jarvis_db_path))
            cur = conn.cursor()
            now = dt.now().strftime("%Y-%m-%d")
            key = f"dialectic_{date_str}_{int(time.time())}"
            cur.execute(
                "INSERT OR REPLACE INTO memory_entries (category, key, value, updated, created) VALUES (?, ?, ?, ?, ?)",
                ("conclusions", key, conclusion[:400], now, now)
            )
            conn.commit()
            conn.close()
            print(f"[Honcho] âœ… Conclusion written to SQLite: {key}")
        except Exception as e:
            print(f"[Honcho] âš ï¸ Failed to write conclusion to SQLite: {e}")

    def _write_conclusion_to_vault(self, conclusion: str, date_str: str) -> None:
        """Write conclusion as dated markdown file in Conclusions folder."""
        try:
            conclusion_path = self.conclusions_dir / f"{date_str}.md"
            content = f"""# Dialectic Conclusion â€” {date_str}

> *Generated by Honcho Dialectic Engine*

---

{conclusion}

---

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            conclusion_path.write_text(content, encoding="utf-8")
            print(f"[Honcho] âœ… Conclusion written to vault: {conclusion_path.name}")
        except Exception as e:
            print(f"[Honcho] âš ï¸ Failed to write conclusion to vault: {e}")

    def _update_user_profile(self, profile_update: str) -> None:
        """Update the User Profile.md with new insights."""
        try:
            existing = self._read_user_profile()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            if existing:
                # Append to existing profile under Dialectic Conclusions section
                if "## Dialectic Conclusions" in existing:
                    parts = existing.split("## Dialectic Conclusions")
                    updated = parts[0] + f"## Dialectic Conclusions\n\n### {now}\n\n{profile_update}\n\n" + "## Dialectic Conclusions".join(parts[1:])
                else:
                    updated = existing + f"\n\n## Dialectic Conclusions\n\n### {now}\n\n{profile_update}\n"
            else:
                updated = self._generate_initial_profile() + f"\n\n## Dialectic Conclusions\n\n### {now}\n\n{profile_update}\n"
            self.user_profile_path.write_text(updated, encoding="utf-8")
            print(f"[Honcho] âœ… User Profile updated")
        except Exception as e:
            print(f"[Honcho] âš ï¸ Failed to update User Profile: {e}")

    def _generate_initial_profile(self) -> str:
        """Generate initial User Profile.md structure."""
        return """# User Profile

> *Living representation of the user â€” updated by Honcho Dialectic Engine*

---

## Identity

*To be populated by dialectic analysis...*

---

## Preferences

*To be populated by dialectic analysis...*

---

## Projects

*To be populated by dialectic analysis...*

---

## Relationships

*To be populated by dialectic analysis...*

---

## Communication Style

*To be populated by dialectic analysis...*

---

## Goals

*To be populated by dialectic analysis...*

---

## Dialectic Conclusions

*Links to detailed conclusions in [[30_Honcho/Conclusions]]*

"""

    def _build_dialectic_prompt(self, turns: List[Dict[str, str]], memory: Dict, existing_profile: str) -> str:
        """Build the dialectic reasoning prompt for Gemini."""
        turns_text = "\n".join([f"[{t['agent']}] User: {t['user']}\n[{t['agent']}] Agent: {t['agent_text']}" for t in turns])

        memory_text = ""
        if memory:
            for cat, entries in memory.items():
                if entries:
                    memory_text += f"\n### {cat.title()}:\n"
                    for key, entry in list(entries.items())[:5]:
                        val = entry.get("value") if isinstance(entry, dict) else entry
                        memory_text += f"  - {key}: {val}\n"

        profile_section = ""
        if existing_profile:
            profile_section = f"\n\n## Existing User Profile (from Vault):\n\n{existing_profile[:2000]}\n"

        return f"""You are Honcho, a dialectic reasoning engine that analyzes conversations to derive deep insights about a user.

## Task
Analyze the following conversation turns and existing memory to derive new insights about the user.

## Recent Conversation Turns:
{turns_text}

## Existing Memory:{memory_text}{profile_section}
## Analysis Questions:
1. What new insights about this user can you derive from this conversation?
2. What preferences, goals, communication patterns, or emotional states are evident?
3. What conclusions go beyond what the user explicitly stated?
4. How should the user profile be updated?

## Output Format:
Respond in JSON format:
```json
{{
  "new_insights": ["insight 1", "insight 2", ...],
  "preferences_observed": ["pref 1", "pref 2", ...],
  "communication_patterns": ["pattern 1", ...],
  "emotional_states": ["state 1", ...],
  "implicit_conclusions": ["conclusion 1", ...],
  "profile_update": "Markdown text for updating the user profile...",
  "summary": "Brief summary of the dialectic analysis..."
}}
```

Be profound. Look for patterns, contradictions, values, and unstated motivations.
"""

    def _run_dialectic(self) -> None:
        """Run the dialectic reasoning using Gemini."""
        with self._lock:
            if not self.turn_buffer:
                return
            turns = list(self.turn_buffer)
            self.turn_buffer.clear()
            self.turn_count = 0

        print(f"[Honcho] ðŸ§  Running dialectic analysis on {len(turns)} turns...")

        try:
            client = self._get_gemini_client()
            if client is None:
                print("[Honcho] âš ï¸ No Gemini client, skipping dialectic")
                return

            memory = self._read_jarvis_memory()
            existing_profile = self._read_user_profile()
            prompt = self._build_dialectic_prompt(turns, memory, existing_profile)

            response = client.models.generate_content(
                model=self.gemini_model,
                contents=prompt
            )

            if not response or not response.text:
                print("[Honcho] âš ï¸ Empty response from Gemini")
                return

            # Parse JSON from response
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            result = json.loads(text)
            date_str = datetime.now().strftime("%Y-%m-%d")

            # Build conclusion text
            conclusion_parts = [
                f"## Dialectic Analysis â€” {date_str}\n",
                f"**Summary:** {result.get('summary', '')}\n",
            ]

            if result.get('new_insights'):
                conclusion_parts.append("\n### New Insights:\n")
                for insight in result['new_insights']:
                    conclusion_parts.append(f"- {insight}\n")

            if result.get('preferences_observed'):
                conclusion_parts.append("\n### Preferences Observed:\n")
                for pref in result['preferences_observed']:
                    conclusion_parts.append(f"- {pref}\n")

            if result.get('communication_patterns'):
                conclusion_parts.append("\n### Communication Patterns:\n")
                for pat in result['communication_patterns']:
                    conclusion_parts.append(f"- {pat}\n")

            if result.get('implicit_conclusions'):
                conclusion_parts.append("\n### Implicit Conclusions:\n")
                for conc in result['implicit_conclusions']:
                    conclusion_parts.append(f"- {conc}\n")

            conclusion_text = "\n".join(conclusion_parts)

            # Write to both locations
            self._write_conclusion_to_sqlite(conclusion_text, date_str)
            self._write_conclusion_to_vault(conclusion_text, date_str)

            # Update user profile
            if result.get('profile_update'):
                self._update_user_profile(result['profile_update'])

            print(f"[Honcho] âœ… Dialectic complete â€” {len(turns)} turns analyzed")

        except json.JSONDecodeError as e:
            print(f"[Honcho] âš ï¸ Failed to parse Gemini JSON: {e}")
        except Exception as e:
            print(f"[Honcho] âš ï¸ Dialectic failed: {e}")
            traceback.print_exc()

    def submit_conversation(self, agent_name: str, user_text: str, agent_text: str) -> None:
        """
        Queue a conversation turn from an agent.
        After cadence is reached, triggers dialectic in background thread.
        """
        if not user_text or not user_text.strip():
            return

        turn = {
            "agent": agent_name,
            "user": user_text.strip(),
            "agent_text": (agent_text or "").strip(),
            "timestamp": datetime.now().isoformat(),
        }

        with self._lock:
            self.turn_buffer.append(turn)
            self.turn_count += 1

        print(f"[Honcho] ðŸ“¥ Turn queued from {agent_name} (buffer={len(self.turn_buffer)}, count={self.turn_count})")

        if self.turn_count >= self.cadence:
            self.maybe_run_dialectic()

    def maybe_run_dialectic(self) -> None:
        """
        Check if cadence reached and run dialectic in background thread if so.
        """
        with self._lock:
            if self.turn_count < self.cadence:
                return
            turns_snapshot = list(self.turn_buffer)
            self.turn_buffer.clear()
            self.turn_count = 0

        print(f"[Honcho] ðŸš€ Launching dialectic thread ({len(turns_snapshot)} turns)...")
        threading.Thread(target=self._run_dialectic, daemon=True).start()

    def get_user_profile(self) -> str:
        """
        Return combined user profile from SQLite facts + vault conclusions.
        """
        profile = self._read_user_profile()
        memory = self._read_jarvis_memory()

        sections = []
        if profile:
            sections.append("# User Profile (from Vault)\n")
            sections.append(profile)

        if memory.get("conclusions"):
            sections.append("\n\n# Recent Conclusions (from SQLite)\n")
            for key, entry in list(memory["conclusions"].items())[:5]:
                val = entry.get("value") if isinstance(entry, dict) else entry
                updated = entry.get("updated") if isinstance(entry, dict) else ""
                sections.append(f"## {key}\n*Updated: {updated}*\n\n{val}\n")

        return "\n".join(sections)

    def inject_context(self, max_tokens: int = 1000) -> str:
        """
        Return formatted context for injection into system prompts.
        """
        profile = self.get_user_profile()
        if not profile:
            return ""

        lines = profile.split("\n")
        if len(lines) <= max_tokens // 4:
            return f"[USER PROFILE â€” derived from dialectic analysis]\n{profile}\n"

        truncated = "\n".join(lines[:max_tokens // 4])
        return f"[USER PROFILE â€” truncated]\n{truncated}\n... (use get_user_profile for full profile)\n"


# Singleton instance
_dialectic_engine: Optional[DialecticEngine] = None
_engine_lock = threading.Lock()


def get_dialectic_engine() -> DialecticEngine:
    """Get or create the singleton dialectic engine."""
    global _dialectic_engine
    if _dialectic_engine is None:
        with _engine_lock:
            if _dialectic_engine is None:
                _dialectic_engine = DialecticEngine()
    return _dialectic_engine


def submit_conversation(agent_name: str, user_text: str, agent_text: str) -> None:
    """Convenience function to submit a conversation turn."""
    return get_dialectic_engine().submit_conversation(agent_name, user_text, agent_text)


def maybe_run_dialectic() -> None:
    """Convenience function to trigger dialectic if cadence reached."""
    return get_dialectic_engine().maybe_run_dialectic()


def get_user_profile() -> str:
    """Convenience function to get combined user profile."""
    return get_dialectic_engine().get_user_profile()


def inject_context(max_tokens: int = 1000) -> str:
    """Convenience function to get formatted context for system prompts."""
    return get_dialectic_engine().inject_context(max_tokens)


if __name__ == "__main__":
    print("=== Honcho Dialectic Engine Test ===")
    engine = DialecticEngine(cadence=2)

    engine.submit_conversation("jarvis", "I really love working with Python and AI projects", "That's great! Python is very versatile for AI.")
    engine.submit_conversation("jarvis", "My goal is to build a local AI assistant", "Ambitious! Local AI is the future.")

    time.sleep(3)
    print("\n=== User Profile ===")
    print(engine.get_user_profile()[:500])
