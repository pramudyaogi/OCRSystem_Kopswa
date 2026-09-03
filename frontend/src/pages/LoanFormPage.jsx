import React, { useState } from 'react';

export default function LoanFormPage() {
  const [file, setFile] = useState(null);
  const [isSimulated, setIsSimulated] = useState(false);

  // Dummy extracted data for Formulir Pengajuan Pinjaman Koperasi
  const dummyData = {
    no_pengajuan: { value: "PJN-2026-0412", confidence: 0.97, needs_review: false },
    nama_pemohon: { value: "KHANSA ALIA SALSABILA", confidence: 0.98, needs_review: false },
    nik: { value: "3175085409950002", confidence: 0.99, needs_review: false },
    jenis_pinjaman: { value: "PINJAMAN REGULER (MULTIGUNA)", confidence: 0.92, needs_review: false },
    jumlah_pinjaman: { value: "Rp 25.000.000", confidence: 0.96, needs_review: false },
    jangka_waktu: { value: "24 Bulan", confidence: 0.94, needs_review: false },
    tujuan_pinjaman: { value: "Renovasi Rumah & Biaya Pendidikan", confidence: 0.84, needs_review: true },
    gaji_pokok: { value: "Rp 8.500.000", confidence: 0.93, needs_review: false },
    angsuran_per_bulan: { value: "Rp 1.187.500", confidence: 0.90, needs_review: false }
  };

  const [formData, setFormData] = useState(dummyData);

  const handleSimulateScan = () => {
    if (!file) {
      alert("Pilih file sampel formulir pengajuan pinjaman terlebih dahulu!");
      return;
    }
    setIsSimulated(true);
  };

  const handleFieldChange = (key, val) => {
    setFormData(prev => ({
      ...prev,
      [key]: { ...prev[key], value: val }
    }));
  };

  return (
    <div className="dummy-page-container">
      {/* STEPPER PROGRESS INDICATOR */}
      <div className="stepper-bar">
        <div className={`step-item ${!isSimulated ? 'active' : ''}`}>
          <span className="step-number">1</span>
          <span className="step-label">Pilih & Upload</span>
        </div>
        <div className={`step-line ${isSimulated ? 'active' : ''}`}></div>
        <div className={`step-item ${isSimulated ? 'active' : ''}`}>
          <span className="step-number">2</span>
          <span className="step-label">Verifikasi Data</span>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <span className="step-number">3</span>
          <span className="step-label">Selesai</span>
        </div>
      </div>

      {/* Header Info */}
      <div className="page-section-header">
        <h2>💰 Scan Pengajuan Pinjaman Koperasi</h2>
        <p className="section-subtitle">Tampilan antarmuka pemindaian formulir permohonan pinjaman anggota Koperasi Swadharma.</p>
      </div>

      <div className="instruction-banner">
        <span className="info-icon">💡</span>
        <span>Pilihlah metode pemindaian Formulir Pinjaman: <strong>Foto Kamera</strong> atau <strong>Upload File Dokumen</strong>.</span>
      </div>

      {!isSimulated ? (
        <div className="dummy-upload-card">
          <div className="upload-options-grid">
            <div className="option-card option-camera">
              <div className="option-card-icon-badge">📷</div>
              <h3>Ambil Foto Kamera</h3>
              <p>Foto fisik Formulir Pinjaman secara langsung.</p>
              <button 
                type="button" 
                className="btn btn-secondary btn-option-act"
                onClick={() => {
                  setFile({ name: "formulir_pinjaman_sample.jpg", size: 520000 });
                }}
              >
                Gunakan Sampel Foto Kamera
              </button>
            </div>

            <div className="option-card option-file">
              <div className="option-card-icon-badge">📁</div>
              <h3>Upload File Formulir</h3>
              <p>Pilih file scan berkas permohonan (JPG/PNG/PDF).</p>
              <div className="file-upload-input-wrapper">
                <input 
                  type="file" 
                  accept="image/*,application/pdf"
                  onChange={(e) => setFile(e.target.files[0])}
                />
                <button type="button" className="btn btn-secondary btn-option-act">
                  {file ? file.name : "Pilih File Dokumen"}
                </button>
              </div>
            </div>
          </div>

          <button 
            className="btn btn-primary btn-process-main"
            style={{ marginTop: '1.25rem' }}
            onClick={handleSimulateScan}
            disabled={!file}
          >
            ⚡ Proses & Ekstraksi Pengajuan Pinjaman
          </button>
        </div>
      ) : (
        <div className="dummy-review-container">
          <div className="review-top-bar">
            <h3>🔍 Hasil Ekstraksi Formulir Pinjaman</h3>
            <button className="btn btn-secondary" onClick={() => setIsSimulated(false)}>
              🔄 Scan Dokumen Lain
            </button>
          </div>

          <div className="dummy-review-grid">
            {/* Form Fields Dummy */}
            <div className="dummy-form-fields">
              {Object.entries(formData).map(([key, item]) => (
                <div key={key} className="form-field-group">
                  <div className="field-label-row">
                    <label>{key.replace(/_/g, ' ').toUpperCase()}</label>
                    <span className={`confidence-badge ${item.needs_review ? 'review' : 'good'}`}>
                      {item.needs_review ? '⚠️ Perlu Review' : `✓ ${(item.confidence * 100).toFixed(0)}%`}
                    </span>
                  </div>
                  <input 
                    type="text" 
                    value={item.value} 
                    onChange={(e) => handleFieldChange(key, e.target.value)}
                  />
                </div>
              ))}

              <div className="form-actions-row">
                <button 
                  className="btn btn-primary btn-process-main"
                  onClick={() => alert("Simulasi: Data Pengajuan Pinjaman Berhasil Disimpan!")}
                >
                  💾 Simpan Data Pinjaman
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
