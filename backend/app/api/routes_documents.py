from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import os
from datetime import datetime

from app.core.services.email_service import send_documents_via_email
from app.core.preprocessing.thumbnail_service import create_thumbnail
from app.core.services.supabase_service import (
    upload_file_to_supabase,
    insert_document_to_supabase,
    fetch_documents_from_supabase,
    fetch_documents_by_ids_from_supabase,
    update_document_in_supabase,
    update_status_kirim_in_supabase,
    delete_documents_from_supabase
)
from app.config import UPLOAD_DIR

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

class DocumentObj:
    """Helper wrapper to ensure compatibility with email_service expectations."""
    def __init__(self, data: dict):
        self.id = data.get("id")
        self.filename = data.get("filename", "")
        self.thumbnail_path = data.get("thumbnail_path")
        self.template_type = data.get("template_type", "ktp")
        self.extracted_data = data.get("extracted_data") or {}
        self.status = data.get("status", "verified")
        self.status_kirim = data.get("status_kirim", "Tersimpan")
        
        ca = data.get("created_at")
        if isinstance(ca, datetime):
            self.created_at = ca
        elif isinstance(ca, str):
            try:
                clean_ca = ca.replace("Z", "+00:00")
                self.created_at = datetime.fromisoformat(clean_ca)
            except Exception:
                self.created_at = datetime.now()
        else:
            self.created_at = datetime.now()

@router.post("/send-email")
@router.post("/send-email/")
def send_documents_email(request: SendEmailRequest):
    """
    Endpoint untuk mengirim data dokumen (tunggal / massal) ke alamat email penerima.
    Membaca data dari Supabase PostgreSQL, melampirkan Laporan PDF + Foto KTP Fisik,
    dan mengupdate status_kirim menjadi 'Terkirim'.
    """
    if not request.doc_ids:
        raise HTTPException(status_code=400, detail="Tidak ada dokumen yang dipilih")
    
    doc_dicts = fetch_documents_by_ids_from_supabase(request.doc_ids)
    if not doc_dicts:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan di Supabase DB")
        
    target_email = request.target_email.strip()
    if not target_email or "@" not in target_email:
        raise HTTPException(status_code=400, detail="Alamat email tidak valid")

    # Convert dictionaries to objects with dot-notation for email_service compatibility
    docs = [DocumentObj(d) for d in doc_dicts]

    success, msg = send_documents_via_email(target_email, docs)
    if not success:
        raise HTTPException(status_code=500, detail=msg)

    # Update status_kirim ke 'Terkirim' di Supabase PostgreSQL
    try:
        update_status_kirim_in_supabase(request.doc_ids, "Terkirim")
    except Exception as e:
        print(f"Error updating status_kirim in Supabase: {e}")

    return {
        "status": "success",
        "message": f"Berhasil mengirim {len(docs)} dokumen ke {target_email}",
        "sent_count": len(docs)
    }

