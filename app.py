import asyncio
from html import escape
from typing import Any

import streamlit as st

from incident_analyzer import analyze_incident


# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------

APP_NAME = "OpsLens AI"

EXAMPLE_INCIDENTS = {
    "Airflow duplicate records": (
        "The Airflow campaign-data pipeline failed after partially loading "
        "records. Airflow retried the task, but the retry now fails with a "
        "duplicate-key error because some rows already exist."
    ),
    "Reporting API timeout": (
        "The reporting API returns HTTP 504 errors during high traffic. "
        "Database requests are slow and the application connection pool "
        "appears to be exhausted."
    ),
    "Duplicate file processing": (
        "The file-ingestion service processed the same source file twice, "
        "causing duplicate rows to appear in the destination table."
    ),
    "Unsupported Kubernetes incident": (
        "A Kubernetes pod cannot be scheduled because every node reports "
        "insufficient memory."
    ),
}


# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------------------------------------------------------
# Custom styling
# -------------------------------------------------------------------

st.markdown(
    """
    <style>
        .stApp {
            background-color: #f7f9fc;
        }

        .block-container {
            max-width: 1280px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        .hero {
            background:
                linear-gradient(
                    135deg,
                    rgba(37, 99, 235, 0.98),
                    rgba(79, 70, 229, 0.95)
                );
            border-radius: 20px;
            padding: 2rem 2.2rem;
            margin-bottom: 1.5rem;
            color: white;
            box-shadow: 0 16px 40px rgba(37, 99, 235, 0.18);
        }

        .hero-title {
            font-size: 2.2rem;
            font-weight: 750;
            margin: 0;
            letter-spacing: -0.03em;
        }

        .hero-subtitle {
            font-size: 1rem;
            margin-top: 0.65rem;
            margin-bottom: 0;
            color: rgba(255, 255, 255, 0.9);
            max-width: 820px;
            line-height: 1.6;
        }

        .section-card {
            background: white;
            border: 1px solid #e7ebf2;
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 5px 18px rgba(15, 23, 42, 0.04);
        }

        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #172033;
            margin-bottom: 0.35rem;
        }

        .section-description {
            color: #64748b;
            font-size: 0.92rem;
            line-height: 1.5;
        }

        .tool-card {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534;
            border-radius: 12px;
            padding: 0.85rem 1rem;
            font-weight: 650;
            text-align: center;
            min-height: 58px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .source-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.85rem;
        }

        .source-name {
            font-size: 1rem;
            font-weight: 700;
            color: #1e293b;
        }

        .source-meta {
            margin-top: 0.25rem;
            margin-bottom: 0.65rem;
            color: #64748b;
            font-size: 0.82rem;
        }

        .source-content {
            color: #334155;
            font-size: 0.92rem;
            line-height: 1.65;
            white-space: pre-wrap;
        }

        .incident-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #6366f1;
            border-radius: 12px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.9rem;
        }

        .incident-title {
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.45rem;
        }

        .incident-field {
            margin-top: 0.35rem;
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.5;
        }

        div[data-testid="stTextArea"] textarea {
            border-radius: 14px;
            border: 1px solid #cbd5e1;
            padding: 1rem;
            min-height: 180px;
            font-size: 0.98rem;
            background: white;
        }

        div[data-testid="stTextArea"] textarea:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
        }

        div[data-testid="stButton"] button {
            border-radius: 10px;
            font-weight: 650;
            min-height: 42px;
        }

        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 0.9rem 1rem;
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e7ebf2;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }

        .footer {
            color: #94a3b8;
            text-align: center;
            font-size: 0.8rem;
            margin-top: 3rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def run_analysis(
    incident_description: str,
) -> dict[str, Any]:
    """
    Run the asynchronous MCP + RAG workflow from Streamlit.
    """

    return asyncio.run(
        analyze_incident(incident_description)
    )


def load_example_incident(
    incident_text: str,
) -> None:
    """
    Load an example incident into the main text area.
    """

    st.session_state["incident_input"] = incident_text


def clear_analysis() -> None:
    """
    Clear the current incident and previous result.
    """

    st.session_state["incident_input"] = ""
    st.session_state["analysis_result"] = None


def get_runbook_results(
    evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Return retrieved runbook results.
    """

    return evidence.get(
        "runbook_search",
        {},
    ).get(
        "results",
        [],
    )


def get_historical_incidents(
    evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Return retrieved historical incident results.
    """

    return evidence.get(
        "incident_search",
        {},
    ).get(
        "results",
        [],
    )


def get_unique_sources(
    evidence: dict[str, Any],
) -> list[str]:
    """
    Return unique retrieved runbook filenames.
    """

    return sorted(
        {
            result.get("source", "Unknown source")
            for result in get_runbook_results(evidence)
        }
    )


def render_source_card(
    result: dict[str, Any],
) -> None:
    """
    Render one retrieved runbook chunk as a styled card.
    """

    source = escape(
        str(result.get("source", "Unknown source"))
    )

    chunk_id = escape(
        str(result.get("chunk_id", "Unknown chunk"))
    )

    text = escape(
        str(result.get("text", ""))
    )

    distance = result.get("distance")

    if isinstance(distance, (int, float)):
        distance_text = f"{distance:.4f}"
    else:
        distance_text = "Not available"

    st.markdown(
        f"""
        <div class="source-card">
            <div class="source-name">{source}</div>
            <div class="source-meta">
                Chunk: {chunk_id}
                &nbsp;•&nbsp;
                Retrieval distance: {distance_text}
            </div>
            <div class="source-content">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_incident_card(
    incident: dict[str, Any],
) -> None:
    """
    Render one historical incident as a styled card.
    """

    incident_id = escape(
        str(incident.get("id", "Unknown"))
    )

    title = escape(
        str(incident.get("title", "Untitled"))
    )

    service = escape(
        str(incident.get("service", "Unknown"))
    )

    category = escape(
        str(incident.get("category", "Unknown"))
    )

    description = escape(
        str(incident.get("description", "Not available"))
    )

    root_cause = escape(
        str(incident.get("root_cause", "Not available"))
    )

    resolution = escape(
        str(incident.get("resolution", "Not available"))
    )

    match_score = incident.get("match_score")

    match_score_html = ""

    if isinstance(match_score, (int, float)):
        match_score_html = (
            '<div class="incident-field">'
            f"<strong>Keyword match score:</strong> {match_score}"
            "</div>"
        )

    st.markdown(
        f"""
        <div class="incident-card">
            <div class="incident-title">
                {incident_id} — {title}
            </div>
            <div class="incident-field">
                <strong>Service:</strong> {service}
            </div>
            <div class="incident-field">
                <strong>Category:</strong> {category}
            </div>
            <div class="incident-field">
                <strong>Description:</strong> {description}
            </div>
            <div class="incident-field">
                <strong>Root cause:</strong> {root_cause}
            </div>
            <div class="incident-field">
                <strong>Resolution:</strong> {resolution}
            </div>
            {match_score_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------
# Session state
# -------------------------------------------------------------------

if "incident_input" not in st.session_state:
    st.session_state["incident_input"] = ""

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None


# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------

with st.sidebar:
    st.markdown("## OpsLens AI")

    st.caption(
        "A portfolio prototype demonstrating RAG, MCP, semantic retrieval, "
        "tool invocation, relevance filtering, and grounded LLM generation."
    )

    st.divider()

    st.markdown("### Architecture")

    st.code(
        """User
  ↓
Streamlit UI
  ↓
MCP Client
  ↓
MCP Server
  ↓
RAG Retrieval
  ↓
Relevance Filter
  ↓
LLM Analysis""",
        language="text",
    )

    st.divider()

    st.markdown("### Technology")

    st.markdown(
        """
        - Python
        - Streamlit
        - Model Context Protocol
        - ChromaDB
        - Local embeddings
        - OpenAI Responses API
        """
    )

    st.divider()

    st.caption(
        "All knowledge-base documents and historical incidents are synthetic."
    )


# -------------------------------------------------------------------
# Header
# -------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">OpsLens AI</div>
        <div class="hero-subtitle">
            An MCP-powered RAG assistant that searches engineering runbooks
            and historical incidents before generating an evidence-grounded
            troubleshooting plan.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------
# Input area
# -------------------------------------------------------------------

input_column, examples_column = st.columns(
    [2.2, 1],
    gap="large",
)

with input_column:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Describe the incident</div>
            <div class="section-description">
                Include the affected service, symptoms, error messages,
                retries, recent changes, and anything already investigated.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    incident_description = st.text_area(
        "Incident description",
        key="incident_input",
        label_visibility="collapsed",
        placeholder=(
            "Example: The Airflow campaign-data pipeline partially loaded "
            "records before failing. After retrying, it now returns a "
            "duplicate-key error..."
        ),
        height=210,
    )

    analyze_column, clear_column = st.columns(
        [3, 1]
    )

    with analyze_column:
        analyze_clicked = st.button(
            "Analyze Incident",
            type="primary",
            use_container_width=True,
        )

    with clear_column:
        st.button(
            "Clear",
            use_container_width=True,
            on_click=clear_analysis,
        )

with examples_column:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Example incidents</div>
            <div class="section-description">
                Load a prepared scenario to test the RAG workflow.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for title, incident_text in EXAMPLE_INCIDENTS.items():
        st.button(
            title,
            key=f"example_{title}",
            use_container_width=True,
            on_click=load_example_incident,
            args=(incident_text,),
        )


# -------------------------------------------------------------------
# Run analysis
# -------------------------------------------------------------------

if analyze_clicked:
    cleaned_incident = incident_description.strip()

    if not cleaned_incident:
        st.warning(
            "Enter an incident description before starting the analysis."
        )

    else:
        try:
            with st.spinner(
                "Calling MCP tools, retrieving evidence, "
                "applying relevance filtering, and generating analysis...",
                show_time=True,
            ):
                result = run_analysis(cleaned_incident)

            st.session_state["analysis_result"] = result

        except Exception as error:
            st.session_state["analysis_result"] = None

            st.error(
                "The incident analysis could not be completed."
            )

            st.exception(error)


# -------------------------------------------------------------------
# Results
# -------------------------------------------------------------------

result = st.session_state.get("analysis_result")

if result:
    evidence = result.get("evidence", {})

    runbook_results = get_runbook_results(evidence)
    historical_incidents = get_historical_incidents(evidence)
    tools_used = evidence.get("tools_used", [])
    unique_sources = get_unique_sources(evidence)

    runbook_search = evidence.get(
        "runbook_search",
        {},
    )

    has_relevant_evidence = runbook_search.get(
        "has_relevant_evidence",
        bool(runbook_results),
    )

    max_distance = runbook_search.get(
        "max_distance",
    )

    st.divider()

    metric_columns = st.columns(4)

    with metric_columns[0]:
        st.metric(
            "MCP tools used",
            len(tools_used),
        )

    with metric_columns[1]:
        st.metric(
            "Runbook chunks",
            len(runbook_results),
        )

    with metric_columns[2]:
        st.metric(
            "Source documents",
            len(unique_sources),
        )

    with metric_columns[3]:
        st.metric(
            "Similar incidents",
            len(historical_incidents),
        )

    st.markdown("")

    if has_relevant_evidence:
        st.success(
            "Relevant runbook evidence was found and supplied "
            "to the language model."
        )
    else:
        st.warning(
            "No sufficiently relevant runbook evidence was found. "
            "The response should identify this as an "
            "insufficient-evidence case."
        )

    analysis_tab, evidence_tab, incidents_tab, debug_tab = st.tabs(
        [
            "Investigation",
            "Runbook Evidence",
            "Historical Incidents",
            "MCP Details",
        ]
    )

    # ---------------------------------------------------------------
    # Investigation tab
    # ---------------------------------------------------------------

    with analysis_tab:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Generated investigation</div>
                <div class="section-description">
                    This response was generated only after retrieving
                    external evidence through MCP tools.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            result.get(
                "analysis",
                "No analysis was generated.",
            )
        )

        st.divider()

        st.markdown("### MCP tools invoked")

        if tools_used:
            tool_columns = st.columns(
                len(tools_used)
            )

            for column, tool_name in zip(
                tool_columns,
                tools_used,
                strict=True,
            ):
                with column:
                    st.markdown(
                        f"""
                        <div class="tool-card">
                            ✓ {escape(str(tool_name))}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No MCP tools were recorded.")

    # ---------------------------------------------------------------
    # Runbook evidence tab
    # ---------------------------------------------------------------

    with evidence_tab:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Retrieved runbook chunks</div>
                <div class="section-description">
                    These sections passed the configured vector-distance
                    threshold and were supplied to the language model.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not runbook_results:
            st.info(
                "No runbook chunks passed the relevance threshold."
            )
        else:
            for runbook_result in runbook_results:
                render_source_card(runbook_result)

    # ---------------------------------------------------------------
    # Historical incidents tab
    # ---------------------------------------------------------------

    with incidents_tab:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Similar historical incidents</div>
                <div class="section-description">
                    These synthetic incidents were returned by the
                    search_incidents MCP tool.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not historical_incidents:
            st.info(
                "No similar historical incidents were found."
            )
        else:
            for historical_incident in historical_incidents:
                render_incident_card(historical_incident)

    # ---------------------------------------------------------------
    # MCP details tab
    # ---------------------------------------------------------------

    with debug_tab:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">MCP execution details</div>
                <div class="section-description">
                    Use this section to inspect retrieval behavior,
                    tool execution, and relevance filtering.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Retrieval policy")

        policy_column, status_column = st.columns(2)

        with policy_column:
            if isinstance(max_distance, (int, float)):
                st.metric(
                    "Maximum retrieval distance",
                    f"{max_distance:.2f}",
                )
            else:
                st.metric(
                    "Maximum retrieval distance",
                    "Not reported",
                )

        with status_column:
            st.metric(
                "Relevant evidence",
                "Yes" if has_relevant_evidence else "No",
            )

        st.caption(
            "Smaller vector distances indicate stronger semantic "
            "similarity. Results exceeding the configured maximum "
            "distance are removed before generation."
        )

        st.markdown("### Tools used")

        if tools_used:
            for tool_name in tools_used:
                st.code(
                    str(tool_name),
                    language="text",
                )
        else:
            st.info("No tools were recorded.")

        st.markdown("### Raw MCP response")

        st.json(evidence)


# -------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------

st.markdown(
    """
    <div class="footer">
        OpsLens AI · RAG + MCP portfolio prototype
    </div>
    """,
    unsafe_allow_html=True,
)