import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.db_models import DocumentRecord
from app.core.supabase_service import upload_file_to_supabase
from app.config import UPLOAD_DIR

def migrate_all_to_supabase():
    db = SessionLocal()
    docs = db.query(DocumentRecord).all()
    print(f"Migrating {len(docs)} documents to Supabase Storage...")

    count = 0
    for doc in docs:
        changed = False

        # 1. Upload original filename if not yet a full URL
        if doc.filename and not doc.filename.startswith("http"):
            local_path = os.path.join(UPLOAD_DIR, doc.filename)
            if os.path.exists(local_path):
                dest_path = f"uploads/{doc.filename}"
                supa_url = upload_file_to_supabase(local_path, dest_path)
                if supa_url:
                    doc.filename = supa_url
                    changed = True

        # 2. Upload thumbnail_path if not yet a full URL
        if doc.thumbnail_path and not doc.thumbnail_path.startswith("http"):
            clean_thumb = doc.thumbnail_path.replace("thumbnails/", "").replace("/thumbnails/", "")
            local_thumb_path = os.path.join(UPLOAD_DIR, "thumbnails", clean_thumb)
            if os.path.exists(local_thumb_path):
                dest_thumb_path = f"thumbnails/{clean_thumb}"
                supa_thumb_url = upload_file_to_supabase(local_thumb_path, dest_thumb_path)
                if supa_thumb_url:
                    doc.thumbnail_path = supa_thumb_url
                    changed = True

        if changed:
            db.commit()
            count += 1
            print(f"OK: Document ID {doc.id} successfully synced to Supabase CDN.")

    print(f"All {count} documents migrated to Supabase Storage successfully!")
    db.close()

if __name__ == "__main__":
    migrate_all_to_supabase()
