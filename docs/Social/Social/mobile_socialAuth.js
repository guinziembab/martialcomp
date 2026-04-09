// src/services/socialAuth.js
/**
 * Service d'authentification sociale pour MartialComp Mobile
 * Gère la connexion via Google, Facebook et Apple
 */

import * as AuthSession from 'expo-auth-session';
import * as Google from 'expo-auth-session/providers/google';
import * as Facebook from 'expo-auth-session/providers/facebook';
import * as AppleAuthentication from 'expo-apple-authentication';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { API_BASE_URL } from '../config';

// ============================================================
// CONFIGURATION
// ============================================================

const GOOGLE_CONFIG = {
  expoClientId: process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID,
  iosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
  androidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
  webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID,
};

const FACEBOOK_CONFIG = {
  clientId: process.env.EXPO_PUBLIC_FACEBOOK_APP_ID,
};

// ============================================================
// STORAGE KEYS
// ============================================================

const STORAGE_KEYS = {
  ACCESS_TOKEN: '@martialcomp_access_token',
  REFRESH_TOKEN: '@martialcomp_refresh_token',
  USER: '@martialcomp_user',
  ACTIVE_CONTEXT: '@martialcomp_active_context',
};

// ============================================================
// SERVICE PRINCIPAL
// ============================================================

