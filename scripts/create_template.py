import cv2
import json

print("=== Alat Bantu Pembuat Template Koordinat OCR ===")
print("Jalankan script ini dengan gambar formulir kosong Anda.")
print("Gunakan mouse untuk drag & drop membuat kotak di atas area teks (field).")
print("Data kotak akan otomatis disimpan ke dalam format JSON.")
print("\n[NOTE: Ini adalah script skeleton / kerangka dasar untuk pengembangan lebih lanjut.]")

# Contoh kerangka logika:
# 1. Load image (cv2.imread)
# 2. window = cv2.namedWindow('Draw Bounding Boxes')
# 3. cv2.setMouseCallback('Draw Bounding Boxes', draw_rectangles)
# 4. Kalau sudah selesai tekan tombol 'S', looping kotak -> simpan ke dictionary -> json.dump()
