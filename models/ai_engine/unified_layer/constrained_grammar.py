"""
Constrained Grammar / JSON Schema Enforcement v1.0
Validates and repairs LLM outputs against JSON schemas.
Based on LocalAI constrained generation pattern.
Prevents malformed tool calls and ensures structured output compliance.
"""

import json
import re
from typing import Any, Optional


class SchemaValidator:
    """Validates JSON against a simple schema definition."""

    @staticmethod
    def validate(obj: Any, schema: dict) -> tuple[bool, list[str]]:
        errors = []
        SchemaValidator._validate(obj, schema, "$", errors)
        return len(errors) == 0, errors

    @staticmethod
    def _validate(obj: Any, schema: dict, path: str, errors: list[str]) -> None:
        schema_type = schema.get("type")

        if schema_type == "object":
            if not isinstance(obj, dict):
                errors.append(f"{path}: expected object, got {type(obj).__name__}")
                return
            required = schema.get("required", [])
            for field in required:
                if field not in obj:
                    errors.append(f"{path}: missing required field '{field}'")
            properties = schema.get("properties", {})
            for key, prop_schema in properties.items():
                if key in obj:
                    SchemaValidator._validate(obj[key], prop_schema, f"{path}.{key}", errors)

        elif schema_type == "array":
            if not isinstance(obj, list):
                errors.append(f"{path}: expected array, got {type(obj).__name__}")
                return
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(obj):
                    SchemaValidator._validate(item, items_schema, f"{path}[{i}]", errors)

        elif schema_type == "string":
            if not isinstance(obj, str):
                errors.append(f"{path}: expected string, got {type(obj).__name__}")

        elif schema_type == "number" or schema_type == "integer":
            if not isinstance(obj, (int, float)):
                errors.append(f"{path}: expected {schema_type}, got {type(obj).__name__}")
            elif schema_type == "integer" and not isinstance(obj, int):
                errors.append(f"{path}: expected integer, got float")

        elif schema_type == "boolean":
            if not isinstance(obj, bool):
                errors.append(f"{path}: expected boolean, got {type(obj).__name__}")


class JSONRepair:
    """Repairs common JSON output issues from LLMs."""

    @staticmethod
    def repair(text: str) -> tuple[str, bool]:
        """
        Attempt to repair malformed JSON.
        Returns (repaired_json, success).
        """
        original = text.strip()

        # Try parsing as-is first
        try:
            json.loads(original)
            return original, True
        except json.JSONDecodeError:
            pass

        # Strip markdown code fences
        cleaned = re.sub(r'^```(?:json)?\s*', '', original, flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE).strip()

        try:
            json.loads(cleaned)
            return cleaned, True
        except json.JSONDecodeError:
            pass

        # Extract first JSON object/array
        extracted = JSONRepair._extract_json(cleaned)
        if extracted:
            try:
                json.loads(extracted)
                return extracted, True
            except json.JSONDecodeError:
                pass

        # Fix common issues
        fixed = JSONRepair._fix_trailing_commas(cleaned)
        try:
            json.loads(fixed)
            return fixed, True
        except json.JSONDecodeError:
            pass

        fixed = JSONRepair._fix_unquoted_keys(fixed)
        try:
            json.loads(fixed)
            return fixed, True
        except json.JSONDecodeError:
            pass

        # Last resort: wrap in object
        if cleaned and not cleaned.startswith("{"):
            wrapped = f'{{"output": "{cleaned.replace(chr(10), "\\n").replace(chr(92), chr(92)+chr(92))}"}}'
            try:
                json.loads(wrapped)
                return wrapped, True
            except json.JSONDecodeError:
                pass

        return original, False

    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """Extract first balanced JSON object or array."""
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            if start == -1:
                continue
            depth = 0
            in_string = False
            escape = False
            for i in range(start, len(text)):
                ch = text[i]
                if escape:
                    escape = False
                    continue
                if ch == '\\':
                    escape = True
                    continue
                if ch == '"' and not escape:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == start_char:
                    depth += 1
                elif ch == end_char:
                    depth -= 1
                    if depth == 0:
                        return text[start:i+1]
        return None

    @staticmethod
    def _fix_trailing_commas(text: str) -> str:
        return re.sub(r',\s*([}\]])', r'\1', text)

    @staticmethod
    def _fix_unquoted_keys(text: str) -> str:
        return re.sub(r'(\b\w+)\b\s*:', r'"\1":', text)


class ConstrainedGrammar:
    """
    Enforces JSON schema constraints on LLM outputs.
    Validates and repairs automatically.
    """

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.validator = SchemaValidator()
        self.repair = JSONRepair()

    def enforce(self, text: str, schema: Optional[dict] = None) -> tuple[dict, list[str]]:
        """
        Parse, validate, and optionally repair JSON output.

        Args:
            text: Raw LLM output
            schema: Optional JSON schema to validate against

        Returns:
            (parsed_dict, errors)
        """
        errors = []

        # Parse
        repaired_text, repair_ok = self.repair.repair(text)
        if not repair_ok:
            errors.append(f"Failed to parse JSON: {text[:100]}")
            return {"_raw": text}, errors

        # Load
        try:
            parsed = json.loads(repaired_text)
        except json.JSONDecodeError as e:
            errors.append(f"JSON parse error: {e}")
            return {"_raw": text}, errors

        # Validate
        if schema:
            valid, schema_errors = self.validator.validate(parsed, schema)
            if not valid:
                errors.extend(schema_errors)
                if self.strict:
                    return {"_raw": text, "_schema_errors": schema_errors}, errors

        return parsed, errors

    def enforce_tool_call(self, text: str) -> tuple[dict, list[str]]:
        """Enforce tool call format."""
        tool_schema = {
            "type": "object",
            "required": ["tool_name", "arguments"],
            "properties": {
                "tool_name": {"type": "string"},
                "arguments": {"type": "object"},
            },
        }
        return self.enforce(text, tool_schema)

    def enforce_rag_query(self, text: str) -> tuple[dict, list[str]]:
        """Enforce RAG query format."""
        query_schema = {
            "type": "object",
            "required": ["query", "filters"],
            "properties": {
                "query": {"type": "string"},
                "filters": {"type": "object"},
                "top_k": {"type": "integer"},
            },
        }
        return self.enforce(text, query_schema)


_global_grammar: Optional[ConstrainedGrammar] = None


def get_constrained_grammar(strict: bool = False) -> ConstrainedGrammar:
    global _global_grammar
    if _global_grammar is None:
        _global_grammar = ConstrainedGrammar(strict)
    return _global_grammar
