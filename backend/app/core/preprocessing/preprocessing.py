import os
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

def is_valid_ktp_rectangle(pts: np.ndarray, img_w: int, img_h: int) -> bool:
    """
    Validasi apakah 4 titik membentuk persegi panjang KTP yang masuk akal:
    1. Harus cembung (convex).
    2. Aspect ratio mendekati rasio KTP (1.3 hingga 1.9).
    3. Luas minimal 15% dari total gambar.
    """
    if len(pts) != 4:
        return False
        
    if not cv2.isContourConvex(pts):
        return False
        
    rect = order_points(pts.reshape(4, 2))
    (tl, tr, br, bl) = rect
    
    # Hitung lebar & tinggi kontur
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    if maxHeight == 0 or maxWidth == 0:
        return False
        
    aspect_ratio = float(maxWidth) / float(maxHeight)
    area = cv2.contourArea(pts)
    total_area = img_w * img_h
    
    # KTP ideal aspect ratio ~ 1.58. Beri toleransi aman (1.2 - 2.0)
    if area > (total_area * 0.15) and (1.2 <= aspect_ratio <= 2.0):
        return True
        
    return False

def perspective_transform_ktp(image: np.ndarray) -> np.ndarray:
    """
    Mendeteksi 4 sudut kartu KTP dan meluruskannya (Perspective Transformation)
    menjadi persegi panjang datar 1000x630 pixel.
    JIKA DETEKSI GAGAL ATAU CONFIDENCE RENDAH -> FALLBACK RETURN ASLI.
    """
    try:
        h_orig, w_orig = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return image
            
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        
        doc_contour = None
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and is_valid_ktp_rectangle(approx, w_orig, h_orig):
                doc_contour = approx
                break
                
        if doc_contour is None:
            return image # Fallback aman tanpa warp jika tidak memenuhi syarat
            
        pts = doc_contour.reshape(4, 2)
        rect = order_points(pts)
        
        # Dimensi standar KTP (1000 x 630 px)
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
        print(f"[WARP FALLBACK]: Gagal meluruskan gambar ({e}), menggunakan gambar asli.")
        return image

def reduce_glare_and_enhance(image: np.ndarray) -> np.ndarray:
    """
    Mengurangi efek bayangan/glare dengan:
    1. Adaptive CLAHE lebih agresif untuk foto kamera HP
    2. Unsharp Mask untuk mempertajam karakter teks
    3. Gamma correction untuk gambar terlalu gelap/terang
    Agar teks KTP tetap jelas terbaca meski foto agak miring/buram.
    """
    try:
        # Konversi ke LAB untuk memproses pencahayaan tanpa merusak warna
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # CLAHE lebih agresif (clipLimit=3.0) untuk foto kamera HP
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # Unsharp Mask: pertajam tepi karakter agar OCR baca lebih akurat
        # Rumus: sharp = original + amount * (original - blur)
        blur = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=2.0)
        sharpened = cv2.addWeighted(enhanced, 1.5, blur, -0.5, 0)

        # Gamma correction: normalisasi kecerahan foto terlalu gelap/terang
        mean_brightness = np.mean(cv2.cvtColor(sharpened, cv2.COLOR_BGR2GRAY))
        if mean_brightness < 80:    # Foto terlalu gelap -> terangkan
            gamma = 0.6
        elif mean_brightness > 200: # Foto terlalu terang/silau -> redam
            gamma = 1.5
        else:
            gamma = 1.0

        if gamma != 1.0:
            inv_gamma = 1.0 / gamma
            table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype(np.uint8)
            sharpened = cv2.LUT(sharpened, table)

        return sharpened
    except Exception as e:
        print(f"[GLARE REDUCE ERROR]: {e}")
        return image

def crop_ktp_with_yolo(image: np.ndarray) -> np.ndarray:
    """
    Integrasi YOLOv8 Object Detection untuk potong KTP dari background.
    Jika model YOLO belum ada/gagal, return gambar asli.
    """
    weights_path = os.path.join(os.path.dirname(__file__), "..", "models", "ktp_detector.pt")
    if not os.path.exists(weights_path):
        return image

    try:
        from ultralytics import YOLO
        model = YOLO(weights_path)
        results = model(image, verbose=False)
        
        if len(results) > 0 and len(results[0].boxes) > 0:
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
        
    return image

def preprocess_pipeline(image_path: str, save_debug: bool = True) -> Optional[np.ndarray]:
    """
    Pipa (Pipeline) lengkap untuk memproses gambar dokumen + Debug Image Logging.
    Termasuk EXIF orientation auto-transpose & deskewing.
    """
    image = None

    # 1. Gunakan PIL + ImageOps.exif_transpose PERTAMA kali untuk membaca metadata EXIF kamera HP
    try:
        from PIL import Image, ImageOps
        pil_img = Image.open(image_path)
        pil_img = ImageOps.exif_transpose(pil_img).convert('RGB')
        image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as pil_err:
        print(f"[PIL EXIF READ ERROR]: {pil_err}")

    # Fallback jika PIL gagal
    if image is None:
        try:
            img_array = np.fromfile(image_path, dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"[IMREAD NP ERROR]: {e}")
            
    if image is None:
        image = cv2.imread(image_path)
        
    if image is None:
        return None
        
    # 2. Pastikan orientasi gambar mendatar (Landscape)
    h, w = image.shape[:2]
    if h > w:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        h, w = w, h # Update dimensi setelah rotasi
        
    # Resize gambar jika sangat besar agar tidak lambat di CPU
    max_dim = 1600
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        
    # Prepare debug dir
    import os
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    debug_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "debug"))
    if save_debug and not os.path.exists(debug_dir):
        os.makedirs(debug_dir, exist_ok=True)
        
    # 3. Potong area KTP dari background (YOLO jika ada model)
    roi_image = crop_ktp_with_yolo(image)
    if save_debug and roi_image is not None:
        cv2.imwrite(os.path.join(debug_dir, f"{base_name}_1_yolo_crop.jpg"), roi_image)
    
    # 4. Perspective Transformation (Auto-Warp 4 sudut ke 1000x630px)
    warped_image = perspective_transform_ktp(roi_image)
    
    # 5. Deskewing tambahan untuk memperbaiki kemiringan kecil (0.5 - 25 derajat)
    warped_image = deskew_image(warped_image)
    
    if save_debug and warped_image is not None:
        cv2.imwrite(os.path.join(debug_dir, f"{base_name}_2_after_warp.jpg"), warped_image)
    
    # 6. Filter Penjernih Glare & Bayangan Lampu (Adaptive LAB CLAHE + Unsharp Mask)
    final_image = reduce_glare_and_enhance(warped_image)
    if save_debug and final_image is not None:
        cv2.imwrite(os.path.join(debug_dir, f"{base_name}_3_after_glare_reduction.jpg"), final_image)
    
    return final_image
