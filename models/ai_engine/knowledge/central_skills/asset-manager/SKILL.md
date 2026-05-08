---
name: asset-manager
description: Manage files, configs, and media across local, cloud, and all UI modes
---

# Cross-Platform Asset Manager

## Overview
Manages files, configs, and media across local, cloud, and all UI modes. Supports voice-driven file search, GUI drag-and-drop, and CLI batch operations.

## Usage
```
assets: search <query> | sync | fetch <url> | organize
```

## Capabilities
- Voice-driven file search with natural language queries
- GUI drag-and-drop support for Omnis interface
- CLI batch file operations via OpenCode tools
- Cloud sync with multiple providers
- Web asset fetching with local caching

## Commands
| Command | Action |
|---------|--------|
| `assets: search <q>` | Search local files with natural language |
| `assets: sync` | Sync to cloud provider |
| `assets: fetch <url>` | Download and cache web asset |
| `assets: organize` | Auto-organize project files |
| `assets: list <filter>` | List assets with filtering |

## Implementation
Leverages:
- OpenCode glob/write/bash tools
- Jarvis web_search/browser_control for cloud assets
- Omnis plugin asset registry

## Cloud Providers
- Local filesystem (primary)
- Google Drive (via API)
- Dropbox (via API)
- OneDrive (via API)

## Cache Structure
```
.knowledge/cache/
  assets/
    images/
    documents/
    code/
    temp/
```
