import os
from dotenv import load_dotenv

load_dotenv()

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" # PATCH WINDOWS shm.dll

try:
    import torch
except Exception as e:
    print(f"Warning: PyTorch tidak dapat dimuat: {e}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_upload, routes_documents, routes_extract

app = FastAPI(
    title="Document OCR System API",
    description="API lokal untuk digitalisasi dokumen menggunakan PaddleOCR",
    version="1.0.0"
)

# Konfigurasi CORS agar frontend Vercel, Ngrok, maupun lokal bisa akses API
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.ngrok-free\.app|http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mendaftarkan router dari folder api/
app.include_router(routes_upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(routes_extract.router, prefix="/api/extract", tags=["Extract"])
app.include_router(routes_documents.router, prefix="/api/documents", tags=["Documents"])

from fastapi.staticfiles import StaticFiles
from app.config import UPLOAD_DIR

# Serve static upload files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

@app.get("/")
def read_root():
    return {"message": "Document OCR System API is running."}
