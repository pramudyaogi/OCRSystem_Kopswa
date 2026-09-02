import React, { useState } from 'react';
import { getApiUrl, resolveUploadUrl, apiFetch } from '../services/api';

const FIELD_LABELS = {
  nik: "NIK",
  nama: "NAMA",
  tempat_tgl_lahir: "TEMPAT / TANGGAL LAHIR",
  alamat: "ALAMAT",
  rt_rw: "RT / RW",
  kel_desa: "KEL / DESA",
  kecamatan: "KECAMATAN",
  alamat_lengkap: "ALAMAT LENGKAP",
  jenis_kelamin: "JENIS KELAMIN",
  agama: "AGAMA",
  status_perkawinan: "STATUS PERKAWINAN",
  pekerjaan: "PEKERJAAN",
  kewarganegaraan: "KEWARGANEGARAAN",
  berlaku_hingga: "BERLAKU HINGGA"
};

export default function ReviewPage({ payload, onReset, onSaveSuccess }) {
  const [formData, setFormData] = useState(payload.data);
  const [saving, setSaving] = useState(false);
  const [isZoomed, setIsZoomed] = useState(false);

  const imageUrl = payload.imagePreview || resolveUploadUrl(payload.filename);

  const handleChange = (key, newValue) => {
    setFormData(prev => ({
      ...prev,
      [key]: { 
        ...prev[key], 
        value: newValue
      } 
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await apiFetch('/api/documents/save', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: payload.filename,
          template_type: payload.template,
          extracted_data: formData
        })
      });
      
      if (res.ok) {
        if (onSaveSuccess) {
          onSaveSuccess({
            filename: payload.filename,
            template: payload.template,
            data: formData
          });
        } else {
          alert("Berhasil! Data telah tersimpan.");
          onReset();
        }
      } else {
        const errorData = await res.json();
        alert("Gagal menyimpan data: " + errorData.detail);
      }
    } catch (e) {
      alert("Error koneksi ke server saat proses penyimpanan.");
    } finally {
      setSaving(false);
    }
  };

  const renderStatusBadge = (item) => {
    const isEmpty = !item.value || item.value.trim() === '';
    if (isEmpty) {
      return <span className="badge-warning">Wajib Diisi</span>;
    }
    return null;
  };

  return (
    <div className="glass-panel">
      {/* HEADER LOGO PERUSAHAAN & BRAND ACCENT BAR */}
      <div className="brand-header">
        <img src="/logo.png" alt="Koperasi Swadharma" className="brand-logo" />
        <div className="brand-accent-line"></div>
      </div>

      {/* STEPPER PROGRESS INDICATOR */}
      <div className="stepper-bar">
        <div className="step-item completed">
          <span className="step-number">✓</span>
          <span className="step-label">Upload Dokumen</span>
        </div>
        <div className="step-line active"></div>
        <div className="step-item active">
          <span className="step-number">2</span>
          <span className="step-label">Verifikasi Data</span>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <span className="step-number">3</span>
          <span className="step-label">Simpan</span>
        </div>
      </div>

      {/* MOBILE NAVBAR HEADER */}
      <div className="mobile-nav-header">
        <button className="btn-icon-back" onClick={onReset} title="Pindai Ulang">
          ← Ulangi
        </button>
        <h2 className="mobile-header-title">Verifikasi Data KTP</h2>
        <div className="nav-placeholder"></div>
      </div>

      {/* MAIN VERIFICATION CONTENT WRAPPER */}
      <div className="desktop-review-grid">
        {/* PRATINJAU FOTO KTP DI ATAS DATA */}
        <div className="ktp-preview-card">
          <div className="preview-header">
            <span className="preview-badge">Dokumen Fisik KTP</span>
            <span className="preview-status-pill">Hasil Ekstraksi</span>
          </div>
          
          <div className="preview-image-wrapper" onClick={() => setIsZoomed(true)}>
            <img 
              src={imageUrl} 
              alt="Dokumen KTP" 
              className="preview-image"
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = `/uploads/${payload.filename}`;
              }}
            />
            <div className="preview-overlay-hint">
              <span>Klik untuk Memperbesar</span>
            </div>
          </div>
        </div>
        
        <div className="fields-container">
          {/* NIK (Kiri) */}
          {formData.nik && (
            <div className="field-item">
              <div className="field-label">
                <span className="field-name">{FIELD_LABELS.nik}</span>
                {renderStatusBadge(formData.nik)}
              </div>
              <input 
                type="text" 
                value={formData.nik.value} 
                onChange={(e) => handleChange('nik', e.target.value)}
                placeholder="Masukkan nik"
                className={!formData.nik.value ? 'input-warning' : 'input-valid'}
              />
            </div>
          )}

          {/* NAMA (Kanan - Textarea) */}
          {formData.nama && (
            <div className="field-item" style={{ gridRow: 'span 2' }}>
              <div className="field-label">
                <span className="field-name">{FIELD_LABELS.nama}</span>
                {renderStatusBadge(formData.nama)}
              </div>
              <textarea 
                rows={2}
                value={formData.nama.value} 
                onChange={(e) => handleChange('nama', e.target.value)}
                placeholder="Masukkan nama"
                className={`edit-textarea ${!formData.nama.value ? 'input-warning' : 'input-valid'}`}
                style={{ minHeight: '42px', height: '110px', maxHeight: '125px' }}
              />
            </div>
          )}

          {/* TEMPAT / TANGGAL LAHIR (Kiri - Tepat Di Bawah NIK) */}
          {formData.tempat_tgl_lahir && (
            <div className="field-item">
              <div className="field-label">
                <span className="field-name">{FIELD_LABELS.tempat_tgl_lahir}</span>
                {renderStatusBadge(formData.tempat_tgl_lahir)}
              </div>
              <input 
                type="text" 
                value={formData.tempat_tgl_lahir.value} 
                onChange={(e) => handleChange('tempat_tgl_lahir', e.target.value)}
                placeholder="Masukkan tempat / tanggal lahir"
                className={!formData.tempat_tgl_lahir.value ? 'input-warning' : 'input-valid'}
              />
            </div>
          )}

          {/* SISANYA (ALAMAT LENGKAP, JENIS KELAMIN, AGAMA, DLL) */}
          {Object.entries(formData)
            .filter(([key]) => !['nik', 'nama', 'tempat_tgl_lahir', 'alamat', 'rt_rw', 'kel_desa', 'kecamatan', 'berlaku_hingga'].includes(key))
            .map(([key, item]) => {
              const isEmpty = !item.value || item.value.trim() === '';
              const displayLabel = FIELD_LABELS[key] || key.replace(/_/g, ' ').toUpperCase();
              const isFullWidth = key.includes('alamat');
              
              return (
                <div key={key} className={`field-item ${isFullWidth ? 'field-item-full' : ''}`}>
                  <div className="field-label">
                    <span className="field-name">{displayLabel}</span>
                    {renderStatusBadge(item)}
                  </div>
                  {isFullWidth ? (
                    <textarea 
                      rows={2}
                      value={item.value} 
                      onChange={(e) => handleChange(key, e.target.value)}
                      placeholder={`Masukkan ${displayLabel.toLowerCase()}`}
                      className={`edit-textarea ${isEmpty ? 'input-warning' : 'input-valid'}`}
                    />
                  ) : (
                    <input 
                      type="text" 
                      value={item.value} 
                      onChange={(e) => handleChange(key, e.target.value)}
                      placeholder={`Masukkan ${displayLabel.toLowerCase()}`}
                      className={isEmpty ? 'input-warning' : 'input-valid'}
                    />
                  )}
                </div>
              );
            })}
        </div>
      </div>
      
      {/* TOMBOL AKSI BERSEBELAHAN (SIDE-BY-SIDE) */}
      <div className="review-action-row">
        <button 
          className="btn btn-secondary flex-1" 
          onClick={onReset}
          disabled={saving}
        >
          Pindai Ulang
        </button>
        <button 
          className="btn btn-primary flex-1" 
          onClick={handleSave} 
          disabled={saving}
        >
          {saving ? 'Menyimpan...' : 'Simpan Data'}
        </button>
      </div>

      {/* MODAL PERBESAR FOTO KTP */}
      {isZoomed && (
        <div className="zoom-modal-overlay" onClick={() => setIsZoomed(false)}>
          <div className="zoom-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="zoom-modal-header">
              <span>Dokumen Fisik KTP</span>
              <button className="btn-close-zoom" onClick={() => setIsZoomed(false)}>✕</button>
            </div>
            <div className="zoom-image-container">
              <img 
                src={imageUrl} 
                alt="Dokumen KTP Asli" 
                className="zoomed-image"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = resolveUploadUrl(payload.filename);
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
