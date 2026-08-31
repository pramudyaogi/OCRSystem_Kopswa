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
