#!/usr/bin/env python3
"""Launch the server the way an MCP client does and exercise one tool call.

This is the check the project did not have: it starts ``sam-gov-mcp`` as a
subprocess, completes the protocol handshake, lists the tools, and calls one.
Every failure that made 0.1.0 unusable -- a missing module, a constructor
signature mismatch, a transport that was never opened, a subpackage left out
of the wheel -- surfaces here.

No API key or network access is required: the tool call is deliberately
invalid, so it returns a validation error without reaching SAM.gov.
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOL = "search_opportunities"


async def main() -> int:
    env = dict(os.environ)
    env.setdefault("SAM_API_KEY", "smoke-test-placeholder")

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "sam_gov_mcp"],
        env=env,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"handshake ok: {init.serverInfo.name} {init.serverInfo.version}")

            listing = await session.list_tools()
            names = [tool.name for tool in listing.tools]
            print(f"tools: {names}")
            if EXPECTED_TOOL not in names:
                print(f"FAIL: {EXPECTED_TOOL} not advertised", file=sys.stderr)
                return 1

            result = await session.call_tool(
                EXPECTED_TOOL,
                {"posted_from": "01/01/2023", "posted_to": "12/31/2024"},
            )
            payload = json.loads(result.content[0].text)
            print(f"tool call returned: {payload.get('error_type')}")

            if payload.get("error_type") != "validation_error":
                print(f"FAIL: unexpected payload {payload}", file=sys.stderr)
                return 1

    print("smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
