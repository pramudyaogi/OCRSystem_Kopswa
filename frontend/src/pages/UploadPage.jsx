import React, { useState, useRef, useEffect } from 'react';
import { getApiUrl, resolveUploadUrl, apiFetch } from '../services/api';

export default function UploadPage({ onExtractionComplete, onViewHistory }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [template, setTemplate] = useState('ktp');
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
      if (!validTypes.includes(droppedFile.type) && !droppedFile.type.startsWith('image/')) {
        alert("Format file tidak didukung! Harap gunakan file JPG, PNG, atau PDF.");
        return;
      }
      setFile(droppedFile);
    }
  };
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const nativeCameraInputRef = useRef(null);

  // Membuka kamera (Stream WebRTC jika HTTPS/localhost, atau Native HP Camera jika HTTP IP)
  const startCamera = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      if (nativeCameraInputRef.current) {
        nativeCameraInputRef.current.click();
      }
      return;
    }

    try {
      setIsCameraActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Camera access error:", err);
      setIsCameraActive(false);
      if (nativeCameraInputRef.current) {
        nativeCameraInputRef.current.click();
      }
    }
  };

  // Menghentikan kamera stream
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  // Mengambil gambar dari stream video kamera
  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob((blob) => {
      const capturedFile = new File([blob], `ktp_scan_${Date.now()}.jpg`, { type: 'image/jpeg' });
      setFile(capturedFile);
      stopCamera();
    }, 'image/jpeg', 0.95);
  };

  useEffect(() => {
    return () => stopCamera();
  }, []);

  const compressImageIfNeeded = (inputFile) => {
    return new Promise((resolve) => {
      if (!inputFile || inputFile.type === 'application/pdf') {
        resolve(inputFile);
        return;
      }
      
      const img = new Image();
      const reader = new FileReader();
      
      reader.onload = (e) => {
        img.src = e.target.result;
      };
      
      img.onload = () => {
        const maxDim = 2400; // High-precision 2400px max dimension for AI OCR
        let width = img.width;
        let height = img.height;
        
        if (width > maxDim || height > maxDim) {
          if (width > height) {
            height = Math.round((height * maxDim) / width);
            width = maxDim;
          } else {
            width = Math.round((width * maxDim) / height);
            height = maxDim;
          }
        }
        
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              resolve(inputFile);
              return;
            }
            const compressedFile = new File([blob], inputFile.name, {
              type: 'image/jpeg',
              lastModified: Date.now()
            });
            resolve(compressedFile);
          },
          'image/jpeg',
          0.92 // 92%+ high JPEG quality to retain maximum OCR text sharpness
        );
      };
      
      img.onerror = () => resolve(inputFile);
      reader.onerror = () => resolve(inputFile);
      
      reader.readAsDataURL(inputFile);
    });
  };

  const handleUpload = async () => {
    if (!file) return alert("Harap tangkap foto atau pilih file dokumen terlebih dahulu!");
    setLoading(true);
    
    // Auto-compress large mobile camera photos before upload (10MB -> ~200KB)
    const fileToUpload = await compressImageIfNeeded(file);

    const formData = new FormData();
    formData.append("file", fileToUpload);
    formData.append("template", template);

    try {
      let result;
      try {
        const res = await apiFetch('/api/upload/', {
          method: "POST",
          body: formData
        });
        result = await res.json();
        
        if (!res.ok) {
          alert("Gagal upload: " + result.detail);
          setLoading(false);
          return;
        }
      } catch (uploadErr) {
        throw new Error("Gagal terhubung ke Mesin AI Laptop. Pastikan Terminal Python & Tunnel di laptop sudah dinyalakan.");
      }

      let extractEndpoint = "";
      try {
        const cleanFilename = encodeURIComponent(result.filename.trim());
        const cleanTemplate = encodeURIComponent(template.trim());
        extractEndpoint = `/api/extract/${cleanFilename}?template_type=${cleanTemplate}`;
        
        const extractRes = await apiFetch(extractEndpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({})
        });
        
        if (!extractRes.ok) {
          const errorData = await extractRes.json().catch(() => ({ detail: `Internal Server Error (${extractRes.status})` }));
          alert("Gagal ekstraksi OCR: " + (errorData.detail || `HTTP ${extractRes.status}`));
          return;
        }
        
        const extractResult = await extractRes.json();
        const previewUrl = file ? URL.createObjectURL(file) : resolveUploadUrl(result.filename);
        onExtractionComplete({
          filename: result.filename,
          template: template,
          data: extractResult.extracted_data,
          imagePreview: previewUrl
        });
      } catch (extractErr) {
        throw new Error("Extract Fetch Error pada URL (" + url + "): " + (extractErr.message || extractErr.toString()));
      }
    } catch (e) {
      console.error("Kesalahan jaringan:", e);
      alert("Error rincian koneksi: " + (e.message || e.toString()));
    } finally {
      setLoading(false);
    }
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
        <div className="step-item active">
          <span className="step-number">1</span>
          <span className="step-label">Pilih & Upload</span>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <span className="step-number">2</span>
          <span className="step-label">Verifikasi Data</span>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <span className="step-number">3</span>
          <span className="step-label">Selesai</span>
        </div>
      </div>

      {/* INSTRUCTION BANNER RINGKAS */}
      <div className="instruction-banner">
        <span className="info-icon">💡</span>
        <span>Pilih tipe dokumen, lalu pilih metode pindaian: **Foto Kamera** atau **Upload File**.</span>
      </div>

      {/* INPUT GROUP TIPE DOKUMEN & NAVIGASI HISTORY */}
      <div className="input-group main-type-selector">
        <div className="label-with-action">
          <label>Tipe Dokumen</label>
          <button 
            type="button"
            className="btn-history-compact"
            onClick={onViewHistory}
            title="Lihat Data Tersimpan"
          >
            📁 Data Tersimpan
          </button>
        </div>
        <select value={template} onChange={(e) => setTemplate(e.target.value)}>
          <option value="ktp">🇮🇩 KTP Indonesia (E-KTP)</option>
          <option value="form_pendaftaran">📝 Formulir Pendaftaran</option>
        </select>
      </div>

      {/* METODE UPLOAD: 2 KARTU OPSI SEJAJAR & SAMA TINGGI */}
      {!isCameraActive ? (
        <div className="upload-options-container">
          <div className="upload-options-grid">
            {/* KARTU 1: AMBIL FOTO KAMERA */}
            <div className="option-card option-camera">
              <div className="option-card-icon-badge">📷</div>
              <h3>Ambil Foto Kamera</h3>
              <p className="option-card-desc">Foto fisik KTP secara langsung via kamera HP/Webcam.</p>
              <button 
                type="button" 
                className="btn btn-secondary btn-option-act"
                onClick={startCamera}
              >
                Ambil Foto Kamera
              </button>
            </div>

            {/* KARTU 2: UPLOAD FILE DOKUMEN (FULL DRAG & DROP ZONE) */}
            <div 
              className={`option-card option-file ${file ? 'has-file' : ''} ${isDragging ? 'is-dragging' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="option-card-icon-badge">{file ? '📄' : (isDragging ? '📥' : '📁')}</div>
              <h3>{isDragging ? "Drop File Di Sini!" : (file ? "File Terpilih" : "Upload File Dokumen")}</h3>
              
              {file ? (
                <div className="file-info-box">
                  <span className="file-name-text">{file.name}</span>
                  <span className="file-size-text">({(file.size / 1024).toFixed(1)} KB)</span>
                </div>
              ) : (
                <p className="file-name-text">
                  {isDragging ? "Lepaskan file di sini" : "Pilih atau geser file KTP dari perangkat (JPG, PNG, PDF)"}
                </p>
              )}

              <div className="file-upload-input-wrapper">
                <input 
                  type="file" 
                  onChange={(e) => setFile(e.target.files[0])} 
                  accept="image/*,application/pdf"
                />
                <button type="button" className="btn btn-secondary btn-option-act">
                  {file ? "Ganti File" : "Pilih File Dokumen"}
                </button>
              </div>
            </div>
          </div>

          {/* TOMBOL UTAMA PROSES DOKUMEN */}
          <button 
            className="btn btn-primary btn-process-main"
            onClick={handleUpload} 
            disabled={loading || !file}
          >
            {loading ? (
              <><span className="spinner">⚙️</span> Memproses Dokumen...</>
            ) : (
              "⚡ Proses & Ekstraksi Dokumen"
            )}
          </button>
        </div>
      ) : (
        /* MODAL KAMERA INTERAKTIF DENGAN KTP FRAME ASPECT RATIO (1.586 : 1) & DARK OVERLAY */
        <div className="camera-overlay-container">
          <div className="camera-header">
            <span>📷 Posisikan KTP Pas di Dalam Bingkai Oranye</span>
            <button className="btn-close-camera" onClick={stopCamera}>✕</button>
          </div>
          
          <div className="video-viewport">
            <video ref={videoRef} autoPlay playsInline muted />
            <div className="camera-dark-overlay">
              <div className="ktp-frame-guide">
                <div className="frame-corner top-left"></div>
                <div className="frame-corner top-right"></div>
                <div className="frame-corner bottom-left"></div>
                <div className="frame-corner bottom-right"></div>
              </div>
              <p className="camera-instruction-subtext">Pastikan seluruh KTP terlihat jelas di dalam kotak oranye</p>
            </div>
          </div>

          <div className="camera-action-row">
            <button className="btn btn-secondary btn-cancel-cam" onClick={stopCamera}>
              Batal
            </button>
            <button className="btn btn-primary btn-capture" onClick={capturePhoto}>
              📷 Tangkap Foto KTP
            </button>
          </div>
        </div>
      )}

      {/* INPUT KAMERA NATIVE TERSEMBUNYI */}
      <input 
        ref={nativeCameraInputRef}
        type="file" 
        accept="image/*" 
        capture="environment" 
        onChange={(e) => setFile(e.target.files[0])} 
        style={{ display: 'none' }}
      />

      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
}
