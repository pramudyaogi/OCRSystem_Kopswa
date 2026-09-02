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
    Ekstraksi data KTP Cerdas berbasis Y-Overlap, Fuzzy Label Anchors, 
    dan Bounded Fallback Spatial Zone.
    """
    all_ktp_keys = [
        "provinsi", "kota", "nik", "nama", "tempat_tgl_lahir", "jenis_kelamin", 
        "gol_darah", "alamat", "rt_rw", "kel_desa", "kecamatan", "agama", 
        "status_perkawinan", "pekerjaan", "kewarganegaraan", "berlaku_hingga"
    ]
    extracted = {f: {"value": "", "confidence": 0.0} for f in all_ktp_keys}
    
    import re
    from rapidfuzz import fuzz

    # List label standar KTP
    ALL_LABELS = [
        "PROVINSI", "KABUPATEN", "KOTA", "NIK", "NAMA", "TEMPAT", "TGL", "LAHIR",
        "JENIS", "KELAMIN", "GOL", "DARAH", "ALAMAT", "RT/RW", "RT/", "/RW",
        "KEL/DESA", "KELURAHAN", "KECAMATAN", "KEC", "AGAMA", "STATUS", "PERKAWINAN",
        "PEKERJAAN", "KEWARGANEGARAAN", "BERLAKU", "HINGGA"
    ]

    MULTI_WORD_LABELS = [
        "JENIS KELAMIN", "GOL DARAH", "KEL DESA", "STATUS PERKAWINAN",
        "BERLAKU HINGGA", "TEMPAT TGL LAHIR", "RT RW", "TEMPAT LAHIR", "KEWARGANEGARAAN"
    ]

    def is_label_text(text: str) -> bool:
        txt_u = text.upper().strip()

        # NIK 16-digit angka -> BUKAN label
        digits = re.sub(r'\D', '', txt_u)
        if len(digits) >= 13:
            return False

        # Format RT/RW angka -> BUKAN label
        if re.match(r'^\d{1,3}[/\-]\d{1,3}$', txt_u):
            return False

        # Kota / Provinsi / Lokasi -> BUKAN label murni
        if any(place in txt_u for place in [
            "JAKARTA", "BARAT", "TIMUR", "SELATAN", "UTARA", "PUSAT",
            "JAWA", "SUMATERA", "BALI", "SULAWESI", "KALIMANTAN",
            "BANDUNG", "SURABAYA", "MEDAN", "ADM.", "CENGKARENG",
            "PURWAKARTA", "TANGERANG", "BEKASI", "DEPOK", "BOGOR",
            "NAGREKALER", "NAGRI", "VETERAN", "SOKA"
        ]):
            return False

        # Jika mengandung kata watermark KTP / value murni, ini BUKAN label murni
        if any(v in txt_u for v in ["ISLAM", "KRISTEN", "KATHOLIK", "HINDU", "BUDDHA", "BELUM", "KAWIN", "PELAJAR", "MAHASISWA", "WNI", "WNA", "SEUMUR", "JAYA RAYA", "LJAYARAYA", "JAKARTA BARAT"]):
            return False

        # Exact match label (harus ber-boundary kata murni)
        for lbl in ALL_LABELS:
            if re.search(r'\b' + re.escape(lbl) + r'\b', txt_u):
                return True

        # Fuzzy match label
        if 4 <= len(txt_u) <= 24:
            for lbl in MULTI_WORD_LABELS:
                if fuzz.ratio(txt_u, lbl) >= 75:
                    return True
            for lbl in ALL_LABELS:
                if len(lbl) >= 4 and fuzz.ratio(txt_u, lbl) >= 78:
                    return True

        return False

    def strip_known_labels(text: str, keywords: list) -> str:
        """Menghapus label dari teks, baik exact regex maupun fuzzy match."""
        txt = text.strip()
        for kw in keywords:
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            txt = pattern.sub("", txt).strip(" :-")
        
        # Fuzzy strip kata pertama jika merupakan typo dari label
        words = txt.split()
        if words and len(words[0]) >= 3:
            for kw in keywords:
                if fuzz.ratio(words[0].upper(), kw.upper()) >= 70:
                    words = words[1:]
                    break
            txt = " ".join(words).strip(" :-")
        return txt

    # 1. Parsing text blocks & hitung dimensi
    parsed_blocks = []
    for b in text_blocks:
        bbox = b["bbox"]
        xs = [pt[0] for pt in bbox]
        ys = [pt[1] for pt in bbox]
        min_y = min(ys)
        max_y = max(ys)
        parsed_blocks.append({
            "text": b["text"],
            "confidence": b["confidence"],
            "cx": sum(xs) / len(xs),
            "cy": sum(ys) / len(ys),
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min_y,
            "max_y": max_y,
            "height": max(max_y - min_y, 1),
            "bbox": bbox
        })

    # 2. Cari NIK via Regex lebih dulu
    for b in parsed_blocks:
        digits = re.sub(r'\D', '', b["text"])
        if len(digits) >= 14:
            extracted["nik"] = {"value": digits, "confidence": b["confidence"]}
            break

    # Ekstraksi Provinsi dan Kota (jika menyatu di 1 block)
    for b in parsed_blocks:
        txt_u = b["text"].upper()
        if "PROVINSI" in txt_u and not extracted.get("provinsi", {}).get("value"):
            val = strip_known_labels(txt_u, ["PROVINSI"])
            if val:
                extracted["provinsi"] = {"value": val, "confidence": b["confidence"]}
        elif ("KABUPATEN" in txt_u or "KOTA" in txt_u) and not extracted.get("kota", {}).get("value"):
            val = strip_known_labels(txt_u, ["KABUPATEN", "KOTA"])
            if val:
                extracted["kota"] = {"value": val, "confidence": b["confidence"]}

    # Helper Spatial Alignment berbasis Keyword Anchor Independen
    def find_field_spatial(keywords: list, field_key: str, is_below: bool = False, next_label_keywords: list = None, ignore_gap: bool = False):
        if field_key in extracted and extracted[field_key].get("value"):
            return

        label_block = None
        # 1. Cari Bbox Label (Exact / Word Boundary match)
        for b in parsed_blocks:
            txt_u = b["text"].upper()
            if any(re.search(r'\b' + re.escape(kw) + r'\b', txt_u) for kw in keywords):
                label_block = b
                break

        # 2. Fuzzy Match jika label terpotong atau typo berat OCR (misal "isEPeaawu", "PAKE:Ino", "Alama")
        if not label_block:
            for b in parsed_blocks:
                txt_u = b["text"].upper()
                words = txt_u.split()
                for kw in keywords:
                    for w in words:
                        if len(w) >= 4 and (fuzz.ratio(w, kw) >= 75 or fuzz.partial_ratio(w, kw) >= 80):
                            label_block = b
                            break
                    if label_block:
                        break
                if label_block:
                    break

        if not label_block:
            return

        next_label_block = None
        if next_label_keywords:
            for b in parsed_blocks:
                txt_u = b["text"].upper()
                if any(kw in txt_u for kw in next_label_keywords):
                    next_label_block = b
                    break

        # Cek jika label & value menyatu dalam 1 bbox
        txt_stripped = strip_known_labels(label_block["text"], keywords)
        val_triggers = ["BELUM", "KAWIN", "WNI", "WNL", "WNA", "SEUMUR", "LAKI", "PEREMPUAN", "ISLAM", "PELAJAR", "MAHASISWA"]
        if ":" in label_block["text"] or any(val_kw in label_block["text"].upper() for val_kw in val_triggers):
            if len(txt_stripped) >= 2 and not is_label_text(txt_stripped):
                extracted[field_key] = {"value": txt_stripped, "confidence": label_block["confidence"], "block": label_block}
                return

        l_min_y = label_block["min_y"]
        l_max_y = label_block["max_y"]
        l_h = label_block["height"]

        raw_candidates = []
        claimed_blocks = []
        for v in extracted.values():
            if isinstance(v, dict):
                if "block" in v:
                    claimed_blocks.append(v["block"])
                if "all_blocks" in v:
                    claimed_blocks.extend(v["all_blocks"])
        for b in parsed_blocks:
            if b == label_block or b in claimed_blocks:
                continue
            if is_label_text(b["text"]):
                continue
            if any(wm in b["text"].upper() for wm in ["JAYA RAYA", "LJAYARAYA", "JAKARTA BARAT"]):
                continue

            # Value harus berada di area kanan dari label
            is_right = (b["cx"] >= label_block["cx"]) or (b["min_x"] >= (label_block["max_x"] - 120))
            
            # Y-Overlap Ratio > 0.40 ATAU selisih Y-center sangat dekat (< 0.40 * l_h)
            overlap_y = max(0, min(l_max_y, b["max_y"]) - max(l_min_y, b["min_y"]))
            overlap_ratio = overlap_y / min(l_h, b["height"])
            
            is_y_aligned = (overlap_ratio > 0.40 or abs(b["cy"] - label_block["cy"]) < (l_h * 0.40))
            is_valid_pos = is_right and is_y_aligned
            
            # Jangan ambil jika candidate berada di sebelah kanan label berikutnya yang satu garis Y
            if is_valid_pos and next_label_block:
                # Hanya batasi jika next_label_block se-garis Y (misal GOL DARAH di kanan JENIS KELAMIN)
                if abs(next_label_block["cy"] - label_block["cy"]) < (l_h * 0.8):
                    if b["min_x"] >= (next_label_block["min_x"] - 5):
                        is_valid_pos = False

            if is_valid_pos:
                raw_candidates.append(b)

        if not raw_candidates:
            extracted[field_key] = {"value": "", "confidence": 0.0, "needs_review": True}
            return

        raw_candidates.sort(key=lambda b: b["min_x"])

        # Grouping baris dengan Y-axis Overlap Ratio & Spasi
        grouped = [raw_candidates[0]]
        for box in raw_candidates[1:]:
            prev_box = grouped[-1]
            gap = box["min_x"] - prev_box["max_x"]
            avg_height = (box["height"] + prev_box["height"]) / 2.0

            max_gap = (avg_height * 10.0) if ignore_gap else (avg_height * 4.5)
            if gap > max_gap:
                break
            grouped.append(box)

        # " ".join untuk SEMUA kata agar spasi tidak pernah hilang
        combined_text = " ".join([b["text"].upper() for b in grouped])
        combined_text = strip_known_labels(combined_text, keywords)
        combined_text = re.sub(r'\s+', ' ', combined_text).strip()

        avg_conf = sum(b["confidence"] for b in grouped) / len(grouped)
        if combined_text:
            extracted[field_key] = {"value": combined_text, "confidence": avg_conf, "block": grouped[0], "all_blocks": grouped}
        else:
            extracted[field_key] = {"value": "", "confidence": 0.0, "needs_review": True}

    # TAHAP 1: Keyword Anchoring Independen per Field (Top-to-Bottom)
    find_field_spatial(["NIK"], "nik")
    find_field_spatial(["NAMA"], "nama")
    find_field_spatial(["TEMPAT", "LAHIR", "TGL"], "tempat_tgl_lahir", next_label_keywords=["JENIS", "KELAMIN"], ignore_gap=True)
    find_field_spatial(["JENIS", "KELAMIN"], "jenis_kelamin", next_label_keywords=["GOL", "DARAH"])
    find_field_spatial(["GOL", "DARAH"], "gol_darah")
    find_field_spatial(["ALAMAT"], "alamat", next_label_keywords=["RT/RW"])
    find_field_spatial(["RT/RW", "RT / RW"], "rt_rw", next_label_keywords=["KEL/DESA"])
    find_field_spatial(["KEL/DESA", "KELURAHAN"], "kel_desa", next_label_keywords=["KECAMATAN"])
    find_field_spatial(["KECAMATAN"], "kecamatan", next_label_keywords=["AGAMA"])
    find_field_spatial(["AGAMA"], "agama", next_label_keywords=["STATUS", "PERKAWINAN"])
    find_field_spatial(["STATUS", "PERKAWINAN"], "status_perkawinan", next_label_keywords=["PEKERJAAN"])
    find_field_spatial(["PEKERJAAN"], "pekerjaan", next_label_keywords=["KEWARGANEGARAAN"])
    find_field_spatial(["KEWARGANEGARAAN"], "kewarganegaraan", next_label_keywords=["BERLAKU", "HINGGA"])
    find_field_spatial(["BERLAKU", "HINGGA"], "berlaku_hingga")

    # TAHAP 2: Isolated Fallback Spatial Zone (TIDAK menyerap data field lain!)
    KTP_ISOLATED_ZONES_PCT = {
        "nik":             {"min_y": 0.17, "max_y": 0.32, "min_x": 0.22, "max_x": 0.88},
        "nama":            {"min_y": 0.29, "max_y": 0.40, "min_x": 0.22, "max_x": 0.92},
        "tempat_tgl_lahir":{"min_y": 0.37, "max_y": 0.47, "min_x": 0.22, "max_x": 0.92},
        "jenis_kelamin":   {"min_y": 0.44, "max_y": 0.54, "min_x": 0.22, "max_x": 0.55},
        "alamat":          {"min_y": 0.51, "max_y": 0.60, "min_x": 0.22, "max_x": 0.92},
        "rt_rw":           {"min_y": 0.58, "max_y": 0.66, "min_x": 0.22, "max_x": 0.92},
        "kel_desa":        {"min_y": 0.64, "max_y": 0.72, "min_x": 0.22, "max_x": 0.92},
        "kecamatan":       {"min_y": 0.70, "max_y": 0.79, "min_x": 0.22, "max_x": 0.92},
        "agama":           {"min_y": 0.77, "max_y": 0.85, "min_x": 0.22, "max_x": 0.70},
        "status_perkawinan":{"min_y": 0.83, "max_y": 0.91, "min_x": 0.22, "max_x": 0.92},
        "pekerjaan":       {"min_y": 0.89, "max_y": 0.96, "min_x": 0.22, "max_x": 0.75},
        "kewarganegaraan": {"min_y": 0.94, "max_y": 1.00, "min_x": 0.22, "max_x": 0.55},
        "berlaku_hingga":  {"min_y": 0.94, "max_y": 1.00, "min_x": 0.55, "max_x": 0.98},
    }

    if parsed_blocks:
        all_xs = [pt[0] for b in parsed_blocks for pt in b["bbox"]]
        all_ys = [pt[1] for b in parsed_blocks for pt in b["bbox"]]
        img_min_x, img_min_y = min(all_xs), min(all_ys)
        img_max_x, img_max_y = max(all_xs), max(all_ys)
        content_w = max(img_max_x - img_min_x, 1)
        content_h = max(img_max_y - img_min_y, 1)
    else:
        img_min_x, img_min_y, content_w, content_h = 0, 0, 1000, 630

    for field_key, zone_pct in KTP_ISOLATED_ZONES_PCT.items():
        if extracted.get(field_key, {}).get("value"):
            continue

        min_y = img_min_y + zone_pct["min_y"] * content_h
        max_y = img_min_y + zone_pct["max_y"] * content_h
        min_x = img_min_x + zone_pct["min_x"] * content_w
        max_x = img_min_x + zone_pct["max_x"] * content_w

        candidates = []
        for b in parsed_blocks:
            if min_y <= b["cy"] <= max_y and min_x <= b["min_x"] <= max_x:
                txt_clean = b["text"].upper()
                if is_label_text(txt_clean):
                    continue
                txt_clean = strip_known_labels(txt_clean, ALL_LABELS)
                if txt_clean:
                    candidates.append((b, txt_clean))

        if candidates:
            candidates.sort(key=lambda item: item[0]["min_x"])
            val = " ".join([c[1] for c in candidates])
            val = re.sub(r'\s+', ' ', val).strip()
            avg_conf = sum([c[0]["confidence"] for c in candidates]) / len(candidates)
            extracted[field_key] = {
                "value": val,
                "confidence": float(avg_conf),
                "needs_review": bool(avg_conf < 0.70)
            }

    # Final Confidence & Format Validation Layer
    for fk, data in extracted.items():
        if isinstance(data, dict):
            val = data.get("value", "")
            conf = data.get("confidence", 0.0)
            
            # Format Safety Nets
            if fk == "nik" and not re.match(r'^\d{16}$', val):
                data["needs_review"] = True
            elif fk == "jenis_kelamin" and val not in ["LAKI-LAKI", "PEREMPUAN"]:
                data["needs_review"] = True
            elif fk == "tempat_tgl_lahir" and not re.search(r'\d{2}-\d{2}-\d{4}', val):
                data["needs_review"] = True
            elif conf < 0.70 or not val:
                data["needs_review"] = True

    return extracted
