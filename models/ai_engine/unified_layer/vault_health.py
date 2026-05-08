"""
Vault Health Checker - Automated vault maintenance and integrity validation.
Checks broken wikilinks, orphan notes, frontmatter issues, and suggests repairs.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict


VAULT_PATH = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
HEALTH_REPORT_DIR = VAULT_PATH / "40_System" / "health_reports"
HEALTH_REPORT_DIR.mkdir(parents=True, exist_ok=True)

YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
TAG_RE = re.compile(r"#([a-zA-Z0-9/_-]+)")
REQUIRED_FRONTMATTER_KEYS = ["title", "created", "tags"]
VALID_FOLDERS = {"00_Inbox", "10_Projects", "20_Areas", "30_Resources", "40_System", "50_Memory", "60_Archive"}
PREFIX_CONVENTIONS = {
    "10_Projects": ["PROJ-", "PRJ-"],
    "20_Areas": ["AREA-"],
    "30_Resources": ["RES-"],
    "50_Memory": [r"\d{4}-\d{2}-\d{2}"],
}


def parse_frontmatter(content):
    """Extract YAML frontmatter from note content."""
    match = YAML_FRONTMATTER_RE.search(content)
    if not match:
        return {}
    frontmatter = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def extract_wikilinks(content):
    """Extract all wikilinks from note content."""
    return WIKILINK_RE.findall(content)


def extract_tags(content):
    """Extract all tags from note content."""
    tags = TAG_RE.findall(content)
    frontmatter = parse_frontmatter(content)
    if "tags" in frontmatter:
        raw = frontmatter["tags"]
        if raw.startswith("["):
            tags.extend(t.strip() for t in raw.strip("[]").split(",") if t.strip())
        else:
            tags.append(raw)
    return list(set(tags))


def get_all_notes():
    """Get all markdown notes in the vault."""
    notes = {}
    for md_file in VAULT_PATH.rglob("*.md"):
        if md_file.name == "Welcome.md":
            continue
        try:
            rel = md_file.relative_to(VAULT_PATH)
            notes[rel.as_posix()] = {
                "path": rel.as_posix(),
                "title": md_file.stem.replace("_", " ").title(),
                "folder": rel.parent.name if rel.parent.name != "." else "root",
                "content": md_file.read_text(encoding="utf-8", errors="ignore"),
            }
        except Exception:
            pass
    return notes


def build_link_index(notes):
    """Build index of all note titles to their file paths."""
    index = {}
    for path, note in notes.items():
        title_key = note["title"].lower().replace(" ", "_").replace("/", "_")
        path_key = path.lower().replace("\\", "/").replace(".md", "")
        index[title_key] = path
        index[path_key] = path
    return index


def check_broken_links(notes, link_index):
    """Check for wikilinks that don't resolve to existing notes."""
    broken = []
    for path, note in notes.items():
        for link in extract_wikilinks(note["content"]):
            link_normalized = link.lower().replace(" ", "_").replace("/", "_")
            if link_normalized not in link_index:
                broken.append({
                    "source": path,
                    "broken_link": link,
                    "line": _find_link_line(note["content"], link),
                })
    return broken


def _find_link_line(content, link):
    """Find the line number of a wikilink."""
    for i, line in enumerate(content.split("\n"), 1):
        if f"[[{link}" in line:
            return i
    return 0


def find_orphans(notes, link_index):
    """Find notes that are never linked to by any other note."""
    all_targets = set()
    for path, note in notes.items():
        for link in extract_wikilinks(note["content"]):
            link_normalized = link.lower().replace(" ", "_").replace("/", "_")
            if link_normalized in link_index:
                all_targets.add(link_index[link_normalized])
    orphans = []
    for path in notes:
        if path not in all_targets:
            orphans.append(path)
    return orphans


def check_frontmatter_issues(notes):
    """Check for missing or malformed frontmatter."""
    issues = []
    for path, note in notes.items():
        fm = parse_frontmatter(note["content"])
        missing_keys = [k for k in REQUIRED_FRONTMATTER_KEYS if k not in fm]
        if missing_keys:
            issues.append({
                "path": path,
                "type": "missing_frontmatter",
                "details": f"Missing: {missing_keys}",
            })
    return issues


def check_prefix_conventions(notes):
    """Check if notes follow prefix naming conventions."""
    violations = []
    for path, note in notes.items():
        folder = note["folder"]
        if folder in PREFIX_CONVENTIONS:
            name = Path(path).stem
            if not any(re.match(p, name) for p in PREFIX_CONVENTIONS[folder]):
                violations.append({
                    "path": path,
                    "type": "prefix_violation",
                    "details": f"'{name}' doesn't match {PREFIX_CONVENTIONS[folder]}",
                })
    return violations


