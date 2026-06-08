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
    allow_origins=["*"],
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
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "GenAI-Powered Procurement Intelligence Platform API is running"}
