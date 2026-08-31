import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase_service import upload_file_to_supabase
from app.config import UPLOAD_DIR

def force_upload():
    print(f"Uploading files from {UPLOAD_DIR} to Supabase Storage...")
    
    # 1. Upload original files
    for fname in os.listdir(UPLOAD_DIR):
        fpath = os.path.join(UPLOAD_DIR, fname)
        if os.path.isfile(fpath):
            url = upload_file_to_supabase(fpath, f"uploads/{fname}")
            print(f"Uploaded orig {fname} -> {url}")

    # 2. Upload thumbnails
    thumb_dir = os.path.join(UPLOAD_DIR, "thumbnails")
    if os.path.exists(thumb_dir):
        for tname in os.listdir(thumb_dir):
            tpath = os.path.join(thumb_dir, tname)
            if os.path.isfile(tpath):
                turl = upload_file_to_supabase(tpath, f"thumbnails/{tname}")
                print(f"Uploaded thumb {tname} -> {turl}")

    print("Force upload complete!")

if __name__ == "__main__":
    force_upload()
