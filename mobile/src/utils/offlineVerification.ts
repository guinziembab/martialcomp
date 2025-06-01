import { ScanType, OfflineQRToken, OfflineProfileData } from '@types/qrScanner';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface VerificationResult {
  isValid: boolean;
  message?: string;
  type?: string;
  data: any;
}

/**
 * Verifies an offline QR token without needing server connectivity
 * This implements the validation logic described in the MartialComp backend
 */
export async function verifyOfflineToken(token: string): Promise<VerificationResult> {
  try {
    // Try to parse the token as JSON first (for new format)
    try {
      // Check if it's a JSON object already
      if (token.trim().startsWith('{')) {
        const jsonData = JSON.parse(token);
        // Process JSON format token
        return processJsonToken(jsonData);
      }
      
      // If not, it might be base64 encoded (new MartialComp format)
      const decodedToken = atob(token);
      // Check if the decoded content is a JSON
      if (decodedToken.trim().startsWith('{')) {
        const jsonData = JSON.parse(decodedToken);
        return processJsonToken(jsonData);
      }
    } catch (error) {
      console.log("Token is not in standard JSON format, trying legacy format...");
      // Continue with legacy format verification below
    }

    // Legacy format verification (for backward compatibility)
    try {
      // The old token format is base64 encoded
      const decodedToken = atob(token);
      const tokenData = JSON.parse(decodedToken);
      
      // Check if the token has the required fields for legacy format
      if (!tokenData.type || !tokenData.data || !tokenData.signature || !tokenData.expiry) {
        return {
          isValid: false,
          message: 'Incomplete QR code data',
          data: {},
        };
      }

      // Check if the token has expired
      const expiryTimestamp = parseInt(tokenData.expiry, 10);
      if (Date.now() > expiryTimestamp) {
        return {
          isValid: false,
          message: 'QR code has expired',
          data: tokenData.data,
        };
      }
      
      // Legacy format verification passed
      return {
        isValid: true,
        type: tokenData.type as ScanType,
        data: tokenData.data,
      };
    } catch (error) {
      return {
        isValid: false,
        message: 'Invalid QR code format',
        data: {},
      };
    }
  } catch (error: any) {
    console.error('Error verifying offline token:', error);
    return {
      isValid: false,
      message: error.message || 'Failed to verify QR code',
      data: {},
    };
  }
}

/**
 * Process a JSON format QR token (new MartialComp format)
 */
function processJsonToken(jsonData: any): VerificationResult {
  // For MartialComp practitioner QR codes
  if (jsonData.prac_id && jsonData.qr_uuid) {
    // This is likely a practitioner QR code
    const tokenData: OfflineQRToken = {
      prac_id: jsonData.prac_id,
      qr_uuid: jsonData.qr_uuid,
      fed_val: jsonData.fed_val || false,
      club_id: jsonData.club_id,
      exp: jsonData.exp || (Date.now() + 7 * 24 * 60 * 60 * 1000) // Default 7 days if not specified
    };
    
    // Check if expired
    if (Date.now() > tokenData.exp) {
      return {
        isValid: false,
        message: 'QR code has expired',
        type: 'practitioner_profile',
        data: tokenData,
      };
    }
    
    return {
      isValid: true,
      type: 'practitioner_profile',
      data: tokenData,
    };
  }
  
  // For MartialComp profile data
  if (jsonData.profile_type === 'practitioner') {
    return {
      isValid: true,
      type: 'practitioner_profile',
      data: jsonData,
    };
  }
  
  // For any other JSON format data, we'll accept it if it has a type field
  if (jsonData.type) {
    return {
      isValid: true,
      type: jsonData.type as ScanType,
      data: jsonData,
    };
  }
  
  // Unknown format
  return {
    isValid: false,
    message: 'Unknown QR code format',
    data: jsonData,
  };
}

/**
 * Parse an offline profile token and return the profile data
 */
export async function parseOfflineProfile(token: string): Promise<OfflineProfileData | null> {
  try {
    // Try to parse directly as JSON first
    if (token.trim().startsWith('{')) {
      const profileData = JSON.parse(token);
      return transformProfileData(profileData);
    }
    
    // Try to decode from base64
    const decodedToken = atob(token);
    if (decodedToken.trim().startsWith('{')) {
      const profileData = JSON.parse(decodedToken);
      return transformProfileData(profileData);
    }
    
    return null;
  } catch (error) {
    console.error('Error parsing offline profile:', error);
    return null;
  }
}

/**
 * Transform raw profile data to the expected OfflineProfileData format
 */
function transformProfileData(data: any): OfflineProfileData {
  // Default expiration to 30 days from now if not specified
  const defaultExpiry = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
  
  return {
    id: data.id || String(data.prac_id) || `profile-${Date.now()}`,
    firstName: data.first_name || data.firstName || '',
    lastName: data.last_name || data.lastName || '',
    birthDate: data.birth_date || data.birthDate || data.date_of_birth || '',
    gender: data.gender || '',
    nationality: data.nationality || '',
    licenseNumber: data.license_number || data.licenseNumber || '',
    clubName: data.club_name || data.clubName || '',
    federationName: data.federation_name || data.federationName || '',
    licenseExpiry: data.license_expiry || data.licenseExpiry || '',
    photo: data.photo || null,
    federation_validated: data.is_federation_validated || data.federation_validated || data.fed_val || false,
    disciplines: data.disciplines || [],
    certifications: data.certifications || [],
    expiration: data.expiration || data.exp || defaultExpiry,
  };
}

/**
 * Creates an offline verification token
 * This is primarily used for testing purposes in the app
 */
export function createOfflineToken(
  type: ScanType,
  data: any,
  expiryMinutes: number = 60
): string {
  // Use the new MartialComp format
  if (type === 'practitioner_profile') {
    const token: OfflineQRToken = {
      prac_id: data.practitionerId || String(Date.now()),
      qr_uuid: data.qrUuid || crypto.randomUUID?.() || `qr-${Date.now()}`,
      fed_val: data.isFederationValidated || false,
      club_id: data.clubId,
      exp: Date.now() + expiryMinutes * 60 * 1000
    };
    
    // Return as base64 encoded JSON
    return btoa(JSON.stringify(token));
  }
  
  // Legacy format for other types
  const expiry = Date.now() + expiryMinutes * 60 * 1000;
  const signature = `test-signature-${type}-${Date.now()}`;
  
  const tokenData = {
    type,
    data,
    signature,
    expiry,
  };
  
  // Convert to base64
  return btoa(JSON.stringify(tokenData));
}