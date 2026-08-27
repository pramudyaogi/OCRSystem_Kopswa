import os
import sys
import json
import glob
from difflib import SequenceMatcher

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.preprocessing import preprocess_pipeline
from app.core.ocr_engine import extract_full_text
from app.core.template_matching import load_template_config, extract_ktp_data_smart
from app.core.postprocessing import postprocess_extracted_data

def string_similarity(a: str, b: str) -> float:
    """Hitung persentase kemiripan teks (0.00 hingga 1.00)"""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    clean_a = "".join(a.upper().split())
    clean_b = "".join(b.upper().split())
    return SequenceMatcher(None, clean_a, clean_b).ratio()

def evaluate():
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_images"))
    gt_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "ground_truth.json"))

    if not os.path.exists(test_dir):
        os.makedirs(test_dir, exist_ok=True)
        
    ground_truth = {}
    if os.path.exists(gt_file):
        with open(gt_file, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

    # Ambil semua file gambar di test_images
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
    image_files = []
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(test_dir, ext)))

    print("\n" + "="*65)
    print("📊 SUITE EVALUASI AKURASI OCR KTP KOP SWA")
    print("="*65)
    print(f"📁 Folder Uji: {test_dir}")
    print(f"🖼️ Total Berkas Ditemukan: {len(image_files)}")
    print(f"📄 Ground Truth Entries: {len(ground_truth)}")
    print("="*65 + "\n")

    if not image_files:
        print("⚠️ BELUM ADA FOTO UJI DI FOLDER `backend/tests/test_images/`!")
        print("Silakan masukkan minimal 5-15 foto KTP ke folder tersebut dan isi `ground_truth.json` untuk memulai evaluasi.\n")
        return

    # Load template config KTP
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "templates_config", "ktp_template.json"))
    template_config = load_template_config(template_path) if os.path.exists(template_path) else {"fields": []}

    all_keys = [
        "provinsi", "kota", "nik", "nama", "tempat_tgl_lahir", "jenis_kelamin", 
        "gol_darah", "alamat", "rt_rw", "kel_desa", "kecamatan", "agama", 
        "status_perkawinan", "pekerjaan", "kewarganegaraan", "berlaku_hingga"
    ]
    
    field_scores = {k: [] for k in all_keys}

    for idx, img_path in enumerate(image_files, 1):
        filename = os.path.basename(img_path)
        print(f"[{idx}/{len(image_files)}] Memproses: {filename}...")
        
        gt_data = ground_truth.get(filename, {})
        if not gt_data:
            print(f"   ⚠️ Warning: File '{filename}' belum punya entry di ground_truth.json (dilewati dari perhitungan skor accuracy).")
            continue

        try:
            # 1. Pipeline Preprocessing
            processed_img = preprocess_pipeline(img_path)
            if processed_img is None:
                print(f"   ❌ Preprocessing gagal untuk '{filename}'!")
                continue

            # 2. Extract AI OCR Text
            text_blocks = extract_full_text(processed_img, use_trocr=False)

            # 3. Parsing Teks
            raw_extracted = extract_ktp_data_smart(text_blocks, template_config)
            final_data = postprocess_extracted_data(raw_extracted, template_config.get("fields", []))

            print(f"   ----------------------------------------")
            for key in all_keys:
                extracted_val = str(final_data.get(key, ""))
                target_val = str(gt_data.get(key, ""))
                sim = string_similarity(extracted_val, target_val)
                field_scores[key].append(sim)
                status_icon = "✅" if sim > 0.85 else ("⚠️" if sim > 0.5 else "❌")
                print(f"   {status_icon} {key:<18}: Hasil='{extracted_val}' | Target='{target_val}' ({sim*100:.1f}%)")
            print(f"   ----------------------------------------\n")

        except Exception as e:
            print(f"   ❌ Error saat menguji '{filename}': {e}\n")

    # Laporan Akhir Evaluasi
    print("="*65)
    print("📈 LAPORAN REKAPITULASI AKURASI EKSTRAKSI PER FIELD")
    print("="*65)
    
    total_samples = 0
    overall_sum = 0.0

    for key in all_keys:
        scores = field_scores[key]
        if scores:
            avg_score = (sum(scores) / len(scores)) * 100
            total_samples = max(total_samples, len(scores))
            overall_sum += avg_score
            bar = "█" * int(avg_score // 5)
            print(f"{key:<18} : {avg_score:6.2f}% | {bar}")
        else:
            print(f"{key:<18} :   N/A   (Belum ada data ground truth valid)")

    if total_samples > 0:
        overall_avg = overall_sum / len(all_keys)
        print("="*65)
        print(f"🏆 RATA-RATA AKURASI KESELURUHAN (OVERALL SCORE): {overall_avg:.2f}%")
        print("="*65 + "\n")

if __name__ == "__main__":
    evaluate()
