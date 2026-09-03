import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../services/api';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [recentDocs, setRecentDocs] = useState([]);
  const [allDocs, setAllDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // 1. Fetch top 6 recent items for recent grid
      const recentRes = await apiFetch('/api/documents/?page=1&limit=6');
      if (recentRes.ok) {
        const recentData = await recentRes.json();
        const items = Array.isArray(recentData) ? recentData : (recentData.items || []);
        setRecentDocs(items);
      }

      // 2. Fetch full list (limit=1000) to calculate accurate total statistics
      const allRes = await apiFetch('/api/documents/?page=1&limit=1000');
      if (allRes.ok) {
        const allData = await allRes.json();
        const allItems = Array.isArray(allData) ? allData : (allData.items || []);
        setAllDocs(allItems);
      }
    } catch (err) {
      console.log("Database fetch offline / pending");
    } finally {
      setLoading(false);
    }
  };

  // Summary stats dynamically calculated from ALL documents in history
  const stats = [
    { title: 'Total Dokumen Tersimpan', value: allDocs.length || '0', label: 'Arsip Terverifikasi', icon: '📁', color: 'teal' },
    { title: 'Scan E-KTP', value: allDocs.filter(d => d.doc_type === 'ktp' || d.template_type === 'ktp' || (!d.doc_type && !d.template_type)).length || '0', label: 'Dokumen KTP', icon: '🆔', color: 'orange' },
    { title: 'Formulir Anggota', value: allDocs.filter(d => d.doc_type === 'member_form' || d.template_type === 'form_pendaftaran').length || '0', label: 'Pendaftaran Anggota', icon: '📋', color: 'blue' },
    { title: 'Pengajuan Pinjaman', value: allDocs.filter(d => d.doc_type === 'loan_form' || d.template_type === 'loan').length || '0', label: 'Berkas Pinjaman', icon: '💰', color: 'green' }
  ];

  return (
    <div className="dashboard-container">
      {/* Dashboard Top Header */}
      <div className="dashboard-welcome-banner">
        <div className="welcome-text-box">
          <h2>Selamat Datang di Sistem OCR Kopswa 👋</h2>
          <p>Kelola digitalisasi dokumen fisik Koperasi Swadharma secara lokal, aman, dan efisien.</p>
        </div>
        <div className="system-status-pill">
          <span className="status-dot-green"></span>
          <span>Sistem OCR Ready (Lokal Engine)</span>
        </div>
      </div>

      {/* Summary Cards Grid */}
      <div className="dashboard-stats-grid">
        {stats.map((item, idx) => (
          <div key={idx} className={`dash-stat-card card-theme-${item.color}`}>
            <div className="stat-card-header">
              <span className="dash-stat-icon">{item.icon}</span>
              <span className="dash-stat-badge">{item.label}</span>
            </div>
            <div className="dash-stat-val">{item.value}</div>
            <div className="dash-stat-title">{item.title}</div>
          </div>
        ))}
      </div>

      {/* Quick Actions Grid */}
      <div className="dashboard-section-box">
        <h3 className="section-heading">⚡ Akses Cepat Pindaian Dokumen</h3>
        <div className="quick-actions-grid">
          <div className="action-card action-ktp" onClick={() => navigate('/scan/ktp')}>
            <div className="action-icon">🆔</div>
            <div className="action-content">
              <h4>Scan E-KTP Indonesia</h4>
              <p>Pindaian fisik KTP dengan ekstraksi NIK, Nama, Alamat, & 15+ field otomatis.</p>
            </div>
            <button className="btn-action-arrow">Mulai Scan →</button>
          </div>

          <div className="action-card action-member" onClick={() => navigate('/scan/member-form')}>
            <div className="action-icon">📋</div>
            <div className="action-content">
              <h4>Scan Formulir Anggota</h4>
              <p>Pindaian berkas pendaftaran keanggotaan baru Koperasi Swadharma.</p>
            </div>
            <button className="btn-action-arrow">Mulai Scan →</button>
          </div>

          <div className="action-card action-loan" onClick={() => navigate('/scan/loan-form')}>
            <div className="action-icon">💰</div>
            <div className="action-content">
              <h4>Scan Pengajuan Pinjaman</h4>
              <p>Digitalisasi dokumen permohonan pinjaman reguler & insidentil anggota.</p>
            </div>
            <button className="btn-action-arrow">Mulai Scan →</button>
          </div>
        </div>
      </div>

      {/* Recent Activity Section (Top 6 Terbaru dari Riwayat) */}
      <div className="dashboard-section-box">
        <div className="section-header-flex" style={{ marginBottom: '1rem' }}>
          <div>
            <h3 className="section-heading" style={{ marginBottom: '0.2rem' }}>🕒 Aktivitas Pindaian Terakhir</h3>
            <p className="section-subtitle" style={{ fontSize: '0.82rem', color: '#64748b', margin: 0 }}>
              6 arsip pindaian dokumen terbaru yang telah terverifikasi.
            </p>
          </div>
          <button className="btn-link-more" onClick={() => navigate('/history')}>Lihat Semua Riwayat →</button>
        </div>

        <div className="dashboard-recent-grid">
          {recentDocs.length > 0 ? (
            recentDocs.map((doc) => {
              const data = doc.extracted_data || {};
              const nikVal = doc.nik || data.nik?.value || "-";
              const namaVal = doc.nama || data.nama?.value || "ANGGOTA KOPERASI";
              const docTypeLabel = doc.doc_type === 'member_form' ? '📝 Formulir' : (doc.doc_type === 'loan_form' ? '💰 Pinjaman' : '🇮🇩 KTP');
              const isSent = doc.status_kirim === 'Terkirim';

              return (
                <div key={doc.id} className="dash-mini-card" onClick={() => navigate('/history')}>
                  <div className="dash-mini-card-header">
                    <span className="dash-mini-tag">{docTypeLabel}</span>
                    <span className={`dash-mini-status ${isSent ? 'is-sent' : 'is-saved'}`}>
                      {isSent ? '✓ Terkirim' : 'Tersimpan'}
                    </span>
                  </div>
                  <div className="dash-mini-card-body">
                    <span className="dash-mini-nik">NIK: {nikVal}</span>
                    <h4 className="dash-mini-nama">{namaVal}</h4>
                  </div>
                  <div className="dash-mini-card-footer">
                    <span className="dash-mini-date">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Baru saja'}
                    </span>
                    <span className="dash-mini-link">Lihat Detail →</span>
                  </div>
                </div>
              );
            })
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', gridColumn: '1 / -1', background: '#f8fafc', borderRadius: '12px', border: '1px dashed #cbd5e1' }}>
              <p style={{ margin: 0, fontWeight: '600' }}>📭 Belum Ada Aktivitas Pindaian Dokumen</p>
              <span style={{ fontSize: '0.82rem' }}>Pilih menu pemindaian di atas untuk memulai.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
