"""
AI Landscape Monitor - Automated scanner for new models, frameworks, and tools.
Checks HuggingFace, GitHub, and llama.cpp releases for anything that could
improve the 3-agent system within the 3GB RAM constraint.

No external dependencies - uses only Python stdlib.
"""

import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta

WATCH_LOG_FILE = Path(
    Path(__file__).resolve().parent.parent / "knowledge" / "memory" / "ai_watch_log.json"
)
WATCH_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

CURRENT_BEST = {
    "quality": "SmolLM3-3B Q4_K_M (1.78GB)",
    "speed": "Qwen3-1.7B Q4_K_M (1.03GB)",
    "ram_limit_gb": 3,
}

SOURCES = {
    "huggingface_trending": {
        "url": "https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=20&filter=gguf",
        "type": "json",
    },
    "llama_cpp_releases": {
        "url": "https://api.github.com/repos/ggerganov/llama.cpp/releases?per_page=5",
        "type": "json",
    },
    "nous_research_models": {
        "url": "https://huggingface.co/api/models?author=NousResearch&sort=lastModified&direction=-1&limit=10",
        "type": "json",
    },
    "google_gemma_models": {
        "url": "https://huggingface.co/api/models?author=google&sort=lastModified&direction=-1&limit=10&search=gemma",
        "type": "json",
    },
    "qwen_models": {
        "url": "https://huggingface.co/api/models?author=Qwen&sort=lastModified&direction=-1&limit=10",
        "type": "json",
    },
    "mistral_models": {
        "url": "https://huggingface.co/api/models?author=mistralai&sort=lastModified&direction=-1&limit=10",
        "type": "json",
    },
}


