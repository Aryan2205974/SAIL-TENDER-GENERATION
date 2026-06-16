# SAIL Tender Generation Platform

A GenAI-powered procurement intelligence platform designed to automatically draft tender documents (Notice Inviting Tender, Scope of Work, Technical Specifications, GCC/SCC, etc.) using a state-of-the-art Retrieval-Augmented Generation (RAG) pipeline. The pipeline retrieves clause structures and numerical specifications from reference PDFs (using OCR and text parsing) and drafts highly standardized documents.

---

## 📂 Project Structure

```
SAIL-TENDER-GENERATION/
├── api/                  # FastAPI Backend API Service
│   ├── routers/          # API endpoint routers (auth, AI, RAG, tenders, etc.)
│   ├── database.py       # SQLAlchemy engine & SQLite configuration
│   ├── main.py           # FastAPI entry point
│   ├── models.py         # SQLAlchemy models (Tenders, Sections, Users, etc.)
│   ├── schemas.py        # Pydantic validation schemas
│   └── requirements.txt  # Python package requirements for backend (Render-compatible)
│
├── backend/              # Core AI Engine & Data Processing
│   ├── config.py         # Multi-provider LLM gateway config (Gemini, Groq, NVIDIA, OpenRouter)
│   ├── create_chunks.py  # PDF text extraction & chunking pipeline (PyMuPDF & RapidOCR)
│   ├── embed_documents.py# FAISS vector database builder & metadata indexer
│   ├── retrieve.py       # RAG semantic search & neural reranker with Low-RAM fallbacks
│   └── generate_subsection.py # AI prompt builder & section generation logic
│
├── frontend/             # Next.js Frontend Dashboard App
│   ├── src/              # Next.js page layouts, components & state stores (Zustand)
│   ├── package.json      # Node dependency registry & build tasks
│   └── next.config.ts    # Static HTML export configuration (`out` directory)
│
├── vectordb/             # Vector database directory (FAISS indexes & metadata)
├── netlify.toml          # Netlify Frontend hosting configuration
└── render.yaml           # Render Backend hosting configuration
```

---

## ⚡ Deployment Compatibility

### 1. Render Compatibility (Backend API)
- The app supports a **`LOW_RAM_MODE`** (automatically enabled when deploying to Render or if RAM is constrained to 512MB). In this mode:
  - Heavy ML model loading (PyTorch, SentenceTransformers, neural rerankers) is bypassed.
  - A lightweight, pure-Python keyword-based search fallback is activated automatically, preventing the container from crashing due to Out-Of-Memory (OOM) errors.
- Dependencies (`api/requirements.txt`) are updated and clean.
- The `render.yaml` configuration is located in the root directory.

### 2. Netlify Compatibility (Frontend)
- The Next.js frontend is configured for static exports (`next.config.ts` has `output: "export"`).
- The `netlify.toml` file correctly sets build settings to direct Next.js static exports to the `out` directory and handles route redirects.

---

## 🛠️ Local Development Setup

### Backend API
1. Navigate to the `api` folder:
   ```bash
   cd api
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the API server:
   ```bash
   python -m uvicorn main:app --reload
   ```

### Frontend App
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Run the Next.js dev server:
   ```bash
   npm run dev
   ```
