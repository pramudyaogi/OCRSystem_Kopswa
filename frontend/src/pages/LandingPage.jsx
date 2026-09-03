import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();
  const [activePreviewTab, setActivePreviewTab] = useState('ktp');

  return (
    <div className="landing-page-container">
      {/* Header Bar */}
      <header className="landing-header">
        <div className="landing-brand">
          <img src="/logo.png" alt="Koperasi Swadharma" className="landing-logo" />
          <div className="landing-brand-text">
            <span className="landing-brand-title">KOPERASI SWADHARMA</span>
            <span className="landing-brand-sub">Digital OCR System</span>
          </div>
        </div>
        <button className="btn-header-cta" onClick={() => navigate('/dashboard')}>
          Masuk ke Aplikasi →
        </button>
      </header>

      {/* Hero Section */}
      <main className="landing-hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-pulse"></span>
            📄 100% Pemrosesan Dokumen Lokal & Aman
          </div>
          <h1 className="hero-title">
            Digitalisasi Dokumen Fisik <br />
            <span className="highlight-orange">Koperasi Swadharma</span> <br />
            Secara <span className="highlight-teal">Otomatis & Presisi</span>
          </h1>
          <p className="hero-description">
            Sistem pemindaian berbasis AI OCR lokal untuk ekstraksi data E-KTP Indonesia, 
            Formulir Keanggotaan, dan Pengajuan Pinjaman tanpa mengunggah data ke server pihak ketiga.
          </p>

          <div className="hero-action-box">
            <button className="btn-hero-primary" onClick={() => navigate('/dashboard')}>
              <span>🚀 Mulai Digitalisasi Dokumen</span>
            </button>
            <div className="hero-meta-text">
              🔒 Jaminan Keamanan Data • Tanpa Ketergantungan Internet Pihak Ke-3
            </div>
          </div>
        </div>

        {/* Hero Visual Mockup */}
        <div className="hero-visual-card">
          <div className="visual-card-header">
            <div className="window-dots">
              <span className="dot red"></span>
              <span className="dot yellow"></span>
              <span className="dot green"></span>
            </div>
            <span className="window-title">AI OCR Preview - Koperasi Swadharma</span>
          </div>

          {/* TAB SWITCHER 3 DOKUMEN */}
          <div className="mockup-tab-nav">
            <button 
              className={`mockup-tab-btn ${activePreviewTab === 'ktp' ? 'active' : ''}`}
              onClick={() => setActivePreviewTab('ktp')}
            >
              🇮🇩 E-KTP
            </button>
            <button 
              className={`mockup-tab-btn ${activePreviewTab === 'member' ? 'active' : ''}`}
              onClick={() => setActivePreviewTab('member')}
            >
              📋 Form Anggota
            </button>
            <button 
              className={`mockup-tab-btn ${activePreviewTab === 'loan' ? 'active' : ''}`}
              onClick={() => setActivePreviewTab('loan')}
            >
              💰 Form Pinjaman
            </button>
          </div>

          <div className="visual-card-body">
            {activePreviewTab === 'ktp' && (
              <div className="mockup-document-scan">
                <div className="mockup-ktp-box">
                  <div className="ktp-chip"></div>
                  <div className="ktp-lines">
                    <div className="ktp-line title">PROVINSI DKI JAKARTA</div>
                    <div className="ktp-line nik">NIK : 3173000000000001</div>
                    <div className="ktp-line">Nama : FADLI ADRIAN</div>
                    <div className="ktp-line">Status : TERVERIFIKASI OCR</div>
                  </div>
                  <div className="scan-laser-line"></div>
                </div>
                <div className="mockup-extraction-panel">
                  <div className="field-extracted-item good">
                    <span>✓ NIK Terdeteksi</span>
                    <strong>100% Akurasi</strong>
                  </div>
                  <div className="field-extracted-item good">
                    <span>✓ Nama Anggota</span>
                    <strong>98% Akurasi</strong>
                  </div>
                  <div className="field-extracted-item good">
                    <span>✓ Alamat Terurai</span>
                    <strong>100% Akurasi</strong>
                  </div>
                </div>
              </div>
            )}

            {activePreviewTab === 'member' && (
              <div className="mockup-document-scan">
                <div className="mockup-ktp-box member-form-style">
                  <div className="ktp-lines">
                    <div className="ktp-line title">FORMULIR PENDAFTARAN ANGGOTA</div>
                    <div className="ktp-line nik">NO ANGGOTA : KOP-2026-0892</div>
                    <div className="ktp-line">Nama : ANGGOTA KOPERASI SWADHARMA</div>
                    <div className="ktp-line">Unit Kerja : DIVISI KEUANGAN & UMUM</div>
                  </div>
                  <div className="scan-laser-line"></div>
                </div>
                <div className="mockup-extraction-panel">
                  <div className="field-extracted-item good">
                    <span>✓ No. Anggota</span>
                    <strong>100% Akurasi</strong>
                  </div>
                  <div className="field-extracted-item good">
                    <span>✓ Unit Kerja</span>
                    <strong>96% Akurasi</strong>
                  </div>
                  <div className="field-extracted-item good">
                    <span>✓ Simpanan Pokok</span>
                    <strong>100% Akurasi</strong>
                  </div>
                </div>
              </div>
            )}

            {activePreviewTab === 'loan' && (
              <div className="mockup-document-scan">
                <div className="mockup-ktp-box loan-form-style">
                  <div className="ktp-lines">
                    <div className="ktp-line title">FORMULIR PENGAJUAN PINJAMAN</div>
                    <div className="ktp-line nik">NO PENGAJUAN : PJM-2026-0041</div>
                    <div className="ktp-line">Jenis Pinjaman : PINJAMAN REGULER</div>
                    <div className="ktp-line">Jumlah : Rp 15.000.000 (12 Bulan)</div>
                  </div>
                  <div className="scan-laser-line"></div>
                </div>
                <div className="mockup-extraction-panel">
                  <div className="field-extracted-item good">
                    <span>✓ Jenis Pinjaman</span>
                    <strong>100% Akurasi</strong>
                  </div>
                  <div className="field-extracted-item good">
                    <span>✓ Nominal Pinjaman</span>
                    <strong>100% Akurasi</strong>
                  </div>
                  <div className="field-extracted-item good">
                    <span>✓ Jangka Waktu</span>
                    <strong>98% Akurasi</strong>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Stats Proof Bar */}
      <section className="landing-stats-bar">
        <div className="stat-item">
          <span className="stat-number">100%</span>
          <span className="stat-label">Lokal & Offline</span>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <span className="stat-number">3 Jenis</span>
          <span className="stat-label">Dokumen Didukung</span>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <span className="stat-number">&lt; 2 Detik</span>
          <span className="stat-label">Kecepatan Ekstraksi</span>
        </div>
      </section>

      {/* Section Cara Kerja */}
      <section className="landing-workflow-section">
        <div className="section-title-box">
          <span className="sub-title-tag">ALUR KERJA MUDAH</span>
          <h2>4 Langkah Digitalisasi Dokumen</h2>
        </div>

        <div className="workflow-steps-grid">
          <div className="step-card">
            <div className="step-number-badge">01</div>
            <div className="step-icon">📷</div>
            <h3>Foto / Upload</h3>
            <p>Ambil foto dokumen fisik langsung dari kamera atau upload file gambar/PDF.</p>
          </div>

          <div className="step-card">
            <div className="step-number-badge">02</div>
            <div className="step-icon">⚙️</div>
            <h3>Preprocessing AI</h3>
            <p>Gambar diluruskan otomatis (deskew), distorsi dikoreksi, & teks diperjelas.</p>
          </div>

          <div className="step-card">
            <div className="step-number-badge">03</div>
            <div className="step-icon">🔍</div>
            <h3>Ekstraksi & Validasi</h3>
            <p>Mesin OCR lokal membaca teks, mengecek Regex, & memberi badge confidence score.</p>
          </div>

          <div className="step-card">
            <div className="step-number-badge">04</div>
            <div className="step-icon">💾</div>
            <h3>Verifikasi & Simpan</h3>
            <p>Periksa hasil bacaan, lakukan koreksi jika perlu, lalu simpan ke database arsip.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>© 2026 Koperasi Swadharma. Sistem Digitalisasi Dokumen Fisik AI OCR.</p>
      </footer>
    </div>
  );
}
