# OpsLens AI

OpsLens AI is a GenAI-powered engineering incident investigation assistant
built to demonstrate Retrieval-Augmented Generation and the Model Context
Protocol.

The application searches synthetic engineering runbooks and historical
incidents before generating an evidence-grounded troubleshooting response.

## Features

- RAG-based engineering runbook search
- Semantic retrieval with ChromaDB
- Historical incident similarity search
- MCP server and client integration
- MCP tool discovery and invocation
- Retrieval-distance relevance filtering
- Grounded LLM responses with citations
- Unsupported-question detection
- Retrieval evaluation suite
- Streamlit portfolio interface

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
  |-----------------------|
  v                       v
search_runbooks       search_incidents
  |                       |
  v                       v
ChromaDB               ChromaDB
  |                       |
  |-------- Evidence -----|
              |
              v
       Prompt Augmentation
              |
              v
        OpenAI LLM
              |
              v
 Grounded Incident Analysis

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
  alt="Insufficient-evidence handling for an unsupported incident"
  width="100%"
/>