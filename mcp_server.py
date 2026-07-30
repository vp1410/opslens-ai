from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from incident_retrieval import (
    get_incident_collection,
    index_incidents,
    search_incidents_semantically,
)
from rag import (
    get_chroma_collection,
    index_runbooks,
    search_runbooks as semantic_search_runbooks,
)


RUNBOOK_DIRECTORY = Path("data/runbooks")

RUNBOOK_MAX_DISTANCE = 0.95
INCIDENT_MAX_DISTANCE = 1.25


mcp = FastMCP(
    name="OpsLens AI Tools",
    instructions=(
        "Tools for searching engineering runbooks and historical incidents. "
        "Use these tools to gather evidence before analyzing an incident."
    ),
)


@mcp.tool()
def search_runbooks(
    query: str,
    limit: int = 3,
    max_distance: float = RUNBOOK_MAX_DISTANCE,
) -> dict[str, Any]:
    """
    Search engineering runbooks using semantic vector similarity.

    Use this tool when an incident requires troubleshooting guidance,
    likely causes, investigation steps, remediation guidance, or
    diagnostic commands.

    Args:
        query:
            Natural-language description of the technical incident.

        limit:
            Maximum number of runbook chunks to inspect.
            Must be between 1 and 5.

        max_distance:
            Maximum vector distance allowed for a result.
            Smaller values require stronger semantic similarity.

    Returns:
        Relevant runbook chunks and retrieval metadata.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("query cannot be empty.")

    if not 1 <= limit <= 5:
        raise ValueError("limit must be between 1 and 5.")

    if max_distance < 0:
        raise ValueError("max_distance cannot be negative.")

    collection = get_chroma_collection()

    if collection.count() == 0:
        index_runbooks(
            collection=collection,
            rebuild=False,
        )

    results = semantic_search_runbooks(
        query=cleaned_query,
        collection=collection,
        limit=limit,
        max_distance=max_distance,
    )

    return {
        "query": cleaned_query,
        "result_count": len(results),
        "max_distance": max_distance,
        "has_relevant_evidence": bool(results),
        "retrieval_method": "semantic_vector_search",
        "results": results,
    }


@mcp.tool()
def search_incidents(
    query: str,
    limit: int = 2,
    max_distance: float = INCIDENT_MAX_DISTANCE,
) -> dict[str, Any]:
    """
    Search historical engineering incidents using semantic similarity.

    Use this tool to find previous incidents with similar symptoms,
    affected services, root causes, or resolutions, even when the current
    incident uses different wording.

    Args:
        query:
            Natural-language description of the current incident.

        limit:
            Maximum number of incident matches to inspect.
            Must be between 1 and 5.

        max_distance:
            Maximum vector distance allowed for a result.
            Smaller values require stronger semantic similarity.

    Returns:
        Relevant historical incidents and retrieval metadata.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("query cannot be empty.")

    if not 1 <= limit <= 5:
        raise ValueError("limit must be between 1 and 5.")

    if max_distance < 0:
        raise ValueError("max_distance cannot be negative.")

    collection = get_incident_collection()

    if collection.count() == 0:
        index_incidents(
            collection=collection,
            rebuild=False,
        )

    results = search_incidents_semantically(
        query=cleaned_query,
        collection=collection,
        limit=limit,
        max_distance=max_distance,
    )

    return {
        "query": cleaned_query,
        "result_count": len(results),
        "max_distance": max_distance,
        "has_relevant_incidents": bool(results),
        "retrieval_method": "semantic_vector_search",
        "results": results,
    }


@mcp.tool()
def read_runbook(filename: str) -> dict[str, str]:
    """
    Read the complete contents of a specific engineering runbook.

    Use this tool when a relevant runbook has already been identified
    and its complete contents are required.

    Args:
        filename:
            Exact Markdown filename, such as airflow_failures.md.

    Returns:
        The filename and complete Markdown content.
    """

    cleaned_filename = filename.strip()

    if not cleaned_filename:
        raise ValueError("filename cannot be empty.")

    safe_filename = Path(cleaned_filename).name

    if safe_filename != cleaned_filename:
        raise ValueError(
            "filename must contain only a file name, not a path."
        )

    if not safe_filename.endswith(".md"):
        raise ValueError("Only Markdown runbooks can be read.")

    file_path = RUNBOOK_DIRECTORY / safe_filename

    if not file_path.exists():
        available_files = sorted(
            path.name
            for path in RUNBOOK_DIRECTORY.glob("*.md")
        )

        raise FileNotFoundError(
            f"Runbook not found: {safe_filename}. "
            f"Available runbooks: {available_files}"
        )

    return {
        "filename": safe_filename,
        "content": file_path.read_text(encoding="utf-8"),
    }


def main() -> None:
    """Start the MCP server over standard input and output."""

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()