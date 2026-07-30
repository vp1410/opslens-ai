# OpsLens AI

OpsLens AI is a GenAI-powered engineering incident investigation assistant built to demonstrate **Retrieval-Augmented Generation (RAG)** and the **Model Context Protocol (MCP)**.

The application searches synthetic engineering runbooks and historical incidents before generating an evidence-grounded troubleshooting response.

## Features

- RAG-based engineering runbook search
- Semantic retrieval using ChromaDB
- Semantic historical incident search
- MCP server and client integration
- MCP tool discovery and invocation
- Retrieval-distance relevance filtering
- Evidence-grounded LLM responses
- Source citations
- Unsupported-question detection
- Retrieval evaluation suite
- Streamlit-based portfolio interface

## Application Screenshots

### Landing Page

<img
  src="docs/screenshots/Landing-page.png"
  alt="OpsLens AI landing page"
  width="100%"
/>

### Incident Investigation

<img
  src="docs/screenshots/Airflow-incident-investigation.png"
  alt="OpsLens AI incident investigation results"
  width="100%"
/>

### Generated Incident Response

<img
  src="docs/screenshots/Airflow-incident-response.png"
  alt="Generated evidence-grounded incident response"
  width="100%"
/>

### Similar Historical Incident

<img
  src="docs/screenshots/Airflow-Historical-incident.png"
  alt="Retrieved similar historical incident"
  width="100%"
/>

### Unsupported Incident Handling

<img
  src="docs/screenshots/Unsupported-Incident.png"
  alt="Unsupported incident handling"
  width="100%"
/>

## Architecture

```text
User
  |
  v
Streamlit UI
  |
  v
Incident Analyzer / MCP Client
  |
  v
MCP Server
  |----------------------------|
  v                            v
search_runbooks          search_incidents
  |                            |
  v                            v
Runbook ChromaDB         Incident ChromaDB
  |                            |
  |--------- Retrieved Evidence|
                |
                v
         Prompt Augmentation
                |
                v
            OpenAI LLM
                |
                v
     Grounded Incident Analysis
```

## How RAG Works

1. Engineering runbooks are loaded from Markdown files.
2. Each runbook is divided into overlapping chunks.
3. ChromaDB creates and stores embeddings for those chunks.
4. The user’s incident description is converted into an embedding.
5. ChromaDB retrieves semantically similar runbook chunks.
6. Weak matches are removed using a retrieval-distance threshold.
7. Relevant historical incidents are retrieved through semantic search.
8. The retrieved evidence is added to the LLM prompt.
9. The language model generates an evidence-grounded investigation.

RAG helps reduce hallucinations because the model is instructed to answer using retrieved project-specific evidence instead of relying only on general model knowledge.

## How MCP Is Used

OpsLens AI runs a local MCP server that exposes the following tools:

- `search_runbooks`
- `search_incidents`
- `read_runbook`

The application acts as an MCP client. It:

1. Starts the MCP server.
2. Initializes an MCP session.
3. Discovers available tools.
4. Calls the retrieval tools using structured arguments.
5. Receives structured evidence.
6. Passes that evidence to the language model.

MCP does not replace RAG.

- **RAG** retrieves relevant knowledge and grounds the model response.
- **MCP** standardizes how the application accesses tools and external data sources.

## Technology Stack

- Python 3.12
- Streamlit
- Model Context Protocol Python SDK
- ChromaDB
- Local embedding model
- OpenAI Responses API
- python-dotenv
- Git and GitHub

## Project Structure

```text
opslens-ai/
├── app.py
├── config.py
├── evaluation.py
├── incident_analyzer.py
├── incident_retrieval.py
├── llm_service.py
├── mcp_client.py
├── mcp_server.py
├── rag.py
├── requirements.txt
├── README.md
├── docs/
│   └── screenshots/
│       ├── Airflow-Historical-incident.png
│       ├── Airflow-incident-investigation.png
│       ├── Airflow-incident-response.png
│       ├── Landing-page.png
│       └── Unsupported-Incident.png
└── data/
    ├── incidents.json
    └── runbooks/
        ├── airflow_failures.md
        ├── api_timeouts.md
        └── database_errors.md
```

# Local Setup

## Prerequisites

Install the following before running the project:

- Python 3.10 or newer
- Git
- An OpenAI API key
- A terminal
- A modern web browser

Check your Python version:

```bash
python3 --version
```

## 1. Clone the repository

```bash
git clone https://github.com/vp1410/opslens-ai.git
cd opslens-ai
```

## 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

After activation, your terminal should show:

```text
(.venv)
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Configure environment variables

Create a `.env` file in the project root:

```bash
touch .env
```

Add:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5-mini
```

Do not commit `.env` to GitHub.

The repository’s `.gitignore` should contain:

