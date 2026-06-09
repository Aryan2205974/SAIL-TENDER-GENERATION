import os
from dotenv import load_dotenv

# Load environment variables from the project root .env file
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, ".env"))

os.environ["HF_HUB_OFFLINE"] = os.getenv("HF_HUB_OFFLINE", "1")
os.environ["TRANSFORMERS_OFFLINE"] = os.getenv("TRANSFORMERS_OFFLINE", "1")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from seed import seed_all
from routers import (
    auth_router, requirements_router, reference_router, rag_router,
    tender_router, ai_router, workflow_router, export_router,
    vendors_router, bids_router, reports_router, notifications_router
)

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GenAI-Powered Procurement Intelligence Platform API",
    version="1.0.0",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router.router)
app.include_router(requirements_router.router)
app.include_router(reference_router.router)
app.include_router(rag_router.router)
app.include_router(tender_router.router)
app.include_router(ai_router.router)
app.include_router(workflow_router.router)
app.include_router(export_router.router)
app.include_router(vendors_router.router)
app.include_router(bids_router.router)
app.include_router(reports_router.router)
app.include_router(notifications_router.router)

@app.on_event("startup")
def startup_populate_db():
    print("INFO:     FastAPI app startup: Checking database status and seeding...", flush=True)
    db = SessionLocal()
    try:
        seed_all(db)
        print("INFO:     FastAPI app startup: Database initialization completed.", flush=True)
    except Exception as e:
        print(f"ERROR:    FastAPI app startup: Database initialization failed: {e}", flush=True)
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "GenAI-Powered Procurement Intelligence Platform API is running"}
