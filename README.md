# Sistem Digitalisasi Dokumen Fisik (OCR Lokal) 📄🔒

Aplikasi web terpadu untuk melakukan OCR (*Optical Character Recognition*) pada dokumen fisik secara **100% lokal / offline**, menjamin privasi data tanpa perlu API ke pihak ketiga (seperti Google Cloud, AWS, dsb).

## 🚀 Fitur Utama
1. **Template Matching**: Ekstraksi sangat cepat dan rapi karena gambar dipotong-potong per *field* (berdasarkan kalibrasi koordinat di file JSON) sebelum dibaca OCR.
2. **Auto Image Preprocessing**: Termasuk pendeteksian kelayakan gambar (deteksi nge-blur), *auto-crop* dokumen dari background, pelurusan (*deskew*), dan peningkatan *contrast* teks.
3. **Validasi Regex & Confidence**: Hasil bacaan mesin yang salah (*typo*) pada bagian NIK atau Tanggal bisa di-koreksi otomatis, plus ada notifikasi tanda bahaya (*needs review*) jika akurasi OCR sedang rendah.
4. **Fleksibilitas Tabel (SQLite)**: Hasil ekstraksi dokumen apa pun disimpan menggunakan format tipe data JSON dalam DB agar skema tidak kaku.

---

## 🛠️ Panduan Menjalankan Sistem (Development Mode)

### 1. Menjalankan Backend (FastAPI + PaddleOCR)
Buka terminal/CMD, lalu ikuti langkah ini:
```bash
# Pindah ke direktori backend
cd backend

# (Opsional) Buat dan aktifkan Virtual Environment Python
python -m venv venv
venv\Scripts\activate      # Untuk Windows

# Install dependensi (Butuh koneksi internet HANYA SAAT INSTALASI ini)
pip install -r requirements.txt

# Jalankan server API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*(Backend akan jalan di `http://localhost:8000`)*

### 2. Menjalankan Frontend (React)
Karena Frontend masih berformat kerangka `.jsx` dasar tanpa *bundler* yang spesifik terinstall, Anda perlu menginisialisasi lingkungan *node* (misal pakai Vite):
```bash
# Buka tab terminal baru
cd frontend

# Jika Anda menginisialisasi dengan Vite (opsional, karena file komponen sudah ada):
# npm create vite@latest . -- --template react
# npm install

# Jalankan server development
npm run dev
```

---
**Desain & Arsitektur oleh Tim Anda.** 
*Seluruh komponen kini siap untuk digunakan, dimodifikasi lebih lanjut, dan di-testing dengan foto dokumen fisik sungguhan.*
