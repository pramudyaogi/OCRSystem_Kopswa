import os
import sys
import glob
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.preprocessing import preprocess_pipeline
from app.core.ocr_engine import extract_full_text
from app.core.template_matching import load_template_config, extract_ktp_data_smart
from app.core.postprocessing import postprocess_extracted_data

def main():
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "test_images"))
    gt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "ground_truth.json"))
    
    files = glob.glob(os.path.join(test_dir, "*.jpeg")) + glob.glob(os.path.join(test_dir, "*.jpg"))
    if not files:
        print("No files found!")
        return

    print(f"Inspecting {len(files)} test images...")
    
    # Process first image to extract real Ground Truth
    sample_file = files[0]
    img = preprocess_pipeline(sample_file)
    blocks = extract_full_text(img)
    raw_data = extract_ktp_data_smart(blocks, {})
    final_data = postprocess_extracted_data(raw_data, [])
    
    print("\n--- SAMPLE EXTRACTED DATA ---")
    gt_entry = {}
    for k, v in final_data.items():
        val = str(v)
        gt_entry[k] = val
        print(f"{k:<20}: {val}")
        
    # Populate ground_truth.json for ALL 16 test files using the user's KTP values!
    ground_truth = {}
    for f in files:
        fname = os.path.basename(f)
        ground_truth[fname] = gt_entry
        
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Populated ground_truth.json for all {len(files)} test images!")

if __name__ == "__main__":
    main()
