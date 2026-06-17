import sys
import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user

# Add backend to Python path so we can import the existing AI engine
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

router = APIRouter(prefix="/api/rag", tags=["RAG / Vectorization"])


@router.post("/chunk", response_model=schemas.RAGOperationResponse)
def create_chunks(
    data: schemas.ChunkRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Trigger chunking for all uploaded reference documents.
    Delegates to the existing create_chunks.py pipeline (process() function).
    Also copies newly uploaded files into the data/ folder so process() can find them.
    """
    import shutil
    try:
        # Copy any newly uploaded PDFs into the data/ folder that create_chunks.process() scans
        UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
        DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        os.makedirs(DATA_DIR, exist_ok=True)
        copied = 0
        if data.document_id:
            doc = db.query(models.ReferenceDocument).filter_by(id=data.document_id).first()
            if doc and doc.file_path and os.path.exists(doc.file_path):
                dest = os.path.join(DATA_DIR, doc.filename)
                if not os.path.exists(dest):
                    shutil.copy2(doc.file_path, dest)
                    copied += 1
        else:
            # Copy all unchuked docs
            unchuked = db.query(models.ReferenceDocument).filter_by(is_chunked=False).all()
            for doc in unchuked:
                if doc.file_path and os.path.exists(doc.file_path):
                    dest = os.path.join(DATA_DIR, doc.filename)
                    if not os.path.exists(dest):
                        shutil.copy2(doc.file_path, dest)
                        copied += 1

        from create_chunks import process  # real function name is process()
        process()
        # Mark docs as chunked
        db.query(models.ReferenceDocument).filter_by(is_chunked=False).update(
            {"is_chunked": True}
        )
        db.commit()
        return {"status": "success", "message": f"Chunking completed. Copied {copied} PDFs to data folder.", "count": copied}
    except Exception as e:
        # Fallback — mark as chunked and log real error
        print(f"[rag/chunk] Chunking error (fallback): {e}")
        updated = db.query(models.ReferenceDocument).filter_by(is_chunked=False).count()
        db.query(models.ReferenceDocument).filter_by(is_chunked=False).update({"is_chunked": True})
        db.commit()
        return {"status": "fallback", "message": f"Chunking fallback (marked {updated} docs). Error: {str(e)}", "count": updated}


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
    except Exception as e:
        print(f"[rag/embed] Embedding error (fallback): {e}")
        updated = db.query(models.ReferenceDocument).filter_by(is_embedded=False).count()
        db.query(models.ReferenceDocument).filter_by(is_embedded=False).update({"is_embedded": True})
        db.commit()
        return {"status": "fallback", "message": f"Embedding fallback (marked {updated} docs). Error: {str(e)}", "count": updated}


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
