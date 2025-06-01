import React from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, SafeAreaView } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import { AuthStackParamList } from '@navigation/AuthNavigator';

type Props = NativeStackScreenProps<AuthStackParamList, 'Welcome'>;

const WelcomeScreen: React.FC<Props> = ({ navigation }) => {
  const { theme } = useTheme();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.content}>
        <View style={styles.logoContainer}>
          {/* Replace with your actual logo */}
          <View style={[styles.logoPlaceholder, { backgroundColor: theme.colors.primary }]}>
            <Text style={[styles.logoText, { color: theme.colors.surface }]}>MC</Text>
          </View>
          <Text style={[styles.appName, { color: theme.colors.text }]}>MartialComp</Text>
        </View>

        <View style={styles.messageContainer}>
          <Text style={[styles.title, { color: theme.colors.text }]}>
            Welcome to MartialComp
          </Text>
          <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
            The ultimate platform for martial arts competitions, practitioners, and organizations
          </Text>
        </View>

        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.button, styles.primaryButton, { backgroundColor: theme.colors.primary }]}
            onPress={() => navigation.navigate('Login')}
          >
            <Text style={[styles.buttonText, { color: theme.colors.surface }]}>Sign In</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[
              styles.button,
              styles.secondaryButton,
              { 
                backgroundColor: theme.colors.surface,
                borderColor: theme.colors.primary 
              }
            ]}
            onPress={() => navigation.navigate('Register')}
          >
            <Text style={[styles.buttonText, { color: theme.colors.primary }]}>Create Account</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.colors.textSecondary }]}>
            By continuing, you agree to our{' '}
            <Text style={{ color: theme.colors.primary }}>Terms of Service</Text> and{' '}
            <Text style={{ color: theme.colors.primary }}>Privacy Policy</Text>
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoPlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  appName: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  messageContainer: {
    marginBottom: 40,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  buttonContainer: {
    marginBottom: 30,
  },
  button: {
    height: 56,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 8,
  },
  primaryButton: {
    // Style defined with theme colors
  },
  secondaryButton: {
    borderWidth: 2,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    alignItems: 'center',
  },
  footerText: {
    textAlign: 'center',
    fontSize: 14,
  },
});

export default WelcomeScreen;