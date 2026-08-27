import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.db_models import DocumentRecord
from app.core.supabase_service import insert_document_to_supabase

def migrate_db_records():
    db = SessionLocal()
    docs = db.query(DocumentRecord).all()
    print(f"Migrating {len(docs)} SQLite records to Supabase PostgreSQL table 'documents'...")

    count = 0
    for doc in docs:
        record_data = {
            "filename": doc.filename,
            "thumbnail_path": doc.thumbnail_path,
            "template_type": doc.template_type,
            "extracted_data": doc.extracted_data,
            "status": doc.status or "verified"
        }
        res = insert_document_to_supabase(record_data)
        if res:
            count += 1
            print(f"Migrated record ID {doc.id} -> Supabase DB ID {res.get('id')}")

    print(f"Successfully migrated {count}/{len(docs)} document records to Supabase PostgreSQL!")
    db.close()

if __name__ == "__main__":
    migrate_db_records()
