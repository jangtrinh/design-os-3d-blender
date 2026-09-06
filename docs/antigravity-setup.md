# Google Antigravity Setup

How Antigravity (Gemini agentic IDE) discovers this repo's agent config,
alongside Claude Code / Codex — no shared file changed to add this.

## Where Antigravity finds things here

- Skills: `.agents/skills/<name>/SKILL.md` (already exists —
  `blender-agent-core`, `blender-image-to-3d`, `blender-knowledge-workbench`,
  `img2threejs`). Legacy `.agent/skills` also supported but unused here.
- Rules: `.agents/rules/blender-agent-operating-rules.md` (new). Antigravity
  rule files are capped at 12,000 characters each.
- Workflows: `.agents/workflows/*.md` (new) — `build-printable-part`,
  `verify-pass`, `headless-render-check`; invoke via `/build-printable-part`
  etc. **UNVERIFIED:** exact workflow folder path not confirmed on
  antigravity.google (only Rules path was documented there); this follows
  the same `.agents/` pattern as skills/rules. If Antigravity's
  Customizations panel doesn't list them, try `.agent/workflows/` instead.
  Also: Google has announced Workflows deprecate in favor of Agent Skills by
  2026-11-01 — re-check after that date.
- `AGENTS.md` at repo root: not confirmed as auto-read by Antigravity;
  treat as the canonical human/Claude/Codex reference. Antigravity's own
  persistent context is `.agents/rules/*.md`.

## MCP config for blender-mcp

Global: `~/.gemini/config/mcp_config.json`. Workspace-local:
`.agents/mcp_config.json`. Both use the same `mcpServers` object.

**uvx form:**
```json
{"mcpServers":{"blender-mcp":{"command":"uvx","args":["blender-mcp"],
"env":{"BLENDER_HOST":"localhost","BLENDER_PORT":"9876"}}}}
```

**Local-checkout form** (checkout at `/Users/jang/blender-mcp` per
`.project-agent.md`):
```json
{"mcpServers":{"blender-mcp":{"command":"uv",
"args":["--directory","/Users/jang/blender-mcp","run","main.py"],
"env":{"BLENDER_HOST":"localhost","BLENDER_PORT":"9876"}}}}
```

## Connect the addon before using MCP tools

Open the Blender GUI → sidebar `N` → `BlenderMCP` tab → **Connect to
Claude** (same addon, any MCP client). Connection error → open/connect the
addon in the GUI; do not retry blindly.

## One writer only

The Blender GUI is the single writer for interactive/MCP sessions. Never run
`scripts/headless-run.sh` against a `.blend` file the GUI has open, from
Antigravity or any other agent — see the operating rules file, rule 8.
