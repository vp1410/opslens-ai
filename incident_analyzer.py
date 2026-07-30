import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

from config import OPENAI_MODEL, validate_config


PROJECT_ROOT = Path(__file__).parent
MCP_SERVER_FILE = PROJECT_ROOT / "mcp_server.py"


async def parse_tool_response(response: Any) -> dict[str, Any]:
    """
    Convert an MCP tool response into a Python dictionary.
    """

    if response.isError:
        raise RuntimeError("The MCP tool returned an error.")

    # MCP tools can return multiple content items.
    # Our tools return one JSON text item.
    for content_item in response.content:
        if content_item.type == "text":
            return json.loads(content_item.text)

    raise ValueError("The MCP tool did not return JSON text content.")


async def retrieve_incident_evidence(
    incident_description: str,
) -> dict[str, Any]:
    """
    Retrieve relevant runbook sections and historical incidents
    through the MCP server.
    """

    cleaned_incident = incident_description.strip()

    if not cleaned_incident:
        raise ValueError("Incident description cannot be empty.")

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(MCP_SERVER_FILE)],
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

            runbook_response = await session.call_tool(
                name="search_runbooks",
                arguments={
                    "query": cleaned_incident,
                    "limit": 3,
                    "max_distance": 0.95,
                },
            )

            incident_response = await session.call_tool(
                name="search_incidents",
                arguments={
                    "query": cleaned_incident,
                    "limit": 2,
                },
            )

            runbook_results = await parse_tool_response(
                runbook_response
            )

            historical_incidents = await parse_tool_response(
                incident_response
            )

    return {
        "incident_description": cleaned_incident,
        "runbook_search": runbook_results,
        "incident_search": historical_incidents,
        "tools_used": [
            "search_runbooks",
            "search_incidents",
        ],
    }
    """
    Retrieve relevant runbook sections and historical incidents
    through the MCP server.
    """

    cleaned_incident = incident_description.strip()

    if not cleaned_incident:
        raise ValueError("Incident description cannot be empty.")

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(MCP_SERVER_FILE)],
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

            runbook_response = await session.call_tool(
                name="search_runbooks",
                arguments={
                    "query": cleaned_incident,
                    "limit": 3,
                    "max_distance": 0.95,
                },
            )

            incident_response = await session.call_tool(
                name="search_incidents",
                arguments={
                    "query": cleaned_incident,
                    "limit": 2,
                },
            )

            runbook_results = await parse_tool_response(
                runbook_response
            )

            historical_incidents = await parse_tool_response(
                incident_response
            )

    return {
        "incident_description": cleaned_incident,
        "runbook_search": runbook_results,
        "incident_search": historical_incidents,
        "tools_used": [
            "search_runbooks",
            "search_incidents",
        ],
    }


def format_runbook_context(
    runbook_search: dict[str, Any],
) -> str:
    """
    Convert retrieved runbook chunks into readable prompt context.
    """

    results = runbook_search.get("results", [])

    if not results:
        return "No relevant runbook sections were found."

    formatted_sections: list[str] = []

    for position, result in enumerate(results, start=1):
        formatted_sections.append(
            "\n".join(
                [
                    f"RUNBOOK RESULT {position}",
                    f"Source: {result['source']}",
                    f"Chunk ID: {result['chunk_id']}",
                    f"Retrieval distance: {result['distance']:.4f}",
                    "Content:",
                    result["text"],
                ]
            )
        )

    return "\n\n---\n\n".join(formatted_sections)


def format_incident_context(
    incident_search: dict[str, Any],
) -> str:
    """
    Convert historical incident results into readable prompt context.
    """

    results = incident_search.get("results", [])

    if not results:
        return "No similar historical incidents were found."

    formatted_incidents: list[str] = []

    for position, incident in enumerate(results, start=1):
        formatted_incidents.append(
            "\n".join(
                [
                    f"HISTORICAL INCIDENT {position}",
                    f"ID: {incident.get('id', 'Unknown')}",
                    f"Title: {incident.get('title', 'Unknown')}",
                    f"Service: {incident.get('service', 'Unknown')}",
                    f"Category: {incident.get('category', 'Unknown')}",
                    f"Description: {incident.get('description', '')}",
                    f"Root cause: {incident.get('root_cause', '')}",
                    f"Resolution: {incident.get('resolution', '')}",
                ]
            )
        )

    return "\n\n---\n\n".join(formatted_incidents)


