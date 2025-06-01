import * as Localization from 'expo-localization';
import { I18n } from 'i18n-js';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Import translations
import en from './translations/en';
import fr from './translations/fr';
import es from './translations/es';
import de from './translations/de';
import it from './translations/it';
import pt from './translations/pt';
import ar from './translations/ar';
import zh from './translations/zh';
import ja from './translations/ja';
import ko from './translations/ko';

// Create i18n instance
const i18n = new I18n({
  en,
  fr,
  es,
  de,
  it,
  pt,
  ar,
  zh,
  ja,
  ko,
});

// Set the locale once at the beginning of your app
const setDefaultLocale = async () => {
  try {
    // Try to get stored locale
    const storedLocale = await AsyncStorage.getItem('@user_locale');
    
    if (storedLocale) {
      i18n.locale = storedLocale;
    } else {
      // Use device locale if no stored preference
      const deviceLocale = Localization.locale.split('-')[0]; // Get language code without region
      
      // Check if we support this language
      if (Object.keys(i18n.translations).includes(deviceLocale)) {
        i18n.locale = deviceLocale;
      } else {
        // Default to English if not supported
        i18n.locale = 'en';
      }
      
      // Store the locale for next time
      await AsyncStorage.setItem('@user_locale', i18n.locale);
    }
  } catch (error) {
    // In case of error, default to English
    i18n.locale = 'en';
    console.error('Error setting locale:', error);
  }
};

// Allow fallbacks if a translation is missing
i18n.enableFallback = true;
i18n.defaultLocale = 'en';

// Function to change locale
export const changeLocale = async (locale: string) => {
  try {
    i18n.locale = locale;
    await AsyncStorage.setItem('@user_locale', locale);
  } catch (error) {
    console.error('Error changing locale:', error);
  }
};

// Get currently active locale
export const getLocale = () => i18n.locale;

// Get all available locales with their native names
export const getAvailableLocales = () => [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'fr', name: 'French', nativeName: 'Français' },
  { code: 'es', name: 'Spanish', nativeName: 'Español' },
  { code: 'de', name: 'German', nativeName: 'Deutsch' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية' },
  { code: 'zh', name: 'Chinese', nativeName: '中文' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語' },
  { code: 'ko', name: 'Korean', nativeName: '한국어' },
];

// Initialize
setDefaultLocale();

export default i18n;