import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  ActivityIndicator,
  Alert,
  Platform,
  Share,
} from 'react-native';
import { useSelector } from 'react-redux';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import { ProfileStackParamList } from '@navigation/MainNavigator';
import { RootState } from '@store/index';
import { OfflineProfile } from '@types/offline';
import { Discipline, Grade } from '@types/profile';
import { createOfflineToken } from '@utils/offlineVerification';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

type Props = NativeStackScreenProps<ProfileStackParamList, 'OfflineProfileDetail'>;

const OfflineProfileDetailScreen: React.FC<Props> = ({ navigation, route }) => {
  const { offlineId } = route.params;
  const { theme } = useTheme();
  
  const { offlineProfiles } = useSelector((state: RootState) => state.offline);
  
  const [profile, setProfile] = useState<OfflineProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpired, setIsExpired] = useState(false);
  const [generatingQR, setGeneratingQR] = useState(false);

  useEffect(() => {
    loadProfile();
  }, [offlineId, offlineProfiles]);

  const loadProfile = () => {
    setIsLoading(true);
    try {
      const foundProfile = offlineProfiles.find(p => p.offlineId === offlineId);
      
      if (foundProfile) {
        setProfile(foundProfile);
        setIsExpired(Date.now() > foundProfile.expiryTimestamp);
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleShareProfile = async () => {
    if (!profile) return;
    
    try {
      setGeneratingQR(true);
      
      // Create token data for sharing
      const tokenData = {
        practitionerId: profile.id,
        practitionerName: `${profile.firstName} ${profile.lastName}`,
        hashedId: profile.hashedId,
        licenseNumber: profile.licenseNumber,
      };
      
      // Create offline token
      const token = createOfflineToken('practitioner_profile', tokenData, 60); // Valid for 60 minutes
      
      // Share the token
      await Share.share({
        message: `
MartialComp Profile Verification
Name: ${profile.firstName} ${profile.lastName}
${profile.licenseNumber ? `License: ${profile.licenseNumber}` : ''}
Valid until: ${new Date(Date.now() + 60 * 60 * 1000).toLocaleString()}

Use this token in the MartialComp app to verify this profile:
${token}
        `.trim(),
        title: 'MartialComp Profile Verification',
      });
    } catch (error) {
      console.error('Error sharing profile:', error);
      Alert.alert(
        'Share Failed',
        'Failed to share profile verification. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setGeneratingQR(false);
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

  if (isLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={[styles.loadingText, { color: theme.colors.text }]}>
          Loading profile...
        </Text>
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={[styles.errorContainer, { backgroundColor: theme.colors.background }]}>
        <Icon name="account-off" size={50} color={theme.colors.error} />
        <Text style={[styles.errorText, { color: theme.colors.text }]}>
          Profile Not Found
        </Text>
        <TouchableOpacity
          style={[styles.backButton, { backgroundColor: theme.colors.primary }]}
          onPress={() => navigation.goBack()}
        >
          <Text style={[styles.backButtonText, { color: theme.colors.surface }]}>
            Go Back
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.header, { backgroundColor: theme.colors.primary }]}>
        <TouchableOpacity
          style={styles.backButtonIcon}
          onPress={() => navigation.goBack()}
        >
          <Icon name="arrow-left" size={24} color={theme.colors.surface} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.colors.surface }]}>
          Offline Profile
        </Text>
        <TouchableOpacity
          style={styles.shareButton}
          onPress={handleShareProfile}
          disabled={generatingQR || isExpired}
        >
          <Icon
            name={generatingQR ? 'loading' : 'share-variant'}
            size={24}
            color={isExpired ? theme.colors.surface + '50' : theme.colors.surface}
          />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Offline Banner */}
        <View
          style={[
            styles.offlineBanner,
            {
              backgroundColor: isExpired
                ? theme.colors.error + '20'
                : theme.colors.warning + '20'
            }
          ]}
        >
          <Icon
            name={isExpired ? 'clock-alert' : 'cloud-off-outline'}
            size={20}
            color={isExpired ? theme.colors.error : theme.colors.warning}
          />
          <Text
            style={[
              styles.offlineText,
              {
                color: isExpired ? theme.colors.error : theme.colors.warning
              }
            ]}
          >
            {isExpired
              ? 'Profile has expired - Please sync to update'
              : 'Offline Profile - Limited functionality'}
          </Text>
        </View>

        <View style={styles.profileHeader}>
          <View style={styles.profileImageContainer}>
            {profile.avatarUrl ? (
              <Image
                source={{ uri: profile.avatarUrl }}
                style={styles.profileImage}
              />
            ) : (
              <View
                style={[
                  styles.profileImagePlaceholder,
                  { backgroundColor: theme.colors.primary + '30' }
                ]}
              >
                <Text style={[styles.profileInitials, { color: theme.colors.primary }]}>
                  {profile.firstName.charAt(0)}{profile.lastName.charAt(0)}
                </Text>
              </View>
            )}
          </View>

          <Text style={[styles.profileName, { color: theme.colors.text }]}>
            {profile.firstName} {profile.lastName}
          </Text>

          <View style={styles.syncInfo}>
            <Text style={[styles.syncInfoText, { color: theme.colors.textSecondary }]}>
              Last synced: {new Date(profile.lastSyncTimestamp).toLocaleString()}
            </Text>
            <Text style={[styles.syncInfoText, { color: theme.colors.textSecondary }]}>
              Expires: {new Date(profile.expiryTimestamp).toLocaleString()}
            </Text>
          </View>
        </View>

        {/* Personal Information Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Personal Information
          </Text>
          
          <View style={[styles.infoCard, { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }]}>
            {profile.licenseNumber && (
              <View style={styles.infoRow}>
                <View style={styles.infoLabelContainer}>
                  <Icon name="card-account-details" size={18} color={theme.colors.primary} />
                  <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
                    License
                  </Text>
                </View>
                <Text style={[styles.infoValue, { color: theme.colors.text }]}>
                  {profile.licenseNumber}
                </Text>
              </View>
            )}

            <View style={styles.infoRow}>
              <View style={styles.infoLabelContainer}>
                <Icon name="cake-variant" size={18} color={theme.colors.primary} />
                <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
                  Date of Birth
                </Text>
              </View>
              <Text style={[styles.infoValue, { color: theme.colors.text }]}>
                {profile.dateOfBirth ? new Date(profile.dateOfBirth).toLocaleDateString() : 'Not provided'}
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
                {profile.nationality || 'Not provided'}
              </Text>
            </View>

            {profile.gender && (
              <View style={styles.infoRow}>
                <View style={styles.infoLabelContainer}>
                  <Icon
                    name={profile.gender === 'M' ? 'gender-male' : profile.gender === 'F' ? 'gender-female' : 'gender-non-binary'}
                    size={18}
                    color={theme.colors.primary}
                  />
                  <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
                    Gender
                  </Text>
                </View>
                <Text style={[styles.infoValue, { color: theme.colors.text }]}>
                  {profile.gender === 'M' ? 'Male' : profile.gender === 'F' ? 'Female' : 'Other'}
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Club Information */}
        {profile.club && (
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
        {profile.disciplines && profile.disciplines.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
              Disciplines & Grades
            </Text>
            
            {profile.disciplines.map(discipline => renderDisciplineItem(discipline))}
          </View>
        )}

        {/* Action Buttons */}
        <View style={styles.actionsSection}>
          <TouchableOpacity
            style={[
              styles.actionButton,
              { backgroundColor: theme.colors.primary }
            ]}
            onPress={handleShareProfile}
            disabled={generatingQR || isExpired}
          >
            {generatingQR ? (
              <ActivityIndicator size="small" color={theme.colors.surface} />
            ) : (
              <>
                <Icon
                  name="qrcode"
                  size={20}
                  color={theme.colors.surface}
                  style={styles.actionIcon}
                />
                <Text style={[styles.actionText, { color: theme.colors.surface }]}>
                  {isExpired ? 'Expired - Cannot Share' : 'Share Profile Verification'}
                </Text>
              </>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.actionButton,
              styles.secondaryAction,
              { backgroundColor: theme.colors.surface, borderColor: theme.colors.primary }
            ]}
            onPress={() => navigation.goBack()}
          >
            <Icon
              name="arrow-left"
              size={20}
              color={theme.colors.primary}
              style={styles.actionIcon}
            />
            <Text style={[styles.actionText, { color: theme.colors.primary }]}>
              Back to Profiles
            </Text>
          </TouchableOpacity>
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 20,
    fontWeight: 'bold',
    marginVertical: 20,
  },
  backButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingBottom: 15,
    paddingHorizontal: 20,
  },
  backButtonIcon: {
    padding: 5,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  shareButton: {
    padding: 5,
  },
  scrollContent: {
    paddingBottom: 30,
  },
  offlineBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 10,
    marginHorizontal: 20,
    marginTop: 10,
    borderRadius: 8,
  },
  offlineText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '500',
  },
  profileHeader: {
    alignItems: 'center',
    marginBottom: 20,
    padding: 20,
  },
  profileImageContainer: {
    marginBottom: 15,
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  profileImagePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileInitials: {
    fontSize: 36,
    fontWeight: 'bold',
  },
  profileName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  syncInfo: {
    alignItems: 'center',
  },
  syncInfoText: {
    fontSize: 12,
    marginBottom: 5,
  },
  section: {
    marginTop: 10,
    paddingHorizontal: 20,
    marginBottom: 20,
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
  actionsSection: {
    paddingHorizontal: 20,
    marginTop: 10,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 50,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  secondaryAction: {
    marginBottom: 10,
  },
  actionIcon: {
    marginRight: 10,
  },
  actionText: {
    fontSize: 16,
    fontWeight: '500',
  },
});

export default OfflineProfileDetailScreen;