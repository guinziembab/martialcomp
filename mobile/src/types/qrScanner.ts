export interface ScanResult {
  id: string;
  timestamp: number;
  type: ScanType;
  isValid: boolean;
  message: string;
  isOffline?: boolean;
  data: ScanData;
}

export type ScanType = 
  | 'practitioner_profile' 
  | 'competition_entry' 
  | 'certificate' 
  | 'attendance' 
  | 'training'
  | 'event'
  | 'check_in'
  | 'licence' 
  | 'grade' 
  | 'unknown';

export interface ScanData {
  practitionerId?: string;
  practitionerName?: string;
  practitionerPhoto?: string;
  clubName?: string;
  licenseNumber?: string;
  isFederationValidated?: boolean;
  competitionId?: string;
  competitionName?: string;
  certificateId?: string;
  certificateType?: string;
  licenceId?: string;
  licenceExpiry?: string;
  gradeId?: string;
  gradeName?: string;
  eventId?: string;
  eventName?: string;
  trainingSessionId?: string;
  trainingSessionName?: string;
  location?: string;
  scanCount?: number;
  [key: string]: any;
}

export interface OfflineQRToken {
  prac_id: string; // Practitioner ID
  qr_uuid: string; // QR code UUID
  fed_val: boolean; // Federation validated
  club_id?: string; // Club ID
  exp: number; // Expiration timestamp
}

export interface OfflineProfileData {
  id: string;
  firstName: string;
  lastName: string;
  birthDate?: string;
  gender?: string;
  nationality?: string;
  licenseNumber?: string;
  clubName?: string;
  federationName?: string;
  licenseExpiry?: string;
  photo?: string; // Base64 encoded photo
  federation_validated: boolean;
  disciplines?: Array<{
    name: string;
    grade?: string;
    grade_date?: string;
  }>;
  certifications?: Array<{
    name: string;
    date?: string;
    issuer?: string;
  }>;
  expiration: string; // ISO date string
}