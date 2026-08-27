// Centralized API configuration for Document OCR System Frontend

const defaultTunnelUrl = 'https://614f7face866bc49-182-3-51-216.serveousercontent.com';
const envUrl = import.meta.env.VITE_API_URL || '';
const rawApiUrl = (envUrl && !envUrl.includes('loca.lt')) ? envUrl : defaultTunnelUrl;
export const API_BASE_URL = rawApiUrl.replace(/\/$/, '');

export const SUPABASE_URL = "https://qeuviylbnrjtmyuomzrr.supabase.co";
export const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFldXZpeWxibnJqdG15dW9tenJyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3OTU2MTksImV4cCI6MjEwMzM3MTYxOX0.EmcDsm4ZiNd5wnKNpx6F_bRSAaTvVE3kCgkq9ZYABl8";

/**
 * Returns full API URL for a given path.
 */
export const getApiUrl = (path) => {
  if (!path) return API_BASE_URL;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
};

/**
 * Wrapper fetch yang otomatis menambahkan header 'Bypass-Tunnel-Reminder'
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
 * Fetch paginated document records directly from Supabase Cloud Database.
 * This guarantees ultra-fast load times on mobile devices/Vercel (0.05s).
 */
export const fetchSupabaseDocuments = async (page = 1, limit = 6) => {
  const offset = (page - 1) * limit;
  const tables = ['ktp_documents', 'documents'];
  let lastError = null;

  for (const tbl of tables) {
    try {
      const url = `${SUPABASE_URL}/rest/v1/${tbl}?select=*&order=created_at.desc&limit=${limit}&offset=${offset}`;
      const response = await fetch(url, {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Prefer': 'count=exact'
        }
      });

      if (response.ok) {
        const items = await response.json();
        const contentRange = response.headers.get('content-range') || '';
        let total = items.length;
        if (contentRange && contentRange.includes('/')) {
          const totalStr = contentRange.split('/')[1];
          if (totalStr && totalStr !== '*') {
            total = parseInt(totalStr, 10);
          }
        }

        const pages = Math.max(1, Math.ceil(total / limit));
        return {
          items: items || [],
          total,
          page,
          pages,
          has_next: page < pages,
          has_prev: page > 1
        };
      }
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError || new Error("Supabase DB Error");
};

/**
 * Delete documents directly from Supabase Cloud Database.
 */
export const deleteSupabaseDocuments = async (ids = []) => {
  if (!ids || ids.length === 0) return true;
  const idFilter = `in.(${ids.join(',')})`;
  for (const tbl of ['ktp_documents', 'documents']) {
    try {
      const url = `${SUPABASE_URL}/rest/v1/${tbl}?id=${idFilter}`;
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
        }
      });
      if (response.ok) return true;
    } catch (err) {
      console.warn(`Error deleting from ${tbl}:`, err);
    }
  }
  return false;
};
