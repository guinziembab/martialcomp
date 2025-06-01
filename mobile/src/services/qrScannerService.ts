import axios from 'axios';
import { ScanResult, ScanType, ScanData, OfflineQRToken, OfflineProfileData } from '@types/qrScanner';
import { API_URL, ENDPOINTS } from '@config/api';
import { verifyOfflineToken, parseOfflineProfile } from '@utils/offlineVerification';

class QRScannerService {
  async processQRCode(token: string, qrData: string, scanType?: string, eventId?: string): Promise<ScanResult> {
    try {
      const requestData: any = {
        qr_code: qrData,
      };
      
      // Add optional parameters if provided
      if (scanType) {
        requestData.scan_type = scanType;
      }
      
      if (eventId) {
        if (scanType === 'competition') {
          requestData.competition_id = eventId;
        } else if (scanType === 'training') {
          requestData.training_session_id = eventId;
        } else if (scanType === 'event') {
          requestData.event_id = eventId;
        }
      }
      
      const response = await axios.post(
        `${API_URL}${ENDPOINTS.QR_PROCESS}`,
        requestData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      return this.transformScanResultResponse(response.data);
    } catch (error: any) {
      console.error('Process QR code error:', error);
      
      // If there's a proper API response with an error message
      if (error.response && error.response.data && error.response.data.message) {
        return {
          id: `error-${Date.now()}`,
          timestamp: Date.now(),
          type: 'unknown',
          isValid: false,
          message: error.response.data.message,
          data: {},
        };
      }
      
      // Default error response
      return {
        id: `error-${Date.now()}`,
        timestamp: Date.now(),
        type: 'unknown',
        isValid: false,
        message: 'Failed to process QR code. Please try again.',
        data: {},
      };
    }
  }

  async getScanHistory(token: string): Promise<ScanResult[]> {
    try {
      const response = await axios.get(`${API_URL}${ENDPOINTS.QR_HISTORY}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      return response.data.scans.map(this.transformScanResultResponse);
    } catch (error) {
      console.error('Get scan history error:', error);
      throw new Error('Failed to fetch scan history.');
    }
  }

  async verifyOfflineQRCode(qrData: string, scanType?: string, eventId?: string): Promise<ScanResult> {
    try {
      // Attempt to verify the QR code with our offline verification function
      const verificationResult = await verifyOfflineToken(qrData);
      
      if (verificationResult.isValid) {
        // Determine the scan type if not provided
        const type = scanType || verificationResult.type || 'practitioner_profile';
        
        // Prepare the data
        const data: ScanData = {
          ...verificationResult.data,
          practitionerId: verificationResult.data.practitionerId || verificationResult.data.prac_id,
          isFederationValidated: verificationResult.data.fed_val || verificationResult.data.federation_validated,
        };
        
        // Add event ID if provided
        if (eventId) {
          if (type === 'competition') {
            data.competitionId = eventId;
          } else if (type === 'training') {
            data.trainingSessionId = eventId;
          } else if (type === 'event') {
            data.eventId = eventId;
          }
        }
        
        return {
          id: `offline-${Date.now()}`,
          timestamp: Date.now(),
          type: type as ScanType,
          isValid: true,
          message: 'Verified offline successfully',
          isOffline: true,
          data: data,
        };
      } else {
        return {
          id: `offline-error-${Date.now()}`,
          timestamp: Date.now(),
          type: 'unknown',
          isValid: false,
          message: verificationResult.message || 'Invalid offline QR code',
          isOffline: true,
          data: {},
        };
      }
    } catch (error: any) {
      console.error('Verify offline QR code error:', error);
      
      return {
        id: `offline-error-${Date.now()}`,
        timestamp: Date.now(),
        type: 'unknown',
        isValid: false,
        message: error.message || 'Failed to verify offline QR code',
        isOffline: true,
        data: {},
      };
    }
  }
  
  async getOfflineProfile(token: string, practitionerId: string): Promise<OfflineProfileData> {
    try {
      const response = await axios.get(
        `${API_URL}${ENDPOINTS.QR_PROFILE}/${practitionerId}/offline-profile/`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          params: {
            format: 'json',
          },
        }
      );
      
      return response.data.profile_data;
    } catch (error) {
      console.error('Get offline profile error:', error);
      throw new Error('Failed to fetch offline profile data.');
    }
  }
  
  async verifyOfflineProfile(profileToken: string): Promise<{valid: boolean; profile?: OfflineProfileData; reason?: string}> {
    try {
      // Parse and verify the profile token
      const profileData = await parseOfflineProfile(profileToken);
      
      if (!profileData) {
        return {
          valid: false,
          reason: 'invalid_token_format',
        };
      }
      
      // Check if the profile has expired
      const expirationDate = new Date(profileData.expiration);
      if (expirationDate < new Date()) {
        return {
          valid: false,
          reason: 'token_expired',
          profile: profileData,
        };
      }
      
      return {
        valid: true,
        profile: profileData,
      };
    } catch (error: any) {
      console.error('Verify offline profile error:', error);
      return {
        valid: false,
        reason: 'verification_error',
      };
    }
  }
  
  async syncOfflineScans(token: string, scans: any[]): Promise<{synced: number; ignored: number}> {
    try {
      const response = await axios.post(
        `${API_URL}${ENDPOINTS.QR_SYNC}`,
        { scans },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      return {
        synced: response.data.synced || 0,
        ignored: response.data.ignored || 0,
      };
    } catch (error) {
      console.error('Sync offline scans error:', error);
      throw new Error('Failed to synchronize offline scans.');
    }
  }

  // Helper method to transform API response to our ScanResult type
  private transformScanResultResponse(data: any): ScanResult {
    const scanData: ScanData = {};
    
    // Extract scan data directly from the practitioner field
    if (data.practitioner) {
      scanData.practitionerId = data.practitioner.id;
      scanData.practitionerName = data.practitioner.name;
      scanData.practitionerPhoto = data.practitioner.photo;
      scanData.clubName = data.practitioner.club;
      scanData.licenseNumber = data.practitioner.license_number;
      scanData.isFederationValidated = data.practitioner.is_federation_validated;
    }
    
    // Extract other data fields
    if (data.competition) {
      scanData.competitionId = data.competition.id;
      scanData.competitionName = data.competition.name;
    }
    
    if (data.training_session) {
      scanData.trainingSessionId = data.training_session.id;
      scanData.trainingSessionName = data.training_session.name;
    }
    
    if (data.event) {
      scanData.eventId = data.event.id;
      scanData.eventName = data.event.name;
    }
    
    // Add scan count if available
    if (data.scan_count !== undefined) {
      scanData.scanCount = data.scan_count;
    }
    
    // Add location if available
    if (data.location) {
      scanData.location = data.location;
    }
    
    // Add any other fields in the data object
    if (data.data) {
      Object.keys(data.data).forEach(key => {
        // Convert snake_case to camelCase
        const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
        scanData[camelKey] = data.data[key];
      });
    }
    
    return {
      id: data.id || `scan-${Date.now()}`,
      timestamp: data.scan_date ? new Date(data.scan_date).getTime() : Date.now(),
      type: data.scan_type as ScanType || 'unknown',
      isValid: data.is_valid !== undefined ? data.is_valid : data.valid || false,
      message: data.validation_message || data.message || '',
      isOffline: data.is_offline_scan || false,
      data: scanData,
    };
  }
}

export const qrScannerService = new QRScannerService();