import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Switch,
  FlatList,
  Alert,
  Modal,
  ScrollView,
  Platform,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import { SettingsStackParamList } from '@navigation/MainNavigator';
import { AppDispatch, RootState } from '@store/index';
import { logout } from '@store/slices/authSlice';
import { setOfflineMode } from '@store/slices/offlineSlice';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import i18n, { getLocale, changeLocale, getAvailableLocales } from '@i18n/index';

type Props = NativeStackScreenProps<SettingsStackParamList, 'SettingsMain'>;

const SettingsScreen: React.FC<Props> = ({ navigation }) => {
  const { theme, themeMode, setThemeMode, toggleTheme } = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  
  const { isOfflineMode } = useSelector((state: RootState) => state.offline);
  
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [wifiOnlySync, setWifiOnlySync] = useState(true);
  const [autoSync, setAutoSync] = useState(true);
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const currentLocale = getLocale();
  const availableLocales = getAvailableLocales();

  const handleLogout = async () => {
    Alert.alert(
      i18n.t('common.logout'),
      i18n.t('profile.deleteConfirmation', { name: '' }),
      [
        {
          text: i18n.t('common.cancel'),
          style: 'cancel',
        },
        {
          text: i18n.t('common.logout'),
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

  const handleLanguageChange = async (languageCode: string) => {
    await changeLocale(languageCode);
    setShowLanguageModal(false);
    
    // Force a reload of the app to apply language changes
    Alert.alert(
      i18n.t('common.success'),
      i18n.t('settings.languageChanged', { language: availableLocales.find(l => l.code === languageCode)?.nativeName }),
      [
        {
          text: i18n.t('common.ok'),
        },
      ]
    );
  };

  const renderLanguageItem = ({ item }: { item: { code: string; name: string; nativeName: string } }) => {
    const isSelected = currentLocale === item.code;
    
    return (
      <TouchableOpacity
        style={[
          styles.languageItem,
          isSelected && { backgroundColor: theme.colors.primary + '20' }
        ]}
        onPress={() => handleLanguageChange(item.code)}
      >
        <Text style={[styles.languageName, { color: theme.colors.text }]}>
          {item.nativeName} ({item.name})
        </Text>
        
        {isSelected && (
          <Icon name="check" size={20} color={theme.colors.primary} />
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.header, { backgroundColor: theme.colors.primary }]}>
        <Text style={[styles.headerTitle, { color: theme.colors.surface }]}>
          {i18n.t('main.settings.title')}
        </Text>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Preferences Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            {i18n.t('main.settings.preferences')}
          </Text>
          
          <View style={[styles.settingsCard, { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }]}>
            <TouchableOpacity
              style={styles.settingsRow}
              onPress={toggleTheme}
            >
              <View style={styles.settingLabelContainer}>
                <Icon
                  name={themeMode === 'dark' ? 'weather-night' : 'weather-sunny'}
                  size={22}
                  color={theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {i18n.t('main.settings.darkMode')}
                </Text>
              </View>
              
              <Switch
                value={themeMode === 'dark'}
                onValueChange={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
                trackColor={{ false: '#767577', true: theme.colors.primary + '80' }}
                thumbColor={themeMode === 'dark' ? theme.colors.primary : '#f4f3f4'}
                ios_backgroundColor="#767577"
              />
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.settingsRow}
              onPress={() => setShowLanguageModal(true)}
            >
              <View style={styles.settingLabelContainer}>
                <Icon
                  name="translate"
                  size={22}
                  color={theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {i18n.t('main.settings.language')}
                </Text>
              </View>
              
              <View style={styles.valueContainer}>
                <Text style={[styles.valueText, { color: theme.colors.textSecondary }]}>
                  {availableLocales.find(l => l.code === currentLocale)?.nativeName}
                </Text>
                <Icon
                  name="chevron-right"
                  size={20}
                  color={theme.colors.textSecondary}
                  style={styles.chevronIcon}
                />
              </View>
            </TouchableOpacity>
          </View>
        </View>

        {/* Notifications Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            {i18n.t('main.settings.notifications')}
          </Text>
          
          <View style={[styles.settingsCard, { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }]}>
            <View style={styles.settingsRow}>
              <View style={styles.settingLabelContainer}>
                <Icon
                  name="bell-outline"
                  size={22}
                  color={theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {i18n.t('main.settings.enableNotifications')}
                </Text>
              </View>
              
              <Switch
                value={notificationsEnabled}
                onValueChange={setNotificationsEnabled}
                trackColor={{ false: '#767577', true: theme.colors.primary + '80' }}
                thumbColor={notificationsEnabled ? theme.colors.primary : '#f4f3f4'}
                ios_backgroundColor="#767577"
              />
            </View>
          </View>
        </View>

        {/* Data Sync Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            {i18n.t('main.settings.dataSync')}
          </Text>
          
          <View style={[styles.settingsCard, { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }]}>
            <View style={styles.settingsRow}>
              <View style={styles.settingLabelContainer}>
                <Icon
                  name="wifi"
                  size={22}
                  color={theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {i18n.t('main.settings.wifiOnly')}
                </Text>
              </View>
              
              <Switch
                value={wifiOnlySync}
                onValueChange={setWifiOnlySync}
                trackColor={{ false: '#767577', true: theme.colors.primary + '80' }}
                thumbColor={wifiOnlySync ? theme.colors.primary : '#f4f3f4'}
                ios_backgroundColor="#767577"
              />
            </View>

            <View style={styles.settingsRow}>
              <View style={styles.settingLabelContainer}>
                <Icon
                  name="sync"
                  size={22}
                  color={theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {i18n.t('main.settings.autoSync')}
                </Text>
              </View>
              
              <Switch
                value={autoSync}
                onValueChange={setAutoSync}
                trackColor={{ false: '#767577', true: theme.colors.primary + '80' }}
                thumbColor={autoSync ? theme.colors.primary : '#f4f3f4'}
                ios_backgroundColor="#767577"
              />
            </View>

            <TouchableOpacity
              style={styles.settingsRow}
              onPress={() => dispatch(setOfflineMode(!isOfflineMode))}
            >
              <View style={styles.settingLabelContainer}>
                <Icon
                  name={isOfflineMode ? 'cloud-off-outline' : 'cloud-outline'}
                  size={22}
                  color={isOfflineMode ? theme.colors.warning : theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {isOfflineMode ? i18n.t('common.offline') : i18n.t('common.online')}
                </Text>
              </View>
              
              <View style={styles.valueContainer}>
                <Text
                  style={[
                    styles.valueText,
                    {
                      color: isOfflineMode ? theme.colors.warning : theme.colors.success
                    }
                  ]}
                >
                  {isOfflineMode ? i18n.t('common.offline') : i18n.t('common.online')}
                </Text>
                <Icon
                  name="chevron-right"
                  size={20}
                  color={theme.colors.textSecondary}
                  style={styles.chevronIcon}
                />
              </View>
            </TouchableOpacity>
          </View>
        </View>

        {/* About Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            {i18n.t('main.settings.about')}
          </Text>
          
          <View style={[styles.settingsCard, { backgroundColor: theme.colors.surface, ...theme.elevation.z1 }]}>
            <View style={styles.settingsRow}>
              <View style={styles.settingLabelContainer}>
                <Icon
                  name="information-outline"
                  size={22}
                  color={theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {i18n.t('main.settings.version')}
                </Text>
              </View>
              
              <Text style={[styles.valueText, { color: theme.colors.textSecondary }]}>
                1.0.0
              </Text>
            </View>

            <TouchableOpacity style={styles.settingsRow}>
              <View style={styles.settingLabelContainer}>
                <Icon
                  name="file-document-outline"
                  size={22}
                  color={theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {i18n.t('main.settings.termsOfService')}
                </Text>
              </View>
              
              <Icon
                name="chevron-right"
                size={20}
                color={theme.colors.textSecondary}
                style={styles.chevronIcon}
              />
            </TouchableOpacity>

            <TouchableOpacity style={styles.settingsRow}>
              <View style={styles.settingLabelContainer}>
                <Icon
                  name="shield-account-outline"
                  size={22}
                  color={theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {i18n.t('main.settings.privacyPolicy')}
                </Text>
              </View>
              
              <Icon
                name="chevron-right"
                size={20}
                color={theme.colors.textSecondary}
                style={styles.chevronIcon}
              />
            </TouchableOpacity>

            <TouchableOpacity style={styles.settingsRow}>
              <View style={styles.settingLabelContainer}>
                <Icon
                  name="email-outline"
                  size={22}
                  color={theme.colors.primary}
                  style={styles.settingIcon}
                />
                <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                  {i18n.t('main.settings.contactUs')}
                </Text>
              </View>
              
              <Icon
                name="chevron-right"
                size={20}
                color={theme.colors.textSecondary}
                style={styles.chevronIcon}
              />
            </TouchableOpacity>
          </View>
        </View>

        {/* Logout Button */}
        <TouchableOpacity
          style={[
            styles.logoutButton,
            { backgroundColor: theme.colors.error }
          ]}
          onPress={handleLogout}
        >
          <Icon
            name="logout"
            size={20}
            color={theme.colors.surface}
            style={styles.logoutIcon}
          />
          <Text style={[styles.logoutText, { color: theme.colors.surface }]}>
            {i18n.t('main.settings.logout')}
          </Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Language Selection Modal */}
      <Modal
        visible={showLanguageModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowLanguageModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View
            style={[
              styles.languageModal,
              { backgroundColor: theme.colors.background, ...theme.elevation.z5 }
            ]}
          >
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.colors.text }]}>
                {i18n.t('main.settings.language')}
              </Text>
              <TouchableOpacity
                onPress={() => setShowLanguageModal(false)}
                style={styles.closeButton}
              >
                <Icon name="close" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>

            <FlatList
              data={availableLocales}
              renderItem={renderLanguageItem}
              keyExtractor={(item) => item.code}
              contentContainerStyle={styles.languageList}
            />
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingBottom: 15,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  scrollContent: {
    paddingBottom: 30,
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
  settingsCard: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E0E0E0',
  },
  settingLabelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingIcon: {
    marginRight: 12,
  },
  settingLabel: {
    fontSize: 16,
  },
  valueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  valueText: {
    fontSize: 14,
  },
  chevronIcon: {
    marginLeft: 5,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 20,
    marginTop: 30,
    paddingVertical: 12,
    borderRadius: 10,
  },
  logoutIcon: {
    marginRight: 8,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  languageModal: {
    width: '85%',
    maxHeight: '70%',
    borderRadius: 12,
    overflow: 'hidden',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 15,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E0E0E0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  closeButton: {
    padding: 5,
  },
  languageList: {
    paddingBottom: 10,
  },
  languageItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 15,
    paddingVertical: 12,
  },
  languageName: {
    fontSize: 16,
  },
});

// Add missing translation
i18n.translations.en = {
  ...i18n.translations.en,
  settings: {
    languageChanged: 'Language changed to {{language}}',
  },
};

i18n.translations.fr = {
  ...i18n.translations.fr,
  settings: {
    languageChanged: 'Langue changée en {{language}}',
  },
};

i18n.translations.es = {
  ...i18n.translations.es,
  settings: {
    languageChanged: 'Idioma cambiado a {{language}}',
  },
};

export default SettingsScreen;