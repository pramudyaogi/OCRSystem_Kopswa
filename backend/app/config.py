import os
from pathlib import Path

# Mendapatkan path absolut dari backend/
BASE_DIR = Path(__file__).resolve().parent.parent

# Konfigurasi direktori penyimpanan (Storage)
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"

# Pastikan direktori selalu ada saat backend dijalankan
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)
