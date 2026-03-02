# Briefly Backend 🚀

An AI-powered, production-ready backend service for document parsing and intelligent text summarization. 

Briefly processes uploaded PDF documents, extracts text using robust parsing techniques, and generates both extractive (spaCy/Heap NLP) and abstractive (DistilBART) summaries. Built with FastAPI, the service is fully containerized, integrated with cloud storage, and features an automated CI/CD pipeline.

---

## 🏗️ Architecture & Tech Stack

**Core API & Backend:**
* **Framework:** FastAPI (High performance, async-ready)
* **Data Validation:** Pydantic
* **Language:** Python 3.10+

**Machine Learning & NLP:**
* **Abstractive Summarization:** Hugging Face `Transformers` (DistilBART)
* **Extractive Summarization:** spaCy + Custom Heap-based NLP
* **Document Processing:** `pdfplumber`

**Database & Storage:**
* **Relational DB:** Supabase (PostgreSQL)
* **Blob Storage:** AWS S3 (for secure PDF storage)

**DevOps & Deployment:**
* **Containerization:** Docker
* **CI/CD:** GitHub Actions
* **Hosting:** Render

---

## 📂 Project Structure

The codebase is organized using Domain-Driven Design (DDD) principles for scalability and maintainability:

```text
Briefly_Backend/
├── .github/workflows/    # CI/CD pipelines (GitHub Actions)
├── core/                 # Core configurations (Settings, Security, AWS/DB setup)
├── database/             # Database connection, ORM models, and migrations
├── ml/                   # Machine Learning models (DistilBART, spaCy pipelines)
├── routers/              # FastAPI route handlers (API endpoints)
├── schemas/              # Pydantic models for request/response validation
├── services/             # Business logic (PDF extraction, summarization logic)
├── test/                 # Pytest test suites
├── venv/                 # Virtual environment (Local)
├── .dockerignore         # Docker context exclusions
├── .env                  # Environment variables (Not committed)
├── .gitignore            # Git exclusions
├── Dockerfile            # Instructions to build the Docker image
├── main.py               # FastAPI application entry point
└── requirements.txt      # Python dependencies