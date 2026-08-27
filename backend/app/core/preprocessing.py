import cv2
import numpy as np
from typing import Tuple, Optional

def detect_blur(image: np.ndarray, threshold: float = 100.0) -> Tuple[bool, float]:
    """
    Mendeteksi apakah gambar buram/blur menggunakan variansi Laplacian.
    Return: (is_blurry, blur_score)
    Semakin tinggi skor, semakin tajam gambarnya.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    score = cv2.Laplacian(gray, cv2.CV_64F).var()
    is_blurry = score < threshold
    return is_blurry, score

def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Meningkatkan kontras gambar agar teks lebih jelas terbaca OCR 
    (menggunakan CLAHE - Contrast Limited Adaptive Histogram Equalization).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Konversi balik ke format 3 channel (opsional, tapi berguna jika OCR butuh BGR)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Meluruskan gambar (deskew) yang miring (rotasi kecil).
    Berguna jika dokumen difoto agak miring.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Balik warna (teks putih, background hitam)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    
    # Ambil semua koordinat pixel teks
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return image
        
    # Hitung bounding box dengan rotasi
    angle = cv2.minAreaRect(coords)[-1]
    
    # Penyesuaian rentang angle dari OpenCV
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    # Abaikan rotasi jika kemiringan sangat kecil
    if abs(angle) < 0.5:
        return image
        
    # Putar gambar
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated

def auto_crop_document(image: np.ndarray) -> np.ndarray:
    """
    Mencari area dokumen (kotak terbesar) dan memotong tepi yang tidak perlu.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    
    # Cari garis kontur luar
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    doc_contour = None
    for c in contours:
        # Perkirakan bentuk sudut
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        # Jika 4 sudut terdeteksi, kemungkinan itu dokumen
        if len(approx) == 4:
            doc_contour = approx
            break
            
    if doc_contour is None:
        return image # Kembalikan asli jika dokumen tidak terdeteksi
        
    # Crop lurus (pendekatan sederhana dengan bounding rect)
    x, y, w, h = cv2.boundingRect(doc_contour)
    return image[y:y+h, x:x+w]

def order_points(pts: np.ndarray) -> np.ndarray:
    """Mengurutkan 4 titik sudut: [top-left, top-right, bottom-right, bottom-left]"""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def perspective_transform_ktp(image: np.ndarray) -> np.ndarray:
    """
    Mendeteksi 4 sudut kartu KTP dan meluruskannya (Perspective Transformation)
    menjadi persegi panjang datar 1000x630 pixel seperti di aplikasi Bank.
    """
    h_orig, w_orig = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    doc_contour = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            area = cv2.contourArea(c)
            # Pastikan kontur kartu cukup besar (minimal 15% dari total gambar)
            if area > (h_orig * w_orig * 0.15):
                doc_contour = approx
                break
            
    if doc_contour is None:
        return image
        
    try:
        pts = doc_contour.reshape(4, 2)
        rect = order_points(pts)
        
        # Dimensi standar KTP 1000 x 630 pixel
        dst = np.array([
            [0, 0],
            [999, 0],
            [999, 629],
            [0, 629]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (1000, 630))
        return warped
    except Exception as e:
        print(f"[PREPROCESSING WARP ERROR]: {e}")
        return image

def remove_ktp_background(image: np.ndarray) -> np.ndarray:
    """
    Menyamarkan corak/ombak pada background KTP dan mempertajam tulisan
    sekelas pemrosesan OCR pada sistem Bank.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    kernel = np.array([[-1, -1, -1], 
                       [-1,  9, -1], 
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)

def crop_ktp_with_yolo(image: np.ndarray) -> np.ndarray:
    """
    [Fase 2] Integrasi YOLOv8 Object Detection.
    Berfungsi untuk mencari kotak KTP (Region of Interest) dari gambar asli.
    Jika model YOLO khusus KTP belum ada, otomatis fallback ke algoritma asli (tanpa crop berisiko).
    """
    try:
        from ultralytics import YOLO
        import os
        
        yolo_model_path = os.path.join(os.path.dirname(__file__), "ktp_detector.pt")
        
        if os.path.exists(yolo_model_path):
            model = YOLO(yolo_model_path)
            results = model(image, verbose=False)
            
            if len(results[0].boxes) > 0:
                box = results[0].boxes[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                h, w = image.shape[:2]
                pad = 20
                x1, y1 = max(0, x1-pad), max(0, y1-pad)
                x2, y2 = min(w, x2+pad), min(h, y2+pad)
                
                print("[YOLOv8] KTP berhasil dideteksi dan dipotong dari background!")
                return image[y1:y2, x1:x2]
    except Exception as e:
        print(f"[YOLO WARN] Bypass deteksi: {e}")
        
    # [Fallback Aman] Kembalikan gambar utuh. 
    # JANGAN pakai auto_crop_document karena rawan salah potong kotak kecil di KTP.
    return image

def preprocess_pipeline(image_path: str) -> Optional[np.ndarray]:
    """
    Pipa (Pipeline) lengkap untuk memproses gambar dokumen.
    """
    # Load gambar secara aman (mendukung path Windows dengan spasi / karakter khusus)
    image = None
    try:
        img_array = np.fromfile(image_path, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[IMREAD NP ERROR]: {e}")
        
    if image is None:
        image = cv2.imread(image_path)
        
    if image is None:
        try:
            from PIL import Image
            pil_img = Image.open(image_path).convert('RGB')
            image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception as pil_err:
            print(f"[PIL READ ERROR]: {pil_err}")
            
    if image is None:
        return None
        
    # 1. Pastikan orientasi gambar mendatar (Landscape)
    h, w = image.shape[:2]
    if h > w:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        h, w = w, h # Update dimensi setelah rotasi
        
    # [PENTING] Resize gambar agar tidak memakan waktu 3 menit di CPU (Penyebab Timeout Vite)
    max_dim = 1280
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        
    # 2. Mata Elang YOLOv8 (Jika file model ada)
    roi_image = crop_ktp_with_yolo(image)
    
    # KEMBALIKAN GAMBAR (Bypass Warping & Sharpening sementara karena menyebabkan OCR gagal total)
    return roi_image
