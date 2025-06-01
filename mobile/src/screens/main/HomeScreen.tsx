import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  Image,
  ActivityIndicator,
  Platform,
  FlatList,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import { HomeStackParamList } from '@navigation/MainNavigator';
import { AppDispatch, RootState } from '@store/index';
import { fetchProfile } from '@store/slices/profileSlice';
import { setOfflineMode } from '@store/slices/offlineSlice';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

type Props = NativeStackScreenProps<HomeStackParamList, 'HomeMain'>;

interface EventCard {
  id: string;
  title: string;
  date: string;
  location: string;
  type: 'competition' | 'training' | 'grading' | 'meeting';
  status: 'upcoming' | 'ongoing' | 'completed';
  imageUrl?: string;
}

interface AnnouncementCard {
  id: string;
  title: string;
  content: string;
  date: string;
  priority: 'high' | 'medium' | 'low';
}

const mockEvents: EventCard[] = [
  {
    id: '1',
    title: 'National Martial Arts Championship',
    date: '2025-06-15',
    location: 'Sports Arena, Paris',
    type: 'competition',
    status: 'upcoming',
    imageUrl: 'https://example.com/competition1.jpg',
  },
  {
    id: '2',
    title: 'Advanced Techniques Workshop',
    date: '2025-05-28',
    location: 'Central Dojo, Lyon',
    type: 'training',
    status: 'upcoming',
  },
  {
    id: '3',
    title: 'Summer Grading Session',
    date: '2025-07-10',
    location: 'Federation HQ, Marseille',
    type: 'grading',
    status: 'upcoming',
  },
];

const mockAnnouncements: AnnouncementCard[] = [
  {
    id: '1',
    title: 'Important COVID-19 Safety Measures',
    content: 'Please be advised that all participants must follow the updated safety guidelines...',
    date: '2025-05-15',
    priority: 'high',
  },
  {
    id: '2',
    title: 'Referee Training Program',
    content: 'The federation is launching a new referee training program for qualified individuals...',
    date: '2025-05-10',
    priority: 'medium',
  },
];

