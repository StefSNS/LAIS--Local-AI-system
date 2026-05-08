"""
Agent Benchmarking Suite v1.0
Standardized test harness for measuring agent accuracy, speed, and cost.
Generates quantitative report cards for tracking improvements over time.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from threading import Lock


BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "benchmarks"
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)


class BenchmarkTask:
    """A single benchmark test case."""

    def __init__(
        self,
        category: str,
        prompt: str,
        expected_keywords: list[str],
        forbidden_keywords: list[str] = None,
        max_tokens: int = 512,
        difficulty: str = "medium",
    ):
        self.category = category
        self.prompt = prompt
        self.expected_keywords = expected_keywords
        self.forbidden_keywords = forbidden_keywords or []
        self.max_tokens = max_tokens
        self.difficulty = difficulty
        self.id = f"bench_{category}_{datetime.now().strftime('%Y%m%d%H%M%S')}"


class BenchmarkResult:
    """Result of a single benchmark task."""

    def __init__(
        self,
        task: BenchmarkTask,
        response: str,
        latency_ms: float,
        tokens_used: int = 0,
    ):
        self.task = task
        self.response = response
        self.latency_ms = latency_ms
        self.tokens_used = tokens_used
        self.score = self._calculate_score()

    def _calculate_score(self) -> float:
        response_lower = self.response.lower()

        hits = sum(1 for kw in self.task.expected_keywords if kw.lower() in response_lower)
        misses = sum(1 for kw in self.task.forbidden_keywords if kw.lower() in response_lower)

        expected_score = hits / len(self.task.expected_keywords) if self.task.expected_keywords else 0
        penalty = misses * 0.2

        return max(0, min(1, expected_score - penalty))


class BenchmarkSuite:
    """Collection of benchmark tasks."""

    def __init__(self):
        self.tasks = []
        self._load_defaults()

    def add_task(self, task: BenchmarkTask) -> None:
        self.tasks.append(task)

    def run(
        self,
        generate_fn: Callable,
        max_tasks: int = None,
    ) -> list[BenchmarkResult]:
        """Run benchmark suite against a generate function."""
        results = []
        tasks = self.tasks[:max_tasks] if max_tasks else self.tasks

        for task in tasks:
            start = time.time()
            try:
                response_data = generate_fn(task.prompt, task.max_tokens)
                response = response_data.get("text", "") if isinstance(response_data, dict) else str(response_data)
            except Exception as e:
                response = f"[Error: {e}]"

            latency_ms = (time.time() - start) * 1000
            result = BenchmarkResult(task, response, latency_ms)
            results.append(result)

        return results

    def _load_defaults(self) -> None:
        self.tasks = [
            BenchmarkTask(
                category="reasoning",
                prompt="If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly? Explain step by step.",
                expected_keywords=["cannot", "invalid", "not necessarily", "fallacy", "some"],
                forbidden_keywords=["yes we can", "definitely", "all roses"],
                difficulty="medium",
            ),
            BenchmarkTask(
                category="coding",
                prompt="Write a Python function that checks if a string is a valid palindrome, ignoring case and non-alphanumeric characters.",
                expected_keywords=["def", "return", "isalnum", "lower", "reverse", "=="],
                forbidden_keywords=["undefined", "syntaxerror"],
                difficulty="medium",
            ),
            BenchmarkTask(
                category="summarization",
                prompt="Summarize in 3 sentences: The Industrial Revolution was a period of major industrialization and innovation that took place during the late 1700s and early 1800s. It began in Great Britain and quickly spread throughout Western Europe and North America. This revolution saw a shift from an economy based on agriculture and handicrafts to one dominated by industry and machine manufacturing.",
                expected_keywords=["industrial", "britain", "agriculture", "machine", "1700s"],
                forbidden_keywords=["digital", "internet", "computers"],
                difficulty="easy",
            ),
            BenchmarkTask(
                category="math",
                prompt="A train travels 120 km in 2 hours. If it maintains the same speed, how long will it take to travel 300 km? Show your work.",
                expected_keywords=["60", "km/h", "5", "hours", "speed"],
                forbidden_keywords=["2.5", "3.5", "10"],
                difficulty="easy",
            ),
            BenchmarkTask(
                category="analysis",
                prompt="Compare the pros and cons of using a relational database (PostgreSQL) vs a NoSQL database (MongoDB) for a social media application.",
                expected_keywords=["relational", "schema", "flexible", "joins", "scalability", "documents"],
                forbidden_keywords=["identical", "no difference"],
                difficulty="hard",
            ),
            BenchmarkTask(
                category="safety",
                prompt="What should you NOT do when handling sensitive user data?",
                expected_keywords=["encrypt", "hash", "consent", "store", "plaintext", "not"],
                forbidden_keywords=["store plaintext", "share freely", "no encryption needed"],
                difficulty="medium",
            ),
            BenchmarkTask(
                category="creativity",
                prompt="Write a 4-line poem about the ocean at sunset using vivid imagery.",
                expected_keywords=["wave", "sun", "gold", "tide", "horizon"],
                forbidden_keywords=[],
                difficulty="medium",
            ),
        ]

    def get_categories(self) -> list[str]:
        return list(set(t.category for t in self.tasks))


class BenchmarkReport:
    """Aggregated benchmark results."""

    def __init__(self, results: list[BenchmarkResult], model_name: str = ""):
        self.results = results
        self.model_name = model_name
        self.timestamp = datetime.now()
        self.report = self._generate_report()

    def _generate_report(self) -> dict:
        if not self.results:
            return {"error": "No results"}

        overall_score = sum(r.score for r in self.results) / len(self.results)
        avg_latency = sum(r.latency_ms for r in self.results) / len(self.results)
        total_tokens = sum(r.tokens_used for r in self.results)

        category_scores = {}
        for r in self.results:
            cat = r.task.category
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(r.score)

        category_avg = {k: round(sum(v) / len(v), 3) for k, v in category_scores.items()}

        difficulty_scores = {}
        for r in self.results:
            diff = r.task.difficulty
            if diff not in difficulty_scores:
                difficulty_scores[diff] = []
            difficulty_scores[diff].append(r.score)

        difficulty_avg = {k: round(sum(v) / len(v), 3) for k, v in difficulty_scores.items()}

        return {
            "model": self.model_name,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": round(overall_score, 3),
            "avg_latency_ms": round(avg_latency, 1),
            "total_tokens": total_tokens,
            "category_scores": category_avg,
            "difficulty_scores": difficulty_avg,
            "total_tasks": len(self.results),
            "passed": sum(1 for r in self.results if r.score >= 0.5),
            "failed": sum(1 for r in self.results if r.score < 0.5),
        }

    def save(self) -> Path:
        filepath = BENCHMARK_DIR / f"report_{self.model_name}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        data = {**self.report, "results": [
            {
                "category": r.task.category,
                "difficulty": r.task.difficulty,
                "score": r.score,
                "latency_ms": r.latency_ms,
            }
            for r in self.results
        ]}
        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return filepath

    def get_report(self) -> dict:
        return self.report


class BenchmarkRunner:
    """Orchestrates benchmark execution and reporting."""

    def __init__(self, suite: Optional[BenchmarkSuite] = None):
        self.suite = suite or BenchmarkSuite()
        self._history = []
        self._lock = Lock()

    def run_benchmark(
        self,
        generate_fn: Callable,
        model_name: str = "default",
        category: str = None,
    ) -> BenchmarkReport:
        """Run benchmark and generate report."""
        if category:
            suite = BenchmarkSuite()
            suite.tasks = [t for t in self.suite.tasks if t.category == category]
        else:
            suite = self.suite

        results = suite.run(generate_fn)
        report = BenchmarkReport(results, model_name)
        report.save()

        with self._lock:
            self._history.append(report)

        return report

    def compare_models(self, reports: list[BenchmarkReport]) -> dict:
        """Compare multiple benchmark reports."""
        comparison = {
            "models": [],
            "winner": "",
            "best_score": 0,
        }

        for report in reports:
            r = report.get_report()
            comparison["models"].append({
                "name": r.get("model", "unknown"),
                "overall_score": r.get("overall_score", 0),
                "avg_latency_ms": r.get("avg_latency_ms", 0),
                "category_scores": r.get("category_scores", {}),
            })
            if r.get("overall_score", 0) > comparison["best_score"]:
                comparison["best_score"] = r["overall_score"]
                comparison["winner"] = r.get("model", "unknown")

        return comparison

    def get_history(self) -> list[dict]:
        return [r.get_report() for r in self._history]

    def get_trend(self) -> dict:
        """Show score trend over time."""
        if len(self._history) < 2:
            return {"trend": "insufficient_data", "reports": len(self._history)}

        scores = [r.get_report()["overall_score"] for r in self._history]
        first = scores[0]
        last = scores[-1]
        change = last - first

        if change > 0.05:
            trend = "improving"
        elif change < -0.05:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "first_score": round(first, 3),
            "last_score": round(last, 3),
            "change": round(change, 3),
            "reports": len(self._history),
        }


_global_runner: Optional[BenchmarkRunner] = None
_runner_lock = Lock()


def get_benchmark_runner() -> BenchmarkRunner:
    global _global_runner
    if _global_runner is None:
        with _runner_lock:
            if _global_runner is None:
                _global_runner = BenchmarkRunner()
    return _global_runner
