import asyncio
from typing import Any

from incident_analyzer import retrieve_incident_evidence


TEST_CASES = [
    {
        "name": "Airflow duplicate retry",
        "query": (
            "The Airflow pipeline partially loaded records, retried, "
            "and now fails with a duplicate-key error."
        ),
        "acceptable_runbooks": {
            "airflow_failures.md",
            "database_errors.md",
        },
        "acceptable_incidents": {
            "INC-1001",
        },
        "require_runbook_match": True,
        "require_incident_match": True,
        "should_find_evidence": True,
    },
    {
        "name": "API timeout",
        "query": (
            "The reporting API returns HTTP 504 errors during high traffic "
            "and the database connection pool is exhausted."
        ),
        "acceptable_runbooks": {
            "api_timeouts.md",
        },
        "acceptable_incidents": {
            "INC-1002",
        },
        "require_runbook_match": True,
        "require_incident_match": True,
        "should_find_evidence": True,
    },
    {
        "name": "Duplicate source file",
        "query": (
            "The ingestion service processed the same input file twice "
            "and created duplicate rows."
        ),
        "acceptable_runbooks": {
            "database_errors.md",
        },
        "acceptable_incidents": {
            "INC-1003",
        },
        # A historical incident is sufficient for this case.
        "require_runbook_match": False,
        "require_incident_match": True,
        "should_find_evidence": True,
    },
    {
        "name": "Unsupported Kubernetes issue",
        "query": (
            "A Kubernetes pod cannot be scheduled because every node "
            "reports insufficient memory."
        ),
        "acceptable_runbooks": set(),
        "acceptable_incidents": set(),
        "require_runbook_match": False,
        "require_incident_match": False,
        "should_find_evidence": False,
    },
]


def extract_runbook_sources(
    evidence: dict[str, Any],
) -> set[str]:
    """Return retrieved runbook filenames."""

    return {
        result.get("source", "")
        for result in evidence.get(
            "runbook_search",
            {},
        ).get(
            "results",
            [],
        )
        if result.get("source")
    }


def extract_incident_ids(
    evidence: dict[str, Any],
) -> set[str]:
    """Return retrieved historical incident IDs."""

    return {
        result.get("id", "")
        for result in evidence.get(
            "incident_search",
            {},
        ).get(
            "results",
            [],
        )
        if result.get("id")
    }


def has_any_match(
    actual_values: set[str],
    acceptable_values: set[str],
) -> bool:
    """
    Return True when at least one acceptable value was retrieved.

    An empty acceptable set means there is no required match.
    """

    if not acceptable_values:
        return True

    return bool(
        actual_values.intersection(acceptable_values)
    )


async def evaluate_test_case(
    test_case: dict[str, Any],
) -> dict[str, Any]:
    """Run one retrieval evaluation case."""

    evidence = await retrieve_incident_evidence(
        test_case["query"]
    )

    actual_runbooks = extract_runbook_sources(
        evidence
    )

    actual_incidents = extract_incident_ids(
        evidence
    )

    has_evidence = bool(
        actual_runbooks
        or actual_incidents
    )

    runbook_match = has_any_match(
        actual_runbooks,
        test_case["acceptable_runbooks"],
    )

    incident_match = has_any_match(
        actual_incidents,
        test_case["acceptable_incidents"],
    )

    runbook_requirement_passed = (
        runbook_match
        if test_case["require_runbook_match"]
        else True
    )

    incident_requirement_passed = (
        incident_match
        if test_case["require_incident_match"]
        else True
    )

    evidence_behavior_match = (
        has_evidence
        == test_case["should_find_evidence"]
    )

    passed = (
        runbook_requirement_passed
        and incident_requirement_passed
        and evidence_behavior_match
    )

    return {
        "name": test_case["name"],
        "passed": passed,
        "actual_runbooks": actual_runbooks,
        "actual_incidents": actual_incidents,
        "runbook_match": runbook_match,
        "incident_match": incident_match,
        "expected_evidence": (
            test_case["should_find_evidence"]
        ),
        "actual_evidence": has_evidence,
    }


async def main() -> None:
    """Run all retrieval evaluation cases."""

    results = []

    for test_case in TEST_CASES:
        print(
            f"\nRunning: {test_case['name']}"
        )

        result = await evaluate_test_case(
            test_case
        )

        results.append(result)

        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )

        print(f"Status: {status}")
        print(
            "Runbooks:",
            sorted(result["actual_runbooks"]),
        )
        print(
            "Incidents:",
            sorted(result["actual_incidents"]),
        )
        print(
            "Runbook acceptable match:",
            result["runbook_match"],
        )
        print(
            "Incident acceptable match:",
            result["incident_match"],
        )

    passed_count = sum(
        1
        for result in results
        if result["passed"]
    )

    total_count = len(results)

    print("\n" + "=" * 70)
    print(
        f"Evaluation result: "
        f"{passed_count}/{total_count} passed"
    )
    print("=" * 70)

    if passed_count != total_count:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())