const HomeScreen: React.FC<Props> = ({ navigation }) => {
  const { theme } = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  
  const { user } = useSelector((state: RootState) => state.auth);
  const { profile, isLoading: profileLoading } = useSelector((state: RootState) => state.profile);
  const { isOfflineMode } = useSelector((state: RootState) => state.offline);
  
  const [refreshing, setRefreshing] = useState(false);
  const [events, setEvents] = useState<EventCard[]>(mockEvents);
  const [announcements, setAnnouncements] = useState<AnnouncementCard[]>(mockAnnouncements);
  const [isEventsLoading, setIsEventsLoading] = useState(false);

  useEffect(() => {
    loadProfileData();
  }, [dispatch]);

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
      await Promise.all([
        dispatch(fetchProfile()).unwrap(),
        loadEvents(),
      ]);
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const loadEvents = async () => {
    setIsEventsLoading(true);
    try {
      // In a real app, this would be an API call
      // Simulating API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      // For now, just use mock data
      setEvents(mockEvents);
    } catch (error) {
      console.error('Failed to load events:', error);
    } finally {
      setIsEventsLoading(false);
    }
  };

  const toggleOfflineMode = () => {
    dispatch(setOfflineMode(!isOfflineMode));
  };

  const renderEventCard = ({ item }: { item: EventCard }) => {
    const typeIcons = {
      competition: 'trophy',
      training: 'dumbbell',
      grading: 'certificate',
      meeting: 'account-group',
    };

    const statusColors = {
      upcoming: theme.colors.primary,
      ongoing: theme.colors.success,
      completed: theme.colors.textSecondary,
    };

    return (
      <TouchableOpacity
        style={[
          styles.eventCard,
          { backgroundColor: theme.colors.surface, ...theme.elevation.z2 }
        ]}
        onPress={() => {
          // Navigate to event details
        }}
      >
        <View style={styles.eventHeader}>
          <View style={styles.eventTypeContainer}>
            <Icon
              name={typeIcons[item.type]}
              size={16}
              color={theme.colors.surface}
              style={[
                styles.eventTypeIcon,
                { backgroundColor: statusColors[item.status] }
              ]}
            />
            <Text
              style={[
                styles.eventTypeText,
                { color: statusColors[item.status] }
              ]}
            >
              {item.type.charAt(0).toUpperCase() + item.type.slice(1)}
            </Text>
          </View>
          <Text style={[styles.eventDate, { color: theme.colors.textSecondary }]}>
            {new Date(item.date).toLocaleDateString()}
          </Text>
        </View>

        <Text style={[styles.eventTitle, { color: theme.colors.text }]}>
          {item.title}
        </Text>

        <View style={styles.eventLocation}>
          <Icon name="map-marker" size={16} color={theme.colors.textSecondary} />
          <Text style={[styles.eventLocationText, { color: theme.colors.textSecondary }]}>
            {item.location}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  const renderAnnouncementCard = ({ item }: { item: AnnouncementCard }) => {
    const priorityColors = {
      high: theme.colors.error,
      medium: theme.colors.primary,
      low: theme.colors.textSecondary,
    };

    return (
      <View
        style={[
          styles.announcementCard,
          { backgroundColor: theme.colors.surface, ...theme.elevation.z2 }
        ]}
      >
        <View style={styles.announcementHeader}>
          <View
            style={[
              styles.priorityIndicator,
              { backgroundColor: priorityColors[item.priority] }
            ]}
          />
          <Text style={[styles.announcementTitle, { color: theme.colors.text }]}>
            {item.title}
          </Text>
        </View>

        <Text style={[styles.announcementContent, { color: theme.colors.textSecondary }]}>
          {item.content}
        </Text>

        <Text style={[styles.announcementDate, { color: theme.colors.textSecondary }]}>
          {new Date(item.date).toLocaleDateString()}
        </Text>
      </View>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.header, { backgroundColor: theme.colors.primary }]}>
        <View style={styles.headerContent}>
          <View>
            <Text style={[styles.welcomeText, { color: theme.colors.surface }]}>
              Welcome back,
            </Text>
            <Text style={[styles.nameText, { color: theme.colors.surface }]}>
              {profileLoading ? 'Loading...' : profile?.firstName || user?.firstName || 'User'}
            </Text>
          </View>

          <TouchableOpacity
            style={[
              styles.profileButton,
              { backgroundColor: theme.colors.surface + '20' }
            ]}
            onPress={() => navigation.navigate('ProfileDetail', { profileId: profile?.id || '' })}
          >
            {profile?.avatarUrl ? (
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
                  {profile?.firstName?.charAt(0) || user?.firstName?.charAt(0) || 'U'}
                </Text>
              </View>
            )}
          </TouchableOpacity>
        </View>
      </View>

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
        {/* Offline Mode Indicator */}
        {isOfflineMode && (
          <TouchableOpacity
            style={[
              styles.offlineBanner,
              { backgroundColor: theme.colors.warning + '30' }
            ]}
            onPress={toggleOfflineMode}
          >
            <Icon name="cloud-off-outline" size={20} color={theme.colors.warning} />
            <Text style={[styles.offlineText, { color: theme.colors.warning }]}>
              Offline Mode Active - Tap to go online
            </Text>
          </TouchableOpacity>
        )}

        {/* Quick Actions */}
        <View style={styles.quickActionsContainer}>
          <TouchableOpacity
            style={[
              styles.quickActionButton,
              { backgroundColor: theme.colors.surface, ...theme.elevation.z2 }
            ]}
            onPress={() => navigation.navigate('QRScanner')}
          >
            <View
              style={[
                styles.quickActionIconContainer,
                { backgroundColor: theme.colors.primary + '20' }
              ]}
            >
              <Icon name="qrcode-scan" size={24} color={theme.colors.primary} />
            </View>
            <Text style={[styles.quickActionText, { color: theme.colors.text }]}>
              Scan QR
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.quickActionButton,
              { backgroundColor: theme.colors.surface, ...theme.elevation.z2 }
            ]}
          >
            <View
              style={[
                styles.quickActionIconContainer,
                { backgroundColor: theme.colors.secondary + '20' }
              ]}
            >
              <Icon name="calendar-check" size={24} color={theme.colors.secondary} />
            </View>
            <Text style={[styles.quickActionText, { color: theme.colors.text }]}>
              Events
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.quickActionButton,
              { backgroundColor: theme.colors.surface, ...theme.elevation.z2 }
            ]}
          >
            <View
              style={[
                styles.quickActionIconContainer,
                { backgroundColor: theme.colors.accent + '20' }
              ]}
            >
              <Icon name="certificate" size={24} color={theme.colors.accent} />
            </View>
            <Text style={[styles.quickActionText, { color: theme.colors.text }]}>
              Grades
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.quickActionButton,
              { backgroundColor: theme.colors.surface, ...theme.elevation.z2 }
            ]}
            onPress={toggleOfflineMode}
          >
            <View
              style={[
                styles.quickActionIconContainer,
                { backgroundColor: isOfflineMode ? theme.colors.warning + '20' : theme.colors.martial.blue + '20' }
              ]}
            >
              <Icon
                name={isOfflineMode ? 'cloud-off-outline' : 'cloud-outline'}
                size={24}
                color={isOfflineMode ? theme.colors.warning : theme.colors.martial.blue}
              />
            </View>
            <Text style={[styles.quickActionText, { color: theme.colors.text }]}>
              {isOfflineMode ? 'Online' : 'Offline'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Upcoming Events Section */}
        <View style={styles.sectionContainer}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
              Upcoming Events
            </Text>
            <TouchableOpacity>
              <Text style={[styles.seeAllText, { color: theme.colors.primary }]}>
                See All
              </Text>
            </TouchableOpacity>
          </View>

          {isEventsLoading ? (
            <ActivityIndicator
              size="large"
              color={theme.colors.primary}
              style={styles.loadingIndicator}
            />
          ) : (
            <FlatList
              data={events}
              renderItem={renderEventCard}
              keyExtractor={item => item.id}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.eventsList}
              style={styles.eventsListContainer}
            />
          )}
        </View>

        {/* Announcements Section */}
        <View style={styles.sectionContainer}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
              Announcements
            </Text>
          </View>

          {announcements.map(announcement => (
            <View key={announcement.id}>
              {renderAnnouncementCard({ item: announcement })}
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingBottom: 20,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  welcomeText: {
    fontSize: 16,
    opacity: 0.9,
  },
  nameText: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  profileButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  profileImage: {
    width: 36,
    height: 36,
    borderRadius: 18,
  },
  profileImagePlaceholder: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileInitials: {
    fontSize: 16,
    fontWeight: 'bold',
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
    marginVertical: 10,
    borderRadius: 8,
  },
  offlineText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '500',
  },
  quickActionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    marginBottom: 20,
    marginTop: 10,
  },
  quickActionButton: {
    width: '22%',
    aspectRatio: 0.9,
    borderRadius: 12,
    padding: 10,
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  quickActionIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 5,
  },
  quickActionText: {
    fontSize: 12,
    fontWeight: '500',
    textAlign: 'center',
  },
  sectionContainer: {
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  seeAllText: {
    fontSize: 14,
  },
  loadingIndicator: {
    marginVertical: 20,
  },
  eventsListContainer: {
    marginBottom: 10,
  },
  eventsList: {
    paddingHorizontal: 15,
  },
  eventCard: {
    width: 250,
    borderRadius: 12,
    padding: 15,
    marginHorizontal: 5,
  },
  eventHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  eventTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  eventTypeIcon: {
    padding: 4,
    borderRadius: 4,
    marginRight: 5,
  },
  eventTypeText: {
    fontSize: 12,
    fontWeight: '500',
  },
  eventDate: {
    fontSize: 12,
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  eventLocation: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  eventLocationText: {
    fontSize: 12,
    marginLeft: 4,
  },
  announcementCard: {
    borderRadius: 12,
    padding: 15,
    marginHorizontal: 20,
    marginBottom: 10,
  },
  announcementHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  priorityIndicator: {
    width: 4,
    height: 16,
    borderRadius: 2,
    marginRight: 8,
  },
  announcementTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    flex: 1,
  },
  announcementContent: {
    fontSize: 14,
    marginBottom: 8,
  },
  announcementDate: {
    fontSize: 12,
    alignSelf: 'flex-end',
  },
});

export default HomeScreen;