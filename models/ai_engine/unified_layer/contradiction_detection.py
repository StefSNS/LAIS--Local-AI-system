import sqlite3
import os
import json
from datetime import datetime
import logging

class ContradictionDetector:
    def __init__(self, knowledge_graph_path=None, memory_sqlite_path=None):
        self.kg_path = knowledge_graph_path
        self.mem_path = memory_sqlite_path
        self.kg_conn = None
        self.mem_conn = None
        
        if knowledge_graph_path and os.path.exists(knowledge_graph_path):
            self.kg_conn = sqlite3.connect(knowledge_graph_path)
            self.kg_conn.row_factory = sqlite3.Row
        if memory_sqlite_path and os.path.exists(memory_sqlite_path):
            self.mem_conn = sqlite3.connect(memory_sqlite_path)
            self.mem_conn.row_factory = sqlite3.Row
        
        self.gemini = None
        try:
            from utils.api_keys import GEMINI_API_KEY
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini = genai.GenerativeModel('gemini-pro')
        except (ImportError, ModuleNotFoundError):
            logging.warning("Gemini API not available")
        
        self.log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "contradictions.log")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def check_contradiction(self, subject, predicate, new_value):
        conflicting = []
        if self.kg_conn:
            cursor = self.kg_conn.cursor()
            try:
                cursor.execute("""
                    SELECT * FROM triples WHERE subject = ? AND predicate = ? AND is_valid = 1
                """, (subject, predicate))
                existing = cursor.fetchall()
                for row in existing:
                    if row['value'] != new_value:
                        conflicting.append(dict(row))
            except sqlite3.OperationalError:
                pass
        
        if not conflicting:
            return {"has_contradiction": False, "conflicting": [], "explanation": ""}
        
        explanation = ""
        if self.gemini:
            prompt = f"""Analyze if these values for {subject} -> {predicate} contradict:
            Existing: {[row['value'] for row in conflicting]}
            New: {new_value}
            Explain if they are contradictory, complementary, or different perspectives."""
            try:
                response = self.gemini.generate_content(prompt)
                explanation = response.text
            except Exception as e:
                explanation = f"Gemini error: {str(e)}"
        else:
            explanation = "Gemini unavailable, assuming contradiction"
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} - Contradiction detected: {subject}->{predicate} (new: {new_value}, existing: {[row['value'] for row in conflicting]})\n")
        
        return {
            "has_contradiction": True,
            "conflicting": conflicting,
            "explanation": explanation
        }

    def auto_resolve(self, subject, predicate, new_value, old_value):
        if not self.gemini:
            return "replace"
        prompt = f"""Given {subject} -> {predicate}:
        Old: {old_value}
        New: {new_value}
        Choose resolution: "replace" (old outdated), "coexist" (both valid), "clarify" (old vague, new specific). Return only the strategy."""
        try:
            response = self.gemini.generate_content(prompt)
            strategy = response.text.strip().lower()
            return strategy if strategy in ["replace", "coexist", "clarify"] else "replace"
        except Exception:
            return "replace"

    def scan_for_contradictions(self):
        if not self.kg_conn:
            return []
        cursor = self.kg_conn.cursor()
        try:
            cursor.execute("""
                SELECT subject, predicate, GROUP_CONCAT(value) as values FROM triples
                WHERE is_valid = 1 GROUP BY subject, predicate HAVING COUNT(DISTINCT value) > 1
            """)
            groups = cursor.fetchall()
        except sqlite3.OperationalError:
            return []
        
        contradictions = []
        for group in groups:
            subject = group['subject']
            predicate = group['predicate']
            values = group['values'].split(',')
            suggested = self.auto_resolve(subject, predicate, values[-1], values[0])
            contradictions.append({
                "subject": subject,
                "predicate": predicate,
                "values": values,
                "suggested_resolution": suggested
            })
        return contradictions

    def apply_resolution(self, subject, predicate, old_value, new_value, strategy):
        if not self.kg_conn:
            return False
        cursor = self.kg_conn.cursor()
        try:
            if strategy == "replace":
                cursor.execute("""
                    UPDATE triples SET is_valid = 0 WHERE subject = ? AND predicate = ? AND value = ?
                """, (subject, predicate, old_value))
                cursor.execute("""
                    INSERT INTO triples (subject, predicate, value, timestamp, is_valid)
                    VALUES (?, ?, ?, ?, 1)
                """, (subject, predicate, new_value, datetime.now().isoformat()))
            elif strategy == "clarify":
                cursor.execute("""
                    UPDATE triples SET is_valid = 0 WHERE subject = ? AND predicate = ? AND value = ?
                """, (subject, predicate, old_value))
                cursor.execute("""
                    INSERT INTO triples (subject, predicate, value, timestamp, is_valid)
                    VALUES (?, ?, ?, ?, 1)
                """, (subject, predicate, new_value, datetime.now().isoformat()))
            self.kg_conn.commit()
        except sqlite3.OperationalError:
            return False
        
        log_entry = f"{datetime.now().isoformat()} - Resolved {subject}->{predicate}: {strategy} (old: {old_value}, new: {new_value})\n"
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        return True
