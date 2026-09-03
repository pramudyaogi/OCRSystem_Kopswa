"""Test extraction on ground truth KTP sample."""
import os, sys, paddle
paddle.set_flags({"FLAGS_use_mkldnn": False})
from app.core.preprocessing.preprocessing import preprocess_pipeline
from app.core.ocr.ocr_engine import extract_full_text
from app.core.matching.template_matching import extract_ktp_data_smart, load_template_config
from app.core.matching.postprocessing import postprocess_extracted_data

upload_dir = "storage/uploads"
files = sorted(
    [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) if f.lower().endswith(('.jpg','.jpeg','.png'))],
    key=os.path.getmtime, reverse=True
)
img_path = "storage/uploads/bc0aff3b-3257-4f30-9d07-04e454bd47c7.jpeg"
print(f"Testing File: {img_path}\n")

img = preprocess_pipeline(img_path)
blocks = extract_full_text(img)
tpl = load_template_config("app/templates_config/ktp_template.json")
raw = extract_ktp_data_smart(blocks, tpl)
final = postprocess_extracted_data(raw, tpl.get("fields", []))

print("=== RAW EXTRACTION ===")
for k, v in raw.items():
    print(f"  {k:20s}: {v}")

print("\n=== FINAL VERIFIED KTP EXTRACTION ===")
for k, v in final.items():
    val = v.get('value', '')
    sys.stdout.buffer.write(f"{k:20s}: {val}\n".encode('utf-8'))
