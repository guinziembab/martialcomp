import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Platform,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import { ProfileStackParamList } from '@navigation/MainNavigator';
import { AppDispatch, RootState } from '@store/index';
import { fetchProfile } from '@store/slices/profileSlice';
import { logout } from '@store/slices/authSlice';
import { downloadOfflineProfiles } from '@store/slices/offlineSlice';
import { Discipline, Grade } from '@types/profile';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import * as ImagePicker from 'expo-image-picker';
import { profileService } from '@services/profileService';

type Props = NativeStackScreenProps<ProfileStackParamList, 'ProfileMain'>;

const ProfileScreen: React.FC<Props> = ({ navigation }) => {
  const { theme } = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  
  const { user } = useSelector((state: RootState) => state.auth);
  const { profile, isLoading: profileLoading, error: profileError } = useSelector((state: RootState) => state.profile);
  const { offlineProfiles, isOfflineMode } = useSelector((state: RootState) => state.offline);
  
  const [refreshing, setRefreshing] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      await dispatch(fetchProfile()).unwrap();
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await dispatch(fetchProfile()).unwrap();
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Logout',
          onPress: async () => {
            try {
              await dispatch(logout()).unwrap();
            } catch (error) {
              console.error('Logout failed:', error);
            }
          },
          style: 'destructive',
        },
      ]
    );
  };

  const downloadProfiles = async () => {
    try {
      await dispatch(downloadOfflineProfiles()).unwrap();
      Alert.alert(
        'Success',
        'Profiles have been downloaded for offline use',
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert(
        'Download Failed',
        'Failed to download profiles for offline use',
        [{ text: 'OK' }]
      );
    }
  };

  const pickImage = async () => {
    // Ask for permission
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert(
        'Permission Required',
        'Please grant permission to access your photos',
        [{ text: 'OK' }]
      );
      return;
    }

    // Launch image picker
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.cancelled && result.assets && result.assets[0].uri) {
      uploadProfileImage(result.assets[0].uri);
    }
  };

  const uploadProfileImage = async (imageUri: string) => {
    setUploadingImage(true);
    try {
      const { token } = user || {};
      if (!token) {
        throw new Error('Authentication token not found');
      }

      const result = await profileService.uploadProfileImage(token, imageUri);
      
      // Refresh profile to get updated avatar
      await dispatch(fetchProfile()).unwrap();
      
      Alert.alert(
        'Success',
        'Profile image updated successfully',
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert(
        'Upload Failed',
        'Failed to upload profile image',
        [{ text: 'OK' }]
      );
    } finally {
      setUploadingImage(false);
    }
  };

  const renderGradeBadge = (grade: Grade) => {
    return (
      <View
        style={[
          styles.gradeBadge,
          { backgroundColor: grade.color || theme.colors.martial.black }
        ]}
      >
        <Text style={[styles.gradeName, { color: '#FFFFFF' }]}>
          {grade.name}
        </Text>
      </View>
    );
  };

  const renderDisciplineItem = (discipline: Discipline) => {
    return (
      <View
        key={discipline.id}
        style={[
          styles.disciplineItem,
          { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }
        ]}
      >
        <View style={styles.disciplineHeader}>
          <Text style={[styles.disciplineName, { color: theme.colors.text }]}>
            {discipline.name}
          </Text>
          {discipline.yearsOfExperience && (
            <Text style={[styles.experienceText, { color: theme.colors.textSecondary }]}>
              {discipline.yearsOfExperience} years
            </Text>
          )}
        </View>

        {discipline.grade && (
          <View style={styles.gradeContainer}>
            {renderGradeBadge(discipline.grade)}
            <Text style={[styles.gradeDate, { color: theme.colors.textSecondary }]}>
              Obtained: {new Date(discipline.grade.dateObtained).toLocaleDateString()}
            </Text>
          </View>
        )}
      </View>
    );
  };

  if (profileLoading && !profile) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={[styles.loadingText, { color: theme.colors.text }]}>
          Loading profile...
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[theme.colors.primary]}
            tintColor={theme.colors.primary}
          />
        }
      >
        <View style={[styles.header, { backgroundColor: theme.colors.primary }]}>
          <View style={styles.headerContent}>
            <TouchableOpacity 
              style={styles.profileImageContainer}
              onPress={pickImage}
              disabled={uploadingImage}
            >
              {uploadingImage ? (
                <ActivityIndicator size="small" color={theme.colors.surface} />
              ) : profile?.avatarUrl ? (
                <Image
                  source={{ uri: profile.avatarUrl }}
                  style={styles.profileImage}
                />
              ) : (
                <View
                  style={[
                    styles.profileImagePlaceholder,
                    { backgroundColor: theme.colors.surface + '60' }
                  ]}
                >
                  <Text style={[styles.profileInitials, { color: theme.colors.surface }]}>
                    {profile?.firstName?.charAt(0) || ''}{profile?.lastName?.charAt(0) || ''}
                  </Text>
                </View>
              )}
              <View style={[styles.editIconContainer, { backgroundColor: theme.colors.secondary }]}>
                <Icon name="pencil" size={12} color={theme.colors.surface} />
              </View>
            </TouchableOpacity>

            <Text style={[styles.profileName, { color: theme.colors.surface }]}>
              {profile?.firstName} {profile?.lastName}
            </Text>

            {profile?.licenseNumber && (
              <View style={styles.licenseContainer}>
                <Text style={[styles.licenseLabel, { color: theme.colors.surface + 'CC' }]}>
                  License:
                </Text>
                <Text style={[styles.licenseNumber, { color: theme.colors.surface }]}>
                  {profile.licenseNumber}
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Personal Information Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Personal Information
          </Text>
          
          <View style={[styles.infoCard, { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }]}>
            <View style={styles.infoRow}>
              <View style={styles.infoLabelContainer}>
                <Icon name="email-outline" size={18} color={theme.colors.primary} />
                <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
                  Email
                </Text>
              </View>
              <Text style={[styles.infoValue, { color: theme.colors.text }]}>
                {user?.email || 'Not provided'}
              </Text>
            </View>

            <View style={styles.infoRow}>
              <View style={styles.infoLabelContainer}>
                <Icon name="cake-variant" size={18} color={theme.colors.primary} />
                <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
                  Date of Birth
                </Text>
              </View>
              <Text style={[styles.infoValue, { color: theme.colors.text }]}>
                {profile?.dateOfBirth ? new Date(profile.dateOfBirth).toLocaleDateString() : 'Not provided'}
              </Text>
            </View>

            <View style={styles.infoRow}>
              <View style={styles.infoLabelContainer}>
                <Icon name="flag-outline" size={18} color={theme.colors.primary} />
                <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
                  Nationality
                </Text>
              </View>
              <Text style={[styles.infoValue, { color: theme.colors.text }]}>
                {profile?.nationality || 'Not provided'}
              </Text>
            </View>

            {profile?.phoneNumber && (
              <View style={styles.infoRow}>
                <View style={styles.infoLabelContainer}>
                  <Icon name="phone-outline" size={18} color={theme.colors.primary} />
                  <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
                    Phone
                  </Text>
                </View>
                <Text style={[styles.infoValue, { color: theme.colors.text }]}>
                  {profile.phoneNumber}
                </Text>
              </View>
            )}

            {profile?.address && (
              <View style={styles.infoRow}>
                <View style={styles.infoLabelContainer}>
                  <Icon name="map-marker-outline" size={18} color={theme.colors.primary} />
                  <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
                    Address
                  </Text>
                </View>
                <Text style={[styles.infoValue, { color: theme.colors.text }]}>
                  {profile.address.street}, {profile.address.city}, {profile.address.postalCode}, {profile.address.country}
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Club Information */}
        {profile?.club && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
              Club
            </Text>
            
            <View style={[styles.clubCard, { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }]}>
              <View style={styles.clubHeader}>
                {profile.club.logoUrl ? (
                  <Image
                    source={{ uri: profile.club.logoUrl }}
                    style={styles.clubLogo}
                  />
                ) : (
                  <View
                    style={[
                      styles.clubLogoPlaceholder,
                      { backgroundColor: theme.colors.primary + '20' }
                    ]}
                  >
                    <Icon name="dojo" size={24} color={theme.colors.primary} />
                  </View>
                )}
                
                <View style={styles.clubInfo}>
                  <Text style={[styles.clubName, { color: theme.colors.text }]}>
                    {profile.club.name}
                  </Text>
                  {profile.club.role && (
                    <View style={[
                      styles.roleBadge,
                      { 
                        backgroundColor: 
                          profile.club.role === 'coach' ? theme.colors.accent :
                          profile.club.role === 'admin' ? theme.colors.primary :
                          theme.colors.secondary
                      }
                    ]}>
                      <Text style={[styles.roleText, { color: theme.colors.surface }]}>
                        {profile.club.role.charAt(0).toUpperCase() + profile.club.role.slice(1)}
                      </Text>
                    </View>
                  )}
                </View>
              </View>

              {profile.club.joinDate && (
                <Text style={[styles.joinDate, { color: theme.colors.textSecondary }]}>
                  Member since: {new Date(profile.club.joinDate).toLocaleDateString()}
                </Text>
              )}
            </View>
          </View>
        )}

        {/* Disciplines & Grades Section */}
        {profile?.disciplines && profile.disciplines.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
              Disciplines & Grades
            </Text>
            
            {profile.disciplines.map(discipline => renderDisciplineItem(discipline))}
          </View>
        )}

        {/* Medical Information */}
        {profile?.medicalCertificate && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
              Medical Certificate
            </Text>
            
            <View
              style={[
                styles.medicalCard,
                { 
                  backgroundColor: theme.colors.surface,
                  borderColor: profile.medicalCertificate.isValid ? theme.colors.success : theme.colors.error,
                  ...theme.elevation.z1
                }
              ]}
            >
              <View style={styles.medicalHeader}>
                <Icon
                  name={profile.medicalCertificate.isValid ? 'check-circle' : 'alert-circle'}
                  size={20}
                  color={profile.medicalCertificate.isValid ? theme.colors.success : theme.colors.error}
                />
                <Text
                  style={[
                    styles.medicalStatus,
                    { 
                      color: profile.medicalCertificate.isValid ? theme.colors.success : theme.colors.error
                    }
                  ]}
                >
                  {profile.medicalCertificate.isValid ? 'Valid' : 'Expired'}
                </Text>
              </View>

              <View style={styles.medicalInfo}>
                <Text style={[styles.medicalLabel, { color: theme.colors.textSecondary }]}>
                  Issued: {new Date(profile.medicalCertificate.issuanceDate).toLocaleDateString()}
                </Text>
                <Text style={[styles.medicalLabel, { color: theme.colors.textSecondary }]}>
                  Expires: {new Date(profile.medicalCertificate.expiryDate).toLocaleDateString()}
                </Text>
              </View>

              {profile.medicalCertificate.documentUrl && (
                <TouchableOpacity
                  style={[
                    styles.viewDocButton,
                    { backgroundColor: theme.colors.primary }
                  ]}
                >
                  <Text style={[styles.viewDocText, { color: theme.colors.surface }]}>
                    View Certificate
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        )}

        {/* Offline Profiles */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Offline Access
          </Text>
          
          <View style={[styles.offlineCard, { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }]}>
            <View style={styles.offlineHeader}>
              <Icon
                name={isOfflineMode ? 'cloud-off-outline' : 'cloud-outline'}
                size={20}
                color={isOfflineMode ? theme.colors.warning : theme.colors.primary}
              />
              <Text
                style={[
                  styles.offlineStatus,
                  { 
                    color: isOfflineMode ? theme.colors.warning : theme.colors.primary
                  }
                ]}
              >
                {isOfflineMode ? 'Offline Mode Active' : 'Online Mode'}
              </Text>
            </View>

            <Text style={[styles.offlineInfo, { color: theme.colors.textSecondary }]}>
              {offlineProfiles.length > 0
                ? `${offlineProfiles.length} profiles available for offline use`
                : 'No profiles downloaded for offline use'}
            </Text>

            <View style={styles.offlineActions}>
              <TouchableOpacity
                style={[
                  styles.offlineButton,
                  { backgroundColor: theme.colors.primary }
                ]}
                onPress={downloadProfiles}
              >
                <Text style={[styles.offlineButtonText, { color: theme.colors.surface }]}>
                  Download Profiles
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.offlineButton,
                  { backgroundColor: theme.colors.surface, borderColor: theme.colors.primary }
                ]}
                onPress={() => navigation.navigate('OfflineProfiles')}
              >
                <Text style={[styles.offlineButtonText, { color: theme.colors.primary }]}>
                  Manage Profiles
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Account Actions */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Account
          </Text>
          
          <View style={styles.accountActions}>
            <TouchableOpacity
              style={[
                styles.accountButton,
                { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }
              ]}
              onPress={() => {/* Navigate to edit profile */}}
            >
              <Icon name="account-edit" size={20} color={theme.colors.primary} />
              <Text style={[styles.accountButtonText, { color: theme.colors.text }]}>
                Edit Profile
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.accountButton,
                { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }
              ]}
              onPress={() => {/* Navigate to settings */}}
            >
              <Icon name="cog" size={20} color={theme.colors.primary} />
              <Text style={[styles.accountButtonText, { color: theme.colors.text }]}>
                Settings
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.accountButton,
                { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }
              ]}
              onPress={handleLogout}
            >
              <Icon name="logout" size={20} color={theme.colors.error} />
              <Text style={[styles.accountButtonText, { color: theme.colors.error }]}>
                Logout
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
  },
  scrollContent: {
    paddingBottom: 30,
  },
  header: {
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingBottom: 20,
    alignItems: 'center',
  },
  headerContent: {
    alignItems: 'center',
  },
  profileImageContainer: {
    position: 'relative',
    marginBottom: 10,
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  profileImagePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  profileInitials: {
    fontSize: 36,
    fontWeight: 'bold',
  },
  editIconContainer: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  profileName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  licenseContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  licenseLabel: {
    fontSize: 14,
    marginRight: 5,
  },
  licenseNumber: {
    fontSize: 14,
    fontWeight: '500',
  },
  section: {
    marginTop: 20,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  infoCard: {
    borderRadius: 12,
    padding: 15,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E0E0E0',
  },
  infoLabelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  infoLabel: {
    fontSize: 14,
    marginLeft: 10,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
    textAlign: 'right',
  },
  clubCard: {
    borderRadius: 12,
    padding: 15,
  },
  clubHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  clubLogo: {
    width: 50,
    height: 50,
    borderRadius: 25,
    marginRight: 15,
  },
  clubLogoPlaceholder: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  clubInfo: {
    flex: 1,
  },
  clubName: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  roleBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  roleText: {
    fontSize: 12,
    fontWeight: '500',
  },
  joinDate: {
    fontSize: 12,
  },
  disciplineItem: {
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
  },
  disciplineHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  disciplineName: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  experienceText: {
    fontSize: 12,
  },
  gradeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  gradeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 5,
  },
  gradeName: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  gradeDate: {
    fontSize: 12,
  },
  medicalCard: {
    borderRadius: 12,
    padding: 15,
    borderWidth: 1,
  },
  medicalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  medicalStatus: {
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  medicalInfo: {
    marginBottom: 15,
  },
  medicalLabel: {
    fontSize: 14,
    marginBottom: 5,
  },
  viewDocButton: {
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  viewDocText: {
    fontSize: 14,
    fontWeight: '500',
  },
  offlineCard: {
    borderRadius: 12,
    padding: 15,
  },
  offlineHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  offlineStatus: {
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  offlineInfo: {
    fontSize: 14,
    marginBottom: 15,
  },
  offlineActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  offlineButton: {
    flex: 1,
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 5,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  offlineButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  accountActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  accountButton: {
    flex: 1,
    padding: 15,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 5,
  },
  accountButtonText: {
    fontSize: 14,
    fontWeight: '500',
    marginTop: 5,
  },
});

export default ProfileScreen;