@router.post("/save")
def save_document_result(request: DocumentSaveRequest):
    """
    Endpoint untuk menyimpan data final ke dalam Supabase PostgreSQL database.
    Juga membuat thumbnail (~300px, quality ~70%) dan menyinkronkan ke Supabase Storage.
    """
    try:
        # 1. Generate thumbnail lokal
        thumb_path = create_thumbnail(request.filename)

        final_filename = request.filename
        final_thumb_path = thumb_path

        # 2. Sync foto asli ke Supabase Storage jika file lokal ada
        if request.filename and not request.filename.startswith("http"):
            local_orig = os.path.join(UPLOAD_DIR, request.filename)
            if os.path.exists(local_orig):
                supa_url = upload_file_to_supabase(local_orig, f"uploads/{request.filename}")
                if supa_url:
                    final_filename = supa_url

        # 3. Sync thumbnail ke Supabase Storage jika file lokal ada
        if thumb_path and not thumb_path.startswith("http"):
            clean_thumb = thumb_path.replace("thumbnails/", "").replace("/thumbnails/", "")
            local_thumb = os.path.join(UPLOAD_DIR, "thumbnails", clean_thumb)
            if os.path.exists(local_thumb):
                supa_thumb = upload_file_to_supabase(local_thumb, f"thumbnails/{clean_thumb}")
                if supa_thumb:
                    final_thumb_path = supa_thumb

        doc_payload = {
            "filename": final_filename,
            "thumbnail_path": final_thumb_path,
            "template_type": request.template_type,
            "extracted_data": request.extracted_data,
            "status": "verified"
        }
        
        inserted_doc = insert_document_to_supabase(doc_payload)
        new_id = inserted_doc.get("id") if inserted_doc else None
        
        # Safe cleanup of local temporary files after successful upload to Supabase Storage
        try:
            if final_filename.startswith("http") and request.filename:
                local_orig_path = os.path.join(UPLOAD_DIR, request.filename)
                if os.path.exists(local_orig_path):
                    os.remove(local_orig_path)
            if final_thumb_path and final_thumb_path.startswith("http") and thumb_path:
                clean_t = thumb_path.replace("thumbnails/", "").replace("/thumbnails/", "")
                local_thumb_path = os.path.join(UPLOAD_DIR, "thumbnails", clean_t)
                if os.path.exists(local_thumb_path):
                    os.remove(local_thumb_path)
        except Exception as cleanup_err:
            print(f"Temporary file cleanup note: {cleanup_err}")

        return {
            "status": "success", 
            "message": "Data berhasil disimpan ke Supabase Cloud Storage & Database.", 
            "id": new_id,
            "filename": final_filename,
            "thumbnail_path": final_thumb_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-multiple")
def delete_multiple_documents(request: BulkDeleteRequest):
    """
    Endpoint untuk menghapus banyak dokumen sekaligus dari Supabase PostgreSQL.
    """
    try:
        success = delete_documents_from_supabase(request.ids)
        if not success:
            raise HTTPException(status_code=500, detail="Gagal menghapus dokumen dari Supabase DB")
        return {"status": "success", "message": f"{len(request.ids)} dokumen berhasil dihapus."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def get_all_documents(page: int = 1, limit: int = 6):
    """
    Endpoint untuk mengambil seluruh histori data OCR dari Supabase PostgreSQL (mendukung Pagination).
    - page: Halaman ke-N (default 1)
    - limit: Jumlah item per halaman (default 6). Jika <= 0 mengembalikan seluruh data.
    """
    result = fetch_documents_from_supabase(page=page, limit=limit)
    items = result.get("items", [])
    
    if limit <= 0:
        return [
            {
                "id": doc.get("id"),
                "filename": doc.get("filename"),
                "thumbnail_path": doc.get("thumbnail_path"),
                "template_type": doc.get("template_type"),
                "extracted_data": doc.get("extracted_data"),
                "status": doc.get("status"),
                "status_kirim": doc.get("status_kirim"),
                "created_at": doc.get("created_at")
            }
            for doc in items
        ]
        
    return {
        "items": [
            {
                "id": doc.get("id"),
                "filename": doc.get("filename"),
                "thumbnail_path": doc.get("thumbnail_path"),
                "template_type": doc.get("template_type"),
                "extracted_data": doc.get("extracted_data"),
                "status": doc.get("status"),
                "status_kirim": doc.get("status_kirim"),
                "created_at": doc.get("created_at")
            }
            for doc in items
        ],
        "total": result.get("total", 0),
        "page": page,
        "limit": limit,
        "pages": result.get("pages", 1),
        "has_next": result.get("has_next", False),
        "has_prev": result.get("has_prev", False)
    }

@router.put("/{doc_id}")
def update_document(doc_id: int, request: DocumentUpdateRequest):
    """
    Endpoint untuk memperbarui data dokumen tersimpan di Supabase PostgreSQL berdasarkan ID.
    """
    try:
        success = update_document_in_supabase(doc_id, {"extracted_data": request.extracted_data})
        if not success:
            raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan atau gagal diperbarui di Supabase DB")
        return {"status": "success", "message": "Data berhasil diperbarui."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{doc_id}")
def delete_document(doc_id: int):
    """
    Endpoint untuk menghapus satu dokumen berdasarkan ID dari Supabase PostgreSQL.
    """
    try:
        success = delete_documents_from_supabase([doc_id])
        if not success:
            raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan atau gagal dihapus dari Supabase DB")
        return {"status": "success", "message": "Dokumen berhasil dihapus."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

