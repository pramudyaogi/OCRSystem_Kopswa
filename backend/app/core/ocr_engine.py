from paddleocr import PaddleOCR
import numpy as np
from typing import Dict, Any

# Inisialisasi Singleton Engine PaddleOCR
# - use_angle_cls=True: Mendeteksi jika ada teks yang terbalik (rotated)
# - lang='id': Dioptimalkan untuk membaca abjad dan kata bahasa Indonesia
# - det_db_unclip_ratio: Diturunkan ke 1.25 (default 1.5) agar bounding box lebih ketat per kata (Saran Ahli)
ocr_model = PaddleOCR(use_angle_cls=True, lang='id', det_db_unclip_ratio=1.25)

def extract_text_from_crop(image: np.ndarray) -> Dict[str, Any]:
    """
    Menjalankan proses inferensi OCR pada satu potongan gambar (array).
    Mengembalikan teks yang terbaca beserta nilai tingkat kepercayaannya (confidence score).
    """
    # Jalankan proses OCR
    # Karena kita sudah set use_angle_cls=True di konstruktor, tidak perlu mengirim cls lagi
    result = ocr_model.ocr(image)
    
    # Format result PaddleOCR:
    # [[ [[x1,y1], [x2,y2],...], ("Teks hasil baca", 0.98 (confidence)) ], ...]
    if not result or result[0] is None:
        return {"text": "", "confidence": 0.0}
        
    lines = result[0]
    
    extracted_texts = []
    total_confidence = 0.0
    count = 0
    
    # Karena terkadang OCR mendeteksi dua baris dalam satu kotak crop, kita gabungkan teksnya
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

from app.core.handwriting_ocr import handwriting_engine
import cv2

def extract_full_text(image: np.ndarray, use_trocr: bool = False) -> list:
    """
    Menjalankan OCR di seluruh gambar utuh dan mengembalikan daftar blok teks 
    berupa tuple (teks, confidence, bbox).
    Jika use_trocr=True, ia menggunakan PaddleOCR untuk mendeteksi lokasi kotak,
    tapi menggunakan TrOCR (Microsoft) untuk MEMBACA teks di dalam kotak tersebut 
    agar super akurat untuk tulisan tangan.
    """
    # 1. Gunakan PaddleOCR untuk mendeteksi lokasi / bounding box (Object Detection)
    # Parameter det=True, rec=not use_trocr (jika pakai trocr, tak perlu recognition dari paddle)
    result = ocr_model.ocr(image, det=True, rec=not use_trocr)
    
    if not result or result[0] is None:
        return []
        
    blocks = []
    for line in result[0]:
        if use_trocr:
            # line hanya berisi koordinat jika rec=False
            coords = line
            # Crop gambar
            pts = np.array(coords, np.int32)
            rect = cv2.boundingRect(pts)
            x, y, w, h = rect
            
            # Beri padding sedikit agar tulisan tidak terpotong (misal 2 pixel)
            y_start = max(0, y - 2)
            y_end = min(image.shape[0], y + h + 2)
            x_start = max(0, x - 2)
            x_end = min(image.shape[1], x + w + 2)
            
            crop_img = image[y_start:y_end, x_start:x_end]
            
            # Lewati jika crop terlalu kecil
            if crop_img.shape[0] < 5 or crop_img.shape[1] < 5:
                continue
                
            # Gunakan TrOCR untuk membaca teks tulisan tangan di potongan ini
            text = handwriting_engine.recognize_text(crop_img)
            conf = 0.95 # TrOCR tidak native mengembalikan nilai probabilitas sederhana
            
        else:
            # line berisi koordinat dan (teks, confidence)
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
