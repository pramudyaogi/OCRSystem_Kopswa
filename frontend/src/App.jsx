import React, { useState } from 'react';
import UploadPage from './pages/UploadPage';
import ReviewPage from './pages/ReviewPage';
import HistoryPage from './pages/HistoryPage';
import SuccessPage from './pages/SuccessPage';
import './index.css';

export default function App() {
  const [view, setView] = useState('upload'); // 'upload' | 'review' | 'success' | 'history'
  const [extractedData, setExtractedData] = useState(null);
  const [savedData, setSavedData] = useState(null);

  const handleExtractionComplete = (data) => {
    setExtractedData(data);
    setView('review');
  };

  const handleSaveSuccess = (saved) => {
    setSavedData(saved);
    setView('success');
  };

  const handleReset = () => {
    setExtractedData(null);
    setSavedData(null);
    setView('upload');
  };

  return (
    <div className="app-container">
      {view === 'upload' && (
        <UploadPage 
          onExtractionComplete={handleExtractionComplete} 
          onViewHistory={() => setView('history')} 
        />
      )}

      {view === 'review' && extractedData && (
        <ReviewPage 
          payload={extractedData} 
          onReset={handleReset}
          onSaveSuccess={handleSaveSuccess} 
        />
      )}

      {view === 'success' && (
        <SuccessPage 
          savedData={savedData}
          onScanAgain={handleReset}
          onViewHistory={() => setView('history')}
        />
      )}

      {view === 'history' && (
        <HistoryPage 
          onBack={() => setView('upload')} 
        />
      )}
    </div>
  );
}
