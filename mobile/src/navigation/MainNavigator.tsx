import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import HomeScreen from '@screens/main/HomeScreen';
import ProfileScreen from '@screens/main/ProfileScreen';
import QRScannerScreen from '@screens/main/QRScannerScreen';
import SettingsScreen from '@screens/main/SettingsScreen';
import ScanResultScreen from '@screens/main/ScanResultScreen';
import ProfileDetailScreen from '@screens/main/ProfileDetailScreen';
import OfflineProfilesScreen from '@screens/main/OfflineProfilesScreen';
import OfflineProfileDetailScreen from '@screens/main/OfflineProfileDetailScreen';
import ScanHistoryScreen from '@screens/main/ScanHistoryScreen';

// Define the param list for the tab navigator
export type MainTabParamList = {
  Home: undefined;
  QRScanner: undefined;
  Profile: undefined;
  Settings: undefined;
};

// Define the param list for each stack
export type HomeStackParamList = {
  HomeMain: undefined;
  ScanResult: { scanId: string };
  ProfileDetail: { profileId: string };
};

export type QRStackParamList = {
  QRScannerMain: undefined;
  ScanResult: { scanId: string };
  ScanHistory: undefined;
};

export type ProfileStackParamList = {
  ProfileMain: undefined;
  ProfileDetail: { profileId: string };
  OfflineProfiles: undefined;
  OfflineProfileDetail: { offlineId: string };
};

export type SettingsStackParamList = {
  SettingsMain: undefined;
};

// Create the stacks
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const QRStack = createNativeStackNavigator<QRStackParamList>();
const ProfileStack = createNativeStackNavigator<ProfileStackParamList>();
const SettingsStack = createNativeStackNavigator<SettingsStackParamList>();

// Home Stack Navigator
const HomeStackNavigator = () => {
  return (
    <HomeStack.Navigator screenOptions={{ headerShown: false }}>
      <HomeStack.Screen name="HomeMain" component={HomeScreen} />
      <HomeStack.Screen name="ScanResult" component={ScanResultScreen} />
      <HomeStack.Screen name="ProfileDetail" component={ProfileDetailScreen} />
    </HomeStack.Navigator>
  );
};

// QR Stack Navigator
const QRStackNavigator = () => {
  return (
    <QRStack.Navigator screenOptions={{ headerShown: false }}>
      <QRStack.Screen name="QRScannerMain" component={QRScannerScreen} />
      <QRStack.Screen name="ScanResult" component={ScanResultScreen} />
      <QRStack.Screen name="ScanHistory" component={ScanHistoryScreen} />
    </QRStack.Navigator>
  );
};

// Profile Stack Navigator
const ProfileStackNavigator = () => {
  return (
    <ProfileStack.Navigator screenOptions={{ headerShown: false }}>
      <ProfileStack.Screen name="ProfileMain" component={ProfileScreen} />
      <ProfileStack.Screen name="ProfileDetail" component={ProfileDetailScreen} />
      <ProfileStack.Screen name="OfflineProfiles" component={OfflineProfilesScreen} />
      <ProfileStack.Screen name="OfflineProfileDetail" component={OfflineProfileDetailScreen} />
    </ProfileStack.Navigator>
  );
};

// Settings Stack Navigator
const SettingsStackNavigator = () => {
  return (
    <SettingsStack.Navigator screenOptions={{ headerShown: false }}>
      <SettingsStack.Screen name="SettingsMain" component={SettingsScreen} />
    </SettingsStack.Navigator>
  );
};

// Create the tab navigator
const Tab = createBottomTabNavigator<MainTabParamList>();

const MainNavigator: React.FC = () => {
  const { theme } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textSecondary,
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
          ...theme.elevation.z2,
        },
        tabBarIcon: ({ color, size }) => {
          let iconName = '';

          if (route.name === 'Home') {
            iconName = 'home';
          } else if (route.name === 'QRScanner') {
            iconName = 'qrcode-scan';
          } else if (route.name === 'Profile') {
            iconName = 'account';
          } else if (route.name === 'Settings') {
            iconName = 'cog';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeStackNavigator} />
      <Tab.Screen name="QRScanner" component={QRStackNavigator} />
      <Tab.Screen name="Profile" component={ProfileStackNavigator} />
      <Tab.Screen name="Settings" component={SettingsStackNavigator} />
    </Tab.Navigator>
  );
};

export default MainNavigator;