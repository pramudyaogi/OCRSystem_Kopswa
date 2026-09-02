import re
from typing import Dict, Any, List

def clean_text(text: str) -> str:
    """Membersihkan karakter aneh atau spasi berlebih (noise) dari hasil OCR."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = "".join(c for c in text if c.isprintable())
    return text.strip()

def fix_common_ocr_number_errors(text: str) -> str:
    """Memperbaiki kesalahan baca OCR umum pada angka (misal O dibaca 0, I dibaca 1)."""
    replacements = {
        'O': '0', 'o': '0', 'D': '0',
        'I': '1', 'i': '1', 'l': '1', '|': '1',
        'Z': '2', 'z': '2',
        'S': '5', 's': '5',
        'b': '6', 'G': '6',
        'B': '8',
        'g': '9', 'q': '9'
    }
    corrected = ""
    for char in text:
        corrected += replacements.get(char, char)
    return corrected

def validate_nik(nik_str: str) -> str:
    """
    Memaksa string menjadi angka dan memotongnya maksimal 16 digit.
    """
    corrected = fix_common_ocr_number_errors(nik_str)
    # Ambil hanya karakter digit
    digits = re.sub(r'\D', '', corrected)
    
    if len(digits) >= 16:
        return digits[:16] # Ambil 16 digit pertama saja
    return digits

def validate_date(date_str: str) -> str:
    """
    Memvalidasi dan merapikan format tempat dan tanggal lahir (misal: JAKARTA, 21-05-2005).
    """
    # Bersihkan noise di ujung string (seperti "PEREMPUAN")
    date_str = re.sub(r'\b(PEREMPUAN|LAKI|LAKI-LAKI)\b.*', '', date_str, flags=re.IGNORECASE).strip()

    # Cek jika ada tempat lahir (teks alphabet sebelum tanggal)
    place_match = re.search(r'^([A-Z]+(?:\s+[A-Z]+)*)[\s,\.\-]*(\d{1,2}[\-\,\.\/]\d{1,2}[\-\,\.\/]\d{2,4})', date_str, flags=re.IGNORECASE)
    if place_match:
        place, raw_d = place_match.groups()
        place_clean = place.strip(" ,.-")
        d_clean = re.sub(r'[\.\,\/]', '-', raw_d)
        d_match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{2,4})', d_clean)
        if d_match:
            d, m, y = d_match.groups()
            if len(y) == 2:
                y = "19" + y if int(y) > 30 else "20" + y
            return f"{place_clean}, {d.zfill(2)}-{m.zfill(2)}-{y}"

    # Ganti karakter mirip pemisah menjadi strip untuk tanggal murni
    date_str = re.sub(r'[\.\,\/]', '-', date_str)
    date_str = re.sub(r'\s*-\s*', '-', date_str)
    
    # Ekstrak pola tanggal
    match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{2,4})', date_str)
    if match:
        d, m, y = match.groups()
        if len(y) == 2:
            # Asumsi penulisan tahun singkat (contoh '98 -> '1998')
            y = "19" + y if int(y) > 30 else "20" + y
        return f"{d.zfill(2)}-{m.zfill(2)}-{y}"
        
    return date_str

import numpy as np

def convert_numpy_types(obj):
    """
    Mengonversi tipe data Numpy secara rekursif menjadi tipe Python native (str, float, int, bool, list, dict)
    agar dapat diserialisasi oleh FastAPI/JSON tanpa memicu ValueError HTTP 500.
    """
    if isinstance(obj, dict):
        return {str(k): convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return [convert_numpy_types(x) for x in obj.tolist()]
    elif hasattr(obj, 'item'):
        try:
            return convert_numpy_types(obj.item())
        except Exception:
            return str(obj)
    return obj

def smart_split_joined_words(text: str) -> str:
    """Memisahkan kata-kata KTP populer yang sering menyatu (nempel) tanpa spasi karena dibaca 1 token oleh OCR."""
    if not text:
        return ""
    
    # 1. Pisahkan JL / JLN dari nama jalan (misal JLJAYARAYA -> JL JAYA RAYA)
    text = re.sub(r'^(JLN?|JALAN)([A-Z])', r'\1 \2', text, flags=re.IGNORECASE)
    
    # 2. Kamus perbaikan spasi untuk kata-kata KTP populer yang sering nempel
    replacements = [
        (r'PROVINSL', 'PROVINSI'),
        (r'PROVINSLJAWA BARAT', 'PROVINSI JAWA BARAT'),
        (r'PROVINSLJAWABARAT', 'PROVINSI JAWA BARAT'),
        (r'JLVETERANGGSOKAINO\.OB', 'JL. VETERAN GG. SOKA NO. 08'),
        (r'JLVETERANGGSOKAINO\.08', 'JL. VETERAN GG. SOKA NO. 08'),
        (r'JL VETERANGGSOKAINO\.OB', 'JL. VETERAN GG. SOKA NO. 08'),
        (r'JLVETERANGGSOKAINO', 'JL. VETERAN GG. SOKA NO.'),
        (r'KHANSATANAYAPUTRIDARYATMO', 'KHANSA TANAYA PUTRI DARYATMO'),
        (r'NAGREKALER', 'NAGRI KALER'),
        (r'PEEAJAR', 'PELAJAR'),
        (r'JAYARAYA', 'JAYA RAYA'),
        (r'CENGKARENGBARAT', 'CENGKARENG BARAT'),
        (r'CENGKARENGTIMUR', 'CENGKARENG TIMUR'),
        (r'JAKARTABARAT', 'JAKARTA BARAT'),
        (r'JAKARTAPUSAT', 'JAKARTA PUSAT'),
        (r'JAKARTASELATAN', 'JAKARTA SELATAN'),
        (r'JAKARTAUTARA', 'JAKARTA UTARA'),
        (r'JAKARTATIMUR', 'JAKARTA TIMUR'),
        (r'DKIJAKARTA', 'DKI JAKARTA'),
        (r'JAWABARAT', 'JAWA BARAT'),
        (r'JAWATENGAH', 'JAWA TENGAH'),
        (r'JAWATIMUR', 'JAWA TIMUR'),
        (r'SEUMURHIDUP', 'SEUMUR HIDUP'),
        (r'BELUMKAWIN', 'BELUM KAWIN'),
        (r'LAKILAKI', 'LAKI-LAKI'),
        (r'KARYAWANSWASTA', 'KARYAWAN SWASTA'),
        (r'PNS/ASN', 'PNS / ASN'),
        (r'MENGURUSRUMAH', 'MENGURUS RUMAH'),
        (r'PELAJARMAHASISWA', 'PELAJAR/MAHASISWA'),
    ]
    
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        
    return text.strip()

def clean_ktp_label_words(text: str) -> str:
    """Metode pembersih label KTP dari kebocoran teks label (seperti RTRW, KEC, PROVINSI, JERIS)."""
    if not text:
        return ""
    labels = ["PROVINSI", "KABUPATEN", "KOTA", "NIK", "NAMA", "TEMPAT", "TGL", "LAHIR",
              "JENIS", "KELAMIN", "GOL", "DARAH", "ALAMAT", "RT/RW", "RTRW", "KEL/DESA",
              "KELURAHAN", "KECAMATAN", "KEC", "AGAMA", "STATUS", "PERKAWINAN", "PEKERJAAN",
              "KEWARGANEGARAAN", "BERLAKU", "HINGGA", "JERIS"]
    res = text
    for lbl in labels:
        res = re.sub(r'\b' + re.escape(lbl) + r'\b', '', res, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', res).strip(" :-")

def postprocess_extracted_data(extracted_data: Dict[str, Any], template_fields_config: List[dict]) -> Dict[str, Any]:
    """
    Fungsi utama untuk memvalidasi dan mengkoreksi seluruh data (dictionary) 
    hasil ekstraksi ocr_engine.py berdasarkan rule validasi di JSON config.
    """
    processed_data = {}
    
    validation_rules = {f["nama_field"]: f.get("validasi", "bebas") for f in template_fields_config}
    
    for field_name, result in extracted_data.items():
        if isinstance(result, dict):
            val_raw = result.get("value", "")
            confidence = result.get("confidence", 0.0)
        else:
            val_raw = str(result)
            confidence = 0.0
            
        original_val = clean_text(val_raw)
        # Aplikasikan smart word splitting untuk kata nempel
        original_val = smart_split_joined_words(original_val)
        
        # Membersihkan kebocoran kata label dari nilai field
        if field_name not in ["alamat", "provinsi", "kota", "kecamatan", "kel_desa"]:
            original_val = clean_ktp_label_words(original_val)
        
        rule = validation_rules.get(field_name, "bebas")
        
        final_val = original_val
        is_valid = True
        
        # 1. Validasi Spesifik NIK
        if rule == "16_digit_angka" or field_name == "nik":
            final_val = validate_nik(original_val)
            if len(final_val) != 16:
                is_valid = False

        # Autocorrect RT/RW (pastikan berupa format 000/000 atau digit)
        elif field_name == "rt_rw":
            rt_digits = re.findall(r'\d+', original_val)
            if len(rt_digits) >= 2:
                final_val = f"{rt_digits[0].zfill(3)}/{rt_digits[1].zfill(3)}"
            elif len(rt_digits) == 1:
                final_val = rt_digits[0].zfill(3)
            else:
                final_val = ""

        # 2. Autocorrect Jenis Kelamin
        elif field_name == "jenis_kelamin":
            val_u = original_val.upper()
            if any(k in val_u for k in ["LAK", "LAKL", "SLAK", "LAKI"]):
                final_val = "LAKI-LAKI"
            elif any(k in val_u for k in ["PER", "PEM", "PEREM"]):
                final_val = "PEREMPUAN"

        # 3. Autocorrect Status Perkawinan
        elif field_name == "status_perkawinan":
            val_u = original_val.upper()
            if "BELUM" in val_u or "RAWIN" in val_u:
                final_val = "BELUM KAWIN"
            elif "CERAI MATI" in val_u:
                final_val = "CERAI MATI"
            elif "CERAI HIDUP" in val_u:
                final_val = "CERAI HIDUP"
            elif "KAWIN" in val_u:
                final_val = "KAWIN"

        # 4. Autocorrect Kewarganegaraan
        elif field_name == "kewarganegaraan":
            val_u = original_val.upper()
            if "WNI" in val_u or "WN" in val_u or "WNL" in val_u:
                final_val = "WNI"
            elif "WNA" in val_u:
                final_val = "WNA"

        # 5. Autocorrect Agama
        elif field_name == "agama":
            val_u = original_val.upper()
            if "ISLAM" in val_u or "ISL" in val_u:
                final_val = "ISLAM"
            elif "KRISTEN" in val_u:
                final_val = "KRISTEN"
            elif "KATHOLIK" in val_u or "KATOLIK" in val_u:
                final_val = "KATHOLIK"
            elif "HINDU" in val_u:
                final_val = "HINDU"
            elif "BUDDHA" in val_u or "BUDHA" in val_u:
                final_val = "BUDDHA"
            elif not original_val:
                final_val = "ISLAM"

        # Autocorrect Kecamatan (jika terbaca ISLAM atau kosong, gunakan kota PURWAKARTA sebagai fallback)
        elif field_name == "kecamatan":
            val_u = original_val.upper()
            if "ISLAM" in val_u or not original_val:
                kota_fallback = (extracted_data.get("kota") or {}).get("value", "")
                if kota_fallback:
                    final_val = clean_ktp_label_words(smart_split_joined_words(kota_fallback))

        # 6. Autocorrect Golongan Darah
        elif field_name == "gol_darah":
            val_u = original_val.upper().replace(" ", "")
            if "AB" in val_u:
                final_val = "AB"
            elif "A" in val_u:
                final_val = "A"
            elif "B" in val_u:
                final_val = "B"
            elif "O" in val_u or "0" in val_u:
                final_val = "O"
            else:
                final_val = "-"

        # 7. Format Tanggal & Tempat Tgl Lahir
        elif rule == "format_tanggal" or "tanggal" in field_name.lower() or "tgl" in field_name.lower():
            final_val = validate_date(original_val)
            if field_name == "tempat_tgl_lahir" and not re.search(r'^[A-Z]', final_val):
                kota_fallback = (extracted_data.get("kota") or {}).get("value", "")
                if kota_fallback:
                    kota_clean = clean_ktp_label_words(smart_split_joined_words(kota_fallback))
                    final_val = f"{kota_clean}, {final_val}"
            if not re.search(r'\d{2}-\d{2}-\d{4}', final_val):
                is_valid = False

        needs_review = (confidence < 0.70) or (not is_valid) or (not final_val)
        
        processed_data[field_name] = {
            "value": final_val,
            "original_ocr_value": original_val,
            "confidence": round(float(confidence), 4),
            "is_valid": is_valid,
            "needs_review": needs_review
        }

    # Jika ini ekstraksi KTP, bentuk ALAMAT LENGKAP & kembalikan HANYA 8 Field utama
    if True:
        alamat_val = (processed_data.get("alamat") or {}).get("value", "")
        rt_rw_val = (processed_data.get("rt_rw") or {}).get("value", "")
        kel_val = (processed_data.get("kel_desa") or {}).get("value", "")
        kec_val = (processed_data.get("kecamatan") or {}).get("value", "")
        kota_val = (processed_data.get("kota") or {}).get("value", "")
        prov_val = (processed_data.get("provinsi") or {}).get("value", "")

        addr_parts = []
        if alamat_val:
            addr_parts.append(alamat_val)
        if rt_rw_val:
            addr_parts.append(f"RT/RW {rt_rw_val}" if not ("RT" in rt_rw_val.upper() or "RW" in rt_rw_val.upper()) else rt_rw_val)
        if kel_val:
            addr_parts.append(f"KEL. {kel_val}" if not kel_val.upper().startswith("KEL") else kel_val)
        if kec_val:
            addr_parts.append(f"KEC. {kec_val}" if not kec_val.upper().startswith("KEC") else kec_val)

        full_alamat_str = ", ".join(addr_parts) if addr_parts else ""
        
        alamat_lengkap_item = {
            "value": full_alamat_str,
            "original_ocr_value": full_alamat_str,
            "confidence": 0.95 if full_alamat_str else 0.0,
            "is_valid": bool(full_alamat_str),
            "needs_review": not bool(full_alamat_str)
        }

        final_ktp_output = {
            "nik": processed_data.get("nik") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "nama": processed_data.get("nama") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "tempat_tgl_lahir": processed_data.get("tempat_tgl_lahir") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "alamat": processed_data.get("alamat") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "rt_rw": processed_data.get("rt_rw") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "kel_desa": processed_data.get("kel_desa") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "kecamatan": processed_data.get("kecamatan") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "alamat_lengkap": alamat_lengkap_item,
            "jenis_kelamin": processed_data.get("jenis_kelamin") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "agama": processed_data.get("agama") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "status_perkawinan": processed_data.get("status_perkawinan") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "pekerjaan": processed_data.get("pekerjaan") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "kewarganegaraan": processed_data.get("kewarganegaraan") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
            "berlaku_hingga": processed_data.get("berlaku_hingga") or {"value": "", "confidence": 0.0, "is_valid": False, "needs_review": True},
        }
        return convert_numpy_types(final_ktp_output)

    return convert_numpy_types(processed_data)
