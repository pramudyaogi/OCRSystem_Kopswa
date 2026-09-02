import paddle
paddle.set_flags({"FLAGS_use_mkldnn": False})
from paddleocr import PaddleOCR
import numpy as np
from typing import Dict, Any

# Inisialisasi Singleton Engine PaddleOCR
# - use_angle_cls=True: Mendeteksi jika ada teks yang terbalik (rotated)
# - lang='id': Dioptimalkan untuk membaca abjad dan kata bahasa Indonesia
# - det_db_unclip_ratio: Diturunkan ke 1.25 (default 1.5) agar bounding box lebih ketat per kata
# - enable_mkldnn=False: Memastikan kestabilan PIR/OneDNN di Linux CPU container
ocr_model = PaddleOCR(use_angle_cls=True, lang='id', det_db_unclip_ratio=1.25, enable_mkldnn=False)

def _normalize_ocr_lines(result):
    if not result:
        return []
    first = result[0]
    if first is None:
        return []
    
    if isinstance(first, dict):
        rec_texts = first.get("rec_texts", [])
        rec_scores = first.get("rec_scores", [])
        rec_polys = first.get("rec_polys", first.get("dt_polys", []))
        
        lines = []
        for idx, text in enumerate(rec_texts):
            score = float(rec_scores[idx]) if idx < len(rec_scores) else 1.0
            poly = rec_polys[idx] if idx < len(rec_polys) else []
            if hasattr(poly, "tolist"):
                poly = poly.tolist()
            lines.append((poly, (text, score)))
        return lines
    
    if isinstance(first, list):
        return first
        
    return []

def extract_text_from_crop(image: np.ndarray) -> Dict[str, Any]:
    """
    Menjalankan proses inferensi OCR pada satu potongan gambar (array).
    Mengembalikan teks yang terbaca beserta nilai tingkat kepercayaannya (confidence score).
    """
    result = ocr_model.ocr(image)
    lines = _normalize_ocr_lines(result)
    
    if not lines:
        return {"text": "", "confidence": 0.0}
        
    extracted_texts = []
    total_confidence = 0.0
    count = 0
    
    for line in lines:
        coords, (text, conf) = line
        extracted_texts.append(text)
        total_confidence += float(conf)
        count += 1
        
    avg_confidence = total_confidence / count if count > 0 else 0.0
    final_text = " ".join(extracted_texts).strip()
    
    return {
        "text": final_text,
        "confidence": avg_confidence
    }

from app.core.ocr.handwriting_ocr import handwriting_engine
import cv2

def reprocess_nik_roi(image: np.ndarray, nik_bbox: list = None) -> str:
    """
    Dedicated NIK ROI Crop & Reprocessing (Sesuai rekomendasi ahli Poin 2):
    1. Ambil ROI khusus NIK (diperluas 10px margin).
    2. Upscale 2.5x dengan cv2.INTER_CUBIC.
    3. Adaptive thresholding & sharpening untuk memperjelas batas digit angka NIK.
    4. Pass ke PaddleOCR khusus ROI untuk mendapatkan NIK murni 16 digit.
    """
    try:
        h, w = image.shape[:2]
        if nik_bbox:
            xs = [pt[0] for pt in nik_bbox]
            ys = [pt[1] for pt in nik_bbox]
            y1 = max(0, int(min(ys)) - 10)
            y2 = min(h, int(max(ys)) + 10)
            x1 = max(0, int(min(xs)) - 15)
            x2 = min(w, int(max(xs)) + 15)
        else:
            # Fallback ROI area NIK standar KTP (Y: 15%-32%, X: 15%-88%)
            y1 = int(h * 0.15)
            y2 = int(h * 0.32)
            x1 = int(w * 0.15)
            x2 = int(w * 0.88)

        roi = image[y1:y2, x1:x2]
        if roi.size == 0 or roi.shape[0] < 10 or roi.shape[1] < 10:
            return ""

        # Upscale 2.5x INTER_CUBIC
        roi_scaled = cv2.resize(roi, (0, 0), fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)

        # Preprocessing khusus ROI NIK (Adaptive Thresholding + Sharpening)
        gray = cv2.cvtColor(roi_scaled, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)
        blur = cv2.GaussianBlur(enhanced, (0, 0), 1.5)
        sharp = cv2.addWeighted(enhanced, 1.5, blur, -0.5, 0)

        # Convert back to BGR for PaddleOCR
        roi_final = cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)

        result = ocr_model.ocr(roi_final)
        lines = _normalize_ocr_lines(result)

        import re
        for line in lines:
            txt = line[1][0] if isinstance(line, (tuple, list)) and len(line) > 1 and isinstance(line[1], (tuple, list)) else ""
            digits = re.sub(r'\D', '', txt)
            if len(digits) >= 14:
                # Koreksi OCR typo umum pada digit NIK
                digits = digits.replace('b', '6').replace('o', '0').replace('O', '0').replace('I', '1').replace('l', '1')
                return digits

    except Exception as e:
        print(f"[NIK REPROCESS ERROR]: {e}")

    return ""

def extract_full_text(image: np.ndarray, use_trocr: bool = False) -> list:
    """
    Menjalankan OCR di seluruh gambar utuh dan mengembalikan daftar blok teks 
    berupa tuple (teks, confidence, bbox).
    """
    result = ocr_model.ocr(image)
    lines = _normalize_ocr_lines(result)
    
    if not lines:
        return []
        
    blocks = []
    for line in lines:
        if use_trocr:
            coords = line[0] if isinstance(line, (tuple, list)) else line
            pts = np.array(coords, np.int32)
            rect = cv2.boundingRect(pts)
            x, y, w, h = rect
            
            y_start = max(0, y - 2)
            y_end = min(image.shape[0], y + h + 2)
            x_start = max(0, x - 2)
            x_end = min(image.shape[1], x + w + 2)
            
            crop_img = image[y_start:y_end, x_start:x_end]
            if crop_img.shape[0] < 5 or crop_img.shape[1] < 5:
                continue
                
            text = handwriting_engine.recognize_text(crop_img)
            conf = 0.95
        else:
            coords, (text, conf) = line
            
        blocks.append({
            "text": text.strip() if type(text) == str else "",
            "confidence": float(conf),
            "bbox": coords
        })

    # Poin 2: Cek NIK 16 digit — Jika NIK awal terdeteksi < 16 digit, jalankan reprocess_nik_roi
    import re
    nik_block = None
    for b in blocks:
        digits = re.sub(r'\D', '', b["text"])
        if 13 <= len(digits) < 16 and ("NIK" in b["text"].upper() or len(digits) >= 14):
            nik_block = b
            break

    if nik_block:
        better_nik = reprocess_nik_roi(image, nik_block["bbox"])
        if len(better_nik) >= 15: # Dapatkan versi 15/16 digit yang lebih utuh
            nik_block["text"] = f"NIK : {better_nik}"
            nik_block["confidence"] = 0.95

    return blocks

def process_cropped_fields(cropped_images_dict: Dict[str, np.ndarray]) -> Dict[str, Dict[str, Any]]:
    """
    Memproses sebuah dictionary gambar-gambar potongan secara otomatis (looping).
    Menerima input dari hasil template matching.
    """
    extracted_data = {}
    
    for field_name, crop_img in cropped_images_dict.items():
        print(f"[OCR] Mengekstrak teks dari field: {field_name}...")
        ocr_result = extract_text_from_crop(crop_img)
        
        extracted_data[field_name] = {
            "value": ocr_result["text"],
            "confidence": ocr_result["confidence"]
        }
        
    return extracted_data
