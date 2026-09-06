# CLAUDE.md — Blender AI Orchestration

Read `.project-agent.md` first (identity, binding rules). The primary operational file is `AGENTS.md` (shared by Claude + Codex), imported verbatim:

@AGENTS.md

## Notes specific to Claude Code
- MCP tools appear as `mcp__blender__*`; if they are not loaded, use `ToolSearch` with `select:mcp__blender__execute_blender_code,mcp__blender__get_viewport_screenshot`.
- A subagent (Agent tool) may only run Blender headless with `--factory-startup`; it may **not** send commands to the open GUI — the single writer for the GUI is the controller session.
- Skill router for every Blender task: `blender-agent-core` (Skill tool) before any domain skill.
