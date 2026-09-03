import React from 'react';

export default function SuccessPage({ savedData, onScanAgain, onViewHistory }) {
  const data = savedData?.data || {};
  const nikVal = data.nik?.value || "-";
  const namaVal = data.nama?.value || "-";

  return (
    <div className="glass-panel">
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
        <div className="success-actions-row" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1.25rem' }}>
          <button 
            type="button" 
            className="btn btn-primary btn-process-main"
            onClick={onScanAgain}
          >
            📸 Scan KTP Lagi
          </button>
          <button 
            type="button" 
            className="btn btn-secondary btn-option-act"
            onClick={onViewHistory}
          >
            🗂️ Lihat Riwayat Dokumen
          </button>
        </div>
      </div>
    </div>
  );
}
