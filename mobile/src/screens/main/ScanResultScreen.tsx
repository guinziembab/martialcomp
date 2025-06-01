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
  Animated,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import { QRStackParamList } from '@navigation/MainNavigator';
import { AppDispatch, RootState } from '@store/index';
import { clearScanResult, setScanning } from '@store/slices/qrScannerSlice';
import { addPendingSyncAction } from '@store/slices/offlineSlice';
import { ScanResult, ScanType } from '@types/qrScanner';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

type Props = NativeStackScreenProps<QRStackParamList, 'ScanResult'>;

const ScanResultScreen: React.FC<Props> = ({ navigation, route }) => {
  const { scanId } = route.params;
  const { theme } = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  
  const { scanHistory, lastScanResult } = useSelector((state: RootState) => state.qrScanner);
  const { isOfflineMode } = useSelector((state: RootState) => state.offline);
  
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [animation] = useState(new Animated.Value(0));

  useEffect(() => {
    // Find the scan result in history or use the last scan result
    const result = scanHistory.find(scan => scan.id === scanId) || lastScanResult;
    setScanResult(result || null);
    
    // Animate the validation status
    Animated.sequence([
      Animated.timing(animation, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(animation, {
        toValue: 0.8,
        duration: 150,
        useNativeDriver: true,
      }),
      Animated.timing(animation, {
        toValue: 1,
        duration: 150,
        useNativeDriver: true,
      }),
    ]).start();
    
    return () => {
      // Clear the scan result when unmounting
      dispatch(clearScanResult());
    };
  }, [scanId, scanHistory, lastScanResult, dispatch, animation]);

  const handleBackToScanner = () => {
    dispatch(setScanning(true));
    navigation.goBack();
  };

  const handleViewProfile = () => {
    if (scanResult?.data.practitionerId) {
      navigation.navigate('ProfileDetail', { profileId: scanResult.data.practitionerId });
    }
  };

  const handleShareResult = async () => {
    if (!scanResult) return;
    
    try {
      const message = `
Scan Result from MartialComp:
Type: ${scanResult.type}
Valid: ${scanResult.isValid ? 'Yes' : 'No'}
${scanResult.data.practitionerName ? `Practitioner: ${scanResult.data.practitionerName}` : ''}
${scanResult.data.competitionName ? `Competition: ${scanResult.data.competitionName}` : ''}
${scanResult.message}
      `.trim();
      
      await Share.share({
        message,
        title: 'MartialComp Scan Result',
      });
    } catch (error) {
      console.error('Error sharing scan result:', error);
    }
  };

  const handleAddToOffline = async () => {
    if (!scanResult) return;
    
    try {
      // Add the scan to pending sync actions
      await dispatch(addPendingSyncAction({
        id: `offline-sync-${Date.now()}`,
        timestamp: Date.now(),
        type: 'scan',
        entityId: scanResult.id,
        entityType: 'scan',
        data: scanResult,
        priority: 'medium',
        attempts: 0,
      })).unwrap();
      
      Alert.alert(
        'Success',
        'Scan result saved for offline sync',
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert(
        'Error',
        'Failed to save scan result for offline sync',
        [{ text: 'OK' }]
      );
    }
  };

  if (!scanResult) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={[styles.loadingText, { color: theme.colors.text }]}>
          Loading scan result...
        </Text>
      </View>
    );
  }

  const getTypeIcon = (type: ScanType) => {
    switch (type) {
      case 'practitioner_profile':
        return 'account-card-details';
      case 'competition_entry':
        return 'ticket-confirmation';
      case 'certificate':
        return 'certificate';
      case 'attendance':
        return 'checkbox-marked-circle';
      case 'licence':
        return 'card-account-details';
      case 'grade':
        return 'medal';
      default:
        return 'qrcode';
    }
  };

  const getTypeColor = (type: ScanType) => {
    switch (type) {
      case 'practitioner_profile':
        return theme.colors.primary;
      case 'competition_entry':
        return theme.colors.secondary;
      case 'certificate':
        return theme.colors.martial.gold;
      case 'attendance':
        return theme.colors.success;
      case 'licence':
        return theme.colors.martial.blue;
      case 'grade':
        return theme.colors.accent;
      default:
        return theme.colors.textSecondary;
    }
  };

  const getValidationColor = (isValid: boolean) => {
    return isValid ? theme.colors.success : theme.colors.error;
  };

  const validationScale = animation.interpolate({
    inputRange: [0, 1],
    outputRange: [0.5, 1],
  });

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.header, { backgroundColor: theme.colors.primary }]}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={handleBackToScanner}
        >
          <Icon name="arrow-left" size={24} color={theme.colors.surface} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.colors.surface }]}>
          Scan Result
        </Text>
        <TouchableOpacity
          style={styles.shareButton}
          onPress={handleShareResult}
        >
          <Icon name="share-variant" size={24} color={theme.colors.surface} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Offline Indicator */}
        {scanResult.isOffline && (
          <View style={[styles.offlineBanner, { backgroundColor: theme.colors.warning + '30' }]}>
            <Icon name="cloud-off-outline" size={20} color={theme.colors.warning} />
            <Text style={[styles.offlineText, { color: theme.colors.warning }]}>
              Verified offline - Limited functionality
            </Text>
          </View>
        )}

        {/* Validation Status */}
        <Animated.View
          style={[
            styles.validationContainer,
            { 
              backgroundColor: getValidationColor(scanResult.isValid) + '20',
              transform: [{ scale: validationScale }],
            }
          ]}
        >
          <Icon
            name={scanResult.isValid ? 'check-circle' : 'close-circle'}
            size={80}
            color={getValidationColor(scanResult.isValid)}
          />
          <Text
            style={[
              styles.validationText,
              { color: getValidationColor(scanResult.isValid) }
            ]}
          >
            {scanResult.isValid ? 'Valid' : 'Invalid'}
          </Text>
          <Text style={[styles.validationMessage, { color: theme.colors.text }]}>
            {scanResult.message}
          </Text>
        </Animated.View>

        {/* Scan Details */}
        <View style={styles.detailsSection}>
          <View style={[styles.detailsCard, { backgroundColor: theme.colors.surface, ...theme.elevation.z2 }]}>
            <View style={styles.typeHeader}>
              <View
                style={[
                  styles.typeIconContainer,
                  { backgroundColor: getTypeColor(scanResult.type) + '20' }
                ]}
              >
                <Icon
                  name={getTypeIcon(scanResult.type)}
                  size={24}
                  color={getTypeColor(scanResult.type)}
                />
              </View>
              <View style={styles.typeInfo}>
                <Text style={[styles.typeTitle, { color: theme.colors.text }]}>
                  {scanResult.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Text>
                <Text style={[styles.timestamp, { color: theme.colors.textSecondary }]}>
                  {new Date(scanResult.timestamp).toLocaleString()}
                </Text>
              </View>
            </View>

            <View style={styles.detailsContent}>
              {scanResult.data.practitionerName && (
                <View style={styles.detailRow}>
                  <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
                    Practitioner:
                  </Text>
                  <Text style={[styles.detailValue, { color: theme.colors.text }]}>
                    {scanResult.data.practitionerName}
                  </Text>
                </View>
              )}

              {scanResult.data.competitionName && (
                <View style={styles.detailRow}>
                  <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
                    Competition:
                  </Text>
                  <Text style={[styles.detailValue, { color: theme.colors.text }]}>
                    {scanResult.data.competitionName}
                  </Text>
                </View>
              )}

              {scanResult.data.certificateType && (
                <View style={styles.detailRow}>
                  <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
                    Certificate Type:
                  </Text>
                  <Text style={[styles.detailValue, { color: theme.colors.text }]}>
                    {scanResult.data.certificateType}
                  </Text>
                </View>
              )}

              {scanResult.data.licenceExpiry && (
                <View style={styles.detailRow}>
                  <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
                    Licence Expiry:
                  </Text>
                  <Text style={[styles.detailValue, { color: theme.colors.text }]}>
                    {new Date(scanResult.data.licenceExpiry).toLocaleDateString()}
                  </Text>
                </View>
              )}

              {scanResult.data.gradeName && (
                <View style={styles.detailRow}>
                  <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
                    Grade:
                  </Text>
                  <Text style={[styles.detailValue, { color: theme.colors.text }]}>
                    {scanResult.data.gradeName}
                  </Text>
                </View>
              )}

              {/* Display any other data from scanResult.data */}
              {Object.entries(scanResult.data).map(([key, value]) => {
                // Skip the already displayed fields
                if ([
                  'practitionerId', 'practitionerName', 'competitionId', 'competitionName',
                  'certificateId', 'certificateType', 'licenceId', 'licenceExpiry',
                  'gradeId', 'gradeName'
                ].includes(key)) {
                  return null;
                }
                
                // Skip complex objects
                if (typeof value === 'object') {
                  return null;
                }
                
                return (
                  <View style={styles.detailRow} key={key}>
                    <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
                      {key.replace(/([A-Z])/g, ' $1')
                        .replace(/^./, str => str.toUpperCase())
                        .replace(/Id$/, 'ID')}:
                    </Text>
                    <Text style={[styles.detailValue, { color: theme.colors.text }]}>
                      {String(value)}
                    </Text>
                  </View>
                );
              })}
            </View>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsSection}>
          {scanResult.type === 'practitioner_profile' && scanResult.data.practitionerId && (
            <TouchableOpacity
              style={[
                styles.actionButton,
                styles.primaryAction,
                { backgroundColor: theme.colors.primary }
              ]}
              onPress={handleViewProfile}
            >
              <Icon name="account" size={20} color={theme.colors.surface} style={styles.actionIcon} />
              <Text style={[styles.actionText, { color: theme.colors.surface }]}>
                View Profile
              </Text>
            </TouchableOpacity>
          )}

          {!scanResult.isOffline && (
            <TouchableOpacity
              style={[
                styles.actionButton,
                styles.secondaryAction,
                { backgroundColor: theme.colors.surface, borderColor: theme.colors.primary }
              ]}
              onPress={handleAddToOffline}
            >
              <Icon name="content-save-outline" size={20} color={theme.colors.primary} style={styles.actionIcon} />
              <Text style={[styles.actionText, { color: theme.colors.primary }]}>
                Save for Offline
              </Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={[
              styles.actionButton,
              styles.secondaryAction,
              { backgroundColor: theme.colors.surface, borderColor: theme.colors.text }
            ]}
            onPress={handleBackToScanner}
          >
            <Icon name="qrcode-scan" size={20} color={theme.colors.text} style={styles.actionIcon} />
            <Text style={[styles.actionText, { color: theme.colors.text }]}>
              Scan Again
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingBottom: 15,
    paddingHorizontal: 20,
  },
  backButton: {
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
  validationContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    margin: 20,
    padding: 20,
    borderRadius: 12,
  },
  validationText: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 10,
  },
  validationMessage: {
    fontSize: 16,
    textAlign: 'center',
    marginTop: 10,
  },
  detailsSection: {
    paddingHorizontal: 20,
  },
  detailsCard: {
    borderRadius: 12,
    padding: 15,
  },
  typeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  typeIconContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  typeInfo: {
    flex: 1,
  },
  typeTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  timestamp: {
    fontSize: 12,
  },
  detailsContent: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E0E0E0',
    paddingTop: 15,
  },
  detailRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  detailLabel: {
    fontSize: 14,
    width: '40%',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
  },
  actionsSection: {
    padding: 20,
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
  primaryAction: {
    marginBottom: 15,
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

export default ScanResultScreen;