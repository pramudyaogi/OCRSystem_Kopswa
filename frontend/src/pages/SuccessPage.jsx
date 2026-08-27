import React from 'react';

export default function SuccessPage({ savedData, onScanAgain, onViewHistory }) {
  const data = savedData?.data || {};
  const nikVal = data.nik?.value || "-";
  const namaVal = data.nama?.value || "-";

  return (
    <div className="glass-panel">
      {/* HEADER LOGO PERUSAHAAN & BRAND ACCENT BAR */}
      <div className="brand-header">
        <img src="/logo.png" alt="Koperasi Swadharma" className="brand-logo" />
        <div className="brand-accent-line"></div>
      </div>

      {/* STEPPER PROGRESS INDICATOR - STEP 3 COMPLETED */}
      <div className="stepper-bar">
        <div className="step-item completed">
          <span className="step-number">✓</span>
          <span className="step-label">Upload</span>
        </div>
        <div className="step-line active"></div>
        <div className="step-item completed">
          <span className="step-number">✓</span>
          <span className="step-label">Verifikasi</span>
        </div>
        <div className="step-line active"></div>
        <div className="step-item active">
          <span className="step-number">3</span>
          <span className="step-label">Selesai</span>
        </div>
      </div>

      {/* SUCCESS HERO BADGE & TEXT */}
      <div className="success-hero-container">
        <div className="success-icon-badge">
          <span>✅</span>
        </div>
        <h2>Data Berhasil Disimpan!</h2>
        <p className="success-subtitle">
          Dokumen KTP telah sukses diverifikasi dan tersimpan ke dalam database.
        </p>

        {/* RINGKASAN DATA YANG BARU DISIMPAN */}
        <div className="success-summary-card">
          <div className="summary-card-header">
            <span className="summary-badge">🇮🇩 KTP Indonesia</span>
            <span className="badge-valid-pill">Tersimpan</span>
          </div>
          <div className="summary-row">
            <span className="summary-label">NIK:</span>
            <span className="summary-val highlight">{nikVal}</span>
          </div>
          <div className="summary-row">
            <span className="summary-label">Nama Pemilik:</span>
            <span className="summary-val">{namaVal}</span>
          </div>
        </div>

        {/* DUA TOMBOL PILIHAN AKSI UTAMA */}
        <div className="success-actions-row">
          <button 
            type="button" 
            className="btn btn-primary btn-process-main"
            onClick={onScanAgain}
          >
            ⚡ Pindai Dokumen Lagi
          </button>
          <button 
            type="button" 
            className="btn btn-secondary btn-option-act"
            onClick={onViewHistory}
            style={{ marginTop: '0.75rem' }}
          >
            📁 Lihat Data Tersimpan
          </button>
        </div>
      </div>
    </div>
  );
}
