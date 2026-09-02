// Centralized API configuration for Document OCR System Frontend
const envUrl = import.meta.env.VITE_API_URL || '';
export const API_BASE_URL = envUrl ? envUrl.replace(/\/$/, '') : 'http://127.0.0.1:8001';



/**
 * Returns full API URL for a given path.
 */
export const getApiUrl = (path) => {
  if (!path) return API_BASE_URL;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
};

/**
 * Wrapper fetch yang otomatis menambahkan header bypass tunnel
 */
export const apiFetch = (path, options = {}) => {
  const url = getApiUrl(path);
  const headers = {
    'Bypass-Tunnel-Reminder': 'true',
    'ngrok-skip-browser-warning': 'true',
    ...(options.headers || {})
  };
  return fetch(url, { ...options, headers });
};

/**
 * Resolves static uploaded file URLs.
 */
export const resolveUploadUrl = (filename) => {
  if (!filename) return '';
  if (filename.startsWith('http://') || filename.startsWith('https://') || filename.startsWith('data:')) {
    return filename;
  }
  const cleanFn = filename.replace(/^\/?(uploads\/)?/, '');
  return `${API_BASE_URL}/uploads/${cleanFn}`;
};

/**
 * Fetch paginated document records from FastAPI backend (/api/documents/).
 */
export const fetchDocuments = async (page = 1, limit = 6) => {
  const res = await apiFetch(`/api/documents/?page=${page}&limit=${limit}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return await res.json();
};

/**
 * Delete documents by IDs via FastAPI backend (/api/documents/delete-multiple).
 */
export const deleteDocuments = async (ids = []) => {
  if (!ids || ids.length === 0) return true;
  const res = await apiFetch('/api/documents/delete-multiple', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids })
  });
  return res.ok;
};

