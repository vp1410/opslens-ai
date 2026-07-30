
from pathlib import Path
from typing import Any, TypedDict

import chromadb
from chromadb.api.models.Collection import Collection


RUNBOOK_DIRECTORY = Path("data/runbooks")
CHROMA_DIRECTORY = "chroma_db"
COLLECTION_NAME = "opslens_runbooks"
DEFAULT_MAX_DISTANCE = 0.95

class DocumentChunk(TypedDict):
    """Represents one searchable piece of a runbook."""

    text: str
    source: str
    chunk_id: str


class SearchResult(TypedDict):
    """Represents one result returned by semantic search."""

    text: str
    source: str
    chunk_id: str
    distance: float


def load_runbooks() -> list[dict[str, str]]:
    """Load every Markdown runbook from data/runbooks."""

    documents: list[dict[str, str]] = []

    if not RUNBOOK_DIRECTORY.exists():
        raise FileNotFoundError(
            f"Runbook directory does not exist: {RUNBOOK_DIRECTORY}"
        )

    for file_path in sorted(RUNBOOK_DIRECTORY.glob("*.md")):
        content = file_path.read_text(encoding="utf-8").strip()

        if not content:
            continue

        documents.append(
            {
                "source": file_path.name,
                "content": content,
            }
        )

    return documents


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[str]:
    """Split text into overlapping chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0:
        raise ValueError("overlap cannot be negative.")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    cleaned_text = text.strip()

    if not cleaned_text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(cleaned_text):
        end = min(start + chunk_size, len(cleaned_text))

        chunk = cleaned_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(cleaned_text):
            break

        start = end - overlap

    return chunks


def create_runbook_chunks() -> list[DocumentChunk]:
    """Load every runbook and divide it into searchable chunks."""

    documents = load_runbooks()
    all_chunks: list[DocumentChunk] = []

    for document in documents:
        source = document["source"]
        chunks = chunk_text(document["content"])

        for index, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk,
                    "source": source,
                    "chunk_id": f"{source}-chunk-{index}",
                }
            )

    return all_chunks


def get_chroma_collection() -> Collection:
    """
    Create or load the persistent ChromaDB collection.

    PersistentClient stores the vector database inside the chroma_db folder.
    """

    client = chromadb.PersistentClient(path=CHROMA_DIRECTORY)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Synthetic engineering runbooks for OpsLens AI"
        },
    )

    return collection


def index_runbooks(
    collection: Collection,
    rebuild: bool = False,
) -> int:
    """
    Add runbook chunks to ChromaDB.

    Args:
        collection:
            The ChromaDB collection where chunks will be stored.

        rebuild:
            When True, remove existing records before indexing.

    Returns:
        Number of chunks currently stored in the collection.
    """

    if rebuild:
        existing_records = collection.get()

        existing_ids = existing_records.get("ids", [])

        if existing_ids:
            collection.delete(ids=existing_ids)

    chunks = create_runbook_chunks()

    if not chunks:
        raise ValueError("No runbook chunks were created.")

    existing_records = collection.get()
    existing_ids = set(existing_records.get("ids", []))

    new_chunks = [
        chunk
        for chunk in chunks
        if chunk["chunk_id"] not in existing_ids
    ]

    if new_chunks:
        collection.add(
            ids=[chunk["chunk_id"] for chunk in new_chunks],
            documents=[chunk["text"] for chunk in new_chunks],
            metadatas=[
                {
                    "source": chunk["source"],
                    "chunk_id": chunk["chunk_id"],
                }
                for chunk in new_chunks
            ],
        )

    return collection.count()


def search_runbooks(
    query: str,
    collection: Collection,
    limit: int = 3,
    max_distance: float | None = DEFAULT_MAX_DISTANCE,
) -> list[SearchResult]:
    """
    Search for runbook chunks semantically related to a query.

    Results with a distance greater than max_distance are removed.
    A smaller distance means stronger semantic similarity.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("Search query cannot be empty.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    if max_distance is not None and max_distance < 0:
        raise ValueError("max_distance cannot be negative.")

    available_records = collection.count()

    if available_records == 0:
        return []

    result_limit = min(limit, available_records)

    raw_results: dict[str, Any] = collection.query(
        query_texts=[cleaned_query],
        n_results=result_limit,
        include=["documents", "metadatas", "distances"],
    )

    documents = raw_results.get("documents", [[]])[0]
    metadatas = raw_results.get("metadatas", [[]])[0]
    distances = raw_results.get("distances", [[]])[0]
    ids = raw_results.get("ids", [[]])[0]

    search_results: list[SearchResult] = []

    for document, metadata, distance, chunk_id in zip(
        documents,
        metadatas,
        distances,
        ids,
        strict=True,
    ):
        numeric_distance = float(distance)

        if (
            max_distance is not None
            and numeric_distance > max_distance
        ):
            continue

        search_results.append(
            {
                "text": document,
                "source": metadata["source"],
                "chunk_id": chunk_id,
                "distance": numeric_distance,
            }
        )

    return search_results


def print_search_results(results: list[SearchResult]) -> None:
    """Print semantic-search results in a readable format."""

    if not results:
        print("No matching runbook sections found.")
        return

    for position, result in enumerate(results, start=1):
        print("\n" + "=" * 80)
        print(f"Result: {position}")
        print(f"Source: {result['source']}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Distance: {result['distance']:.4f}")
        print("-" * 80)
        print(result["text"])


def main() -> None:
    """Create the index and perform a test search."""

    collection = get_chroma_collection()

    total_chunks = index_runbooks(
        collection=collection,
        rebuild=True,
    )

    print(f"Indexed chunks: {total_chunks}")

    test_query = (
        "The Airflow job retried after partially loading data "
        "and now fails because the same records already exist."
    )

    print(f"\nSearch query:\n{test_query}")

    results = search_runbooks(
        query=test_query,
        collection=collection,
        limit=3,
    )

    print_search_results(results)


if __name__ == "__main__":
    main()