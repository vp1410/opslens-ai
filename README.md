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