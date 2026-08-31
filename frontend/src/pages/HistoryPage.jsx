import React, { useEffect, useState, useRef } from 'react';
import { getApiUrl, resolveUploadUrl, apiFetch } from '../services/api';

const FIELD_LABELS = {
  nik: "NIK",
  nama: "NAMA",
  tempat_tgl_lahir: "TEMPAT / TANGGAL LAHIR",
  alamat_lengkap: "ALAMAT LENGKAP",
  jenis_kelamin: "JENIS KELAMIN",
  agama: "AGAMA",
  status_perkawinan: "STATUS PERKAWINAN",
  pekerjaan: "PEKERJAAN"
};

const resolveImgUrl = (filename) => {
  return resolveUploadUrl(filename);
};


function PinchZoomImage({ src, alt, onError }) {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const isDragging = useRef(false);
  const containerRef = useRef(null);
  const touchStartRef = useRef({
    dist: 0,
    scale: 1,
    center: { x: 0, y: 0 },
    pos: { x: 0, y: 0 },
    singleStart: { x: 0, y: 0 }
  });

  const clampPosition = (x, y, currentScale) => {
    if (!containerRef.current || currentScale <= 1.05) {
      return { x: 0, y: 0 };
    }
    const rect = containerRef.current.getBoundingClientRect();
    const maxBoundX = Math.max(0, (rect.width * (currentScale - 1)) / 2);
    const maxBoundY = Math.max(0, (rect.height * (currentScale - 1)) / 2);

    return {
      x: Math.min(Math.max(x, -maxBoundX), maxBoundX),
      y: Math.min(Math.max(y, -maxBoundY), maxBoundY)
    };
  };

  const handleTouchStart = (e) => {
    if (e.touches.length === 2) {
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
      const center = {
        x: (t1.clientX + t2.clientX) / 2,
        y: (t1.clientY + t2.clientY) / 2
      };
      touchStartRef.current = {
        dist,
        scale,
        center,
        pos: { ...position },
        singleStart: { x: 0, y: 0 }
      };
    } else if (e.touches.length === 1 && scale > 1) {
      isDragging.current = true;
      touchStartRef.current.singleStart = {
        x: e.touches[0].clientX - position.x,
        y: e.touches[0].clientY - position.y
      };
    }
  };

  const handleTouchMove = (e) => {
    if (e.touches.length === 2 && touchStartRef.current.dist > 0) {
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
      const factor = dist / touchStartRef.current.dist;
      const newScale = Math.min(Math.max(touchStartRef.current.scale * factor, 1), 4);

      const currentCenter = {
        x: (t1.clientX + t2.clientX) / 2,
        y: (t1.clientY + t2.clientY) / 2
      };

      const dx = currentCenter.x - touchStartRef.current.center.x;
      const dy = currentCenter.y - touchStartRef.current.center.y;

      setScale(newScale);
      const clamped = clampPosition(touchStartRef.current.pos.x + dx, touchStartRef.current.pos.y + dy, newScale);
      setPosition(clamped);
    } else if (e.touches.length === 1 && isDragging.current && scale > 1) {
      const rawX = e.touches[0].clientX - touchStartRef.current.singleStart.x;
      const rawY = e.touches[0].clientY - touchStartRef.current.singleStart.y;
      const clamped = clampPosition(rawX, rawY, scale);
      setPosition(clamped);
    }
  };

  const handleTouchEnd = (e) => {
    if (e.touches.length < 2) {
      touchStartRef.current.dist = 0;
    }
    if (e.touches.length === 0) {
      isDragging.current = false;
      if (scale <= 1.05) {
        setScale(1);
        setPosition({ x: 0, y: 0 });
      } else {
        setPosition(prev => clampPosition(prev.x, prev.y, scale));
      }
    }
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.2 : 0.8;
    const newScale = Math.min(Math.max(scale * zoomFactor, 1), 4);

    setScale(newScale);
    setPosition(prev => clampPosition(prev.x, prev.y, newScale));
  };

  const handleMouseDown = (e) => {
    if (scale > 1) {
      isDragging.current = true;
      touchStartRef.current.singleStart = {
        x: e.clientX - position.x,
        y: e.clientY - position.y
      };
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging.current && scale > 1) {
      const rawX = e.clientX - touchStartRef.current.singleStart.x;
      const rawY = e.clientY - touchStartRef.current.singleStart.y;
      const clamped = clampPosition(rawX, rawY, scale);
      setPosition(clamped);
    }
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  return (
    <div
      ref={containerRef}
      className="pinch-zoom-viewport"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{ cursor: scale > 1 ? 'grab' : 'default' }}
    >
      <img
        src={src}
        alt={alt}
        className="full-image-lightbox-img"
        style={{
          transform: `translate3d(${position.x}px, ${position.y}px, 0px) scale(${scale})`,
          transition: isDragging.current ? 'none' : 'transform 0.05s linear',
          userSelect: 'none',
          WebkitUserDrag: 'none'
        }}
        onError={onError}
      />
    </div>
  );
}

