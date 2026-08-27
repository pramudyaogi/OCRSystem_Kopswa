from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List

from app.db.database import get_db, engine, Base
from app.models.db_models import DocumentRecord
from app.core.email_service import send_documents_via_email
from app.core.thumbnail_service import create_thumbnail

Base.metadata.create_all(bind=engine)

router = APIRouter()

class DocumentSaveRequest(BaseModel):
    filename: str
    template_type: str
    extracted_data: Dict[str, Any]

class DocumentUpdateRequest(BaseModel):
    extracted_data: Dict[str, Any]

class BulkDeleteRequest(BaseModel):
    ids: List[int]

class SendEmailRequest(BaseModel):
    doc_ids: List[int]
    target_email: str

@router.post("/send-email")
@router.post("/send-email/")
def send_documents_email(request: SendEmailRequest, db: Session = Depends(get_db)):
    """
    Endpoint untuk mengirim data dokumen (tunggal / massal) ke alamat email penerima.
    Melampirkan Laporan PDF + Foto KTP Fisik. Update status_kirim menjadi 'Terkirim'.
    """
    if not request.doc_ids:
        raise HTTPException(status_code=400, detail="Tidak ada dokumen yang dipilih")
    
    docs = db.query(DocumentRecord).filter(DocumentRecord.id.in_(request.doc_ids)).all()
    if not docs:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
        
    target_email = request.target_email.strip()
    if not target_email or "@" not in target_email:
        raise HTTPException(status_code=400, detail="Alamat email tidak valid")

    success, msg = send_documents_via_email(target_email, docs)
    if not success:
        raise HTTPException(status_code=500, detail=msg)

    # Update status_kirim ke 'Terkirim'
    try:
        for doc in docs:
            doc.status_kirim = "Terkirim"
        db.commit()
    except Exception as e:
        print(f"Error updating status_kirim: {e}")

    return {
        "status": "success",
        "message": f"Berhasil mengirim {len(docs)} dokumen ke {target_email}",
        "sent_count": len(docs)
    }

@router.post("/save")
def save_document_result(request: DocumentSaveRequest, db: Session = Depends(get_db)):
    """
    Endpoint untuk menyimpan data final ke dalam database SQLite.
    Juga membuat thumbnail (~300px, quality ~70%) secara otomatis.
    """
    try:
        # Generate thumbnail untuk foto KTP
        thumb_path = create_thumbnail(request.filename)

        new_doc = DocumentRecord(
            filename=request.filename,
            thumbnail_path=thumb_path,
            template_type=request.template_type,
            extracted_data=request.extracted_data,
            status="verified"
        )
        
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        return {
            "status": "success", 
            "message": "Data berhasil disimpan secara lokal.", 
            "id": new_doc.id,
            "thumbnail_path": thumb_path
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-multiple")
def delete_multiple_documents(request: BulkDeleteRequest, db: Session = Depends(get_db)):
    """
    Endpoint untuk menghapus banyak dokumen sekaligus.
    """
    try:
        db.query(DocumentRecord).filter(DocumentRecord.id.in_(request.ids)).delete(synchronize_session=False)
        db.commit()
        return {"status": "success", "message": f"{len(request.ids)} dokumen berhasil dihapus."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def get_all_documents(
    page: int = 1, 
    limit: int = 6, 
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk mengambil seluruh histori data OCR dari Database (mendukung Pagination).
    - page: Halaman ke-N (default 1)
    - limit: Jumlah item per halaman (default 6). Jika <= 0 mengembalikan seluruh data.
    """
    query = db.query(DocumentRecord).order_by(DocumentRecord.created_at.desc())
    total = query.count()
    
    if limit <= 0:
        return query.all()
        
    offset = (page - 1) * limit
    docs = query.offset(offset).limit(limit).all()
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return {
        "items": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "thumbnail_path": doc.thumbnail_path,
                "template_type": doc.template_type,
                "extracted_data": doc.extracted_data,
                "status": doc.status,
                "status_kirim": doc.status_kirim,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }
            for doc in docs
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }

@router.put("/{doc_id}")
def update_document(doc_id: int, request: DocumentUpdateRequest, db: Session = Depends(get_db)):
    """
    Endpoint untuk memperbarui data dokumen tersimpan berdasarkan ID.
    """
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    
    try:
        doc.extracted_data = request.extracted_data
        db.commit()
        db.refresh(doc)
        return {"status": "success", "message": "Data berhasil diperbarui."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Endpoint untuk menghapus satu dokumen berdasarkan ID.
    """
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    
    try:
        db.delete(doc)
        db.commit()
        return {"status": "success", "message": "Dokumen berhasil dihapus."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
