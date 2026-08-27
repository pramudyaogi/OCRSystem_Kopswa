from PIL import Image
import os
from pathlib import Path
from app.config import UPLOAD_DIR, THUMBNAIL_DIR

def create_thumbnail(image_path: str, max_width: int = 300, quality: int = 70) -> str:
    """
    Membuat thumbnail dari file gambar KTP/dokumen.
    - Lebar maksimum: ~300px (menjaga rasio aspek)
    - Kompresi JPEG quality: ~70% (target ukuran < 50-100KB)
    - Mengembalikan relative path thumbnail (misal: 'thumbnails/filename_thumb.jpg')
    """
    try:
        full_path = Path(image_path)
        if not full_path.is_absolute():
            full_path = UPLOAD_DIR / full_path

        if not full_path.exists():
            return None

        with Image.open(full_path) as img:
            # Konversi RGBA / Palette ke RGB jika perlu (untuk format PNG / WebP)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Hitung rasio aspek untuk resize max_width ~300px
            if img.size[0] > max_width:
                w_percent = (max_width / float(img.size[0]))
                h_size = int((float(img.size[1]) * float(w_percent)))
                img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)

            # Simpan file thumbnail di UPLOAD_DIR / thumbnails /
            thumb_filename = f"{full_path.stem}_thumb.jpg"
            thumb_save_path = THUMBNAIL_DIR / thumb_filename
            
            img.save(thumb_save_path, "JPEG", quality=quality, optimize=True)
            
            # Path relatif yang dapat diakses via `/uploads/thumbnails/filename_thumb.jpg`
            return f"thumbnails/{thumb_filename}"
    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        return None
