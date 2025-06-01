import axios from 'axios';
import { Profile } from '@types/profile';
import { API_URL, ENDPOINTS, buildUrl } from '@config/api';

class ProfileService {
  async getProfile(token: string): Promise<Profile> {
    try {
      const response = await axios.get(`${API_URL}${ENDPOINTS.PROFILE}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      return this.transformProfileResponse(response.data);
    } catch (error) {
      console.error('Get profile error:', error);
      throw new Error('Failed to fetch profile information.');
    }
  }

  async updateProfile(token: string, profileData: Partial<Profile>): Promise<Profile> {
    try {
      const response = await axios.patch(
        `${API_URL}${ENDPOINTS.PROFILE_UPDATE}`,
        this.transformProfileRequest(profileData),
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      return this.transformProfileResponse(response.data);
    } catch (error) {
      console.error('Update profile error:', error);
      throw new Error('Failed to update profile information.');
    }
  }

  async uploadProfileImage(token: string, imageUri: string): Promise<{ avatarUrl: string }> {
    try {
      // Create form data
      const formData = new FormData();
      
      // Extract filename from URI
      const uriParts = imageUri.split('/');
      const fileName = uriParts[uriParts.length - 1];
      
      // Append image file
      formData.append('avatar', {
        uri: imageUri,
        name: fileName,
        type: 'image/jpeg', // Adjust as needed based on the image type
      } as any);
      
      const response = await axios.post(
        `${API_URL}${ENDPOINTS.PROFILE}/upload-avatar/`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      return {
        avatarUrl: response.data.avatar_url,
      };
    } catch (error) {
      console.error('Upload profile image error:', error);
      throw new Error('Failed to upload profile image.');
    }
  }

  // Helper method to transform API response to our Profile type
  private transformProfileResponse(data: any): Profile {
    return {
      id: data.id,
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
      address: data.address ? {
        street: data.address.street,
        city: data.address.city,
        postalCode: data.address.postal_code,
        country: data.address.country,
      } : undefined,
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
      achievements: data.achievements ? data.achievements.map((a: any) => ({
        id: a.id,
        title: a.title,
        description: a.description,
        date: a.date,
        category: a.category,
        place: a.place,
        competitionName: a.competition_name,
      })) : undefined,
    };
  }

  // Helper method to transform our Profile type to API request format
  private transformProfileRequest(profile: Partial<Profile>): any {
    const request: any = {};
    
    if (profile.firstName !== undefined) request.first_name = profile.firstName;
    if (profile.lastName !== undefined) request.last_name = profile.lastName;
    if (profile.dateOfBirth !== undefined) request.date_of_birth = profile.dateOfBirth;
    if (profile.gender !== undefined) request.gender = profile.gender;
    if (profile.nationality !== undefined) request.nationality = profile.nationality;
    if (profile.phoneNumber !== undefined) request.phone_number = profile.phoneNumber;
    
    if (profile.address) {
      request.address = {
        street: profile.address.street,
        city: profile.address.city,
        postal_code: profile.address.postalCode,
        country: profile.address.country,
      };
    }
    
    return request;
  }
}

export const profileService = new ProfileService();