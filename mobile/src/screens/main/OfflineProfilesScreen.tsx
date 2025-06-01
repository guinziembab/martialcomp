import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  TextInput,
  Alert,
  RefreshControl,
  Platform,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import { ProfileStackParamList } from '@navigation/MainNavigator';
import { AppDispatch, RootState } from '@store/index';
import { downloadOfflineProfiles, loadOfflineState, syncOfflineData } from '@store/slices/offlineSlice';
import { OfflineProfile } from '@types/offline';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import AsyncStorage from '@react-native-async-storage/async-storage';

type Props = NativeStackScreenProps<ProfileStackParamList, 'OfflineProfiles'>;

const OfflineProfilesScreen: React.FC<Props> = ({ navigation }) => {
  const { theme } = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  
  const { offlineProfiles, isSyncing, lastSyncTimestamp, pendingSync } = useSelector((state: RootState) => state.offline);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredProfiles, setFilteredProfiles] = useState<OfflineProfile[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadProfiles();
  }, []);

  useEffect(() => {
    filterProfiles();
  }, [searchQuery, offlineProfiles]);

  const loadProfiles = async () => {
    setIsLoading(true);
    try {
      await dispatch(loadOfflineState()).unwrap();
    } catch (error) {
      console.error('Failed to load offline state:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterProfiles = () => {
    if (!searchQuery.trim()) {
      setFilteredProfiles(offlineProfiles);
      return;
    }

    const query = searchQuery.toLowerCase().trim();
    const filtered = offlineProfiles.filter(profile => {
      const fullName = `${profile.firstName} ${profile.lastName}`.toLowerCase();
      return fullName.includes(query) || 
             (profile.licenseNumber && profile.licenseNumber.toLowerCase().includes(query));
    });

    setFilteredProfiles(filtered);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        dispatch(loadOfflineState()).unwrap(),
        dispatch(downloadOfflineProfiles()).unwrap(),
      ]);
    } catch (error) {
      console.error('Refresh failed:', error);
      Alert.alert(
        'Refresh Failed',
        'Failed to refresh offline profiles. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setRefreshing(false);
    }
  };

  const handleSync = async () => {
    try {
      if (pendingSync.length === 0) {
        Alert.alert(
          'No Pending Changes',
          'There are no pending changes to sync.',
          [{ text: 'OK' }]
        );
        return;
      }

      await dispatch(syncOfflineData()).unwrap();
      Alert.alert(
        'Sync Complete',
        'All pending changes have been synced successfully.',
        [{ text: 'OK' }]
      );
    } catch (error) {
      console.error('Sync failed:', error);
      Alert.alert(
        'Sync Failed',
        'Failed to sync offline changes. Please try again later.',
        [{ text: 'OK' }]
      );
    }
  };

  const handleDeleteProfile = async (profile: OfflineProfile) => {
    Alert.alert(
      'Delete Profile',
      `Are you sure you want to delete ${profile.firstName} ${profile.lastName}'s offline profile?`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Delete',
          onPress: async () => {
            try {
              // Remove the profile from AsyncStorage
              const profilesJson = await AsyncStorage.getItem('@offline_profiles');
              if (profilesJson) {
                const profiles = JSON.parse(profilesJson);
                const updatedProfiles = profiles.filter((p: any) => p.offlineId !== profile.offlineId);
                await AsyncStorage.setItem('@offline_profiles', JSON.stringify(updatedProfiles));
              }
              
              // Reload the state
              await dispatch(loadOfflineState()).unwrap();
              
              Alert.alert(
                'Profile Deleted',
                'The offline profile has been deleted successfully.',
                [{ text: 'OK' }]
              );
            } catch (error) {
              console.error('Delete failed:', error);
              Alert.alert(
                'Delete Failed',
                'Failed to delete the offline profile. Please try again.',
                [{ text: 'OK' }]
              );
            }
          },
          style: 'destructive',
        },
      ]
    );
  };

  const renderProfileItem = ({ item }: { item: OfflineProfile }) => {
    const isExpired = Date.now() > item.expiryTimestamp;

    return (
      <TouchableOpacity
        style={[
          styles.profileCard,
          { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }
        ]}
        onPress={() => navigation.navigate('OfflineProfileDetail', { offlineId: item.offlineId })}
      >
        <View style={styles.profileHeader}>
          <View style={styles.profileInfo}>
            <Text style={[styles.profileName, { color: theme.colors.text }]}>
              {item.firstName} {item.lastName}
            </Text>
            {item.licenseNumber && (
              <Text style={[styles.licenseNumber, { color: theme.colors.textSecondary }]}>
                License: {item.licenseNumber}
              </Text>
            )}
          </View>

          {isExpired && (
            <View
              style={[
                styles.expiredBadge,
                { backgroundColor: theme.colors.error + '20' }
              ]}
            >
              <Text style={[styles.expiredText, { color: theme.colors.error }]}>
                Expired
              </Text>
            </View>
          )}
        </View>

        <View style={styles.profileFooter}>
          <Text style={[styles.syncTimestamp, { color: theme.colors.textSecondary }]}>
            Last Synced: {new Date(item.lastSyncTimestamp).toLocaleString()}
          </Text>

          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => handleDeleteProfile(item)}
          >
            <Icon name="delete-outline" size={20} color={theme.colors.error} />
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.header, { backgroundColor: theme.colors.primary }]}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Icon name="arrow-left" size={24} color={theme.colors.surface} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.colors.surface }]}>
          Offline Profiles
        </Text>
        <TouchableOpacity
          style={styles.syncButton}
          onPress={handleSync}
          disabled={isSyncing || pendingSync.length === 0}
        >
          <Icon
            name={isSyncing ? 'sync' : 'cloud-sync'}
            size={24}
            color={theme.colors.surface}
          />
        </TouchableOpacity>
      </View>

      <View style={styles.content}>
        {/* Search Bar */}
        <View style={[styles.searchContainer, { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }]}>
          <Icon name="magnify" size={20} color={theme.colors.textSecondary} style={styles.searchIcon} />
          <TextInput
            style={[styles.searchInput, { color: theme.colors.text }]}
            placeholder="Search profiles..."
            placeholderTextColor={theme.colors.textSecondary}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity
              style={styles.clearButton}
              onPress={() => setSearchQuery('')}
            >
              <Icon name="close-circle" size={16} color={theme.colors.textSecondary} />
            </TouchableOpacity>
          )}
        </View>

        {/* Sync Status */}
        <View style={styles.syncStatusContainer}>
          <View style={styles.syncInfo}>
            <Text style={[styles.syncStatusText, { color: theme.colors.text }]}>
              {lastSyncTimestamp
                ? `Last Sync: ${new Date(lastSyncTimestamp).toLocaleString()}`
                : 'Never Synced'}
            </Text>
            <Text style={[styles.pendingChangesText, { color: theme.colors.textSecondary }]}>
              {pendingSync.length > 0
                ? `${pendingSync.length} pending changes`
                : 'No pending changes'}
            </Text>
          </View>

          <TouchableOpacity
            style={[
              styles.downloadButton,
              { backgroundColor: theme.colors.primary }
            ]}
            onPress={() => dispatch(downloadOfflineProfiles())}
            disabled={isSyncing}
          >
            {isSyncing ? (
              <ActivityIndicator size="small" color={theme.colors.surface} />
            ) : (
              <>
                <Icon name="cloud-download" size={16} color={theme.colors.surface} style={styles.buttonIcon} />
                <Text style={[styles.buttonText, { color: theme.colors.surface }]}>
                  Update Profiles
                </Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Profiles List */}
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.colors.primary} />
            <Text style={[styles.loadingText, { color: theme.colors.text }]}>
              Loading profiles...
            </Text>
          </View>
        ) : (
          <FlatList
            data={filteredProfiles}
            renderItem={renderProfileItem}
            keyExtractor={(item) => item.offlineId}
            contentContainerStyle={styles.listContent}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                colors={[theme.colors.primary]}
                tintColor={theme.colors.primary}
              />
            }
            ListEmptyComponent={() => (
              <View style={styles.emptyContainer}>
                <Icon name="account-off" size={50} color={theme.colors.textSecondary} />
                <Text style={[styles.emptyText, { color: theme.colors.text }]}>
                  No offline profiles found
                </Text>
                <Text style={[styles.emptySubtext, { color: theme.colors.textSecondary }]}>
                  {searchQuery
                    ? 'Try a different search term'
                    : 'Download profiles for offline use'}
                </Text>
                {!searchQuery && (
                  <TouchableOpacity
                    style={[
                      styles.downloadEmptyButton,
                      { backgroundColor: theme.colors.primary }
                    ]}
                    onPress={() => dispatch(downloadOfflineProfiles())}
                  >
                    <Icon name="cloud-download" size={16} color={theme.colors.surface} style={styles.buttonIcon} />
                    <Text style={[styles.buttonText, { color: theme.colors.surface }]}>
                      Download Profiles
                    </Text>
                  </TouchableOpacity>
                )}
              </View>
            )}
          />
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  syncButton: {
    padding: 5,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 10,
    paddingHorizontal: 15,
    height: 50,
    marginBottom: 15,
  },
  searchIcon: {
    marginRight: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
  },
  clearButton: {
    padding: 5,
  },
  syncStatusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  syncInfo: {
    flex: 1,
  },
  syncStatusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  pendingChangesText: {
    fontSize: 12,
    marginTop: 2,
  },
  downloadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  buttonIcon: {
    marginRight: 5,
  },
  buttonText: {
    fontSize: 12,
    fontWeight: '500',
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
  listContent: {
    paddingBottom: 20,
  },
  profileCard: {
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
  },
  profileHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  licenseNumber: {
    fontSize: 12,
  },
  expiredBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    alignSelf: 'flex-start',
  },
  expiredText: {
    fontSize: 12,
    fontWeight: '500',
  },
  profileFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  syncTimestamp: {
    fontSize: 12,
  },
  deleteButton: {
    padding: 5,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 5,
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
  },
  downloadEmptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 8,
  },
});

export default OfflineProfilesScreen;