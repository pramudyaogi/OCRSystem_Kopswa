import React, { useState } from 'react';

export default function MemberFormPage() {
  const [file, setFile] = useState(null);
  const [isSimulated, setIsSimulated] = useState(false);

  // Dummy extracted data for Formulir Pendaftaran Anggota Koperasi
  const dummyData = {
    no_anggota: { value: "KPS-2026-0891", confidence: 0.98, needs_review: false },
    nama_lengkap: { value: "BAMBANG SUDARMONO", confidence: 0.95, needs_review: false },
    nik: { value: "3174091804880003", confidence: 0.99, needs_review: false },
    tanggal_bergabung: { value: "15/01/2026", confidence: 0.91, needs_review: false },
    telepon: { value: "081298765432", confidence: 0.88, needs_review: false },
    unit_kerja: { value: "DIVISI TEKNOLOGI INFORMASI", confidence: 0.82, needs_review: true },
    alamat_domisili: { value: "JL. CIPETE RAYA NO. 45, JAKARTA SELATAN", confidence: 0.94, needs_review: false },
    simpanan_pokok: { value: "Rp 500.000", confidence: 0.97, needs_review: false },
    simpanan_wajib: { value: "Rp 100.000 / Bulan", confidence: 0.96, needs_review: false }
  };

  const [formData, setFormData] = useState(dummyData);

  const handleSimulateScan = () => {
    if (!file) {
      alert("Pilih file sampel formulir terlebih dahulu!");
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
        <h2>📋 Scan Formulir Anggota Koperasi</h2>
        <p className="section-subtitle">Tampilan antarmuka pemindaian berkas pendaftaran anggota baru Koperasi Swadharma.</p>
      </div>

      <div className="instruction-banner">
        <span className="info-icon">💡</span>
        <span>Pilihlah metode pemindaian Formulir Anggota: <strong>Foto Kamera</strong> atau <strong>Upload File Dokumen</strong>.</span>
      </div>

      {!isSimulated ? (
        <div className="dummy-upload-card">
          <div className="upload-options-grid">
            <div className="option-card option-camera">
              <div className="option-card-icon-badge">📷</div>
              <h3>Ambil Foto Kamera</h3>
              <p>Foto fisik Formulir Anggota secara langsung.</p>
              <button 
                type="button" 
                className="btn btn-secondary btn-option-act"
                onClick={() => {
                  setFile({ name: "formulir_anggota_sample.jpg", size: 450000 });
                }}
              >
                Gunakan Sampel Foto Kamera
              </button>
            </div>

            <div className="option-card option-file">
              <div className="option-card-icon-badge">📁</div>
              <h3>Upload File Formulir</h3>
              <p>Pilih file scan berkas pendaftaran (JPG/PNG/PDF).</p>
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
            ⚡ Proses & Ekstraksi Formulir Anggota
          </button>
        </div>
      ) : (
        <div className="dummy-review-container">
          <div className="review-top-bar">
            <h3>🔍 Hasil Ekstraksi Formulir Anggota</h3>
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
                  onClick={() => alert("Simulasi: Data Formulir Anggota Berhasil Disimpan!")}
                >
                  💾 Simpan Data Keanggotaan
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
