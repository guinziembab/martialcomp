import { createOfflineToken, verifyOfflineToken } from '@utils/offlineVerification';
import AsyncStorage from '@react-native-async-storage/async-storage';

describe('offlineVerification', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock AsyncStorage.getItem to return mock offline profiles
    (AsyncStorage.getItem as jest.Mock).mockImplementation((key: string) => {
      if (key === '@offline_profiles') {
        return Promise.resolve(JSON.stringify([{
          id: 'test-profile-id',
          offlineId: 'test-offline-id',
          firstName: 'John',
          lastName: 'Doe',
          hashedId: 'test-hashed-id',
          verificationToken: 'test-verification-token',
          expiryTimestamp: Date.now() + 3600000, // 1 hour in the future
        }]));
      }
      return Promise.resolve(null);
    });
  });

  describe('createOfflineToken', () => {
    it('should create a valid token with correct format', () => {
      const type = 'practitioner_profile';
      const data = { 
        practitionerId: 'test-id',
        practitionerName: 'John Doe',
      };
      const expiryMinutes = 60;
      
      const token = createOfflineToken(type, data, expiryMinutes);
      
      // Token should be a string (base64 encoded)
      expect(typeof token).toBe('string');
      
      // Decode and verify token structure
      const decodedToken = JSON.parse(atob(token));
      expect(decodedToken).toHaveProperty('type', type);
      expect(decodedToken).toHaveProperty('data', data);
      expect(decodedToken).toHaveProperty('signature');
      expect(decodedToken).toHaveProperty('expiry');
      
      // Verify expiry is in the future
      const now = Date.now();
      const expiry = parseInt(decodedToken.expiry, 10);
      expect(expiry).toBeGreaterThan(now);
      
      // Verify expiry is approximately correct
      const expectedExpiry = now + expiryMinutes * 60 * 1000;
      const tolerance = 5000; // 5 seconds tolerance
      expect(Math.abs(expiry - expectedExpiry)).toBeLessThan(tolerance);
    });
  });

  describe('verifyOfflineToken', () => {
    it('should return invalid result for malformed token', async () => {
      const result = await verifyOfflineToken('invalid-token');
      
      expect(result.isValid).toBe(false);
      expect(result.message).toBe('Invalid QR code format');
    });

    it('should return invalid result for expired token', async () => {
      // Create a token that's already expired
      const type = 'practitioner_profile';
      const data = { practitionerId: 'test-id' };
      const expiry = Date.now() - 60000; // 1 minute in the past
      
      const token = btoa(JSON.stringify({
        type,
        data,
        signature: 'test-signature',
        expiry,
      }));
      
      const result = await verifyOfflineToken(token);
      
      expect(result.isValid).toBe(false);
      expect(result.message).toBe('QR code has expired');
    });

    it('should return invalid result for incomplete token', async () => {
      // Create a token missing required fields
      const token = btoa(JSON.stringify({
        type: 'practitioner_profile',
        // Missing data, signature, and expiry
      }));
      
      const result = await verifyOfflineToken(token);
      
      expect(result.isValid).toBe(false);
      expect(result.message).toBe('Incomplete QR code data');
    });

    it('should validate practitioner profile token correctly', async () => {
      // Create a valid practitioner profile token
      const token = btoa(JSON.stringify({
        type: 'practitioner_profile',
        data: {
          hashedId: 'test-hashed-id',
        },
        signature: 'test-verification-token', // This matches the mock profile's verification token
        expiry: Date.now() + 3600000, // 1 hour in the future
      }));
      
      const result = await verifyOfflineToken(token);
      
      expect(result.isValid).toBe(true);
      expect(result.type).toBe('practitioner_profile');
      expect(result.data).toHaveProperty('profileId', 'test-profile-id');
      expect(result.data).toHaveProperty('practitionerId', 'test-profile-id');
      expect(result.data).toHaveProperty('practitionerName', 'John Doe');
    });
  });
});