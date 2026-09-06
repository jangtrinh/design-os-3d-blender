# CLAUDE.md — Blender AI Orchestration

Đọc `.project-agent.md` trước (identity, binding rules). File vận hành chính là `AGENTS.md` (dùng chung Claude + Codex), import nguyên văn:

@AGENTS.md

## Ghi chú riêng cho Claude Code
- MCP tools xuất hiện dạng `mcp__blender__*`; nếu chưa nạp, dùng `ToolSearch` với `select:mcp__blender__execute_blender_code,mcp__blender__get_viewport_screenshot`.
- Subagent (Agent tool) chỉ được chạy Blender headless `--factory-startup`; **không** được gửi lệnh tới GUI đang mở — một writer duy nhất cho GUI là phiên controller.
- Skill router cho mọi task Blender: `blender-agent-core` (Skill tool) trước bất kỳ skill domain nào.
