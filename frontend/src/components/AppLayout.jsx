import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AppLayout({ activeTab, children }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const mainMenuItems = [
    { id: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: '📊' }
  ];

  const scanMenuItems = [
    { id: 'scan_ktp', path: '/scan/ktp', label: 'Scan KTP', icon: '🆔' },
    { id: 'scan_member', path: '/scan/member-form', label: 'Scan Formulir Anggota', icon: '📋' },
    { id: 'scan_loan', path: '/scan/loan-form', label: 'Scan Pengajuan Pinjaman', icon: '💰' },
  ];

  const archiveMenuItems = [
    { id: 'history', path: '/history', label: 'Riwayat Dokumen', icon: '🗂️' }
  ];

  const systemMenuItems = [
    { id: 'settings', path: '/settings', label: 'Pengaturan', icon: '⚙️' }
  ];

  const handleNavClick = (path) => {
    navigate(path);
    setIsMobileMenuOpen(false);
  };

  return (
    <div className={`app-layout-wrapper ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Top Mobile Bar */}
      <header className="mobile-header">
        <button 
          className="btn-hamburger" 
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle Menu"
        >
          ☰
        </button>
        <div className="mobile-logo-container" onClick={() => navigate('/')}>
          <img src="/logo.png" alt="Swadharma Logo" className="mobile-logo" />
        </div>
      </header>

      {/* Backdrop Overlay for Mobile */}
      {isMobileMenuOpen && (
        <div 
          className="sidebar-backdrop" 
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside className={`sidebar-nav ${isCollapsed ? 'is-collapsed' : ''} ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
        {/* Brand Header */}
        <div className="sidebar-brand-box" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <img src="/logo.png" alt="Koperasi Swadharma" className="sidebar-logo" />
          {!isCollapsed && (
            <div className="sidebar-brand-text">
              <span className="brand-subtitle">SYSTEM OCR</span>
            </div>
          )}
        </div>

        {/* Collapse Toggle Button (Desktop) */}
        <button 
          className="btn-toggle-sidebar"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? "Buka Sidebar" : "Tutup Sidebar"}
        >
          {isCollapsed ? '❯' : '❮'}
        </button>

        {/* Menu Navigation Grouping */}
        <nav className="sidebar-menu">
          {/* MENU UTAMA */}
          <div className="menu-group-label">{!isCollapsed && "MENU UTAMA"}</div>
          {mainMenuItems.map((item) => (
            <button
              key={item.id}
              className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => handleNavClick(item.path)}
              title={item.label}
            >
              <span className="sidebar-icon">{item.icon}</span>
              {!isCollapsed && <span className="sidebar-label">{item.label}</span>}
            </button>
          ))}

          {/* PEMINDAIAN DOKUMEN */}
          <div className="menu-group-label margin-top-md">{!isCollapsed && "PEMINDAIAN DOKUMEN"}</div>
          {scanMenuItems.map((item) => (
            <button
              key={item.id}
              className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => handleNavClick(item.path)}
              title={item.label}
            >
              <span className="sidebar-icon">{item.icon}</span>
              {!isCollapsed && <span className="sidebar-label">{item.label}</span>}
            </button>
          ))}

          {/* MANAJEMEN ARSIP */}
          <div className="menu-group-label margin-top-md">{!isCollapsed && "MANAJEMEN ARSIP"}</div>
          {archiveMenuItems.map((item) => (
            <button
              key={item.id}
              className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => handleNavClick(item.path)}
              title={item.label}
            >
              <span className="sidebar-icon">{item.icon}</span>
              {!isCollapsed && <span className="sidebar-label">{item.label}</span>}
            </button>
          ))}

          {/* SISTEM */}
          <div className="menu-group-label margin-top-md">{!isCollapsed && "SISTEM"}</div>
          {systemMenuItems.map((item) => (
            <button
              key={item.id}
              className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => handleNavClick(item.path)}
              title={item.label}
            >
              <span className="sidebar-icon">{item.icon}</span>
              {!isCollapsed && <span className="sidebar-label">{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <button className="sidebar-home-btn" onClick={() => navigate('/')}>
            <span className="sidebar-icon">🏠</span>
            {!isCollapsed && <span className="sidebar-label">Kembali ke Landing</span>}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="layout-content-area">
        {children}
      </main>
    </div>
  );
}
