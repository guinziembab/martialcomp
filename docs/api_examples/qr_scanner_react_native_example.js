// Exemple d'application React Native pour le scan de QR codes avec support hors-ligne
// MartialComp Mobile QR Scanner

import React, { useState, useEffect, useCallback } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TouchableOpacity, 
  Image, 
  Modal, 
  SafeAreaView, 
  ScrollView, 
  Alert,
  ActivityIndicator,
  NetInfo,
  AsyncStorage
} from 'react-native';
import { Camera } from 'expo-camera';
import { BarCodeScanner } from 'expo-barcode-scanner';
import * as FileSystem from 'expo-file-system';
import * as LocalAuthentication from 'expo-local-authentication';
import * as Network from 'expo-network';
import * as SecureStore from 'expo-secure-store';
import { useFocusEffect } from '@react-navigation/native';

// Configuration de l'API
const API_BASE_URL = 'https://api.martialcomp.com/api/v1';
const AUTH_TOKEN_KEY = 'martialcomp_auth_token';
const OFFLINE_SCANS_KEY = 'martialcomp_offline_scans';
const OFFLINE_CACHE_DIR = FileSystem.documentDirectory + 'qr_codes/';

// Composant principal du scanner QR
export default function QRScanner({ route, navigation }) {
  const [hasPermission, setHasPermission] = useState(null);
  const [scanned, setScanned] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [flashMode, setFlashMode] = useState(Camera.Constants.FlashMode.off);
  const [scanResult, setScanResult] = useState(null);
  const [offlineMode, setOfflineMode] = useState(false);
  const [scanType, setScanType] = useState('check_in');
  const [showModal, setShowModal] = useState(false);
  const [offlineScans, setOfflineScans] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [syncNeeded, setSyncNeeded] = useState(false);
  
  // Paramètres pour l'événement actuel
  const eventId = route.params?.eventId;
  const eventType = route.params?.eventType || 'event';
  
  // Vérifier les permissions de caméra
  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestPermissionsAsync();
      setHasPermission(status === 'granted');
      
      // Vérifier la connexion réseau
      checkNetworkStatus();
      
      // Charger les scans hors-ligne
      loadOfflineScans();
    })();
  }, []);
  
  // Vérifier la connexion réseau à chaque fois que l'écran obtient le focus
  useFocusEffect(
    useCallback(() => {
      checkNetworkStatus();
      loadOfflineScans();
      return () => {};
    }, [])
  );
  
  // Vérifier l'état de la connexion réseau
  const checkNetworkStatus = async () => {
    try {
      const networkState = await Network.getNetworkStateAsync();
      const isConnected = networkState.isConnected && networkState.isInternetReachable;
      setOfflineMode(!isConnected);
      
      // Si nous sommes de retour en ligne mais avons des scans hors-ligne, suggérer une synchronisation
      if (isConnected && offlineScans.length > 0) {
        setSyncNeeded(true);
      }
    } catch (error) {
      console.log('Erreur lors de la vérification du réseau:', error);
      setOfflineMode(true);
    }
  };
  
  // Charger les scans hors-ligne depuis le stockage local
  const loadOfflineScans = async () => {
    try {
      const storedScans = await AsyncStorage.getItem(OFFLINE_SCANS_KEY);
      if (storedScans) {
        const parsedScans = JSON.parse(storedScans);
        setOfflineScans(parsedScans);
        
        // Vérifier s'il faut synchroniser
        const networkState = await Network.getNetworkStateAsync();
        if (networkState.isConnected && parsedScans.length > 0) {
          setSyncNeeded(true);
        }
      }
    } catch (error) {
      console.log('Erreur lors du chargement des scans hors-ligne:', error);
    }
  };
  
  // Sauvegarder un nouveau scan hors-ligne
  const saveOfflineScan = async (scanData) => {
    try {
      const updatedScans = [...offlineScans, scanData];
      await AsyncStorage.setItem(OFFLINE_SCANS_KEY, JSON.stringify(updatedScans));
      setOfflineScans(updatedScans);
    } catch (error) {
      console.log('Erreur lors de la sauvegarde du scan hors-ligne:', error);
      Alert.alert('Erreur', 'Impossible de sauvegarder le scan hors-ligne');
    }
  };
  
  // Synchroniser les scans hors-ligne avec le serveur
  const syncOfflineScans = async () => {
    if (offlineScans.length === 0) return;
    
    setIsLoading(true);
    
    try {
      // Récupérer le token d'authentification
      const authToken = await SecureStore.getItemAsync(AUTH_TOKEN_KEY);
      if (!authToken) {
        Alert.alert('Erreur', "Vous devez être connecté pour synchroniser les données");
        setIsLoading(false);
        return;
      }
      
      // Envoyer les scans au serveur
      const response = await fetch(`${API_BASE_URL}/scan/sync-offline/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ scans: offlineScans })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        // Afficher un message de confirmation
        Alert.alert(
          'Synchronisation terminée',
          `${result.synced} scans synchronisés, ${result.ignored} ignorés.`
        );
        
        // Effacer les scans hors-ligne
        await AsyncStorage.setItem(OFFLINE_SCANS_KEY, JSON.stringify([]));
        setOfflineScans([]);
        setSyncNeeded(false);
      } else {
        Alert.alert('Erreur', 'La synchronisation a échoué');
      }
    } catch (error) {
      console.log('Erreur lors de la synchronisation:', error);
      Alert.alert('Erreur', "Impossible de synchroniser les données");
    } finally {
      setIsLoading(false);
    }
  };
  
  // Scanner un QR code 
  const handleBarCodeScanned = async ({ type, data }) => {
    if (scanned || scanning) return;
    
    setScanned(true);
    setScanning(true);
    setIsLoading(true);
    
    try {
      // En mode hors-ligne, vérifier si c'est un token hors-ligne
      if (offlineMode) {
        await processOfflineScan(data);
      } else {
        // En mode connecté, envoyer au serveur
        await processOnlineScan(data);
      }
    } catch (error) {
      console.log('Erreur lors du scan:', error);
      
      // En cas d'erreur de connexion, basculer en mode hors-ligne et réessayer
      if (error.message.includes('network') || error.message.includes('connection')) {
        setOfflineMode(true);
        
        // Vérifier si les données sont au format de token hors-ligne
        try {
          await processOfflineScan(data);
        } catch (offlineError) {
          setScanResult({
            success: false,
            message: "Impossible de scanner le QR code en mode hors-ligne"
          });
        }
      } else {
        setScanResult({
          success: false,
          message: "Erreur lors du scan: " + error.message
        });
      }
    } finally {
      setScanning(false);
      setIsLoading(false);
      setShowModal(true);
    }
  };
  
  // Traiter un scan en mode connecté
  const processOnlineScan = async (qrCodeData) => {
    // Récupérer le token d'authentification
    const authToken = await SecureStore.getItemAsync(AUTH_TOKEN_KEY);
    if (!authToken) {
      throw new Error("Vous devez être connecté pour scanner les QR codes");
    }
    
    // Préparer les données pour le scan
    const scanData = {
      qr_code: qrCodeData,
      scan_type: scanType,
      location: await getCurrentLocation()
    };
    
    // Ajouter l'ID de l'événement si disponible
    if (eventId) {
      if (eventType === 'competition') {
        scanData.competition_id = eventId;
      } else if (eventType === 'training') {
        scanData.training_session_id = eventId;
      } else if (eventType === 'event') {
        scanData.event_id = eventId;
      }
    }
    
    // Envoyer le scan au serveur
    const response = await fetch(`${API_BASE_URL}/scan/process/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(scanData)
    });
    
    if (response.ok) {
      const result = await response.json();
      setScanResult(result);
    } else {
      const errorData = await response.json();
      throw new Error(errorData.message || "Erreur lors du scan");
    }
  };
  
  // Traiter un scan en mode hors-ligne
  const processOfflineScan = async (offlineToken) => {
    // Préparer les données pour le scan
    const scanData = {
      token: offlineToken,
      scan_type: scanType,
      location: await getCurrentLocation()
    };
    
    // Ajouter l'ID de l'événement si disponible
    if (eventId) {
      scanData.event_id = eventId;
    }
    
    try {
      // Valider localement le token hors-ligne
      let validationResult;
      
      // Si nous avons une connexion, envoyons au serveur pour validation 
      if (!offlineMode) {
        const authToken = await SecureStore.getItemAsync(AUTH_TOKEN_KEY);
        
        const response = await fetch(`${API_BASE_URL}/scan/process-offline/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify(scanData)
        });
        
        if (response.ok) {
          validationResult = await response.json();
        } else {
          throw new Error("Impossible de valider le token");
        }
      } else {
        // Validation locale (simulée ici)
        validationResult = validateOfflineToken(offlineToken, scanType, eventId);
      }
      
      if (validationResult.valid || validationResult.success) {
        // En mode hors-ligne, sauvegarder le scan pour synchronisation ultérieure
        if (offlineMode) {
          // Ajouter un ID unique et un timestamp
          const offlineScanData = {
            ...validationResult.scan_data,
            timestamp: Date.now() / 1000, // En secondes pour être compatible avec le serveur
            id: generateUUID(),
            synced: false
          };
          
          await saveOfflineScan(offlineScanData);
        }
        
        setScanResult(validationResult);
      } else {
        setScanResult({
          success: false,
          message: validationResult.message || "Token hors-ligne invalide"
        });
      }
    } catch (error) {
      console.log('Erreur lors du traitement du scan hors-ligne:', error);
      throw error;
    }
  };
  
  // Simulation de validation locale d'un token hors-ligne
  // Dans une implémentation réelle, cette logique serait plus complexe et sécurisée
  const validateOfflineToken = (token, scanType, eventId) => {
    try {
      // Décodage du token (basé sur Base64 URL-safe)
      let tokenData;
      try {
        // Simuler le décodage et la vérification du token
        // Dans une véritable application, cela devrait vérifier la signature et décoder correctement le token
        const decoded = atob(token.replace(/-/g, '+').replace(/_/g, '/'));
        tokenData = JSON.parse(decoded);
      } catch (e) {
        return { valid: false, message: "Format de token invalide" };
      }
      
      // Vérifier l'expiration
      const now = Date.now() / 1000;
      if (tokenData.exp < now) {
        return { valid: false, message: "Token expiré" };
      }
      
      // Vérifier la validation fédération pour certains types de scan
      if ((scanType === 'competition' || scanType === 'event') && !tokenData.fed_val) {
        return { 
          valid: false, 
          message: "Validation fédération requise pour ce type d'événement" 
        };
      }
      
      // Token valide, générer les données de scan
      const practitionerId = tokenData.prac_id;
      const qrUuid = tokenData.qr_uuid;
      
      return {
        valid: true,
        success: true,
        message: "Scan validé (mode hors-ligne)",
        offline: true,
        scan_data: {
          practitioner_id: practitionerId,
          qr_uuid: qrUuid,
          scan_type: scanType,
          event_id: eventId,
          location: "",
        },
        practitioner: {
          id: practitionerId,
          name: `Pratiquant #${practitionerId}`,
          license_number: "Vérifié hors-ligne",
          is_federation_validated: tokenData.fed_val
        }
      };
    } catch (error) {
      console.log('Erreur lors de la validation hors-ligne:', error);
      return { valid: false, message: "Erreur lors de la validation du token" };
    }
  };
  
  // Générer un UUID v4 pour les IDs des scans hors-ligne
  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };
  
  // Obtenir la position actuelle
  const getCurrentLocation = async () => {
    try {
      const { status } = await Location.requestPermissionsAsync();
      if (status !== 'granted') {
        return "";
      }
      
      const location = await Location.getCurrentPositionAsync({});
      return `${location.coords.latitude},${location.coords.longitude}`;
    } catch (error) {
      console.log('Erreur lors de la récupération de la position:', error);
      return "";
    }
  };

  // Si pas de permission pour la caméra
  if (hasPermission === null) {
    return <View style={styles.container}><Text>Demande de permission de caméra...</Text></View>;
  }
  if (hasPermission === false) {
    return <View style={styles.container}><Text>Pas d'accès à la caméra</Text></View>;
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.statusBar}>
        <Text style={[styles.statusText, offlineMode ? styles.offlineText : styles.onlineText]}>
          {offlineMode ? "Mode hors-ligne" : "Connecté"}
        </Text>
        
        {syncNeeded && (
          <TouchableOpacity 
            style={styles.syncButton} 
            onPress={syncOfflineScans}
            disabled={isLoading}>
            <Text style={styles.syncText}>
              {isLoading ? "Synchronisation..." : `Synchroniser (${offlineScans.length})`}
            </Text>
          </TouchableOpacity>
        )}
      </View>
      
      <View style={styles.scanTypeContainer}>
        <Text style={styles.label}>Type de scan:</Text>
        <View style={styles.scanTypeButtons}>
          {QR_SCAN_TYPES.map(type => (
            <TouchableOpacity 
              key={type.value}
              style={[styles.scanTypeButton, scanType === type.value && styles.activeScanType]}
              onPress={() => setScanType(type.value)}>
              <Text style={[styles.scanTypeText, scanType === type.value && styles.activeScanTypeText]}>
                {type.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
      
      <View style={styles.cameraContainer}>
        <Camera
          style={styles.camera}
          type={Camera.Constants.Type.back}
          flashMode={flashMode}
          onBarCodeScanned={scanned ? undefined : handleBarCodeScanned}
          barCodeScannerSettings={{
            barCodeTypes: [BarCodeScanner.Constants.BarCodeType.qr],
          }}>
          <View style={styles.cameraOverlay}>
            <View style={styles.scanFrame} />
            
            <View style={styles.cameraControls}>
              <TouchableOpacity 
                style={styles.flashButton}
                onPress={() => setFlashMode(
                  flashMode === Camera.Constants.FlashMode.off
                    ? Camera.Constants.FlashMode.torch
                    : Camera.Constants.FlashMode.off
                )}>
                <Text style={styles.flashText}>
                  {flashMode === Camera.Constants.FlashMode.off ? "Flash: OFF" : "Flash: ON"}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </Camera>
      </View>
      
      {scanned && (
        <TouchableOpacity style={styles.scanAgainButton} onPress={() => setScanned(false)}>
          <Text style={styles.scanAgainText}>Scanner à nouveau</Text>
        </TouchableOpacity>
      )}
      
      {/* Modal pour afficher le résultat du scan */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={showModal}
        onRequestClose={() => setShowModal(false)}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>
              {scanResult?.success ? "Scan réussi" : "Échec du scan"}
            </Text>
            
            {scanResult?.offline && (
              <View style={styles.offlineBadge}>
                <Text style={styles.offlineBadgeText}>Mode hors-ligne</Text>
              </View>
            )}
            
            <Text style={styles.modalMessage}>{scanResult?.message}</Text>
            
            {scanResult?.practitioner && (
              <View style={styles.practitionerContainer}>
                {scanResult.practitioner.photo && (
                  <Image 
                    source={{ uri: scanResult.practitioner.photo }} 
                    style={styles.practitionerPhoto} 
                  />
                )}
                <Text style={styles.practitionerName}>{scanResult.practitioner.name}</Text>
                <Text style={styles.practitionerDetails}>
                  Licence: {scanResult.practitioner.license_number}
                </Text>
                {scanResult.practitioner.club && (
                  <Text style={styles.practitionerDetails}>
                    Club: {scanResult.practitioner.club}
                  </Text>
                )}
                <Text style={[
                  styles.federationStatus,
                  scanResult.practitioner.is_federation_validated 
                    ? styles.validatedStatus 
                    : styles.notValidatedStatus
                ]}>
                  {scanResult.practitioner.is_federation_validated 
                    ? "Validé par la fédération" 
                    : "Non validé par la fédération"}
                </Text>
              </View>
            )}
            
            <TouchableOpacity 
              style={styles.closeButton} 
              onPress={() => {
                setShowModal(false);
                setScanned(false);
              }}>
              <Text style={styles.closeButtonText}>Fermer</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      
      {isLoading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#3498db" />
          <Text style={styles.loadingText}>Traitement en cours...</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

// Types de scan disponibles
const QR_SCAN_TYPES = [
  { value: 'check_in', label: 'Check-in' },
  { value: 'attendance', label: 'Présence' },
  { value: 'competition', label: 'Compétition' },
  { value: 'event', label: 'Événement' },
  { value: 'training', label: 'Entraînement' },
];

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 10,
    backgroundColor: '#2c3e50',
  },
  statusText: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  onlineText: {
    color: '#2ecc71',
  },
  offlineText: {
    color: '#e74c3c',
  },
  syncButton: {
    backgroundColor: '#3498db',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 5,
  },
  syncText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  scanTypeContainer: {
    padding: 10,
    backgroundColor: 'white',
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  scanTypeButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  scanTypeButton: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    marginRight: 8,
    marginBottom: 8,
    borderRadius: 20,
    backgroundColor: '#f1f2f6',
  },
  activeScanType: {
    backgroundColor: '#3498db',
  },
  scanTypeText: {
    color: '#34495e',
    fontSize: 14,
  },
  activeScanTypeText: {
    color: 'white',
    fontWeight: 'bold',
  },
  cameraContainer: {
    flex: 1,
    overflow: 'hidden',
  },
  camera: {
    flex: 1,
  },
  cameraOverlay: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanFrame: {
    width: 250,
    height: 250,
    borderWidth: 2,
    borderColor: '#3498db',
    backgroundColor: 'transparent',
  },
  cameraControls: {
    position: 'absolute',
    bottom: 30,
    width: '100%',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  flashButton: {
    backgroundColor: 'rgba(52, 152, 219, 0.7)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 5,
  },
  flashText: {
    color: 'white',
    fontWeight: 'bold',
  },
  scanAgainButton: {
    backgroundColor: '#3498db',
    padding: 15,
    margin: 20,
    borderRadius: 5,
    alignItems: 'center',
  },
  scanAgainText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContent: {
    width: '80%',
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    alignItems: 'center',
    elevation: 5,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#2c3e50',
  },
  offlineBadge: {
    backgroundColor: '#e67e22',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 15,
    marginBottom: 10,
  },
  offlineBadgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  modalMessage: {
    fontSize: 16,
    marginBottom: 15,
    textAlign: 'center',
    color: '#34495e',
  },
  practitionerContainer: {
    width: '100%',
    alignItems: 'center',
    padding: 10,
    backgroundColor: '#f1f2f6',
    borderRadius: 5,
    marginBottom: 15,
  },
  practitionerPhoto: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 10,
  },
  practitionerName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
    color: '#2c3e50',
  },
  practitionerDetails: {
    fontSize: 14,
    marginBottom: 3,
    color: '#7f8c8d',
  },
  federationStatus: {
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 5,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 15,
  },
  validatedStatus: {
    backgroundColor: '#2ecc71',
    color: 'white',
  },
  notValidatedStatus: {
    backgroundColor: '#e74c3c',
    color: 'white',
  },
  closeButton: {
    backgroundColor: '#3498db',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 5,
  },
  closeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: 'white',
    marginTop: 10,
    fontSize: 16,
  },
});