// Centralized API configuration for Document OCR System Frontend

const rawApiUrl = import.meta.env.VITE_API_URL || '';
export const API_BASE_URL = rawApiUrl.replace(/\/$/, '');

/**
 * Returns full API URL for a given path.
 * Example: getApiUrl('/api/upload/') -> "https://xxxx.ngrok-free.app/api/upload/"
 */
export const getApiUrl = (path) => {
  if (!path) return API_BASE_URL;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
};

/**
 * Wrapper fetch yang otomatis menambahkan header 'Bypass-Tunnel-Reminder'
 * agar Localtunnel tidak pernah menampilkan halaman peringatan HTML.
 */
export const apiFetch = (path, options = {}) => {
  const url = getApiUrl(path);
  const headers = {
    'Bypass-Tunnel-Reminder': 'true',
    ...(options.headers || {})
  };
  return fetch(url, { ...options, headers });
};

/**
 * Resolves static uploaded file URLs.
 * If filename is already a full URL or data URI, returns it directly.
 * Otherwise returns `${API_BASE_URL}/uploads/${cleanFilename}`.
 */
export const resolveUploadUrl = (filename) => {
  if (!filename) return '';
  if (filename.startsWith('http://') || filename.startsWith('https://') || filename.startsWith('data:')) {
    return filename;
  }
  const cleanFn = filename.replace(/^\/?(uploads\/)?/, '');
  return `${API_BASE_URL}/uploads/${cleanFn}`;
};
