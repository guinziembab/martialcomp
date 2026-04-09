// src/screens/auth/LoginScreen.js
/**
 * Écran de connexion MartialComp Mobile
 * Supporte Google, Facebook, Apple et connexion par email
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
  Alert,
  ActivityIndicator,
  Image,
  SafeAreaView,
  KeyboardAvoidingView,
  ScrollView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import * as AppleAuthentication from 'expo-apple-authentication';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../hooks/useAuth';
import { colors, typography, spacing } from '../../theme';

// ============================================================
// COMPOSANT PRINCIPAL
// ============================================================

export default function LoginScreen() {
  const navigation = useNavigation();
  const {
    signInWithGoogle,
    signInWithFacebook,
    signInWithApple,
    isLoading,
    error,
    googleReady,
    facebookReady,
    appleAvailable,
  } = useAuth();

  const [localLoading, setLocalLoading] = useState(false);

  // Afficher les erreurs
  useEffect(() => {
    if (error) {
      Alert.alert(
        'Erreur de connexion',
        error,
        [{ text: 'OK', onPress: () => {} }]
      );
    }
  }, [error]);

  // ============================================================
  // HANDLERS
  // ============================================================

  const handleGoogleSignIn = async () => {
    if (!googleReady) {
      Alert.alert('Erreur', 'Google Sign In n\'est pas prêt');
      return;
    }
    
    setLocalLoading(true);
    try {
      await signInWithGoogle();
    } catch (e) {
      Alert.alert('Erreur', e.message || 'Échec de la connexion Google');
    } finally {
      setLocalLoading(false);
    }
  };

  const handleFacebookSignIn = async () => {
    if (!facebookReady) {
      Alert.alert('Erreur', 'Facebook Sign In n\'est pas prêt');
      return;
    }
    
    setLocalLoading(true);
    try {
      await signInWithFacebook();
    } catch (e) {
      Alert.alert('Erreur', e.message || 'Échec de la connexion Facebook');
    } finally {
      setLocalLoading(false);
    }
  };

  const handleAppleSignIn = async () => {
    setLocalLoading(true);
    try {
      const result = await signInWithApple();
      if (result) {
        // Navigation gérée par le contexte d'authentification
      }
    } catch (e) {
      if (e.code !== 'ERR_CANCELED') {
        Alert.alert('Erreur', e.message || 'Échec de la connexion Apple');
      }
    } finally {
      setLocalLoading(false);
    }
  };

  const handleEmailSignIn = () => {
    navigation.navigate('EmailLogin');
  };

  const handleSignUp = () => {
    navigation.navigate('SignUp');
  };

  // ============================================================
  // RENDER
  // ============================================================

  const loading = isLoading || localLoading;

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.keyboardAvoid}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Logo et Titre */}
          <View style={styles.header}>
            <Image
              source={require('../../../assets/logo.png')}
              style={styles.logo}
              resizeMode="contain"
            />
            <Text style={styles.title}>MartialComp</Text>
            <Text style={styles.subtitle}>
              Gérez vos compétitions d'arts martiaux
            </Text>
          </View>

          {/* Boutons de connexion sociale */}
          <View style={styles.socialButtonsContainer}>
            {/* Google */}
            <TouchableOpacity
              style={[styles.socialButton, styles.googleButton]}
              onPress={handleGoogleSignIn}
              disabled={loading || !googleReady}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Ionicons name="logo-google" size={22} color="#fff" />
                  <Text style={styles.socialButtonText}>
                    Continuer avec Google
                  </Text>
                </>
              )}
            </TouchableOpacity>

            {/* Facebook */}
            <TouchableOpacity
              style={[styles.socialButton, styles.facebookButton]}
              onPress={handleFacebookSignIn}
              disabled={loading || !facebookReady}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Ionicons name="logo-facebook" size={22} color="#fff" />
                  <Text style={styles.socialButtonText}>
                    Continuer avec Facebook
                  </Text>
                </>
              )}
            </TouchableOpacity>

            {/* Apple - iOS only */}
            {appleAvailable && (
              <AppleAuthentication.AppleAuthenticationButton
                buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
                buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
                cornerRadius={8}
                style={styles.appleButton}
                onPress={handleAppleSignIn}
              />
            )}
          </View>

          {/* Séparateur */}
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>ou</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Connexion par email */}
          <TouchableOpacity
            style={styles.emailButton}
            onPress={handleEmailSignIn}
            disabled={loading}
          >
            <Ionicons name="mail-outline" size={22} color={colors.primary} />
            <Text style={styles.emailButtonText}>
              Connexion par email
            </Text>
          </TouchableOpacity>

          {/* Lien d'inscription */}
          <View style={styles.signUpContainer}>
            <Text style={styles.signUpText}>
              Pas encore de compte ?{' '}
            </Text>
            <TouchableOpacity onPress={handleSignUp}>
              <Text style={styles.signUpLink}>S'inscrire</Text>
            </TouchableOpacity>
          </View>

          {/* Mentions légales */}
          <Text style={styles.legalText}>
            En vous connectant, vous acceptez nos{' '}
            <Text 
              style={styles.legalLink}
              onPress={() => navigation.navigate('Terms')}
            >
              Conditions d'utilisation
            </Text>
            {' '}et notre{' '}
            <Text 
              style={styles.legalLink}
              onPress={() => navigation.navigate('Privacy')}
            >
              Politique de confidentialité
            </Text>
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* Loader global */}
      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Connexion en cours...</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

// ============================================================
// STYLES
// ============================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7FAFC',
  },
  keyboardAvoid: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 40,
    paddingBottom: 24,
    justifyContent: 'center',
  },

  // Header
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logo: {
    width: 100,
    height: 100,
    marginBottom: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#1A365D',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#718096',
    textAlign: 'center',
  },

  // Social Buttons
  socialButtonsContainer: {
    gap: 12,
    marginBottom: 24,
  },
  socialButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    gap: 12,
  },
  googleButton: {
    backgroundColor: '#DB4437',
  },
  facebookButton: {
    backgroundColor: '#4267B2',
  },
  appleButton: {
    height: 50,
    width: '100%',
  },
  socialButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },

  // Divider
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#E2E8F0',
  },
  dividerText: {
    paddingHorizontal: 16,
    color: '#718096',
    fontSize: 14,
  },

  // Email Button
  emailButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: '#1A365D',
    gap: 12,
    marginBottom: 24,
  },
  emailButtonText: {
    color: '#1A365D',
    fontSize: 16,
    fontWeight: '600',
  },

  // Sign Up
  signUpContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  signUpText: {
    color: '#718096',
    fontSize: 14,
  },
  signUpLink: {
    color: '#1A365D',
    fontSize: 14,
    fontWeight: '600',
  },

  // Legal
  legalText: {
    textAlign: 'center',
    color: '#A0AEC0',
    fontSize: 12,
    lineHeight: 18,
  },
  legalLink: {
    color: '#4A5568',
    textDecorationLine: 'underline',
  },

  // Loading Overlay
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    color: '#4A5568',
    fontSize: 16,
  },
});


// ============================================================
// VARIANTE: LoginScreen avec Animations (optionnel)
// ============================================================

/*
import Animated, { 
  FadeIn, 
  FadeInDown, 
  FadeInUp 
} from 'react-native-reanimated';

// Remplacer les View par des Animated.View avec des animations:
<Animated.View entering={FadeInDown.delay(100).duration(600)}>
  <Image source={...} />
</Animated.View>

<Animated.View entering={FadeInUp.delay(300).duration(600)}>
  <TouchableOpacity ... />
</Animated.View>
*/