function DocCardItem({ doc, isChecked, isSelectMode, handleOpenDetail, handleToggleSelect, formatDate, handleOpenSendEmailModal }) {
  const [hasImgError, setHasImgError] = useState(false);
  const data = doc.extracted_data || {};
  const nikVal = data.nik?.value || "-";
  const namaVal = data.nama?.value || "-";
  const docTypeLabel = doc.template_type === 'form_pendaftaran' ? '📝 Formulir' : '🇮🇩 KTP Indonesia';
  
  // Utamakan thumbnail ringan (300px, quality 70%), fallback ke foto asli jika tidak ada
  const thumbPath = doc.thumbnail_path || doc.filename;
  const thumbUrl = thumbPath ? resolveImgUrl(thumbPath) : null;
  const isSent = doc.status_kirim === 'Terkirim';

  return (
    <div
      className={`doc-card ${isChecked ? 'selected' : ''}`}
      onClick={() => handleOpenDetail(doc)}
    >
      {/* THUMBNAIL FOTO DOKUMEN (HANYA DITAMPILKAN JIKA GAMBAR TERSEDIA & TIDAK ERROR) */}
      {!hasImgError && thumbUrl && (
        <div className="doc-card-thumb">
          <img
            src={thumbUrl}
            alt="Thumbnail KTP"
            loading="lazy"
            onError={() => setHasImgError(true)}
          />
          <span className="doc-type-badge">{docTypeLabel}</span>
          <span className={`badge-status-pill ${isSent ? 'is-sent' : 'is-saved'}`}>
            {isSent ? '✓ Terkirim' : 'Tersimpan'}
          </span>
        </div>
      )}

      <div className="doc-card-content">
        {!(!hasImgError && thumbUrl) && (
          <div className="doc-card-top-row-compact">
            <span className="doc-type-tag">{docTypeLabel}</span>
            <span className={`badge-status-pill-inline ${isSent ? 'is-sent' : 'is-saved'}`}>
              {isSent ? '✓ Terkirim' : 'Tersimpan'}
            </span>
          </div>
        )}

        <div className="doc-card-main-info">
          {isSelectMode && (
            <input
              type="checkbox"
              checked={isChecked}
              onChange={() => handleToggleSelect(doc.id)}
              className="doc-checkbox"
              onClick={(e) => e.stopPropagation()}
            />
          )}
          <div className="doc-info-text">
            <span className="doc-nik">NIK: {nikVal}</span>
            <span className="doc-nama">{namaVal}</span>
          </div>
        </div>

        <div className="doc-card-footer-row">
          <span className="doc-date">{formatDate(doc.created_at)}</span>
          <div className="doc-card-actions">
            <span className="view-detail-link">Detail Data →</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HistoryPage({ onBack }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Pagination State (6 items per page for ultra-fast mobile load)
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({ total: 0, pages: 1, hasNext: false, hasPrev: false });

  // Select Mode State
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);

  // Detail Modal & Edit State
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editFormData, setEditFormData] = useState({});
  const [updating, setUpdating] = useState(false);
  const [modalImgError, setModalImgError] = useState(false);
  const [fullImageZoom, setFullImageZoom] = useState(null);
  const [isZoomedIn, setIsZoomedIn] = useState(false);

  // Email Modal & Toast State
  const [emailModal, setEmailModal] = useState({
    isOpen: false,
    docs: [],
    targetPrefix: '',
    isSending: false,
    error: ''
  });
  const [toast, setToast] = useState({ show: false, type: 'success', message: '' });

  const triggerToast = (type, message) => {
    setToast({ show: true, type, message });
    setTimeout(() => setToast({ show: false, type: 'success', message: '' }), 4000);
  };

  useEffect(() => {
    fetchDocuments(1);
  }, []);

  const fetchDocuments = async (pageNum = 1) => {
    setLoading(true);
    try {
      // Ambil seluruh data dokumen dari FastAPI Backend (/api/documents/)
      const res = await apiFetch(`/api/documents/?page=${pageNum}&limit=6`);
      if (res.ok) {
        const data = await res.json();
        let itemsList = [];
        let totalCount = 0;
        let pagesCount = 1;
        let hasNext = false;
        let hasPrev = false;

        if (Array.isArray(data)) {
          itemsList = data;
          totalCount = data.length;
        } else if (data && Array.isArray(data.items)) {
          itemsList = data.items;
          totalCount = data.total || itemsList.length;
          pagesCount = data.pages || 1;
          hasNext = !!data.has_next;
          hasPrev = !!data.has_prev;
        }

        setDocuments(itemsList);
        setPagination({ total: totalCount, pages: pagesCount, hasNext, hasPrev });
        setPage(pageNum);
      } else {
        setDocuments([]);
        triggerToast('error', "Gagal mengambil daftar dokumen.");
      }
    } catch (e) {
      console.error(e);
      setDocuments([]);
      triggerToast('error', "Terjadi kesalahan jaringan saat mengambil data.");
    } finally {
      setLoading(false);
    }
  };


  const formatDate = (isoStr) => {
    if (!isoStr) return "-";
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return isoStr;
    }
  };

  const handleToggleSelect = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    const docsArr = documents || [];
    if (selectedIds.length === docsArr.length && docsArr.length > 0) {
      setSelectedIds([]);
    } else {
      setSelectedIds(docsArr.map(d => d.id));
    }
  };

  const handleExitSelectMode = () => {
    setIsSelectMode(false);
    setSelectedIds([]);
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return alert("Pilih minimal 1 data untuk dihapus.");
    if (!window.confirm(`Hapus ${selectedIds.length} data terpilih?`)) return;

    try {
      const res = await apiFetch('/api/documents/delete-multiple', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: selectedIds })
      });
      if (res.ok) {
        setDocuments(prev => (prev || []).filter(d => !selectedIds.includes(d.id)));
        setSelectedIds([]);
        setIsSelectMode(false);
        triggerToast('success', "Data terpilih berhasil dihapus!");
      } else {
        triggerToast('error', "Gagal menghapus data terpilih.");
      }
    } catch (err) {
      triggerToast('error', "Terjadi kesalahan saat menghapus data.");
    }
  };

  const handleOpenSendEmailModal = (docsToProcess) => {
    setEmailModal({
      isOpen: true,
      docs: docsToProcess,
      targetPrefix: '',
      isSending: false,
      error: ''
    });
  };

  const handleBulkSend = () => {
    if (selectedIds.length === 0) return alert("Pilih minimal 1 data untuk dikirim.");
    const selectedDocsList = (documents || []).filter(d => selectedIds.includes(d.id));
    handleOpenSendEmailModal(selectedDocsList);
  };

  const handleExecuteSendEmail = async () => {
    const cleanPrefix = (emailModal.targetPrefix || '').trim();
    if (!cleanPrefix) {
      setEmailModal(prev => ({ ...prev, error: 'Masukkan nama pengguna (username) email terlebih dahulu.' }));
      return;
    }

    const fullTargetEmail = `${cleanPrefix}@gmail.com`;

    setEmailModal(prev => ({ ...prev, isSending: true, error: '' }));
    try {
      const ids = emailModal.docs.map(d => d.id);
      const res = await apiFetch('/api/documents/send-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_ids: ids,
          target_email: fullTargetEmail
        })
      });

      const data = await res.json();

      if (res.ok) {
        setDocuments(prev => (prev || []).map(d => ids.includes(d.id) ? { ...d, status_kirim: 'Terkirim' } : d));
        if (selectedDoc && ids.includes(selectedDoc.id)) {
          setSelectedDoc(prev => ({ ...prev, status_kirim: 'Terkirim' }));
        }
        setEmailModal({ isOpen: false, docs: [], targetPrefix: '', isSending: false, error: '' });
        setIsSelectMode(false);
        setSelectedIds([]);
        triggerToast('success', `📧 ${data.message || 'Email berhasil dikirim!'}`);
      } else {
        setEmailModal(prev => ({ ...prev, isSending: false, error: data.detail || 'Gagal mengirim email.' }));
      }
    } catch (err) {
      setEmailModal(prev => ({ ...prev, isSending: false, error: 'Koneksi terputus. Pastikan server backend aktif.' }));
    }
  };

  const handleOpenDetail = (doc) => {
    if (isSelectMode) {
      handleToggleSelect(doc.id);
      return;
    }
    setModalImgError(false);
    setSelectedDoc(doc);
    setEditFormData(JSON.parse(JSON.stringify(doc.extracted_data || {})));
    setIsEditing(false);
  };

  const handleSaveEdit = async () => {
    if (!selectedDoc) return;
    setUpdating(true);
    try {
      const res = await apiFetch(`/api/documents/${selectedDoc.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ extracted_data: editFormData })
      });

      if (res.ok) {
        setDocuments(prev => (prev || []).map(d => d.id === selectedDoc.id ? { ...d, extracted_data: editFormData } : d));
        setSelectedDoc(prev => ({ ...prev, extracted_data: editFormData }));
        setIsEditing(false);
        triggerToast('success', "Data KTP berhasil diperbarui!");
      } else {
        triggerToast('error', "Gagal memperbarui data.");
      }
    } catch (err) {
      triggerToast('error', "Error koneksi saat menyimpan perubahan.");
    } finally {
      setUpdating(false);
    }
  };

  const handleDeleteFromModal = async () => {
    if (!selectedDoc) return;
    if (!window.confirm("Apakah Anda yakin ingin menghapus data ini?")) return;

    try {
      const res = await apiFetch(`/api/documents/${selectedDoc.id}`, { method: 'DELETE' });
      if (res.ok) {
        setDocuments(prev => (prev || []).filter(d => d.id !== selectedDoc.id));
        setSelectedDoc(null);
        triggerToast('success', "Dokumen berhasil dihapus.");
      } else {
        triggerToast('error', "Gagal menghapus dokumen.");
      }
    } catch (err) {
      triggerToast('error', "Terjadi kesalahan saat menghapus data.");
    }
  };

  return (
    <div className="glass-panel history-panel">
      {/* TOAST NOTIFICATION CONTAINER */}
      {toast.show && (
        <div className={`toast-notification toast-${toast.type}`}>
          <span>{toast.message}</span>
        </div>
      )}

      {/* HEADER LOGO PERUSAHAAN */}
      <div className="brand-header">
        <img src="/logo.png" alt="Koperasi Swadharma" className="brand-logo" />
      </div>

      {/* MOBILE NAVBAR HEADER (CLEAN ALIGNED ROW) */}
      <div className="mobile-nav-header">
        <button className="btn-icon-back" onClick={onBack} title="Kembali">
          ← Kembali
        </button>

        <h2 className="mobile-header-title">Data Tersimpan</h2>

        {!isSelectMode && documents.length > 0 ? (
          <button
            className="btn-select-toggle"
            onClick={() => setIsSelectMode(true)}
          >
            Pilih
          </button>
        ) : (
          <div className="nav-placeholder"></div>
        )}
      </div>

      {/* POP-UP BAR SELECT MODE */}
      {isSelectMode && (
        <div className="select-mode-popup-bar">
          <div className="popup-top-row">
            <label className="select-all-label">
              <input
                type="checkbox"
                checked={selectedIds.length === documents.length && documents.length > 0}
                onChange={handleSelectAll}
                className="doc-checkbox"
              />
              <span>Pilih Semua ({selectedIds.length})</span>
            </label>
            <button className="btn-popup-act btn-popup-cancel" onClick={handleExitSelectMode}>
              ✕ Batal
            </button>
          </div>

          <div className="popup-actions-row">
            <button
              className="btn-popup-act btn-popup-send"
              onClick={handleBulkSend}
              disabled={selectedIds.length === 0}
            >
              🚀 Kirim Email
            </button>
            <button
              className="btn-popup-act btn-popup-delete"
              onClick={handleBulkDelete}
              disabled={selectedIds.length === 0}
            >
              🗑️ Hapus
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <span className="spinner">⚙️</span> Memuat Data...
        </div>
      ) : documents.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">📂</span>
          <p>Belum ada data KTP yang tersimpan di database.</p>
        </div>
      ) : (
        <>
          {/* PAGINATION NAVIGATION BAR (DI ATAS LIST DOKUMEN) */}
          {pagination.pages > 1 && (
            <div className="pagination-bar pagination-top">
              <button
                className="btn-pagination"
                onClick={() => fetchDocuments(page - 1)}
                disabled={!pagination.hasPrev || loading}
              >
                ← Sebelumnya
              </button>
              <span className="pagination-info">
                Halaman {page} dari {pagination.pages}
              </span>
              <button
                className="btn-pagination"
                onClick={() => fetchDocuments(page + 1)}
                disabled={!pagination.hasNext || loading}
              >
                Selanjutnya →
              </button>
            </div>
          )}

          <div className="document-list">
            {documents.map((doc) => (
              <DocCardItem
                key={doc.id}
                doc={doc}
                isChecked={selectedIds.includes(doc.id)}
                isSelectMode={isSelectMode}
                handleOpenDetail={handleOpenDetail}
                handleToggleSelect={handleToggleSelect}
                formatDate={formatDate}
                handleOpenSendEmailModal={handleOpenSendEmailModal}
              />
            ))}
          </div>
        </>
      )}

      {/* MODAL SEND EMAIL DIALOG */}
      {emailModal.isOpen && (
        <div className="zoom-modal-overlay" onClick={() => !emailModal.isSending && setEmailModal(prev => ({ ...prev, isOpen: false }))}>
          <div className="zoom-modal-content email-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="zoom-modal-header">
              <span>📧 Kirim Data KTP via Email</span>
              <button
                className="btn-close-zoom"
                onClick={() => setEmailModal(prev => ({ ...prev, isOpen: false }))}
                disabled={emailModal.isSending}
              >
                ✕
              </button>
            </div>

            <div className="email-modal-body">
              <div className="email-summary-box">
                <span className="summary-icon">📄</span>
                <div>
                  <strong>{emailModal.docs.length} Dokumen KTP Terpilih</strong>
                  <div className="summary-subtext">Akan dikirimkan beserta Laporan PDF & File Foto Fisik KTP.</div>
                </div>
              </div>

              {emailModal.error && (
                <div className="email-error-alert">
                  ⚠️ {emailModal.error}
                </div>
              )}

              <div className="form-group-email">
                <label className="email-field-label">Alamat Email Tujuan:</label>
                <div className="email-input-wrapper">
                  <input
                    type="text"
                    value={emailModal.targetPrefix}
                    onChange={(e) => {
                      const cleanVal = e.target.value.replace(/[@\s]/g, '');
                      setEmailModal(prev => ({ ...prev, targetPrefix: cleanVal }));
                    }}
                    placeholder="nama.pengguna"
                    className="input-email-prefix"
                    disabled={emailModal.isSending}
                  />
                  <span className="email-domain-suffix">@gmail.com</span>
                </div>
                <span className="email-help-text">Email pengirim: <strong>guinnessyogi2@gmail.com</strong> (SMTP Gmail)</span>
              </div>

              <div className="modal-footer-actions margin-top-lg">
                <button
                  className="btn-modal-footer btn-save-primary"
                  onClick={handleExecuteSendEmail}
                  disabled={emailModal.isSending}
                >
                  {emailModal.isSending ? '⏳ Mengirim Email...' : '🚀 Kirim Sekarang'}
                </button>
                <button
                  className="btn-modal-footer btn-close-secondary"
                  onClick={() => setEmailModal(prev => ({ ...prev, isOpen: false }))}
                  disabled={emailModal.isSending}
                >
                  Batal
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL DETAIL & EDIT DOKUMEN */}
      {selectedDoc && (
        <div className="zoom-modal-overlay" onClick={() => setSelectedDoc(null)}>
          <div className="zoom-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="zoom-modal-header">
              <span>{isEditing ? "Edit Data KTP" : "Detail Data KTP Tersimpan"}</span>
              <button className="btn-close-zoom" onClick={() => setSelectedDoc(null)}>✕</button>
            </div>

            <div className="history-modal-body">
              {/* PRATINJAU FOTO FISIK KTP (UTAMA DI MOBILE & DESKTOP) */}
              <div
                className="history-image-preview clickable-preview"
                onClick={() => {
                  setFullImageZoom(resolveImgUrl(selectedDoc.filename));
                  setIsZoomedIn(false);
                }}
                title="Klik untuk memperbesar gambar KTP"
              >
                <span className="history-preview-badge">📷 Foto Fisik KTP</span>
                <span className="zoom-icon-badge">🔍</span>
                <img
                  src={resolveImgUrl(selectedDoc.filename)}
                  alt="Foto KTP Tersimpan"
                  onError={(e) => {
                    if (!e.target.src.includes('127.0.0.1')) {
                      const cleanFn = (selectedDoc.filename || '').replace(/^uploads\//, '');
                      e.target.src = `http://127.0.0.1:8000/uploads/${cleanFn}`;
                    }
                  }}
                />
              </div>

              {/* RINCIAN 8 FIELD */}
              <div className="history-fields-list">
                {Object.entries(isEditing ? editFormData : (selectedDoc.extracted_data || {})).map(([key, item]) => {
                  const label = FIELD_LABELS[key] || key.replace(/_/g, ' ').toUpperCase();
                  const val = item.value || "";

                  return (
                    <div key={key} className="history-field-row">
                      <span className="history-field-label">{label}</span>
                      {isEditing ? (
                        <input
                          type="text"
                          value={val}
                          onChange={(e) => setEditFormData(prev => ({
                            ...prev,
                            [key]: { ...prev[key], value: e.target.value }
                          }))}
                          className="input-valid edit-modal-input"
                        />
                      ) : (
                        <span className="history-field-value">{val || "-"}</span>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* TOMBOL AKSI MODAL */}
              <div className="modal-footer-actions">
                {!isEditing ? (
                  <>
                    <button className="btn-modal-footer btn-save-primary" onClick={() => handleOpenSendEmailModal([selectedDoc])}>
                      📤 Kirim Email
                    </button>
                    <button className="btn-modal-footer btn-edit-primary" onClick={() => setIsEditing(true)}>
                      ✏️ Edit Data
                    </button>
                    <button className="btn-modal-footer btn-delete-secondary" onClick={handleDeleteFromModal}>
                      🗑️ Hapus
                    </button>
                    <button className="btn-modal-footer btn-close-secondary" onClick={() => setSelectedDoc(null)}>
                      Tutup
                    </button>
                  </>
                ) : (
                  <>
                    <button className="btn-modal-footer btn-save-primary" onClick={handleSaveEdit} disabled={updating}>
                      {updating ? 'Menyimpan...' : '💾 Simpan Perubahan'}
                    </button>
                    <button className="btn-modal-footer btn-close-secondary" onClick={() => setIsEditing(false)} disabled={updating}>
                      Batal
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* FULL RESOLUTION LIGHTBOX POPUP WITH NATIVE MULTI-TOUCH PINCH TO ZOOM */}
      {fullImageZoom && (
        <div
          className="full-image-lightbox-overlay"
          onClick={() => setFullImageZoom(null)}
        >
          <div className="full-image-lightbox-container" onClick={(e) => e.stopPropagation()}>
            <button
              className="btn-close-lightbox"
              onClick={() => setFullImageZoom(null)}
            >
              ✕
            </button>
            <PinchZoomImage
              src={fullImageZoom}
              alt="Foto KTP Resolusi Penuh"
              onError={(e) => {
                if (!e.target.src.includes('127.0.0.1')) {
                  const cleanFn = (selectedDoc?.filename || '').replace(/^uploads\//, '');
                  e.target.src = `http://127.0.0.1:8000/uploads/${cleanFn}`;
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
