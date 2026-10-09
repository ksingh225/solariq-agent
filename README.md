# SolarIQ — Real-Time Solar Energy Intelligence Agent



## Overview



SolarIQ is a proof of concept exploring the evolution from Retrieval-Augmented Generation (RAG) to real-time AI agent-based decision support for solar energy operations.



The project is being developed incrementally, with an emphasis on evidence-based recommendations, explainability, testing, and production-oriented engineering practices.



## Week 1 — RAG Retrieval Foundation



The first milestone implements a knowledge retrieval pipeline for solar photovoltaic systems.



### Implemented Components



- **Document ingestion:** Extracts text from TXT and PDF documents.

- **Chunking:** Splits documents into paragraph-aware chunks while preserving source metadata.

- **Embeddings:** Uses Sentence Transformers with the `all-MiniLM-L6-v2` model to generate 384-dimensional embeddings.

- **Vector database:** Uses a local Qdrant collection named `solariq_knowledge`.

- **Semantic retrieval:** Retrieves relevant knowledge passages based on query embeddings.

- **API layer:** Uses FastAPI to expose health and retrieval endpoints.



### API Endpoints



| Method | Endpoint | Purpose |

|---|---|---|

| GET | `/health` | Checks service health |

| POST | `/rag/query` | Retrieves relevant knowledge passages |



Example request:



```json

{

&#x20; "query": "What factors can reduce solar generation?",

&#x20; "top\_k": 3

}

```



The retrieval response includes relevant text passages, source metadata, page information, and similarity scores.



### Testing



The current unit test suite covers:



- Document ingestion

- Paragraph-aware chunking

- Embedding dimensions

- Retriever behavior

- Qdrant vector storage



**Current validation:** All five unit tests passed in the local development environment. The health endpoint and semantic retrieval API have also been tested successfully.



## Technology Stack



- Python 3.13

- FastAPI and Uvicorn

- Sentence Transformers

- Qdrant

- PyMuPDF

- Pytest



## Planned Roadmap



- **Week 2 — Real-Time Data:** Integrate solar irradiance and weather data from public APIs.

- **Week 3 — Agentic Decision Support:** Introduce an AI agent that combines retrieved knowledge, live data, and deterministic analytics.

- **Week 4 — Production-Oriented Engineering:** Add evaluation, observability, guardrails, integration tests, and deployment preparation.



## Design Principles



- Separate retrieved evidence, measured observations, calculated values, and inferred conclusions.

- Use deterministic calculations where appropriate rather than delegating all logic to an LLM.

- Preserve source information to support traceability.

- Apply suitable human oversight to operationally risky recommendations.



## Current Status



Week 1 retrieval foundation implemented and locally validated. Real-time data integration and the agent layer are planned milestones, not yet implemented.



