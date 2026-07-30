import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag import (
    get_chroma_collection,
    index_runbooks,
    search_runbooks as semantic_search_runbooks,
)


RUNBOOK_DIRECTORY = Path("data/runbooks")
INCIDENTS_FILE = Path("data/incidents.json")


mcp = FastMCP(
    name="OpsLens AI Tools",
    instructions=(
        "Tools for searching engineering runbooks and historical incidents. "
        "Use these tools to gather evidence before analyzing an incident."
    ),
)


def load_incidents() -> list[dict[str, Any]]:
    """Load historical incidents from the local JSON file."""

    if not INCIDENTS_FILE.exists():
        raise FileNotFoundError(
            f"Incident file does not exist: {INCIDENTS_FILE}"
        )

    with INCIDENTS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("The incident file must contain a JSON list.")

    return data


@mcp.tool()
def search_runbooks(
    query: str,
    limit: int = 3,
    max_distance: float = 0.95,
) -> dict[str, Any]:
    """
    Search engineering runbooks using semantic similarity.

    Use this tool when an incident requires troubleshooting guidance,
    likely causes, investigation procedures, remediation steps, or
    diagnostic commands.

     Args:
        query:
            A natural-language description of the technical problem.

        limit:
            Maximum number of runbook chunks to inspect.
            Must be between 1 and 5.

        max_distance:
            Maximum vector distance allowed for a result.
            Smaller values require stronger semantic similarity.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("query cannot be empty.")

    if not 1 <= limit <= 5:
        raise ValueError("limit must be between 1 and 5.")

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
        "results": results,
    }


@mcp.tool()
def search_incidents(
    query: str,
    limit: int = 3,
) -> dict[str, Any]:
    """
    Search historical engineering incidents using keyword matching.

    Use this tool to find previous incidents with similar symptoms,
    categories, services, root causes, or resolutions.

    Args:
        query:
            Words describing the current incident.

        limit:
            Maximum number of incidents to return.
            Must be between 1 and 5.
    """

    cleaned_query = query.strip().lower()

    if not cleaned_query:
        raise ValueError("query cannot be empty.")

    if not 1 <= limit <= 5:
        raise ValueError("limit must be between 1 and 5.")

    query_terms = set(cleaned_query.split())
    incidents = load_incidents()

    ranked_incidents: list[tuple[int, dict[str, Any]]] = []

    searchable_fields = (
        "title",
        "service",
        "category",
        "description",
        "root_cause",
        "resolution",
    )

    for incident in incidents:
        searchable_text = " ".join(
            str(incident.get(field, ""))
            for field in searchable_fields
        ).lower()

        score = sum(
            1
            for term in query_terms
            if term in searchable_text
        )

        if score > 0:
            ranked_incidents.append((score, incident))

    ranked_incidents.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    matches = [
        {
            **incident,
            "match_score": score,
        }
        for score, incident in ranked_incidents[:limit]
    ]

    return {
        "query": query,
        "result_count": len(matches),
        "results": matches,
    }


@mcp.tool()
def read_runbook(filename: str) -> dict[str, str]:
    """
    Read the complete contents of a specific engineering runbook.

    Use this tool after identifying a relevant source when the full
    runbook is needed.

    Args:
        filename:
            Exact Markdown filename, such as airflow_failures.md.
    """

    safe_filename = Path(filename).name

    if safe_filename != filename:
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
    """Start the MCP server using the standard input/output transport."""

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()