def generate_grounded_analysis(
    evidence: dict[str, Any],
) -> str:
    """
    Ask the LLM to analyze the incident using only retrieved evidence.
    """

    validate_config()
    client = OpenAI()

    incident_description = evidence["incident_description"]

    runbook_context = format_runbook_context(
        evidence["runbook_search"]
    )

    incident_context = format_incident_context(
        evidence["incident_search"]
    )

    has_runbook_evidence = bool(
        evidence.get(
            "runbook_search",
            {},
        ).get(
            "results",
            [],
        )
    )

    has_incident_evidence = bool(
        evidence.get(
            "incident_search",
            {},
        ).get(
            "results",
            [],
        )
    )

    has_any_evidence = (
        has_runbook_evidence
        or has_incident_evidence
    )

    augmented_input = f"""
CURRENT INCIDENT

{incident_description}


RETRIEVED RUNBOOK EVIDENCE

{runbook_context}


SIMILAR HISTORICAL INCIDENTS

{incident_context}


EVIDENCE STATUS

Relevant runbook evidence found: {has_runbook_evidence}
Similar historical incidents found: {has_incident_evidence}
Any supporting evidence found: {has_any_evidence}


TASK

Analyze the current incident using only the evidence provided above.

Return the response using these Markdown sections:

## Incident Summary

Provide a brief summary of the reported problem.

## Likely Causes

List the most likely causes.

Clearly label each cause as a hypothesis unless the supplied evidence
directly proves it.

## Investigation Steps

Provide a numbered sequence of safe diagnostic steps.

## Suggested Commands

Include relevant SQL, shell commands, or operational checks only when
they are supported by the retrieved evidence.

Put commands inside code blocks.

## Similar Historical Incidents

Mention relevant historical incident IDs and explain why they are
similar.

State that no similar incidents were found when applicable.

## Sources

List the exact runbook filenames and historical incident IDs used.

## Confidence and Limitations

Use one of these confidence levels:

- Low
- Medium
- High

Explain what information or evidence is missing.

If no supporting evidence was found:

- Clearly state that the knowledge base does not contain sufficient
  information for this incident.
- Do not provide a root-cause diagnosis.
- Do not generate unsupported commands.
- Do not use general model knowledge to troubleshoot the incident.
- Briefly explain what additional runbook, log, metric, or operational
  evidence would be required.

Do not invent:

- logs
- metrics
- table contents
- deployment details
- credentials
- confirmed root causes
- historical incident information

Do not claim that a hypothesis is confirmed unless the supplied
evidence explicitly proves it.

Do not recommend destructive production actions such as deleting data
without review, backup, and approval.
""".strip()

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You are OpsLens AI, a cautious engineering incident "
            "investigation assistant. Use only the supplied evidence. "
            "Treat retrieved runbooks and historical incidents as supporting "
            "context, not proof that the same root cause applies to the "
            "current incident. When evidence is insufficient, explicitly "
            "say so instead of relying on general model knowledge."
        ),
        input=augmented_input,
    )

    return response.output_text


async def analyze_incident(
    incident_description: str,
) -> dict[str, Any]:
    """
    Execute the complete MCP + RAG + LLM workflow.
    """

    evidence = await retrieve_incident_evidence(
        incident_description
    )

    analysis = generate_grounded_analysis(evidence)

    return {
        "incident_description": incident_description,
        "analysis": analysis,
        "evidence": evidence,
    }


async def main() -> None:
    """Run an end-to-end test."""

    test_incident = (
        "The Airflow campaign-data pipeline failed after partially "
        "loading records. Airflow retried the task, but the retry now "
        "fails with a duplicate-key error because some rows already exist."
    )

    print("Analyzing incident...")
    print(f"\nIncident:\n{test_incident}")

    result = await analyze_incident(test_incident)

    print("\n" + "=" * 80)
    print("GENERATED ANALYSIS")
    print("=" * 80)
    print(result["analysis"])

    print("\n" + "=" * 80)
    print("TOOLS USED")
    print("=" * 80)

    for tool_name in result["evidence"]["tools_used"]:
        print(f"- {tool_name}")


if __name__ == "__main__":
    asyncio.run(main())