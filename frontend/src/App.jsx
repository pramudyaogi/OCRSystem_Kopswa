import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import AppLayout from './components/AppLayout';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import ReviewPage from './pages/ReviewPage';
import HistoryPage from './pages/HistoryPage';
import SuccessPage from './pages/SuccessPage';
import MemberFormPage from './pages/MemberFormPage';
import LoanFormPage from './pages/LoanFormPage';
import SettingsPage from './pages/SettingsPage';
import './index.css';

// KTP Flow Component for /scan/ktp route
function KtpScanFlow() {
  const [ktpView, setKtpView] = useState('upload'); // 'upload' | 'review' | 'success'
  const [extractedData, setExtractedData] = useState(null);
  const [savedData, setSavedData] = useState(null);
  const navigate = useNavigate();

  const handleExtractionComplete = (data) => {
    setExtractedData(data);
    setKtpView('review');
  };

  const handleSaveSuccess = (saved) => {
    setSavedData(saved);
    setKtpView('success');
  };

  const handleResetKtp = () => {
    setExtractedData(null);
    setSavedData(null);
    setKtpView('upload');
  };

  return (
    <div className="ktp-flow-wrapper">
      {ktpView === 'upload' && (
        <UploadPage 
          onExtractionComplete={handleExtractionComplete} 
          onViewHistory={() => navigate('/history')} 
        />
      )}

      {ktpView === 'review' && extractedData && (
        <ReviewPage 
          payload={extractedData} 
          onReset={handleResetKtp}
          onSaveSuccess={handleSaveSuccess} 
        />
      )}

      {ktpView === 'success' && (
        <SuccessPage 
          savedData={savedData}
          onScanAgain={handleResetKtp}
          onViewHistory={() => navigate('/history')}
        />
      )}
    </div>
  );
}

export default function App() {
  const navigate = useNavigate();

  return (
    <Routes>
      {/* 1. Landing Page Route */}
      <Route path="/" element={<LandingPage />} />

      {/* 2. Dashboard Route */}
      <Route 
        path="/dashboard" 
        element={
          <AppLayout activeTab="dashboard">
            <DashboardPage />
          </AppLayout>
        } 
      />

      {/* 3. Scan E-KTP Route */}
      <Route 
        path="/scan/ktp" 
        element={
          <AppLayout activeTab="scan_ktp">
            <KtpScanFlow />
          </AppLayout>
        } 
      />

      {/* 4. Scan Formulir Anggota Route */}
      <Route 
        path="/scan/member-form" 
        element={
          <AppLayout activeTab="scan_member">
            <MemberFormPage />
          </AppLayout>
        } 
      />

      {/* 5. Scan Pengajuan Pinjaman Route */}
      <Route 
        path="/scan/loan-form" 
        element={
          <AppLayout activeTab="scan_loan">
            <LoanFormPage />
          </AppLayout>
        } 
      />

      {/* 6. Riwayat Dokumen Route */}
      <Route 
        path="/history" 
        element={
          <AppLayout activeTab="history">
            <HistoryPage onBack={() => navigate('/dashboard')} />
          </AppLayout>
        } 
      />

      {/* 7. Pengaturan Route */}
      <Route 
        path="/settings" 
        element={
          <AppLayout activeTab="settings">
            <SettingsPage />
          </AppLayout>
        } 
      />

      {/* Fallback Route */}
      <Route path="*" element={<LandingPage />} />
    </Routes>
  );
}