def fetch_json(url: str, timeout: int = 30) -> tuple[bool, any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return False, str(e)


def estimate_model_size(params: str, quant: str) -> float:
    """Rough estimate of GGUF file size in GB based on params and quantization."""
    param_match = re.search(r"(\d+\.?\d*)\s*[Bb]", params)
    if not param_match:
        return 999
    params_b = float(param_match.group(1))
    quant_ratios = {
        "Q2_K": 0.4, "Q3_K_S": 0.5, "Q3_K_M": 0.55, "Q3_K_L": 0.6,
        "Q4_0": 0.55, "Q4_K_S": 0.6, "Q4_K_M": 0.65,
        "Q5_0": 0.7, "Q5_K_S": 0.75, "Q5_K_M": 0.8,
        "Q6_K": 0.85, "Q8_0": 1.0, "IQ1_S": 0.2, "IQ1_M": 0.25,
        "IQ2_XXS": 0.3, "IQ2_XS": 0.35, "IQ2_S": 0.4, "IQ2_M": 0.45,
        "IQ3_XXS": 0.5, "IQ3_XS": 0.55, "IQ3_S": 0.6, "IQ3_M": 0.65,
        "F16": 2.0, "F32": 4.0,
    }
    ratio = quant_ratios.get(quant, 0.65)
    return params_b * ratio


def fits_ram(estimate_gb: float) -> bool:
    return estimate_gb <= CURRENT_BEST["ram_limit_gb"]


def scan_huggingface_trending() -> list[dict]:
    findings = []
    success, data = fetch_json(SOURCES["huggingface_trending"]["url"])
    if not success:
        return [{"source": "huggingface_trending", "status": "error", "detail": data}]

    for model in data:
        model_id = model.get("id", "")
        tags = [t.lower() for t in model.get("tags", [])]
        if "gguf" not in tags:
            continue

        # Check for small model indicators in name/tags
        small_signals = ["1b", "1.5b", "2b", "3b", "smol", "tiny", "nano", "micro", "edge"]
        name_lower = model_id.lower()
        if any(s in name_lower for s in small_signals):
            findings.append({
                "source": "huggingface_trending",
                "model_id": model_id,
                "downloads": model.get("downloads", 0),
                "likes": model.get("likes", 0),
                "modified": model.get("lastModified"),
                "tags": [t for t in tags if t in small_signals],
                "action": "INVESTIGATE - trending small model",
            })

    return findings


def scan_llama_cpp_releases() -> list[dict]:
    findings = []
    success, data = fetch_json(SOURCES["llama_cpp_releases"]["url"])
    if not success:
        return [{"source": "llama_cpp", "status": "error", "detail": data}]

    for release in data:
        name = release.get("name", "")
        body = release.get("body", "")
        new_features = []

        # Look for new quantization methods
        quant_patterns = re.findall(r"IQ[0-9_]+|Q[0-9]_[A-Z]", body)
        if quant_patterns:
            new_features.append(f"New quantization methods: {', '.join(set(quant_patterns))}")

        # Look for new architecture support
        arch_patterns = re.findall(r"(?:support|added|new)\s+(?:\w+\s+)?(?:architecture|model)\s+\w+", body, re.IGNORECASE)
        if arch_patterns:
            new_features.extend(arch_patterns)

        if new_features:
            findings.append({
                "source": "llama_cpp",
                "release": name,
                "date": release.get("published_at", "")[:10],
                "features": new_features,
                "action": "REVIEW - may improve inference or enable new models",
            })

    return findings


def scan_author_models(url: str, source_name: str, known_skip: list[str] = None) -> list[dict]:
    findings = []
    success, data = fetch_json(url)
    if not success:
        return [{"source": source_name, "status": "error", "detail": data}]

    known_skip = known_skip or []

    for model in data:
        model_id = model.get("id", "")
        if any(skip in model_id.lower() for skip in known_skip):
            continue

        tags = [t.lower() for t in model.get("tags", [])]
        name_lower = model_id.lower()

        # Check if it's a small model
        small_signals = ["1b", "1.5b", "2b", "3b", "smol", "tiny", "nano", "micro", "edge"]
        is_small = any(s in name_lower for s in small_signals)

        # Check for GGUF
        has_gguf = "gguf" in tags

        if is_small or has_gguf:
            modified = model.get("lastModified", "")
            try:
                mod_date = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                days_ago = (datetime.now(mod_date.tzinfo) - mod_date).days
            except Exception:
                days_ago = 999

            if days_ago <= 30:
                findings.append({
                    "source": source_name,
                    "model_id": model_id,
                    "downloads": model.get("downloads", 0),
                    "likes": model.get("likes", 0),
                    "modified": modified[:10],
                    "days_ago": days_ago,
                    "has_gguf": has_gguf,
                    "is_small": is_small,
                    "action": "INVESTIGATE" if days_ago <= 7 else "MONITOR",
                })

    return findings


def run_scan() -> dict:
    """Run all scans and return consolidated findings."""
    all_findings = []
    scan_results = {"timestamp": datetime.now().isoformat(), "findings": [], "errors": []}

    print(f"=== AI Landscape Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    # 1. HuggingFace trending GGUF models
    print("[1/6] Scanning HuggingFace trending GGUF models...")
    findings = scan_huggingface_trending()
    all_findings.extend(findings)
    new_items = [f for f in findings if f.get("action") == "INVESTIGATE"]
    print(f"  Found {len(findings)} items, {len(new_items)} need investigation")

    # 2. llama.cpp releases
    print("[2/6] Checking llama.cpp releases...")
    findings = scan_llama_cpp_releases()
    all_findings.extend(findings)
    print(f"  Found {len(findings)} relevant updates")

    # 3. Nous Research (Hermes)
    print("[3/6] Checking Nous Research models...")
    findings = scan_author_models(
        SOURCES["nous_research_models"]["url"],
        "nous_research",
        known_skip=["gemma"],
    )
    all_findings.extend(findings)
    print(f"  Found {len(findings)} recent models")

    # 4. Google Gemma
    print("[4/6] Checking Google Gemma models...")
    findings = scan_author_models(
        SOURCES["google_gemma_models"]["url"],
        "google_gemma",
        known_skip=["26b", "27b"],
    )
    all_findings.extend(findings)
    print(f"  Found {len(findings)} recent models")

    # 5. Qwen
    print("[5/6] Checking Qwen models...")
    findings = scan_author_models(
        SOURCES["qwen_models"]["url"],
        "qwen",
        known_skip=["32b", "72b", "110b", "14b"],
    )
    all_findings.extend(findings)
    print(f"  Found {len(findings)} recent models")

    # 6. Mistral
    print("[6/6] Checking Mistral models...")
    findings = scan_author_models(
        SOURCES["mistral_models"]["url"],
        "mistral",
        known_skip=["7b", "8x7", "12b", "24b"],
    )
    all_findings.extend(findings)
    print(f"  Found {len(findings)} recent models")

    # Consolidate
    investigate = [f for f in all_findings if f.get("action") == "INVESTIGATE"]
    monitor = [f for f in all_findings if f.get("action") == "MONITOR"]
    errors = [f for f in all_findings if f.get("status") == "error"]

    scan_results["findings"] = all_findings
    scan_results["summary"] = {
        "total_scanned": len(all_findings),
        "investigate": len(investigate),
        "monitor": len(monitor),
        "errors": len(errors),
    }

    if investigate:
        print(f"\n*** ACTION REQUIRED - {len(investigate)} items to investigate ***")
        for item in investigate:
            print(f"  - {item.get('model_id', item.get('release', 'unknown'))}: {item.get('action')}")

    if errors:
        print(f"\n*** {len(errors)} sources had errors (may be rate limited) ***")

    # Save log
    log = []
    if WATCH_LOG_FILE.exists():
        try:
            log = json.loads(WATCH_LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            log = []
    log.append(scan_results)
    WATCH_LOG_FILE.write_text(json.dumps(log[-50:], indent=2), encoding="utf-8")

    print(f"\nScan complete. Results saved to {WATCH_LOG_FILE}")
    return scan_results


if __name__ == "__main__":
    run_scan()
