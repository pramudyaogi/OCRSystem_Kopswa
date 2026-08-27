import os
import sys
from pathlib import Path

# Tambahkan direktori root backend ke sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.db.database import engine, SessionLocal
from app.models.db_models import DocumentRecord
from app.core.thumbnail_service import create_thumbnail

def run_migration():
    print("=== MEMULAI MIGRASI THUMBNAIL DOKUMEN ===")
    
    # 1. Pastikan kolom thumbnail_path ada di SQLite
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE documents ADD COLUMN thumbnail_path VARCHAR;"))
            conn.commit()
            print("[+] Kolom 'thumbnail_path' berhasil ditambahkan ke tabel 'documents'.")
        except Exception as e:
            # Jika kolom sudah ada, abaikan error
            print("[-] Kolom 'thumbnail_path' sudah ada atau tidak perlu ditambahkan.")

    # 2. Query dokumen yang belum memiliki thumbnail_path
    db = SessionLocal()
    try:
        docs = db.query(DocumentRecord).all()
        print(f"[*] Total dokumen di database: {len(docs)}")
        
        migrated_count = 0
        for doc in docs:
            if not doc.thumbnail_path:
                thumb_path = create_thumbnail(doc.filename)
                if thumb_path:
                    doc.thumbnail_path = thumb_path
                    migrated_count += 1
                    print(f"  -> Generated thumbnail for ID {doc.id} ({doc.filename}): {thumb_path}")
        
        db.commit()
        print(f"\n[SUCCESS] Selesai! Berhasil membuat thumbnail untuk {migrated_count} dokumen lama.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Migrasi gagal: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
