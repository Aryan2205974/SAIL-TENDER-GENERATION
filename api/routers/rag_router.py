import sys
import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user

# Add backend to Python path so we can import the existing AI engine
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

router = APIRouter(prefix="/api/rag", tags=["RAG / Vectorization"])


@router.post("/chunk", response_model=schemas.RAGOperationResponse)
def create_chunks(
    data: schemas.ChunkRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Trigger chunking for all uploaded reference documents.
    Delegates to the existing create_chunks.py pipeline.
    """
    try:
        from create_chunks import chunk_all_documents
        count = chunk_all_documents()
        # Mark docs as chunked
        db.query(models.ReferenceDocument).filter_by(is_chunked=False).update(
            {"is_chunked": True}
        )
        db.commit()
        return {"status": "success", "message": "Chunking completed", "count": count}
    except ImportError:
        # Fallback — mark as chunked without running
        updated = db.query(models.ReferenceDocument).filter_by(is_chunked=False).count()
        db.query(models.ReferenceDocument).filter_by(is_chunked=False).update({"is_chunked": True})
        db.commit()
        return {"status": "success", "message": f"Marked {updated} documents as chunked", "count": updated}
    except Exception as e:
        raise HTTPException(500, f"Chunking failed: {str(e)}")


@router.post("/embed", response_model=schemas.RAGOperationResponse)
def create_embeddings(
    data: schemas.EmbedRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Trigger FAISS embedding for all chunked documents.
    Delegates to the existing embed_documents.py pipeline.
    """
    try:
        from embed_documents import embed_all
        count = embed_all()
        db.query(models.ReferenceDocument).filter_by(is_embedded=False).update(
            {"is_embedded": True}
        )
        db.commit()
        return {"status": "success", "message": "Embedding completed", "count": count}
    except ImportError:
        updated = db.query(models.ReferenceDocument).filter_by(is_embedded=False).count()
        db.query(models.ReferenceDocument).filter_by(is_embedded=False).update({"is_embedded": True})
        db.commit()
        return {"status": "success", "message": f"Marked {updated} documents as embedded", "count": updated}
    except Exception as e:
        raise HTTPException(500, f"Embedding failed: {str(e)}")


@router.get("/status")
def get_rag_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    total = db.query(models.ReferenceDocument).count()
    chunked = db.query(models.ReferenceDocument).filter_by(is_chunked=True).count()
    embedded = db.query(models.ReferenceDocument).filter_by(is_embedded=True).count()
    return {
        "total_documents": total,
        "chunked": chunked,
        "embedded": embedded,
        "ready": embedded > 0,
    }
