import cv2
import json
import numpy as np
from typing import Dict, Any

def load_template_config(json_path: str) -> dict:
    """
    Membaca dan memuat file konfigurasi template berformat JSON.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def crop_fields_by_template(image: np.ndarray, template_config: dict) -> Dict[str, np.ndarray]:
    """
    Menyelaraskan skala gambar sesuai ukuran (base) template dan 
    memotong gambar per field (kolom) untuk diteruskan ke proses OCR.
    
    Return: 
      Dictionary berupa { 'nama_field': gambar_hasil_crop }
    """
    base_w = template_config.get("base_width", 1000)
    base_h = template_config.get("base_height", 630)
    fields = template_config.get("fields", [])
    
    # 1. Samakan resolusi/skala gambar dengan ukuran template kalibrasi awal
    resized_image = cv2.resize(image, (base_w, base_h), interpolation=cv2.INTER_AREA)
    
    cropped_fields = {}
    
    # 2. Lakukan perulangan untuk mengekstrak tiap kotak area berdasarkan koordinat X, Y
    for field in fields:
        name = field["nama_field"]
        x, y = field["x"], field["y"]
        w, h = field["width"], field["height"]
        
        # Validasi batas koordinat agar tidak terjadi array index out of bounds
        x_start = max(0, x)
        y_start = max(0, y)
        x_end = min(base_w, x + w)
        y_end = min(base_h, y + h)
        
        # Proses pemotongan matriks (Y, X) di Numpy / OpenCV
        crop_img = resized_image[y_start:y_end, x_start:x_end]
        cropped_fields[name] = crop_img
        
    return cropped_fields

def extract_ktp_data_smart(text_blocks: list, template_config: dict) -> Dict[str, Dict[str, Any]]:
    """
    Ekstraksi data KTP secara Cerdas menggunakan Spatial Alignment (Pencocokan Koordinat X,Y).
    Mengabaikan seluruh teks label dan hanya mengambil nilai asli di sebelah kanan label.
    """
    all_ktp_keys = [
        "provinsi", "kota", "nik", "nama", "tempat_tgl_lahir", "jenis_kelamin", 
        "gol_darah", "alamat", "rt_rw", "kel_desa", "kecamatan", "agama", 
        "status_perkawinan", "pekerjaan", "kewarganegaraan", "berlaku_hingga"
    ]
    extracted = {f: {"value": "", "confidence": 0.0} for f in all_ktp_keys}
    
    import re
    
    # Kata kunci yang tergolong Label KTP (bukan nilai data)
    ALL_LABELS = [
        "PROVINSI", "KABUPATEN", "KOTA", "NIK", "NAMA", "TEMPAT", "TGL", "LAHIR", 
        "JENIS", "KELAMIN", "GOL", "DARAH", "ALAMAT", "RT/RW", "RT/", "/RW", 
        "KEL/DESA", "KELURAHAN", "KECAMATAN", "AGAMA", "STATUS", "PERKAWINAN", 
        "PEKERJAAN", "KEWARGANEGARAAN", "BERLAKU", "HINGGA"
    ]
                  
    def is_label_text(text: str) -> bool:
        txt_u = text.upper()
        # Jika teksnya murni 16 digit angka NIK, itu BUKAN label
        digits = re.sub(r'\D', '', txt_u)
        if len(digits) >= 14:
            return False
            
        # Jika teks mengandung nama tempat/daerah khas KTP, itu BUKAN label murni
        if any(place in txt_u for place in ["JAKARTA", "BARAT", "TIMUR", "SELATAN", "UTARA", "PUSAT", "JAWA", "SUMATERA", "BALI", "SULAWESI", "KALIMANTAN", "BANDUNG", "SURABAYA", "MEDAN", "ADM."]):
            return False

        return any(lbl in txt_u for lbl in ALL_LABELS)

    # 1. Ekstrak koordinat tengah (center_x, center_y) untuk tiap blok
    parsed_blocks = []
    for b in text_blocks:
        bbox = b["bbox"]
        xs = [pt[0] for pt in bbox]
        ys = [pt[1] for pt in bbox]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        min_x = min(xs)
        max_x = max(xs)
        height = max(ys) - min(ys)  # Hitung tinggi teks sesungguhnya
        parsed_blocks.append({
            "text": b["text"],
            "confidence": b["confidence"],
            "cx": cx,
            "cy": cy,
            "min_x": min_x,
            "max_x": max_x,
            "height": height,
            "bbox": bbox
        })

    # 2. Cari NIK berbasis RegEx 16 digit angka lebih dulu
    for b in parsed_blocks:
        digits = re.sub(r'\D', '', b["text"])
        if len(digits) >= 14: # Memenuhi kriteria NIK
            extracted["nik"] = {"value": digits, "confidence": b["confidence"]}
            break

    # Ekstraksi Provinsi dan Kota awal (jika menyatu di 1 block)
    for b in parsed_blocks:
        txt_u = b["text"].upper()
        if "PROVINSI" in txt_u and not extracted.get("provinsi", {}).get("value"):
            val = txt_u.replace("PROVINSI", "").strip(" :-")
            if val:
                extracted["provinsi"] = {"value": val, "confidence": b["confidence"]}
        elif ("KABUPATEN" in txt_u or "KOTA" in txt_u) and not extracted.get("kota", {}).get("value"):
            val = txt_u.replace("KABUPATEN", "").replace("KOTA", "").strip(" :-")
            if val:
                extracted["kota"] = {"value": val, "confidence": b["confidence"]}

    # Helper untuk mencari nilai berdasarkan posisi relatif terhadap label
    def find_field_spatial(keywords: list, field_key: str, is_below: bool = False, next_label_keywords: list = None):
        # Jika nilai sudah terisi (misal NIK 16 digit yang sudah diparsing), jangan ditimpa lagi
        if field_key in extracted and extracted[field_key].get("value"):
            return

        label_block = None
        for b in parsed_blocks:
            txt_u = b["text"].upper()
            if any(kw in txt_u for kw in keywords):
                label_block = b
                break
                
        if not label_block:
            return

        # Cari label berikutnya untuk dijadikan boundary/batas kanan (misal GOL DARAH di kanan JENIS KELAMIN)
        next_label_block = None
        if next_label_keywords:
            for b in parsed_blocks:
                txt_u = b["text"].upper()
                if any(kw in txt_u for kw in next_label_keywords):
                    next_label_block = b
                    break

        # 1. Cek apakah PaddleOCR menggabungkan Label dan Nilai dalam satu kotak teks yang sama
        txt = label_block["text"].upper()
        for kw in keywords:
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            txt = pattern.sub("", txt).strip(" :-")
            
        if len(txt) > 2 and not is_label_text(txt):
            extracted[field_key] = {"value": txt, "confidence": label_block["confidence"]}
            return

        # 2. Jika tidak menyatu, cari kotak-kotak teks di sebelahnya atau di bawahnya
        l_cy = label_block["cy"]
        l_min_x = label_block["min_x"]
        l_h = label_block["height"]  # Tinggi kotak teks label ini

        raw_candidates = []
        for b in parsed_blocks:
            if b == label_block:
                continue
            if is_label_text(b["text"]):
                continue
                
            y_diff = b["cy"] - l_cy
            
            # Toleransi spasial berbasis tinggi font
            if is_below:
                # Teks harus ada di bawah label (selisih Y positif) maksimal sejauh 3x tinggi font
                is_valid_pos = (0 < y_diff < (l_h * 3.0))
            else:
                # Teks harus sejajar secara horizontal (Toleransi kemiringan Y maksimal 80% dari tinggi font)
                is_valid_pos = (abs(y_diff) < (l_h * 0.8) and b["min_x"] >= (l_min_x - (l_h * 0.5)))
                
                # Boundary Check: Jika ada label berikutnya (seperti GOL DARAH), kotak tak boleh melewatinya
                if is_valid_pos and next_label_block:
                    if abs(next_label_block["cy"] - l_cy) < (l_h * 1.5):
                        if b["min_x"] >= next_label_block["min_x"]:
                            is_valid_pos = False
            
            if is_valid_pos:
                raw_candidates.append(b)
                
        if not raw_candidates:
            return

        # Urutkan kandidat dari kiri ke kanan (berdasarkan min_x)
        raw_candidates.sort(key=lambda b: b["min_x"])
        
        # Horizontal Line Grouping dengan Gap Threshold
        grouped = [raw_candidates[0]]
        for box in raw_candidates[1:]:
            prev_box = grouped[-1]
            gap = box["min_x"] - prev_box["max_x"]
            avg_height = (box["height"] + prev_box["height"]) / 2.0
            
            # Jika selisih jarak horizontal (gap) lebih dari 3x tinggi huruf, jangan gabungkan
            if gap > (avg_height * 3.0):
                break
            grouped.append(box)

        # Gabungkan teks dari seluruh kelompok kotak sebaris dengan spasi
        combined_text = " ".join([b["text"].upper() for b in grouped])
        for kw in keywords:
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            combined_text = pattern.sub("", combined_text).strip(" :-")
            
        avg_conf = sum(b["confidence"] for b in grouped) / len(grouped)
        extracted[field_key] = {"value": combined_text.strip(), "confidence": avg_conf}

    # Jalankan pencocokan spasial untuk seluruh kolom KTP
    find_field_spatial(["PROVINSI"], "provinsi")
    find_field_spatial(["KABUPATEN", "KOTA"], "kota")
    find_field_spatial(["NIK"], "nik")
    find_field_spatial(["NAMA"], "nama")
    find_field_spatial(["TEMPAT", "LAHIR", "TGL"], "tempat_tgl_lahir")
    find_field_spatial(["JENIS", "KELAMIN"], "jenis_kelamin", next_label_keywords=["GOL", "DARAH"])
    find_field_spatial(["GOL", "DARAH"], "gol_darah")
    find_field_spatial(["ALAMAT"], "alamat")
    find_field_spatial(["RT/RW", "RT/"], "rt_rw")
    find_field_spatial(["KEL/DESA", "KELURAHAN"], "kel_desa")
    find_field_spatial(["KECAMATAN"], "kecamatan")
    find_field_spatial(["AGAMA"], "agama")
    find_field_spatial(["STATUS", "PERKAWINAN"], "status_perkawinan")
    find_field_spatial(["PEKERJAAN"], "pekerjaan")
    find_field_spatial(["KEWARGANEGARAAN"], "kewarganegaraan")
    find_field_spatial(["BERLAKU", "HINGGA"], "berlaku_hingga")

    return extracted
