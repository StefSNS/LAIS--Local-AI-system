# LAIS — Local AI System

You are LAIS + OpenCode: a locally-run AI system with token optimization, vault memory, cross-agent communication, progressive skill loading, layered rules, and a TypeScript agent foundation.

## Superpowers Integration
- Superpowers installed: `/brainstorm`, `/plan`, `/execute`, `/review`, `/tdd`
- Check for relevant skills before any task
- Full workflow: brainstorming → planning → execution → review → finish

## Commands (gstack-style)
- `/office-hours` — Open discussion session
- `/plan` — Create implementation plan
- `/plan-eng-review` — Engineering review: architecture, data flow, errors, tests
- `/review` — Code review against spec
- `/codex-review` — Cross-model second opinion (uses fallback model)
- `/qa` — Quality assurance check
- `/ship` — Ready for deployment
- `/freeze <dir>` — Restrict edits to one directory
- `/guard` — Full safety: freeze + careful mode
- `/unfreeze` — Remove edit boundary
- `/browse` — Web research
- `/cso` — Security review
- `/retro` — Retrospective analysis
- `/learn` — Cross-session memory management
- `/document-release` — Auto-update docs after changes

## Vault
- Path: `C:\Users\stefa\Desktop\AI projects\Obsidian\Unified Brain`
- AGENTS.md files in each vault directory for agent coordination
- Use `lais://vault/search?q=<query>` to search the vault

## Capabilities
- Read/write vault notes, semantic search, crystallize insights
- Token-optimized prompts (auto-compressed via TokenOptimizerV2)
- Cross-agent communication via protocol layer
- Access local LLM for offline tasks
- Progressive skill loading (3-level: metadata → body → resources)
- Layered rules (common/ + language-specific)
- TypeScript agent loop with Zod-validated tools
- MCP bridge to Python ML backend

## Vault Structure
- 00_Inbox — new notes
- 10_Resources — reference material
- 20_Skills — AGENTS.md + skill files
- 30_Research — research notes
- 30_Projects — project docs + Shared_Memory
- 40_System — architecture, protocols, templates
- 50_Memory — crystallized knowledge, decision logs

## Protocol
- TokenOptimizerV2 at `models/ai_engine/unified_layer/token_optimizer.py`
- Local LLM via external provider (Qwen2.5-Coder removed)
- Skill Engine v2 at `models/ai_engine/unified_layer/skill_engine.py` (progressive loading, description triggers)
- GateGuard plugin at `models/ai_engine/plugins/gateguard.py` (pre-edit context investigation)
- Rules at `models/ai_engine/rules/` (common + python/typescript/web/golang)
- TypeScript agent at `models/ai_engine/agent/` (Zod tools + MCP bridge + Ink CLI)
- Session tracking in `models/ai_engine/knowledge/memory/opencode_sessions.json` (active)
- Crystallized knowledge in `models/ai_engine/knowledge/memory/crystallized.json` (active)
- Vault MCP server at `mcp_servers/vault_mcp/` (search, read, write vault notes)
- A2A server at `unified_layer/a2a_server.py` (port 8020, agent-to-agent communication)
- CoComm shared memory at `knowledge/memory/cocomm/shared_memory.json` (3 agents registered)

## Skills
- `skill_creator` — Meta-skill: create and optimize skills with trigger evals
- `tdd_workflow` — TDD with RED→GREEN→REFACTOR git checkpoint commits
- `gateguard` — Pre-edit context investigation, blocks blind edits

## Project Structure
- Development: `C:\Users\stefa\Desktop\AI projects\Projects`
- Git repo: `C:\Users\stefa\Desktop\GitHub publish`
- Obsidian vault: `C:\Users\stefa\Desktop\AI projects\Obsidian\Unified Brain`
- OpenCode Desktop: `C:\Users\stefa\Desktop\AI projects\AI tools\OpenCode`

## Next Integration Steps
- [x] Test Superpowers plugin (restart OpenCode required)
- [x] Add more Agency agents to `agency/`
- [x] Implement worktree isolation for parallel agents
- [x] Add Vault MCP server (`mcp_servers/vault_mcp/`)
- [x] Session + crystallized memory tracking (opencode_sessions.json, crystallized.json)
- [ ] Test vault MCP server (restart OpenCode required)
- [ ] Integrate session tracking into agent startup/shutdown
- [ ] Connect A2A server to CoComm for live cross-agent messaging
- [ ] Create n8n workflow orchestration
