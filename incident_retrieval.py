import json
from pathlib import Path
from typing import Any, TypedDict

import chromadb
from chromadb.api.models.Collection import Collection


INCIDENTS_FILE = Path("data/incidents.json")
CHROMA_DIRECTORY = "chroma_db"
INCIDENT_COLLECTION_NAME = "opslens_incidents"
DEFAULT_MAX_DISTANCE = 1.25


class IncidentSearchResult(TypedDict):
    id: str
    title: str
    service: str
    category: str
    description: str
    root_cause: str
    resolution: str
    status: str
    distance: float


def load_incidents() -> list[dict[str, Any]]:
    """Load synthetic historical incidents from JSON."""

    if not INCIDENTS_FILE.exists():
        raise FileNotFoundError(
            f"Incident file does not exist: {INCIDENTS_FILE}"
        )

    with INCIDENTS_FILE.open("r", encoding="utf-8") as file:
        incidents = json.load(file)

    if not isinstance(incidents, list):
        raise ValueError(
            "data/incidents.json must contain a JSON list."
        )

    return incidents


def build_incident_document(
    incident: dict[str, Any],
) -> str:
    """
    Combine important incident fields into one searchable document.

    The embedding model converts this combined text into one vector.
    """

    return "\n".join(
        [
            f"Incident ID: {incident.get('id', '')}",
            f"Title: {incident.get('title', '')}",
            f"Service: {incident.get('service', '')}",
            f"Category: {incident.get('category', '')}",
            f"Description: {incident.get('description', '')}",
            f"Root cause: {incident.get('root_cause', '')}",
            f"Resolution: {incident.get('resolution', '')}",
            f"Status: {incident.get('status', '')}",
        ]
    )


def get_incident_collection() -> Collection:
    """Create or load the persistent incident vector collection."""

    client = chromadb.PersistentClient(
        path=CHROMA_DIRECTORY
    )

    return client.get_or_create_collection(
        name=INCIDENT_COLLECTION_NAME,
        metadata={
            "description": (
                "Synthetic historical incidents for OpsLens AI"
            )
        },
    )


def index_incidents(
    collection: Collection,
    rebuild: bool = False,
) -> int:
    """Create embeddings and store historical incidents in ChromaDB."""

    if rebuild:
        existing = collection.get()
        existing_ids = existing.get("ids", [])

        if existing_ids:
            collection.delete(ids=existing_ids)

    incidents = load_incidents()

    existing_ids = set(
        collection.get().get("ids", [])
    )

    new_incidents = [
        incident
        for incident in incidents
        if str(incident.get("id", "")) not in existing_ids
    ]

    if new_incidents:
        collection.add(
            ids=[
                str(incident["id"])
                for incident in new_incidents
            ],
            documents=[
                build_incident_document(incident)
                for incident in new_incidents
            ],
            metadatas=[
                {
                    "id": str(incident.get("id", "")),
                    "title": str(incident.get("title", "")),
                    "service": str(incident.get("service", "")),
                    "category": str(incident.get("category", "")),
                    "description": str(
                        incident.get("description", "")
                    ),
                    "root_cause": str(
                        incident.get("root_cause", "")
                    ),
                    "resolution": str(
                        incident.get("resolution", "")
                    ),
                    "status": str(
                        incident.get("status", "")
                    ),
                }
                for incident in new_incidents
            ],
        )

    return collection.count()


def search_incidents_semantically(
    query: str,
    collection: Collection,
    limit: int = 2,
    max_distance: float | None = DEFAULT_MAX_DISTANCE,
) -> list[IncidentSearchResult]:
    """Search historical incidents by semantic meaning."""

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("query cannot be empty.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    if max_distance is not None and max_distance < 0:
        raise ValueError(
            "max_distance cannot be negative."
        )

    available_records = collection.count()

    if available_records == 0:
        return []

    raw_results = collection.query(
        query_texts=[cleaned_query],
        n_results=min(limit, available_records),
        include=[
            "metadatas",
            "distances",
        ],
    )

    metadatas = raw_results.get(
        "metadatas",
        [[]],
    )[0]

    distances = raw_results.get(
        "distances",
        [[]],
    )[0]

    results: list[IncidentSearchResult] = []

    for metadata, distance in zip(
        metadatas,
        distances,
        strict=True,
    ):
        numeric_distance = float(distance)

        if (
            max_distance is not None
            and numeric_distance > max_distance
        ):
            continue

        results.append(
            {
                "id": str(metadata.get("id", "")),
                "title": str(metadata.get("title", "")),
                "service": str(metadata.get("service", "")),
                "category": str(metadata.get("category", "")),
                "description": str(
                    metadata.get("description", "")
                ),
                "root_cause": str(
                    metadata.get("root_cause", "")
                ),
                "resolution": str(
                    metadata.get("resolution", "")
                ),
                "status": str(
                    metadata.get("status", "")
                ),
                "distance": numeric_distance,
            }
        )

    return results


def main() -> None:
    """Index incidents and run a semantic-search test."""

    collection = get_incident_collection()

    count = index_incidents(
        collection=collection,
        rebuild=True,
    )

    print(f"Indexed incidents: {count}")

    query = (
        "The scheduled job reran after partially completing "
        "and created duplicate database rows."
    )

    results = search_incidents_semantically(
        query=query,
        collection=collection,
        limit=3,
    )

    if not results:
        print("No incidents found.")
        return

    for result in results:
        print("\n" + "=" * 70)
        print(f"ID: {result['id']}")
        print(f"Title: {result['title']}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Root cause: {result['root_cause']}")


if __name__ == "__main__":
    main()