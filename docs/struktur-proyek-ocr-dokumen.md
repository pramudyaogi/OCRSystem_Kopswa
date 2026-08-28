# Struktur Proyek — Sistem Digitalisasi Dokumen (OCR Lokal, PaddleOCR)

## 1. Ringkasan Proyek

Sistem web untuk membaca dokumen fisik (KTP, form isian tulisan tangan rapi, PDF) menjadi data terstruktur, berjalan **100% lokal** (tanpa API cloud pihak ketiga) karena sifat data yang privat.

- **Platform**: Web app, dijalankan lokal di satu komputer
- **OCR Engine**: PaddleOCR
- **Pendekatan ekstraksi**: Template matching (crop per-field) karena dokumen form-based dengan posisi field konsisten

---

## 2. Struktur Folder Proyek

```
document-ocr-system/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # Entry point FastAPI
│   │   ├── config.py                # Konfigurasi umum (path, setting server)
│   │   │
│   │   ├── api/
│   │   │   ├── routes_upload.py     # Endpoint upload dokumen
│   │   │   ├── routes_extract.py    # Endpoint proses ekstraksi OCR
│   │   │   ├── routes_documents.py  # Endpoint CRUD data hasil ekstraksi
│   │   │   └── routes_templates.py  # Endpoint kelola template dokumen
│   │   │
│   │   ├── core/
│   │   │   ├── preprocessing.py     # Fungsi OpenCV: deskew, crop, enhance, deteksi blur
│   │   │   ├── template_matching.py # Alignment gambar ke template + crop per-field
│   │   │   ├── ocr_engine.py        # Wrapper pemanggilan PaddleOCR
│   │   │   ├── postprocessing.py    # Regex validation, fuzzy matching, checksum NIK
│   │   │   └── pdf_extractor.py     # Ekstraksi teks dari PDF (text-based) via PyMuPDF/pdfplumber
│   │   │
│   │   ├── models/
│   │   │   ├── db_models.py         # Model tabel database (SQLAlchemy)
│   │   │   └── schemas.py           # Pydantic schema request/response API
│   │   │
│   │   ├── templates_config/
│   │   │   ├── ktp_template.json    # Koordinat field untuk KTP
│   │   │   ├── form_pendaftaran.json# Koordinat field untuk form pendaftaran (contoh)
│   │   │   └── ...                  # Template dokumen lain
│   │   │
│   │   └── db/
│   │       └── database.py          # Koneksi & inisialisasi SQLite
│   │
│   ├── storage/
│   │   ├── uploads/                 # File dokumen asli yang diupload
│   │   └── processed/               # Hasil crop per-field (opsional, untuk audit/debug)
│   │
│   ├── requirements.txt             # Daftar dependency Python
│   └── README.md                    # Cara menjalankan backend
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx       # Halaman pilih kategori dokumen + upload/foto
│   │   │   ├── ReviewPage.jsx       # Halaman form hasil ekstraksi (editable, verifikasi)
│   │   │   └── HistoryPage.jsx      # Halaman riwayat dokumen yang sudah diproses
│   │   │
│   │   ├── components/
│   │   │   ├── CameraCapture.jsx    # Komponen kamera + guide overlay frame
│   │   │   ├── DocumentTypeSelect.jsx
│   │   │   ├── FieldConfidenceBadge.jsx # Indikator confidence score per field
│   │   │   └── ExtractedForm.jsx    # Form dinamis sesuai kolom template
│   │   │
│   │   ├── services/
│   │   │   └── api.js               # Fungsi pemanggilan API ke backend (fetch/axios)
│   │   │
│   │   └── App.jsx
│   │
│   ├── package.json
│   └── README.md
│
├── database/
│   └── app.db                       # File database SQLite
│
├── scripts/
│   ├── setup_env.sh                 # Script instalasi environment & dependency
│   ├── create_template.py           # Tools bantu bikin file template koordinat baru
│   └── retrain_notes.md             # Catatan proses fine-tuning model (jangka panjang)
│
├── docs/
│   ├── arsitektur.md                # Penjelasan arsitektur sistem
│   ├── alur-ekstraksi.md            # Detail alur preprocessing -> OCR -> validasi
│   └── panduan-template.md          # Cara menambah template dokumen baru
│
└── README.md                        # Overview proyek keseluruhan
```

---

## 3. Penjelasan Alur Data

```
[Frontend: Upload/Foto Dokumen]
        │
        ▼
[Backend: routes_upload.py] → simpan file asli ke storage/uploads/
        │
        ▼
[core/preprocessing.py] → deskew, crop otomatis, enhance kontras, cek blur
        │
        ▼
[core/template_matching.py] → align ke template sesuai kategori dokumen,
                                crop per-field berdasarkan koordinat JSON
        │
        ▼
[core/ocr_engine.py] → PaddleOCR membaca tiap field hasil crop
        │
        ▼
[core/postprocessing.py] → validasi regex, fuzzy matching, checksum NIK
        │
        ▼
[Frontend: ReviewPage.jsx] → tampilkan hasil ke user, field low-confidence
                              di-highlight untuk verifikasi manual
        │
        ▼
[Backend: routes_documents.py] → simpan data final ke database/app.db (SQLite)
```

---

## 4. Komponen Teknologi per Bagian

| Bagian | Teknologi |
|---|---|
| Frontend | HTML/CSS/JS atau React |
| Backend | Python + FastAPI |
| Preprocessing gambar | OpenCV |
| OCR Engine | **PaddleOCR** |
| Ekstraksi PDF text-based | PyMuPDF / pdfplumber |
| Validasi & koreksi | Regex, rapidfuzz |
| Database | SQLite |
| Storage file | Folder lokal (storage/uploads) |

---

## 5. Catatan Desain Template (templates_config/*.json)

Format konfigurasi template per dokumen, contoh struktur isi file:

```
{
  "nama_template": "KTP",
  "fields": [
    { "nama_field": "nik", "x": 0, "y": 0, "width": 0, "height": 0, "validasi": "16_digit_angka" },
    { "nama_field": "nama", "x": 0, "y": 0, "width": 0, "height": 0, "validasi": "huruf" },
    { "nama_field": "tanggal_lahir", "x": 0, "y": 0, "width": 0, "height": 0, "validasi": "format_tanggal" }
  ]
}
```

Koordinat (x, y, width, height) diisi berdasarkan hasil kalibrasi manual pada contoh dokumen kosong per kategori.

---

## 6. Tahapan Pengembangan yang Disarankan

1. Setup struktur folder & environment (backend + frontend)
2. Implementasi upload dokumen + penyimpanan lokal
3. Implementasi preprocessing (OpenCV)
4. Buat template koordinat untuk 1 jenis dokumen dulu (misal KTP)
5. Integrasi PaddleOCR untuk baca hasil crop per-field
6. Implementasi validasi & confidence highlighting
7. Buat halaman review/edit hasil ekstraksi
8. Simpan ke database, uji end-to-end dengan sampel dokumen asli
9. Tambah template untuk jenis dokumen lain
10. (Lanjutan) Feedback loop dari koreksi manual untuk fine-tuning model
