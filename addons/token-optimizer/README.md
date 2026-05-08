# Token Optimization Pack

Cross-agent token governance for LAIS — prompt compression, budget enforcement, shell output caching.

## Install

```powershell
pip install -r addons/token-optimizer/requirements.txt
```

## What You Get

| Component | What It Does |
|-----------|-------------|
| **claw-compactor** | Markdown/code stripping, tiktoken-based estimation, 14-stage in place |
| **tokenpruner** | Code/text dedup with 40-60% compression via COMPOSITE strategy |
| **LLMLingua** | 20x prompt compression using microsoft/llmlingua-2 (model downloaded on first use) |
| **shekel** | Per-agent USD budget enforcement with spend tracking |
| **sqz** | Native shell output compressor (built-in, no install needed) |

## Usage

The `TokenOptimizer` auto-detects installed libs and uses the best available compressor. No config needed.
