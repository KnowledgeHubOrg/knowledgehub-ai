# KnowledgeHub AI

A modern, production-ready Knowledge Hub platform powered by Retrieval-Augmented Generation (RAG), FastAPI, PostgreSQL, and Ollama LLMs. Designed for secure document management, semantic search, and intelligent Q&A over enterprise knowledge.

## Features

- **User Authentication:** JWT-based login, registration, password reset, and admin controls.
- **Document Upload & Ingestion:** Supports PDF, DOCX, TXT. Async file handling, semantic chunking, and vector embedding.
- **Domain Management:** Organize documents by domain (HR, Tech, etc.), upload by domain name.
- **RAG Pipeline:**
  - Vector search with pgvector
  - LLM-based reranking (Ollama, Gemma, Llama3, etc.)
  - Context optimization and safe prompt engineering
  - Citations and hallucination guard
- **Semantic Chunking:** Uses LangChain for sentence/paragraph-aware chunking.
- **Embeddings:** Uses dedicated embedding models (nomic-embed-text, etc.)
- **Admin Controls:** Only admins can upload documents, manage domains.
- **Logging:** Audit logs for uploads, LLM responses, and system actions.
- **Dockerized:** Full Docker Compose setup for web, database, Ollama, Redis, pgAdmin.
- **Database:** PostgreSQL with pgvector extension for vector search.
- **API:** FastAPI async endpoints for document upload, search, and Q&A.
- **Sample Data:** Includes sample HR and Tech policy files for testing.

## Tech Stack

- **Backend:** FastAPI (async), SQLAlchemy (async)
- **Database:** PostgreSQL + pgvector
- **Vector Search:** pgvector
- **LLM:** Ollama (Gemma, Llama3, Mistral, etc.)
- **Embeddings:** nomic-embed-text, Hugging Face models
- **Chunking:** LangChain
- **Auth:** JWT, passlib
- **Logging:** loguru, Python logging
- **Containerization:** Docker, docker-compose
- **Admin UI:** pgAdmin

## Main Functionalities

- Secure user authentication and admin management
- Upload and ingest documents by domain name
- Semantic chunking and vector embedding
- RAG pipeline for intelligent Q&A with citations
- LLM-based reranking and answer generation
- Context window management and prompt safety
- Audit logging and error handling
- Sample document ingestion for quick testing

## Getting Started

1. Clone the repo and set up `.env` with your config.
2. Run `docker-compose up -d` to start all services.
3. Access FastAPI endpoints for document upload, search, and Q&A.
4. Use sample files in `sample_docs/` for testing.

## API Endpoints

- `/auth/login` - User login
- `/auth/register` - User registration
- `/auth/reset-password` - Password reset
- `/documents/upload` - Upload document (by domain name)
- `/questions/ask` - Ask a question (RAG pipeline)
- `/domains/` - List domains

## License

MIT

---

For more details, see the source code and comments. Contributions welcome!