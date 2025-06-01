// Base API URL
// export const API_URL = 'https://api.martialcomp.com/api/v1';

// For local development using Expo
export const API_URL = 'http://localhost:8000/api/v1';

// For testing on physical device with local server
// export const API_URL = 'http://YOUR_MACHINE_IP:8000/api/v1';

// Timeout settings (in milliseconds)
export const API_TIMEOUT = 30000; // 30 seconds

// Request retry settings
export const MAX_RETRIES = 3;
export const RETRY_DELAY = 1000; // 1 second

// API Endpoints
export const ENDPOINTS = {
  // Auth
  LOGIN: '/auth/login/',
  REGISTER: '/auth/register/',
  REFRESH_TOKEN: '/auth/token/refresh/',
  CURRENT_USER: '/auth/me/',
  LOGOUT: '/auth/logout/',
  PASSWORD_RESET: '/auth/password-reset/',
  PASSWORD_RESET_CONFIRM: '/auth/password-reset/confirm/',
  
  // Profile
  PROFILE: '/profile/',
  PROFILE_UPDATE: '/profile/update/',
  
  // QR Scanner
  QR_PROCESS: '/qr/scan/process/',
  QR_HISTORY: '/qr/scan/history/',
  QR_SYNC: '/qr/scan/sync-offline/',
  QR_PROFILE: '/qr/practitioner',  // Add practitioner ID: /qr/practitioner/123/
  QR_OFFLINE_TOKEN: '/qr/practitioner/:id/offline-token/',
  QR_OFFLINE_PROFILE: '/qr/practitioner/:id/offline-profile/',
  QR_OFFLINE_VERIFY: '/qr/scan/verify-offline-token/',
  QR_OFFLINE_PROFILE_VERIFY: '/qr/scan/verify-offline-profile/',
  QR_VIEW: '/qr/practitioner/:id/',
  QR_EVENT_CHECKIN: '/qr/event/:id/check-in/',
  
  // Offline
  OFFLINE_PROFILES: '/offline/profiles/',
  OFFLINE_SYNC: '/offline/sync/',
  
  // Disciplines
  DISCIPLINES: '/disciplines/',
  DISCIPLINE_GRADES: '/disciplines/:id/grades/',
  
  // Clubs
  CLUBS: '/clubs/',
  CLUB_DETAIL: '/clubs/:id/',
  
  // Competitions
  COMPETITIONS: '/competitions/',
  COMPETITION_DETAIL: '/competitions/:id/',
  COMPETITION_REGISTER: '/competitions/:id/register/',
  
  // Notifications
  NOTIFICATIONS: '/notifications/',
  NOTIFICATION_READ: '/notifications/:id/read/',
};

// Helper to build URLs with path parameters
export const buildUrl = (endpoint: string, params: Record<string, string | number> = {}): string => {
  let url = endpoint;
  
  // Replace path parameters
  Object.entries(params).forEach(([key, value]) => {
    url = url.replace(`:${key}`, String(value));
  });
  
  return url;
};