```gitignore
.env
.venv/
__pycache__/
*.pyc
chroma_db/
.DS_Store
.streamlit/
```

## 5. Build and test the retrieval indexes

Run the runbook retrieval test:

```bash
python rag.py
```

Run the historical incident retrieval test:

```bash
python incident_retrieval.py
```

These commands create local ChromaDB collections inside:

```text
chroma_db/
```

The directory is generated locally and is not committed to Git.

## 6. Validate the MCP server

```bash
python -c "import mcp_server; print('MCP server valid')"
```

Expected output:

```text
MCP server valid
```

## 7. Test the MCP client

```bash
python mcp_client.py
```

This verifies:

- MCP server startup
- session initialization
- tool discovery
- tool invocation
- structured tool responses

## 8. Test the complete workflow

```bash
python incident_analyzer.py
```

This runs the full pipeline:

```text
Incident
  ↓
MCP tools
  ↓
Semantic retrieval
  ↓
Prompt augmentation
  ↓
OpenAI generation
```

## 9. Run the evaluation suite

```bash
python evaluation.py
```

Expected result:

```text
Evaluation result: 4/4 passed
```

The evaluation currently tests:

- Airflow duplicate-retry retrieval
- API-timeout retrieval
- duplicate-source-file retrieval
- unsupported Kubernetes incident rejection

## 10. Start the Streamlit application

```bash
python -m streamlit run app.py
```

The application should open in your browser at:

```text
http://localhost:8501
```

# Example Incidents

## Airflow Duplicate-Key Failure

```text
The Airflow campaign-data pipeline partially loaded records before failing.
After its automatic retry, it now receives a duplicate-key error.
```

Expected behavior:

- retrieves `airflow_failures.md`
- may retrieve `database_errors.md`
- retrieves `INC-1001`
- discusses idempotency, partial inserts, UPSERT, and safe retry behavior

## API Timeout

```text
The reporting API returns HTTP 504 errors during high traffic.
Database requests are slow and the application connection pool appears exhausted.
```

Expected behavior:

- retrieves `api_timeouts.md`
- retrieves `INC-1002`
- discusses downstream latency, database performance, tracing, and connection-pool usage

## Duplicate Source File

```text
The ingestion service processed the same source file twice and created duplicate rows.
```

Expected behavior:

- retrieves `INC-1003`
- discusses processed-file tracking, checksums, and deduplication

## Unsupported Kubernetes Incident

```text
A Kubernetes pod cannot be scheduled because every node reports insufficient memory.
```

Expected behavior:

- no runbook evidence should pass the relevance threshold
- no unrelated historical incident should be used
- the model should return an insufficient-evidence response
- the model should not invent unsupported Kubernetes commands

# Retrieval Relevance Filtering

Vector databases always return nearest neighbors, even when the available results are poor matches.

OpsLens AI applies distance thresholds before sending retrieved content to the language model.

Current thresholds:

```text
Runbook maximum distance: 0.95
Historical incident maximum distance: 1.25
```

Results above these thresholds are discarded.

These values were tested against both supported and unsupported incident examples.

## Safety and Reliability

The project includes:

- synthetic knowledge-base content only
- API keys stored outside source control
- path-traversal protection for runbook access
- retrieval relevance thresholds
- explicit insufficient-evidence behavior
- separation of evidence and hypotheses
- no automatic execution of generated commands
- no destructive production actions without review
- user-friendly API and application error handling

## Current Limitations

- Small synthetic knowledge base
- Local embedding model
- MCP server runs through stdio
- MCP server is started for each analysis request
- Limited number of historical incidents
- No authentication or user accounts
- No direct access to real logs, metrics, databases, or monitoring tools
- Generated recommendations still require human review
- Response latency may be noticeable during local execution

## Future Improvements

- Persistent Streamable HTTP MCP server
- response streaming
- faster model configuration
- concurrent MCP tool calls
- hybrid keyword and vector retrieval
- retrieval reranking
- automated RAG quality metrics
- LangGraph workflow orchestration
- Amazon Bedrock support
- S3-backed knowledge-base ingestion
- OpenTelemetry or CloudWatch observability
- Jira, PagerDuty, Datadog, or ServiceNow integration
- user authentication and role-based access

## Interview Summary

A concise explanation of the project:

> OpsLens AI is an MCP-powered RAG incident investigation assistant. Engineering runbooks and historical incidents are embedded and stored in ChromaDB. When a user describes an incident, the application invokes MCP tools to retrieve semantically relevant evidence. It applies relevance thresholds to remove weak matches, augments the LLM prompt with the retrieved context, and generates a cautious investigation with likely causes, diagnostic steps, sources, confidence, and limitations.

## Disclaimer

This is a portfolio prototype.

Generated recommendations must be reviewed by a qualified engineer before they are used in a production environment.