import axios from 'axios';
import { API_URL, ENDPOINTS } from '@config/api';
import { OfflineProfile, PendingSyncAction } from '@types/offline';

interface SyncResult {
  syncedCount: number;
  failedCount: number;
  failedActions?: { id: string; reason: string }[];
}

class OfflineService {
  async getOfflineProfiles(token: string): Promise<OfflineProfile[]> {
    try {
      const response = await axios.get(`${API_URL}${ENDPOINTS.OFFLINE_PROFILES}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      return response.data.profiles.map(this.transformOfflineProfileResponse);
    } catch (error) {
      console.error('Get offline profiles error:', error);
      throw new Error('Failed to fetch offline profiles.');
    }
  }

  async syncPendingActions(token: string, pendingActions: PendingSyncAction[]): Promise<SyncResult> {
    try {
      const response = await axios.post(
        `${API_URL}${ENDPOINTS.OFFLINE_SYNC}`,
        {
          actions: pendingActions.map(action => ({
            id: action.id,
            timestamp: action.timestamp,
            type: action.type,
            entity_id: action.entityId,
            entity_type: action.entityType,
            data: action.data,
          })),
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      return {
        syncedCount: response.data.synced_count,
        failedCount: response.data.failed_count,
        failedActions: response.data.failed_actions?.map((action: any) => ({
          id: action.id,
          reason: action.reason,
        })),
      };
    } catch (error) {
      console.error('Sync pending actions error:', error);
      throw new Error('Failed to synchronize offline data.');
    }
  }

  // Helper method to transform API response to our OfflineProfile type
  private transformOfflineProfileResponse(data: any): OfflineProfile {
    return {
      id: data.id,
      offlineId: data.offline_id,
      userId: data.user_id,
      firstName: data.first_name,
      lastName: data.last_name,
      dateOfBirth: data.date_of_birth,
      gender: data.gender,
      nationality: data.nationality,
      phoneNumber: data.phone_number,
      avatarUrl: data.avatar_url,
      licenseNumber: data.license_number,
      licenseExpiryDate: data.license_expiry_date,
      encryptedData: data.encrypted_data,
      hashedId: data.hashed_id,
      lastSyncTimestamp: new Date(data.last_sync_timestamp).getTime(),
      verificationToken: data.verification_token,
      expiryTimestamp: new Date(data.expiry_timestamp).getTime(),
      disciplines: data.disciplines.map((d: any) => ({
        id: d.id,
        name: d.name,
        grade: d.grade ? {
          id: d.grade.id,
          name: d.grade.name,
          level: d.grade.level,
          color: d.grade.color,
          dateObtained: d.grade.date_obtained,
          issuingAuthority: d.grade.issuing_authority,
        } : undefined,
        startDate: d.start_date,
        yearsOfExperience: d.years_of_experience,
      })),
      medicalCertificate: data.medical_certificate ? {
        id: data.medical_certificate.id,
        issuanceDate: data.medical_certificate.issuance_date,
        expiryDate: data.medical_certificate.expiry_date,
        isValid: data.medical_certificate.is_valid,
        documentUrl: data.medical_certificate.document_url,
      } : undefined,
      club: data.club ? {
        id: data.club.id,
        name: data.club.name,
        logoUrl: data.club.logo_url,
        address: data.club.address ? {
          street: data.club.address.street,
          city: data.club.address.city,
          postalCode: data.club.address.postal_code,
          country: data.club.address.country,
        } : undefined,
        role: data.club.role,
        joinDate: data.club.join_date,
      } : undefined,
    };
  }
}

export const offlineService = new OfflineService();