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

RUNBOOK_MAX_DISTANCE = 0.95
INCIDENT_MAX_DISTANCE = 1.0


def parse_tool_response(
    response: Any,
) -> dict[str, Any]:
    """
    Convert an MCP tool response into a Python dictionary.

    Our FastMCP tools return dictionaries, which MCP serializes as
    JSON text content.
    """

    if response.isError:
        error_messages = [
            getattr(content_item, "text", "")
            for content_item in response.content
            if getattr(content_item, "type", None) == "text"
        ]

        error_detail = " ".join(
            message
            for message in error_messages
            if message
        )

        raise RuntimeError(
            error_detail or "The MCP tool returned an error."
        )

    for content_item in response.content:
        if getattr(content_item, "type", None) != "text":
            continue

        text = getattr(content_item, "text", "")

        if not text:
            continue

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(
                "The MCP tool returned text that was not valid JSON."
            ) from error

        if not isinstance(parsed, dict):
            raise ValueError(
                "The MCP tool response must be a JSON object."
            )

        return parsed

    raise ValueError(
        "The MCP tool did not return JSON text content."
    )


async def retrieve_incident_evidence(
    incident_description: str,
) -> dict[str, Any]:
    """
    Retrieve relevant runbook sections and historical incidents
    through the MCP server.
    """

    cleaned_incident = incident_description.strip()

    if not cleaned_incident:
        raise ValueError(
            "Incident description cannot be empty."
        )

    if not MCP_SERVER_FILE.exists():
        raise FileNotFoundError(
            f"MCP server file not found: {MCP_SERVER_FILE}"
        )

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
                    "max_distance": RUNBOOK_MAX_DISTANCE,
                },
            )

            incident_response = await session.call_tool(
                name="search_incidents",
                arguments={
                    "query": cleaned_incident,
                    "limit": 2,
                    "max_distance": INCIDENT_MAX_DISTANCE,
                },
            )

            runbook_results = parse_tool_response(
                runbook_response
            )

            historical_incidents = parse_tool_response(
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
    Convert retrieved runbook chunks into readable LLM context.
    """

    results = runbook_search.get("results", [])

    if not results:
        return "No relevant runbook sections were found."

    formatted_sections: list[str] = []

    for position, result in enumerate(
        results,
        start=1,
    ):
        source = result.get(
            "source",
            "Unknown source",
        )

        chunk_id = result.get(
            "chunk_id",
            "Unknown chunk",
        )

        distance = result.get("distance")
        text = result.get("text", "")

        if isinstance(distance, (int, float)):
            distance_text = f"{distance:.4f}"
        else:
            distance_text = "Not available"

        formatted_sections.append(
            "\n".join(
                [
                    f"RUNBOOK RESULT {position}",
                    f"Source: {source}",
                    f"Chunk ID: {chunk_id}",
                    f"Retrieval distance: {distance_text}",
                    "Content:",
                    str(text),
                ]
            )
        )

    return "\n\n---\n\n".join(
        formatted_sections
    )


def format_incident_context(
    incident_search: dict[str, Any],
) -> str:
    """
    Convert retrieved historical incidents into readable LLM context.
    """

    results = incident_search.get("results", [])

    if not results:
        return "No similar historical incidents were found."

    formatted_incidents: list[str] = []

    for position, incident in enumerate(
        results,
        start=1,
    ):
        distance = incident.get("distance")

        if isinstance(distance, (int, float)):
            distance_text = f"{distance:.4f}"
        else:
            distance_text = "Not available"

        formatted_incidents.append(
            "\n".join(
                [
                    f"HISTORICAL INCIDENT {position}",
                    f"ID: {incident.get('id', 'Unknown')}",
                    f"Title: {incident.get('title', 'Unknown')}",
                    f"Service: {incident.get('service', 'Unknown')}",
                    f"Category: {incident.get('category', 'Unknown')}",
                    (
                        "Description: "
                        f"{incident.get('description', '')}"
                    ),
                    (
                        "Root cause: "
                        f"{incident.get('root_cause', '')}"
                    ),
                    (
                        "Resolution: "
                        f"{incident.get('resolution', '')}"
                    ),
                    f"Status: {incident.get('status', 'Unknown')}",
                    f"Retrieval distance: {distance_text}",
                ]
            )
        )

    return "\n\n---\n\n".join(
        formatted_incidents
    )


def generate_grounded_analysis(
    evidence: dict[str, Any],
) -> str:
    """
    Generate an incident analysis using only retrieved evidence.
    """

    validate_config()

    client = OpenAI()

    incident_description = evidence[
        "incident_description"
    ]

    runbook_search = evidence.get(
        "runbook_search",
        {},
    )

    incident_search = evidence.get(
        "incident_search",
        {},
    )

    runbook_context = format_runbook_context(
        runbook_search
    )

    incident_context = format_incident_context(
        incident_search
    )

    has_runbook_evidence = bool(
        runbook_search.get("results", [])
    )

    has_incident_evidence = bool(
        incident_search.get("results", [])
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

State that no similar historical incidents were found when applicable.

## Sources

List the exact runbook filenames and historical incident IDs used.

## Confidence and Limitations

Use one of these confidence levels:

- Low
- Medium
- High

Explain which facts or evidence are missing.

If no supporting evidence was found:

- Clearly state that the knowledge base does not contain sufficient
  information for this incident.
- Do not provide a root-cause diagnosis.
- Do not generate unsupported commands.
- Do not use general model knowledge to troubleshoot the incident.
- Briefly explain which runbook, log, metric, trace, or operational
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
            "Treat retrieved runbooks and historical incidents as "
            "supporting context, not proof that the same root cause "
            "applies to the current incident. When evidence is "
            "insufficient, explicitly say so instead of relying on "
            "general model knowledge."
        ),
        input=augmented_input,
    )

    generated_text = response.output_text.strip()

    if not generated_text:
        raise ValueError(
            "The language model returned an empty response."
        )

    return generated_text


async def analyze_incident(
    incident_description: str,
) -> dict[str, Any]:
    """
    Execute the complete MCP, retrieval, and generation workflow.
    """

    cleaned_incident = incident_description.strip()

    if not cleaned_incident:
        raise ValueError(
            "Incident description cannot be empty."
        )

    evidence = await retrieve_incident_evidence(
        cleaned_incident
    )

    analysis = generate_grounded_analysis(
        evidence
    )

    return {
        "incident_description": cleaned_incident,
        "analysis": analysis,
        "evidence": evidence,
    }


async def main() -> None:
    """Run a command-line end-to-end test."""

    test_incident = (
        "The scheduled campaign ingestion job partially loaded "
        "database records before failing. The job reran and now "
        "attempts to insert the same records again, causing a "
        "duplicate-key error."
    )

    print("Analyzing incident...")
    print(f"\nIncident:\n{test_incident}")

    result = await analyze_incident(
        test_incident
    )

    print("\n" + "=" * 80)
    print("GENERATED ANALYSIS")
    print("=" * 80)
    print(result["analysis"])

    print("\n" + "=" * 80)
    print("RETRIEVAL SUMMARY")
    print("=" * 80)

    runbook_search = result["evidence"][
        "runbook_search"
    ]

    incident_search = result["evidence"][
        "incident_search"
    ]

    print(
        "Relevant runbook chunks: "
        f"{runbook_search.get('result_count', 0)}"
    )

    print(
        "Relevant historical incidents: "
        f"{incident_search.get('result_count', 0)}"
    )

    print("\nTools used:")

    for tool_name in result["evidence"]["tools_used"]:
        print(f"- {tool_name}")


if __name__ == "__main__":
    asyncio.run(main())