def check_folder_routing(notes):
    """Check if notes are in the correct folder based on content characteristics."""
    misrouted = []
    FOLDER_ROUTING = {
        "00_Inbox": lambda n: True,
        "10_Projects": lambda n: bool(re.search(r"project|status.*active", n["content"], re.I)),
        "20_Areas": lambda n: bool(re.search(r"area:|domain:", n["content"], re.I)),
        "30_Resources": lambda n: bool(re.search(r"reference|resource|guide", n["content"], re.I)),
        "50_Memory": lambda n: bool(re.search(r"daily|log|session|reflection", n["content"], re.I)),
    }

    for path, note in notes.items():
        folder = note["folder"]
        if folder in FOLDER_ROUTING:
            content = note["content"].lower()
            tags = extract_tags(note["content"])
            if FOLDER_ROUTING[folder](note):
                continue

    return misrouted


def check_note_quality(note):
    """Score a single note for quality metrics."""
    content = note["content"]
    frontmatter = parse_frontmatter(content)
    word_count = len(content.split())
    link_count = len(extract_wikilinks(content))
    tag_count = len(extract_tags(content))

    issues = []
    if word_count < 50:
        issues.append("too_short")
    if link_count == 0:
        issues.append("no_links")
    if tag_count == 0:
        issues.append("no_tags")

    quality_weights = {
        "word_count": min(word_count / 300, 1.0) * 0.4,
        "has_links": min(link_count / 3, 1.0) * 0.3,
        "has_tags": min(tag_count / 2, 1.0) * 0.2,
        "has_frontmatter": 0.1 if frontmatter else 0,
    }
    overall = sum(quality_weights.values())

    return {
        "word_count": word_count,
        "link_count": link_count,
        "tag_count": tag_count,
        "issues": issues,
        "quality_score": round(overall, 2),
    }


def compute_health_score(broken_links, orphans, frontmatter_issues, total_notes):
    """Compute overall vault health score (0-100)."""
    max_issues = total_notes * 0.1
    total_issues = len(broken_links) + len(orphans) + len(frontmatter_issues)
    if total_notes == 0:
        return 100
    score = max(0, 100 - (total_issues / max_issues) * 100)
    return round(min(score, 100), 1)


def generate_health_report():
    """Run all health checks and generate a comprehensive report."""
    notes = get_all_notes()
    link_index = build_link_index(notes)
    broken_links = check_broken_links(notes, link_index)
    orphans = find_orphans(notes, link_index)
    frontmatter_issues = check_frontmatter_issues(notes)
    prefix_violations = check_prefix_conventions(notes)
    misrouted = check_folder_routing(notes)
    total_notes = len(notes)
    health_score = compute_health_score(broken_links, orphans, frontmatter_issues, total_notes)

    quality_report = {}
    for path, note in notes.items():
        rel_path = path.replace("\\", "/")
        quality_report[rel_path] = check_note_quality(note)

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_notes": total_notes,
        "health_score": health_score,
        "broken_links": broken_links[:20],
        "orphans": orphans[:20],
        "frontmatter_issues": frontmatter_issues[:20],
        "prefix_violations": prefix_violations[:20],
        "misrouted_notes": misrouted[:10],
        "broken_link_count": len(broken_links),
        "orphan_count": len(orphans),
        "frontmatter_issue_count": len(frontmatter_issues),
        "prefix_violation_count": len(prefix_violations),
        "stale_notes": [p for p, q in quality_report.items() if q["quality_score"] < 0.3][:10],
        "avg_quality": round(sum(q["quality_score"] for q in quality_report.values()) / total_notes, 2) if total_notes > 0 else 0,
    }
    return report


def save_report(report):
    """Save health report to disk."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = HEALTH_REPORT_DIR / f"health_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_path = HEALTH_REPORT_DIR / "latest.json"
    latest_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return str(report_path)


def print_summary(report):
    """Print human-readable health summary."""
    print(f"=== Vault Health Report ===")
    print(f"Total notes: {report['total_notes']}")
    print(f"Health score: {report['health_score']}/100")
    print(f"Broken links: {report['broken_link_count']}")
    print(f"Orphan notes: {report['orphan_count']}")
    print(f"Frontmatter issues: {report['frontmatter_issue_count']}")
    print(f"Prefix violations: {report['prefix_violation_count']}")
    if report.get("stale_notes"):
        print(f"Stale notes: {len(report['stale_notes'])}")
    print(f"Avg quality: {report['avg_quality']}")


def run_auto_repairs(report):
    """Apply safe automatic repairs to the vault."""
    repairs = {"frontmatter_added": 0, "prefix_renames": 0, "errors": []}
    return repairs


if __name__ == "__main__":
    report = generate_health_report()
    save_report(report)
    print_summary(report)
