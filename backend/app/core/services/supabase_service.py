import os
import logging
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qeuviylbnrjtmyuomzrr.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFldXZpeWxibnJqdG15dW9tenJyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3OTU2MTksImV4cCI6MjEwMzM3MTYxOX0.EmcDsm4ZiNd5wnKNpx6F_bRSAaTvVE3kCgkq9ZYABl8")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "ktp-documents")


supabase_client: Client = None

try:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logging.error(f"Failed to initialize Supabase client: {e}")


def upload_file_to_supabase(file_path: str, destination_path: str) -> str:
    """
    Uploads a local file to Supabase Storage bucket 'ktp-documents'
    and returns its public CDN URL.
    """
    if not os.path.exists(file_path) or not supabase_client:
        return ""

    try:
        content_type = "image/jpeg"
        if file_path.lower().endswith(".png"):
            content_type = "image/png"
        elif file_path.lower().endswith(".webp"):
            content_type = "image/webp"
        elif file_path.lower().endswith(".pdf"):
            content_type = "application/pdf"

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        clean_dest = destination_path.lstrip("/")

        supabase_client.storage.from_(BUCKET_NAME).upload(
            file=file_bytes,
            path=clean_dest,
            file_options={"content-type": content_type, "x-upsert": "true"}
        )

        return supabase_client.storage.from_(BUCKET_NAME).get_public_url(clean_dest)
    except Exception as e:
        logging.error(f"Error uploading {file_path} to Supabase: {e}")
        try:
            return supabase_client.storage.from_(BUCKET_NAME).get_public_url(destination_path.lstrip("/"))
        except Exception:
            return ""


def insert_document_to_supabase(doc_data: dict) -> dict:
    """
    Inserts a new document record into Supabase PostgreSQL 'ktp_documents' or 'documents' table.
    """
    if not supabase_client:
        return None
    for tbl in ["ktp_documents", "documents"]:
        try:
            res = supabase_client.table(tbl).insert(doc_data).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logging.error(f"Error inserting document to Supabase DB ({tbl}): {e}")
    return None


def fetch_documents_from_supabase(page: int = 1, limit: int = 6) -> dict:
    """
    Fetches paginated document records from Supabase PostgreSQL table.
    """
    if not supabase_client:
        return {"items": [], "total": 0, "page": page, "pages": 1, "has_next": False, "has_prev": False}
    for tbl in ["ktp_documents", "documents"]:
        try:
            if limit <= 0:
                res = supabase_client.table(tbl).select("*", count="exact").order("created_at", desc=True).execute()
                items = res.data or []
                total = res.count if res.count is not None else len(items)
                return {
                    "items": items,
                    "total": total,
                    "page": 1,
                    "pages": 1,
                    "has_next": False,
                    "has_prev": False
                }

            offset = (page - 1) * limit
            res = supabase_client.table(tbl).select("*", count="exact").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            items = res.data or []
            total = res.count if res.count is not None else len(items)
            pages = (total + limit - 1) // limit if total > 0 else 1
            return {
                "items": items,
                "total": total,
                "page": page,
                "pages": pages,
                "has_next": page < pages,
                "has_prev": page > 1
            }
        except Exception as e:
            logging.error(f"Error fetching documents from Supabase DB ({tbl}): {e}")
    return {"items": [], "total": 0, "page": page, "pages": 1, "has_next": False, "has_prev": False}


def fetch_documents_by_ids_from_supabase(doc_ids: list) -> list:
    """
    Fetches documents by ID list from Supabase PostgreSQL table.
    """
    if not supabase_client or not doc_ids:
        return []
    for tbl in ["ktp_documents", "documents"]:
        try:
            res = supabase_client.table(tbl).select("*").in_("id", doc_ids).execute()
            if res.data is not None:
                return res.data
        except Exception as e:
            logging.error(f"Error fetching documents by ids from Supabase DB ({tbl}): {e}")
    return []


def update_document_in_supabase(doc_id: int, update_data: dict) -> bool:
    """
    Updates document by ID in Supabase PostgreSQL table.
    """
    if not supabase_client:
        return False
    for tbl in ["ktp_documents", "documents"]:
        try:
            res = supabase_client.table(tbl).update(update_data).eq("id", doc_id).execute()
            if res.data:
                return True
        except Exception as e:
            logging.error(f"Error updating document {doc_id} in Supabase DB ({tbl}): {e}")
    return False


def update_status_kirim_in_supabase(doc_ids: list, status_kirim: str = "Terkirim") -> bool:
    """
    Updates status_kirim for a list of document IDs in Supabase PostgreSQL table.
    """
    if not supabase_client or not doc_ids:
        return False
    for tbl in ["ktp_documents", "documents"]:
        try:
            res = supabase_client.table(tbl).update({"status_kirim": status_kirim}).in_("id", doc_ids).execute()
            if res.data:
                return True
        except Exception as e:
            logging.error(f"Error updating status_kirim in Supabase DB ({tbl}): {e}")
    return False


def delete_documents_from_supabase(doc_ids: list) -> bool:
    """
    Deletes documents by ID list from Supabase PostgreSQL table.
    """
    if not supabase_client or not doc_ids:
        return False
    for tbl in ["ktp_documents", "documents"]:
        try:
            res = supabase_client.table(tbl).delete().in_("id", doc_ids).execute()
            if res.data is not None:
                return True
        except Exception as e:
            logging.error(f"Error deleting documents from Supabase DB ({tbl}): {e}")
    return False

