"""
Template Engine v1.0
Templater-like template system for auto-generating Markdown notes.
Supports: variables, date functions, file functions, user scripts.
Based on Templater and Obsidian patterns.
"""

import re
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Any


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "templates"
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)


class TemplateFunctions:
    """Built-in template functions (like Templater's tp modules)."""

    @staticmethod
    def date_now(format: str = "%Y-%m-%d", offset_days: int = 0) -> str:
        target = datetime.now() + timedelta(days=offset_days)
        return target.strftime(format)

    @staticmethod
    def date_yesterday(format: str = "%Y-%m-%d") -> str:
        return (datetime.now() - timedelta(days=1)).strftime(format)

    @staticmethod
    def date_tomorrow(format: str = "%Y-%m-%d") -> str:
        return (datetime.now() + timedelta(days=1)).strftime(format)

    @staticmethod
    def date_weekday(offset: int = 0) -> str:
        return (datetime.now() + timedelta(days=offset)).strftime("%A")

    @staticmethod
    def file_title(title: str = "") -> str:
        return title

    @staticmethod
    def file_creation_date(format: str = "%Y-%m-%d %H:%M") -> str:
        return datetime.now().strftime(format)

    @staticmethod
    def file_last_modified(format: str = "%Y-%m-%d %H:%M") -> str:
        return datetime.now().strftime(format)

    @staticmethod
    def file_prompt(message: str = "Enter value:") -> str:
        try:
            return input(message)
        except Exception:
            return ""

    @staticmethod
    def file_cursor() -> str:
        return "<% cursor %>"

    @staticmethod
    def sys_eval(expression: str) -> str:
        try:
            return str(eval(expression))
        except Exception:
            return ""

    @staticmethod
    def sys_exec(command: str) -> str:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def web_daily_quote() -> str:
        quotes = [
            "Do the best you can until you know better. Then when you know better, do better. — Maya Angelou",
            "The only way to do great work is to love what you do. — Steve Jobs",
            "Stay hungry, stay foolish. — Stewart Brand",
            "Simplicity is the ultimate sophistication. — Leonardo da Vinci",
            "The future belongs to those who believe in the beauty of their dreams. — Eleanor Roosevelt",
        ]
        idx = int(datetime.now().strftime("%j")) % len(quotes)
        return quotes[idx]

    @staticmethod
    def random_uuid() -> str:
        return str(uuid.uuid4())


class TemplateEngine:
    """
    Templater-like template engine.
    Syntax: <% function() %>, {{ variable }}, {{date:YYYY-MM-DD}}
    """

    def __init__(self):
        self.functions = TemplateFunctions()
        self._user_functions: dict[str, Callable] = {}
        self._variables: dict[str, Any] = {}

    def set_variable(self, name: str, value: Any) -> None:
        self._variables[name] = value

    def set_variables(self, **kwargs) -> None:
        self._variables.update(kwargs)

    def register_function(self, name: str, fn: Callable) -> None:
        self._user_functions[name] = fn

    def render(self, template: str, extra_vars: dict = None) -> str:
        result = template
        result = self._process_variables(result, extra_vars)
        result = self._process_date_tags(result)
        result = self._process_functions(result)
        result = self._process_javascript(result)
        return result

    def render_file(self, template_name: str, extra_vars: dict = None) -> str:
        template_path = TEMPLATE_DIR / template_name
        if not template_path.exists():
            return f"[Template not found: {template_name}]"
        content = template_path.read_text(encoding="utf-8")
        return self.render(content, extra_vars)

    def create_template(self, name: str, content: str) -> str:
        template_path = TEMPLATE_DIR / name
        template_path.write_text(content, encoding="utf-8")
        return str(template_path)

    def list_templates(self) -> list[str]:
        return [f.name for f in TEMPLATE_DIR.glob("*.md")] + [f.name for f in TEMPLATE_DIR.glob("*.txt")]

    def _process_variables(self, text: str, extra_vars: dict = None) -> str:
        all_vars = {**self._variables, **(extra_vars or {})}
        pattern = r'\{\{(\w+)\}\}'

        def replace_var(match):
            var_name = match.group(1)
            return str(all_vars.get(var_name, f"{{{{{var_name}}}}}"))

        return re.sub(pattern, replace_var, text)

    def _process_date_tags(self, text: str) -> str:
        pattern = r'\{\{date:([^}]+)\}\}'

        def replace_date(match):
            fmt = match.group(1).strip()
            try:
                return datetime.now().strftime(fmt)
            except Exception:
                return match.group(0)

        return re.sub(pattern, replace_date, text)

    def _process_functions(self, text: str) -> str:
        pattern = r'<%\s*([\w.]+)\(([^)]*)\)\s*%>'

        def replace_fn(match):
            fn_name = match.group(1)
            args_str = match.group(2).strip()

            if "." in fn_name:
                module, func = fn_name.split(".", 1)
                target = self._get_module(module)
                if target and hasattr(target, func):
                    fn = getattr(target, func)
                    args = self._parse_args(args_str)
                    try:
                        return str(fn(*args))
                    except Exception as e:
                        return f"[Error: {e}]"

            if fn_name in self._user_functions:
                args = self._parse_args(args_str)
                try:
                    return str(self._user_functions[fn_name](*args))
                except Exception as e:
                    return f"[Error: {e}]"

            return match.group(0)

        return re.sub(pattern, replace_fn, text)

    def _process_javascript(self, text: str) -> str:
        pattern = r'<%\s*js\s+(.*?)\s*%>'

        def replace_js(match):
            code = match.group(1)
            if "date" in code.lower():
                return datetime.now().strftime("%Y-%m-%d")
            return ""

        return re.sub(pattern, replace_js, text)

    def _get_module(self, module: str):
        modules = {
            "date": self.functions,
            "file": self.functions,
            "sys": self.functions,
            "web": self.functions,
            "tp": self.functions,
        }
        return modules.get(module)

    def _parse_args(self, args_str: str) -> list:
        if not args_str:
            return []
        args = []
        current = ""
        in_string = False
        for ch in args_str:
            if ch == '"' or ch == "'":
                in_string = not in_string
                current += ch
            elif ch == ',' and not in_string:
                args.append(current.strip().strip('"').strip("'"))
                current = ""
            else:
                current += ch
        if current.strip():
            args.append(current.strip().strip('"').strip("'"))

        parsed = []
        for a in args:
            try:
                parsed.append(int(a))
            except ValueError:
                try:
                    parsed.append(float(a))
                except ValueError:
                    parsed.append(a)
        return parsed


_global_template: Optional[TemplateEngine] = None


def get_template_engine() -> TemplateEngine:
    global _global_template
    if _global_template is None:
        _global_template = TemplateEngine()
    return _global_template
