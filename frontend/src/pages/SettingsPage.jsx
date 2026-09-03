import React, { useState } from 'react';

export default function SettingsPage() {
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.75);
  const [defaultPage, setDefaultPage] = useState('dashboard');
  const [autoEnhance, setAutoEnhance] = useState(true);

  return (
    <div className="settings-page-container">
      <div className="page-section-header">
        <h2>⚙️ Pengaturan Sistem OCR</h2>
        <p className="section-subtitle">Konfigurasi preferensi tampilan, ambang batas akurasi, dan informasi versi sistem.</p>
      </div>

      <div className="settings-grid">
        {/* System Information Card */}
        <div className="settings-card">
          <h3>ℹ️ Informasi Versi Sistem</h3>
          <div className="setting-info-list">
            <div className="info-row">
              <span className="info-label">Aplikasi Frontend:</span>
              <span className="info-val">v1.2.0 (Swadharma UI Overhaul)</span>
            </div>
            <div className="info-row">
              <span className="info-label">Backend Engine:</span>
              <span className="info-val">FastAPI (Python 3.10)</span>
            </div>
            <div className="info-row">
              <span className="info-label">OCR Core:</span>
              <span className="info-val">PaddleOCR v4 + EasyOCR Engine</span>
            </div>
            <div className="info-row">
              <span className="info-label">Mode Operasi:</span>
              <span className="info-badge-offline">🔒 100% Pemrosesan Lokal</span>
            </div>
          </div>
        </div>

        {/* OCR Preferences Card */}
        <div className="settings-card">
          <h3>🎛️ Preferensi Ambang Batas OCR <span className="preview-tag-badge">(Preview — belum aktif)</span></h3>
          <div className="setting-item">
            <div className="setting-label-row">
              <label>Threshold Minimum Confidence <span className="preview-inline-tag">(Preview — belum aktif)</span></label>
              <div className="threshold-input-wrap">
                <input 
                  type="number" 
                  min="50" 
                  max="95" 
                  value={Math.round(confidenceThreshold * 100)}
                  onChange={(e) => {
                    const val = Math.max(50, Math.min(95, Number(e.target.value) || 50));
                    setConfidenceThreshold(val / 100);
                  }}
                  className="threshold-number-input"
                />
                <span className="unit-percent">%</span>
              </div>
            </div>
            <p className="setting-desc">Field dengan skor kepercayaan di bawah nilai ini akan ditandai "Perlu Review".</p>
            <input 
              type="range" 
              min="0.50" 
              max="0.95" 
              step="0.05" 
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
              className="settings-range-slider"
            />
          </div>

          <div className="setting-item flex-row-toggle">
            <div>
              <label>Auto Preprocessing & Deskew <span className="preview-inline-tag">(Preview — belum aktif)</span></label>
              <p className="setting-desc">Otomatis meluruskan dokumen miring dan meningkatkan kontras sebelum OCR.</p>
            </div>
            <input 
              type="checkbox" 
              checked={autoEnhance}
              onChange={(e) => setAutoEnhance(e.target.checked)}
              className="settings-checkbox"
            />
          </div>
        </div>

        {/* Navigation Default Settings */}
        <div className="settings-card">
          <h3>🖥️ Halaman Awal Aplikasi</h3>
          <div className="setting-item">
            <label>Default Menu Saat Masuk</label>
            <select value={defaultPage} onChange={(e) => setDefaultPage(e.target.value)} className="settings-select">
              <option value="dashboard">📊 Dashboard Utama</option>
              <option value="scan_ktp">🆔 Langsung ke Scan KTP</option>
              <option value="history">🗂️ Langsung ke Riwayat Dokumen</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
