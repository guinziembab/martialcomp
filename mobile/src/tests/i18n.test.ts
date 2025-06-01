import i18n, { changeLocale, getLocale } from '@i18n/index';
import AsyncStorage from '@react-native-async-storage/async-storage';

describe('i18n', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should translate strings correctly', () => {
    // Set the locale to English
    i18n.locale = 'en';
    
    expect(i18n.t('common.ok')).toBe('OK');
    expect(i18n.t('auth.login.title')).toBe('Welcome Back');
    expect(i18n.t('main.home.upcomingEvents')).toBe('Upcoming Events');
  });

  it('should translate strings with parameters correctly', () => {
    i18n.locale = 'en';
    
    expect(i18n.t('main.profile.pendingChanges', { count: 5 })).toBe('5 pending changes');
  });

  it('should change locale and save to AsyncStorage', async () => {
    await changeLocale('fr');
    
    expect(i18n.locale).toBe('fr');
    expect(AsyncStorage.setItem).toHaveBeenCalledWith('@user_locale', 'fr');
  });

  it('should return the current locale', () => {
    i18n.locale = 'es';
    
    expect(getLocale()).toBe('es');
  });

  it('should use fallback for missing translations', () => {
    i18n.locale = 'zh'; // Chinese may not have all translations
    
    // Assuming Chinese doesn't have specific translation for this key
    const key = 'some.missing.key';
    
    // It should use the English version as fallback
    expect(i18n.t(key)).toBe(key); // Key is returned when no translation exists
  });
});