export const socialAuthService = {
  /**
   * Hook pour l'authentification Google
   * À utiliser dans un composant React:
   * 
   * const [request, response, promptAsync] = socialAuthService.useGoogleAuth();
   */
  useGoogleAuth() {
    return Google.useAuthRequest({
      ...GOOGLE_CONFIG,
      scopes: ['profile', 'email'],
    });
  },

  /**
   * Hook pour l'authentification Facebook
   */
  useFacebookAuth() {
    return Facebook.useAuthRequest({
      ...FACEBOOK_CONFIG,
      permissions: ['public_profile', 'email'],
    });
  },

  /**
   * Traite la réponse d'authentification Google
   */
  async handleGoogleResponse(response) {
    if (response?.type === 'success') {
      const { authentication } = response;
      return this.exchangeTokenWithBackend('google', authentication.accessToken);
    }
    return null;
  },

  /**
   * Traite la réponse d'authentification Facebook
   */
  async handleFacebookResponse(response) {
    if (response?.type === 'success') {
      const { authentication } = response;
      return this.exchangeTokenWithBackend('facebook', authentication.accessToken);
    }
    return null;
  },

  /**
   * Authentification Apple (iOS uniquement)
   */
  async signInWithApple() {
    if (Platform.OS !== 'ios') {
      throw new Error('Apple Sign In is only available on iOS');
    }

    try {
      // Vérifier la disponibilité
      const isAvailable = await AppleAuthentication.isAvailableAsync();
      if (!isAvailable) {
        throw new Error('Apple Sign In is not available on this device');
      }

      // Demander l'authentification
      const credential = await AppleAuthentication.signInAsync({
        requestedScopes: [
          AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
          AppleAuthentication.AppleAuthenticationScope.EMAIL,
        ],
      });

      // Échanger le token avec le backend
      return this.exchangeTokenWithBackend(
        'apple',
        credential.identityToken,
        credential.authorizationCode
      );

    } catch (error) {
      if (error.code === 'ERR_CANCELED') {
        // L'utilisateur a annulé, ne pas traiter comme une erreur
        return null;
      }
      throw error;
    }
  },

  /**
   * Échange le token social contre des tokens JWT MartialComp
   */
  async exchangeTokenWithBackend(provider, accessToken, authorizationCode = null) {
    try {
      const body = {
        provider,
        access_token: accessToken,
      };

      // Pour Apple, ajouter le code d'autorisation
      if (authorizationCode) {
        body.code = authorizationCode;
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/social/token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.error || 'Authentication failed');
      }

      // Stocker les tokens
      await this.storeTokens(data.access, data.refresh);
      
      // Stocker les infos utilisateur
      await this.storeUser(data.user);

      return {
        user: data.user,
        onboardingRequired: data.onboarding_required,
        accessToken: data.access,
        refreshToken: data.refresh,
      };

    } catch (error) {
      console.error('Social auth exchange error:', error);
      throw error;
    }
  },

  /**
   * Stocke les tokens d'authentification
   */
  async storeTokens(accessToken, refreshToken) {
    try {
      await AsyncStorage.multiSet([
        [STORAGE_KEYS.ACCESS_TOKEN, accessToken],
        [STORAGE_KEYS.REFRESH_TOKEN, refreshToken],
      ]);
    } catch (error) {
      console.error('Error storing tokens:', error);
      throw error;
    }
  },

  /**
   * Stocke les informations utilisateur
   */
  async storeUser(user) {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
    } catch (error) {
      console.error('Error storing user:', error);
      throw error;
    }
  },

  /**
   * Récupère le token d'accès stocké
   */
  async getAccessToken() {
    try {
      return await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    } catch (error) {
      console.error('Error getting access token:', error);
      return null;
    }
  },

  /**
   * Récupère le token de rafraîchissement
   */
  async getRefreshToken() {
    try {
      return await AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    } catch (error) {
      console.error('Error getting refresh token:', error);
      return null;
    }
  },

  /**
   * Récupère les informations utilisateur stockées
   */
  async getStoredUser() {
    try {
      const userJson = await AsyncStorage.getItem(STORAGE_KEYS.USER);
      return userJson ? JSON.parse(userJson) : null;
    } catch (error) {
      console.error('Error getting stored user:', error);
      return null;
    }
  },

  /**
   * Vérifie si l'utilisateur est connecté
   */
  async isAuthenticated() {
    const token = await this.getAccessToken();
    return !!token;
  },

  /**
   * Rafraîchit le token d'accès
   */
  async refreshAccessToken() {
    try {
      const refreshToken = await this.getRefreshToken();
      
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (!response.ok) {
        // Token de rafraîchissement invalide, déconnecter
        await this.signOut();
        throw new Error('Session expired');
      }

      const data = await response.json();
      
      // Stocker le nouveau token d'accès
      await AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access);
      
      // Si un nouveau refresh token est fourni, le stocker aussi
      if (data.refresh) {
        await AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh);
      }

      return data.access;

    } catch (error) {
      console.error('Error refreshing token:', error);
      throw error;
    }
  },

  /**
   * Déconnexion
   */
  async signOut() {
    try {
      // Appeler le backend pour invalider les tokens (optionnel)
      const accessToken = await this.getAccessToken();
      if (accessToken) {
        try {
          await fetch(`${API_BASE_URL}/api/auth/logout/`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${accessToken}`,
            },
          });
        } catch (e) {
          // Ignorer les erreurs de logout côté serveur
        }
      }

      // Supprimer toutes les données locales
      await AsyncStorage.multiRemove([
        STORAGE_KEYS.ACCESS_TOKEN,
        STORAGE_KEYS.REFRESH_TOKEN,
        STORAGE_KEYS.USER,
        STORAGE_KEYS.ACTIVE_CONTEXT,
      ]);

    } catch (error) {
      console.error('Error signing out:', error);
      // Même en cas d'erreur, essayer de supprimer les données locales
      try {
        await AsyncStorage.multiRemove(Object.values(STORAGE_KEYS));
      } catch (e) {}
    }
  },

  /**
   * Crée un client HTTP authentifié
   */
  async createAuthenticatedFetch() {
    const accessToken = await this.getAccessToken();
    
    return async (url, options = {}) => {
      const headers = {
        ...options.headers,
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      };

      let response = await fetch(url, { ...options, headers });

      // Si 401, essayer de rafraîchir le token
      if (response.status === 401) {
        try {
          const newToken = await this.refreshAccessToken();
          headers.Authorization = `Bearer ${newToken}`;
          response = await fetch(url, { ...options, headers });
        } catch (e) {
          // Refresh a échoué, propager l'erreur 401
        }
      }

      return response;
    };
  },
};


// ============================================================
// HOOK PERSONNALISÉ POUR L'AUTHENTIFICATION
// ============================================================

import { useState, useEffect, useCallback } from 'react';

/**
 * Hook personnalisé pour gérer l'état d'authentification
 * 
 * Usage:
 * const { 
 *   user, 
 *   isLoading, 
 *   isAuthenticated, 
 *   signInWithGoogle,
 *   signInWithFacebook,
 *   signInWithApple,
 *   signOut,
 *   error 
 * } = useAuth();
 */
export function useAuth() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Google Auth
  const [googleRequest, googleResponse, googlePromptAsync] = socialAuthService.useGoogleAuth();
  
  // Facebook Auth
  const [facebookRequest, facebookResponse, facebookPromptAsync] = socialAuthService.useFacebookAuth();

  // Charger l'utilisateur au démarrage
  useEffect(() => {
    loadUser();
  }, []);

  // Traiter la réponse Google
  useEffect(() => {
    if (googleResponse) {
      handleAuthResponse('google', googleResponse);
    }
  }, [googleResponse]);

  // Traiter la réponse Facebook
  useEffect(() => {
    if (facebookResponse) {
      handleAuthResponse('facebook', facebookResponse);
    }
  }, [facebookResponse]);

  const loadUser = async () => {
    try {
      setIsLoading(true);
      const storedUser = await socialAuthService.getStoredUser();
      const isAuth = await socialAuthService.isAuthenticated();
      
      if (isAuth && storedUser) {
        setUser(storedUser);
      }
    } catch (e) {
      console.error('Error loading user:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthResponse = async (provider, response) => {
    if (response?.type !== 'success') {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let result;
      if (provider === 'google') {
        result = await socialAuthService.handleGoogleResponse(response);
      } else if (provider === 'facebook') {
        result = await socialAuthService.handleFacebookResponse(response);
      }

      if (result) {
        setUser(result.user);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const signInWithGoogle = useCallback(async () => {
    setError(null);
    await googlePromptAsync();
  }, [googlePromptAsync]);

  const signInWithFacebook = useCallback(async () => {
    setError(null);
    await facebookPromptAsync();
  }, [facebookPromptAsync]);

  const signInWithApple = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await socialAuthService.signInWithApple();
      if (result) {
        setUser(result.user);
        return result;
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signOut = useCallback(async () => {
    setIsLoading(true);
    try {
      await socialAuthService.signOut();
      setUser(null);
    } catch (e) {
      console.error('Sign out error:', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateUser = useCallback((updatedUser) => {
    setUser(updatedUser);
    socialAuthService.storeUser(updatedUser);
  }, []);

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    signInWithGoogle,
    signInWithFacebook,
    signInWithApple,
    signOut,
    updateUser,
    error,
    // Exposer les états des providers pour l'UI
    googleReady: !!googleRequest,
    facebookReady: !!facebookRequest,
    appleAvailable: Platform.OS === 'ios',
  };
}

export default socialAuthService;
