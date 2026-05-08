"""
Goal Cascade - Automated rollup from daily logs to quarterly reviews.
Implements auto-rollup mechanism for goal tracking across time scales.
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


VAULT_PATH = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
MEMORY_DIR = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\memory")
GOAL_CASCADE_FILE = MEMORY_DIR / "goal_cascade.json"
DAILY_LOG_DIR = VAULT_PATH / "50_Memory"
ROLLUP_LEVELS = ["daily", "weekly", "monthly", "quarterly"]
GOAL_STATUSES = ["active", "completed", "paused", "archived"]


def find_daily_logs(date_from=None, date_to=None):
    """Find daily log files in the vault."""
    logs = []
    pattern = re.compile(r"\d{4}-\d{2}-\d{2}(?:\s*.+)?\.md")
    for f in DAILY_LOG_DIR.rglob("*.md"):
        if pattern.match(f.name):
            logs.append(f)
    return sorted(logs)


def extract_goals_from_log(content):
    """Extract goals and tasks from a daily log."""
    goals = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            goals.append({
                "text": re.sub(r"^- \[.\] ", "", line),
                "completed": line.startswith("- [x]"),
            })
    return goals


def extract_insights(content):
    """Extract key insights from a daily log."""
    insights = []
    lines = content.split("\n")
    in_insights = False
    for line in lines:
        if re.match(r"^##+\s+Insights|Learnings|Key Takeaways", line, re.IGNORECASE):
            in_insights = True
            continue
        if in_insights:
            if line.startswith("#"):
                in_insights = False
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                insights.append(line.strip().lstrip("-* ").strip())
    return insights


def extract_metrics(content):
    """Extract key metrics from a daily log."""
    metrics = {}
    lines = content.split("\n")
    for line in lines:
        match = re.match(r"^\*\*(\w[\w\s]+?)\*\*:\s*([\d.]+)", line)
        if match:
            metrics[match.group(1).strip()] = float(match.group(2))
    return metrics


def compute_rollup_stats(logs, level="weekly"):
    """Compute aggregated stats across a set of log entries."""
    total_goals = 0
    completed_goals = 0
    all_insights = []
    all_metrics = defaultdict(list)

    for log in logs:
        goals = extract_goals_from_log(log)
        total_goals += len(goals)
        completed_goals += sum(1 for g in goals if g["completed"])
        all_insights.extend(extract_insights(log))
        metrics = extract_metrics(log)
        for k, v in metrics.items():
            all_metrics[k].append(v)

    avg_metrics = {k: sum(v) / len(v) for k, v in all_metrics.items()}

    return {
        "level": level,
        "date": datetime.now().isoformat(),
        "total_goals": total_goals,
        "completed_goals": completed_goals,
        "completion_rate": round(completed_goals / total_goals, 2) if total_goals > 0 else 0,
        "insights_count": len(all_insights),
        "top_insights": all_insights[:5],
        "avg_metrics": avg_metrics,
    }


def generate_weekly_rollup(week_start=None):
    """Generate a weekly rollup from daily logs."""
    if week_start is None:
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_end = week_start + timedelta(days=7)
    logs = find_daily_logs(week_start, week_end)
    return compute_rollup_stats(logs, level="weekly")


def generate_monthly_summary(month=None, year=None):
    """Generate a monthly summary from weekly rollups."""
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    logs = find_daily_logs(
        datetime(year, month, 1),
        datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1),
    )
    return compute_rollup_stats(logs, level="monthly")


def save_rollup(rollup_data):
    """Save rollup data to cascade file."""
    existing = []
    if GOAL_CASCADE_FILE.exists():
        try:
            existing = json.loads(GOAL_CASCADE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.append(rollup_data)
    GOAL_CASCADE_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return len(existing)


def update_goal_cascade_note(rollup_data):
    """Update the Goal Cascade vault note with latest rollup."""
    note_path = VAULT_PATH / "40_System" / "Project - Goal Cascade.md"
    if not note_path.exists():
        note_path.write_text(
            f"# Goal Cascade\n\nAuto-generated goal tracking dashboard.\n\n", encoding="utf-8"
        )
    existing = note_path.read_text(encoding="utf-8")
    update = f"\n## {rollup_data['level'].title()} Rollup ({rollup_data['date'][:10]})\n"
    update += f"- Total goals: {rollup_data['total_goals']}\n"
    update += f"- Completed: {rollup_data['completed_goals']}\n"
    update += f"- Completion rate: {rollup_data['completion_rate']*100:.0f}%\n"
    note_path.write_text(existing + update, encoding="utf-8")


def run_rollup(level="weekly"):
    """Run a full rollup cycle at the specified level."""
    if level == "daily":
        logs = find_daily_logs(datetime.now(), datetime.now())
        stats = compute_rollup_stats(logs, "daily")
    elif level == "weekly":
        stats = generate_weekly_rollup()
    elif level == "monthly":
        stats = generate_monthly_summary()
    else:
        return {"error": f"Unknown level: {level}"}

    save_rollup(stats)
    update_goal_cascade_note(stats)
    return stats


if __name__ == "__main__":
    result = run_rollup("weekly")
    print(json.dumps(result, indent=2))
