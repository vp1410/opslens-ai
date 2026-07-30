import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).parent
SERVER_FILE = PROJECT_ROOT / "mcp_server.py"


async def list_available_tools(
    session: ClientSession,
) -> None:
    """Request and display all tools exposed by the MCP server."""

    response = await session.list_tools()

    print("\nAvailable MCP tools:")

    for tool in response.tools:
        print("\n" + "-" * 70)
        print(f"Name: {tool.name}")
        print(f"Description: {tool.description}")
        print("Input schema:")
        print(json.dumps(tool.inputSchema, indent=2))


async def call_tool(
    session: ClientSession,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    Call an MCP tool and convert its returned content into a Python dictionary.
    """

    response = await session.call_tool(
        name=tool_name,
        arguments=arguments,
    )

    if response.isError:
        raise RuntimeError(
            f"MCP tool '{tool_name}' returned an error."
        )

    for content_item in response.content:
        if content_item.type == "text":
            return json.loads(content_item.text)

    raise ValueError(
        f"MCP tool '{tool_name}' did not return text content."
    )


async def main() -> None:
    """Start the MCP server, connect to it, and call a test tool."""

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server_parameters) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:
            await session.initialize()

            print("Connected to OpsLens MCP server.")

            await list_available_tools(session)

            query = (
                "The Airflow pipeline retried after partially "
                "loading data and now fails with duplicate records."
            )

            print("\n" + "=" * 70)
            print("Calling MCP tool: search_runbooks")
            print(f"Query: {query}")

            result = await call_tool(
                session=session,
                tool_name="search_runbooks",
                arguments={
                    "query": query,
                    "limit": 3,
                },
            )

            print("\nTool result:")
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())