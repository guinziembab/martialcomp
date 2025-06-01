import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import { AuthStackParamList } from '@navigation/AuthNavigator';
import { authService } from '@services/authService';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

type Props = NativeStackScreenProps<AuthStackParamList, 'ForgotPassword'>;

const ForgotPasswordScreen: React.FC<Props> = ({ navigation }) => {
  const { theme } = useTheme();
  
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const validateEmail = () => {
    if (!email) {
      setError('Please enter your email address');
      return false;
    }
    
    // Simple email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return false;
    }
    
    return true;
  };

  const handleResetPassword = async () => {
    if (!validateEmail()) {
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const result = await authService.forgotPassword(email);
      
      setIsSuccess(true);
      
      // Show success message
      Alert.alert(
        'Reset Email Sent',
        'Instructions to reset your password have been sent to your email address. Please check your inbox.',
        [
          {
            text: 'OK',
            onPress: () => navigation.navigate('Login'),
          },
        ]
      );
    } catch (err: any) {
      setError(err.toString());
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={[
          styles.container,
          { backgroundColor: theme.colors.background }
        ]}
      >
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Icon name="arrow-left" size={24} color={theme.colors.text} />
        </TouchableOpacity>

        <View style={styles.headerContainer}>
          <Text style={[styles.title, { color: theme.colors.text }]}>Forgot Password</Text>
          <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
            Enter your email address and we'll send you instructions to reset your password
          </Text>
        </View>

        <View style={styles.formContainer}>
          {error ? (
            <View style={[styles.errorContainer, { backgroundColor: theme.colors.error + '20' }]}>
              <Text style={[styles.errorText, { color: theme.colors.error }]}>{error}</Text>
            </View>
          ) : null}

          {isSuccess ? (
            <View style={[styles.successContainer, { backgroundColor: theme.colors.success + '20' }]}>
              <Text style={[styles.successText, { color: theme.colors.success }]}>
                Password reset instructions have been sent to your email.
              </Text>
            </View>
          ) : null}

          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, { color: theme.colors.text }]}>Email</Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: theme.colors.surface,
                  borderColor: theme.colors.border,
                  color: theme.colors.text,
                }
              ]}
              placeholder="Your email address"
              placeholderTextColor={theme.colors.textSecondary}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              editable={!isLoading && !isSuccess}
            />
          </View>

          <TouchableOpacity
            style={[
              styles.resetButton,
              { backgroundColor: theme.colors.primary },
              (isLoading || isSuccess) && { opacity: 0.7 }
            ]}
            onPress={handleResetPassword}
            disabled={isLoading || isSuccess}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color={theme.colors.surface} />
            ) : (
              <Text style={[styles.resetButtonText, { color: theme.colors.surface }]}>
                Reset Password
              </Text>
            )}
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.colors.textSecondary }]}>
            Remember your password?{' '}
          </Text>
          <TouchableOpacity
            onPress={() => navigation.navigate('Login')}
            disabled={isLoading}
          >
            <Text style={[styles.signInText, { color: theme.colors.primary }]}>
              Sign In
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.helpSection}>
          <Text style={[styles.helpTitle, { color: theme.colors.text }]}>
            Need Help?
          </Text>
          <Text style={[styles.helpText, { color: theme.colors.textSecondary }]}>
            If you don't receive an email within a few minutes, please check your spam folder or contact support.
          </Text>
          <TouchableOpacity
            style={[
              styles.contactButton,
              { 
                backgroundColor: theme.colors.surface,
                borderColor: theme.colors.primary 
              }
            ]}
          >
            <Icon name="email-outline" size={20} color={theme.colors.primary} style={styles.contactIcon} />
            <Text style={[styles.contactButtonText, { color: theme.colors.primary }]}>
              Contact Support
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 20,
    paddingTop: 60,
  },
  backButton: {
    position: 'absolute',
    top: 40,
    left: 20,
    zIndex: 10,
  },
  headerContainer: {
    marginBottom: 30,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  formContainer: {
    marginBottom: 30,
  },
  errorContainer: {
    padding: 10,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
  },
  successContainer: {
    padding: 10,
    borderRadius: 8,
    marginBottom: 16,
  },
  successText: {
    fontSize: 14,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    marginBottom: 8,
    fontSize: 16,
    fontWeight: '500',
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  resetButton: {
    height: 56,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  resetButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
  },
  footerText: {
    fontSize: 14,
  },
  signInText: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  helpSection: {
    marginTop: 20,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  helpTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  helpText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 16,
  },
  contactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
  },
  contactIcon: {
    marginRight: 8,
  },
  contactButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
});

export default ForgotPasswordScreen;