#!/usr/bin/env python3
"""Unit and protocol tests for design-os-3d-blender MCP server."""

import asyncio
import json
from pathlib import Path
import sys
import unittest

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from design_os_3d_blender_mcp import server


class TestMCPServerProtocol(unittest.TestCase):
    """Verify MCP protocol surface and sandbox tolerance."""

    def test_tools_registered(self):
        """Ensure all required tools are registered unconditionally."""
        async def check():
            tools = await server.mcp.list_tools()
            tool_names = [t.name for t in tools]
            self.assertIn("blender_runtime_status", tool_names)
            self.assertIn("query_blender_knowledge", tool_names)
            self.assertIn("validate_part_spec", tool_names)
            self.assertIn("execute_blender_pass", tool_names)
        asyncio.run(check())

    def test_prompts_registered(self):
        """Ensure prompts/list returns >= 1 prompt template."""
        async def check():
            prompts = await server.mcp.list_prompts()
            prompt_names = [p.name for p in prompts]
            self.assertIn("design_parametric_part", prompt_names)
            self.assertIn("review_geometry_gate", prompt_names)
        asyncio.run(check())

    def test_resources_registered(self):
        """Ensure resources/list returns >= 1 concrete resource."""
        async def check():
            resources = await server.mcp.list_resources()
            resource_uris = [str(r.uri) for r in resources]
            self.assertIn("blender://knowledge/index", resource_uris)
            self.assertIn("blender://specs/bracket-example", resource_uris)
        asyncio.run(check())

    def test_knowledge_query_tool(self):
        """Verify knowledge query returns structured results."""
        res_raw = server.query_blender_knowledge("bevel")
        res = json.loads(res_raw)
        self.assertEqual(res["query"], "bevel")
        self.assertGreaterEqual(res["total_results"], 1)

    def test_spec_validate_tool(self):
        """Verify part spec validation works with existing fixture."""
        spec_path = "specs/examples/bracket-m3.spec.json"
        res_raw = server.validate_part_spec(spec_path)
        res = json.loads(res_raw)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)

    def test_sandbox_zero_blender_survival(self):
        """Ensure server tools survive in environments where Blender is not installed."""
        orig_find = server.find_blender_bin
        try:
            server.find_blender_bin = lambda: None
            status_raw = server.blender_runtime_status()
            status = json.loads(status_raw)
            self.assertFalse(status["blender_available"])
            self.assertIsNone(status["blender_bin"])

            exec_raw = server.execute_blender_pass("dummy_script.py")
            exec_res = json.loads(exec_raw)
            self.assertEqual(exec_res["status"], "error")
            self.assertEqual(exec_res["sentinel"], "AGENT_FAIL")
        finally:
            server.find_blender_bin = orig_find


if __name__ == "__main__":
    unittest.main()
