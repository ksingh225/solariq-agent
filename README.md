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



## Implementation Roadmap

- **Week 1 — RAG Retrieval Foundation:** Implemented document ingestion, chunking, embeddings, Qdrant vector storage, semantic retrieval, and FastAPI endpoints.
- **Week 2 — Real-Time Data:** Solar data integration milestone.
- **Week 3 — Agentic Decision Support:** Implemented an AI agent with tools, structured assessments, and safety controls.
- **Week 4 — Evaluation and Reliability:** Implemented repeatable evaluation scenarios, response checks, automated tests, and evaluation reporting.

## Week 4 — Latest Validation

- **Evaluation scenarios:** 6 of 6 completed successfully.
- **Evaluation checks:** 18 of 18 passed.
- **Check pass rate:** 100% for the current evaluation run.
- **Automated tests:** 33 passed across the Week 3 agent and Week 4 evaluation test suites.
- **Evaluation report:** `week4-evaluation/evaluation_report.json`

These results apply to the scenarios and tests executed in the current development environment. They do not establish universal correctness or production readiness.

## Design Principles

- Separate retrieved evidence, measured observations, calculated values, and inferred conclusions.
- Use deterministic calculations where appropriate rather than delegating all logic to an LLM.
- Preserve source information to support traceability.
- Apply suitable human oversight to operationally risky recommendations.

## Current Status



SolarIQ has progressed from its RAG retrieval foundation to an agent-based solar intelligence proof of concept with structured assessments, safety controls, repeatable evaluation scenarios, and automated tests. Next steps include broader evaluation coverage, live API failure handling, real-world output assessment, and exploring LLM-as-a-Judge and Evidently AI.



