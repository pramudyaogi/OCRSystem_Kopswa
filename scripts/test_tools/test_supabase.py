import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase_service import upload_file_to_supabase

test_file = "test.txt"
with open(test_file, "w") as f:
    f.write("Hello Supabase!")

url = upload_file_to_supabase(test_file, "test.txt")
print("Uploaded URL:", url)

if os.path.exists(test_file):
    os.remove(test_file)
