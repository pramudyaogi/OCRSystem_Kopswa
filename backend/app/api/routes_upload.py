import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import UPLOAD_DIR

router = APIRouter()

@router.post("/")
async def upload_document(file: UploadFile = File(...)):
    """
    Menerima file dokumen dari frontend dan menyimpannya ke storage/uploads/.
    Digenerate UUID agar nama file unik dan tidak tertimpa.
    """
    # Validasi tipe file (MIME type & Ekstensi)
    allowed_mimes = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/pjpeg", "application/pdf", "application/octet-stream"]
    allowed_exts = [".jpg", ".jpeg", ".png", ".webp", ".pdf"]

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file.content_type not in allowed_mimes and file_ext not in allowed_exts:
        raise HTTPException(
            status_code=400, 
            detail="Tipe file tidak didukung. Harap upload gambar (JPEG/PNG/WEBP) atau PDF."
        )

    # Generate nama unik menggunakan UUID
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Menyimpan file fisik secara lokal
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan file: {str(e)}")
    finally:
        file.file.close()

    return {
        "status": "success",
        "message": "File berhasil diupload",
        "filename": unique_filename,
        "original_filename": file.filename
    }
