/**
 * Dynamic API Base URL configuration for local and LAN hosting.
 * Resolves to the current hostname on port 8000, or relative URL if served from port 8000.
 */
export const getApiBase = (): string => {
  if (typeof window === 'undefined') return 'http://127.0.0.1:8000';
  if (window.location.port === '8000') {
    return '';
  }
  const host = window.location.hostname || '127.0.0.1';
  return `http://${host}:8000`;
};

export const API_BASE = getApiBase();
