import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Platform,
  ScrollView,
} from 'react-native';
import { BarCodeScanner } from 'expo-barcode-scanner';
import { Camera } from 'expo-camera';
import { useDispatch, useSelector } from 'react-redux';
import { Picker } from '@react-native-picker/picker';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useTheme } from '@theme/ThemeProvider';
import { QRStackParamList } from '@navigation/MainNavigator';
import { AppDispatch, RootState } from '@store/index';
import {
  processQRCode,
  verifyOfflineQRCode,
  setScanning,
  setScannedData,
  setScanType,
  setEventId,
} from '@store/slices/qrScannerSlice';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

type Props = NativeStackScreenProps<QRStackParamList, 'QRScannerMain'>;

const QRScannerScreen: React.FC<Props> = ({ navigation }) => {
  const { theme } = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  
  const { isScanning, scannedData, isProcessing, lastScanResult } = useSelector(
    (state: RootState) => state.qrScanner
  );
  const { isOfflineMode } = useSelector((state: RootState) => state.offline);
  
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isTorchOn, setIsTorchOn] = useState(false);

  useEffect(() => {
    dispatch(setScanning(true));
    dispatch(setScannedData(null));
    
    // Request camera permissions
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
      
      if (status !== 'granted') {
        Alert.alert(
          'Camera Permission Required',
          'Please grant camera permission to use the QR scanner',
          [{ text: 'OK' }]
        );
      }
    })();
    
    return () => {
      dispatch(setScanning(false));
    };
  }, [dispatch]);
  
  // Handle scan type changes
  const handleScanTypeChange = (type: string) => {
    dispatch(setScanType(type));
    
    // Reset event ID when changing scan type
    dispatch(setEventId(null));
  };
  
  // Handle event selection
  const handleEventSelection = (id: string) => {
    dispatch(setEventId(id));
  };

  useEffect(() => {
    // When we have a scan result, navigate to the result screen
    if (lastScanResult && !isProcessing) {
      navigation.navigate('ScanResult', { scanId: lastScanResult.id });
    }
  }, [lastScanResult, isProcessing, navigation]);

  const handleBarCodeScanned = async ({ data }: { type: string; data: string }) => {
    if (isProcessing || !isScanning || scannedData === data) {
      return;
    }

    // Set the scanned data and disable scanning temporarily
    dispatch(setScannedData(data));
    dispatch(setScanning(false));
    
    try {
      if (isOfflineMode) {
        // Process QR code offline
        await dispatch(verifyOfflineQRCode({
          qrData: data,
          scanType: state.qrScanner.scanType || undefined,
          eventId: state.qrScanner.eventId || undefined
        })).unwrap();
      } else {
        // Process QR code online
        await dispatch(processQRCode({
          qrData: data,
          scanType: state.qrScanner.scanType || undefined,
          eventId: state.qrScanner.eventId || undefined
        })).unwrap();
      }
    } catch (error: any) {
      Alert.alert('Scan Error', error.toString());
      // Re-enable scanning
      dispatch(setScanning(true));
      dispatch(setScannedData(null));
    }
  };

  const toggleTorch = () => {
    setIsTorchOn(!isTorchOn);
  };

  const navigateToScanHistory = () => {
    navigation.navigate('ScanHistory');
  };

  if (hasPermission === null) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <Text style={[styles.permissionText, { color: theme.colors.text }]}>
          No access to camera
        </Text>
        <TouchableOpacity
          style={[styles.button, { backgroundColor: theme.colors.primary }]}
          onPress={() => Camera.requestCameraPermissionsAsync()}
        >
          <Text style={[styles.buttonText, { color: theme.colors.surface }]}>
            Request Permission
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.headerContainer}>
        <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
          {isOfflineMode ? 'Offline QR Scanner' : 'QR Scanner'}
        </Text>
        <TouchableOpacity style={styles.historyButton} onPress={navigateToScanHistory}>
          <Icon name="history" size={24} color={theme.colors.text} />
        </TouchableOpacity>
      </View>

      <View style={styles.cameraContainer}>
        {isScanning ? (
          <Camera
            style={styles.camera}
            type={Camera.Constants.Type.back}
            barCodeScannerSettings={{
              barCodeTypes: [BarCodeScanner.Constants.BarCodeType.qr],
            }}
            onBarCodeScanned={isScanning ? handleBarCodeScanned : undefined}
            flashMode={
              isTorchOn
                ? Camera.Constants.FlashMode.torch
                : Camera.Constants.FlashMode.off
            }
          >
            <View style={styles.scannerOverlay}>
              <View style={styles.scannerGuide}>
                <View style={[styles.guideCorner, styles.topLeft]} />
                <View style={[styles.guideCorner, styles.topRight]} />
                <View style={[styles.guideCorner, styles.bottomLeft]} />
                <View style={[styles.guideCorner, styles.bottomRight]} />
              </View>
            </View>
          </Camera>
        ) : (
          <View style={[styles.processingContainer, { backgroundColor: theme.colors.background }]}>
            <ActivityIndicator size="large" color={theme.colors.primary} />
            <Text style={[styles.processingText, { color: theme.colors.text }]}>
              Processing QR code...
            </Text>
          </View>
        )}
      </View>

      <View style={styles.controlsContainer}>
        <TouchableOpacity
          style={[
            styles.controlButton,
            { backgroundColor: theme.colors.surface, borderColor: theme.colors.border },
          ]}
          onPress={toggleTorch}
        >
          <Icon
            name={isTorchOn ? 'flashlight-off' : 'flashlight'}
            size={24}
            color={isTorchOn ? theme.colors.secondary : theme.colors.text}
          />
          <Text
            style={[
              styles.controlText,
              { color: isTorchOn ? theme.colors.secondary : theme.colors.text },
            ]}
          >
            {isTorchOn ? 'Turn Off Flash' : 'Turn On Flash'}
          </Text>
        </TouchableOpacity>

        <View style={styles.scannerStatusContainer}>
          <View
            style={[
              styles.statusIndicator,
              {
                backgroundColor: isOfflineMode
                  ? theme.colors.warning
                  : isScanning
                  ? theme.colors.success
                  : theme.colors.error,
              },
            ]}
          />
          <Text style={[styles.statusText, { color: theme.colors.text }]}>
            {isOfflineMode
              ? 'Offline Mode'
              : isScanning
              ? 'Ready to Scan'
              : 'Processing...'}
          </Text>
        </View>
      </View>
      
      <View style={[styles.scanOptionsContainer, { backgroundColor: theme.colors.backgroundSecondary }]}>
        <View style={styles.optionsRow}>
          <Text style={[styles.optionsLabel, { color: theme.colors.text }]}>
            Type de scan:
          </Text>
          <View style={[styles.pickerContainer, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border }]}>
            <Picker
              selectedValue={state.qrScanner.scanType || 'practitioner_profile'}
              onValueChange={(value) => handleScanTypeChange(value)}
              style={styles.picker}
              dropdownIconColor={theme.colors.text}
            >
              <Picker.Item label="Profil Pratiquant" value="practitioner_profile" color={theme.colors.text} />
              <Picker.Item label="Compétition" value="competition" color={theme.colors.text} />
              <Picker.Item label="Entraînement" value="training" color={theme.colors.text} />
              <Picker.Item label="Événement" value="event" color={theme.colors.text} />
              <Picker.Item label="Présence" value="attendance" color={theme.colors.text} />
            </Picker>
          </View>
        </View>
        
        {state.qrScanner.scanType === 'competition' && (
          <View style={styles.optionsRow}>
            <Text style={[styles.optionsLabel, { color: theme.colors.text }]}>
              Compétition:
            </Text>
            <View style={[styles.pickerContainer, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border }]}>
              <Picker
                selectedValue={state.qrScanner.eventId || ''}
                onValueChange={(value) => handleEventSelection(value)}
                style={styles.picker}
                dropdownIconColor={theme.colors.text}
              >
                <Picker.Item label="Sélectionner une compétition" value="" color={theme.colors.textSecondary} />
                <Picker.Item label="Championnat national 2025" value="1" color={theme.colors.text} />
                <Picker.Item label="Coupe régionale - Été 2025" value="2" color={theme.colors.text} />
              </Picker>
            </View>
          </View>
        )}
        
        {state.qrScanner.scanType === 'training' && (
          <View style={styles.optionsRow}>
            <Text style={[styles.optionsLabel, { color: theme.colors.text }]}>
              Entraînement:
            </Text>
            <View style={[styles.pickerContainer, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border }]}>
              <Picker
                selectedValue={state.qrScanner.eventId || ''}
                onValueChange={(value) => handleEventSelection(value)}
                style={styles.picker}
                dropdownIconColor={theme.colors.text}
              >
                <Picker.Item label="Sélectionner une session" value="" color={theme.colors.textSecondary} />
                <Picker.Item label="Cours avancé - 25/05/2025" value="1" color={theme.colors.text} />
                <Picker.Item label="Cours débutant - 26/05/2025" value="2" color={theme.colors.text} />
              </Picker>
            </View>
          </View>
        )}
        
        {state.qrScanner.scanType === 'event' && (
          <View style={styles.optionsRow}>
            <Text style={[styles.optionsLabel, { color: theme.colors.text }]}>
              Événement:
            </Text>
            <View style={[styles.pickerContainer, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border }]}>
              <Picker
                selectedValue={state.qrScanner.eventId || ''}
                onValueChange={(value) => handleEventSelection(value)}
                style={styles.picker}
                dropdownIconColor={theme.colors.text}
              >
                <Picker.Item label="Sélectionner un événement" value="" color={theme.colors.textSecondary} />
                <Picker.Item label="Gala annuel - 15/06/2025" value="1" color={theme.colors.text} />
                <Picker.Item label="Séminaire technique - 22/07/2025" value="2" color={theme.colors.text} />
              </Picker>
            </View>
          </View>
        )}
      </View>

      <View style={styles.instructionsContainer}>
        <Text style={[styles.instructionsText, { color: theme.colors.textSecondary }]}>
          Position the QR code within the frame to scan. Make sure it's well-lit and the entire code is visible.
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerContainer: {
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingHorizontal: 20,
    paddingBottom: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  historyButton: {
    padding: 8,
  },
  cameraContainer: {
    flex: 1,
    overflow: 'hidden',
    borderRadius: 20,
    margin: 20,
  },
  camera: {
    flex: 1,
  },
  scannerOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scannerGuide: {
    width: 250,
    height: 250,
    position: 'relative',
  },
  guideCorner: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderColor: '#FFFFFF',
    borderWidth: 4,
  },
  topLeft: {
    top: 0,
    left: 0,
    borderBottomWidth: 0,
    borderRightWidth: 0,
    borderTopLeftRadius: 20,
  },
  topRight: {
    top: 0,
    right: 0,
    borderBottomWidth: 0,
    borderLeftWidth: 0,
    borderTopRightRadius: 20,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderTopWidth: 0,
    borderRightWidth: 0,
    borderBottomLeftRadius: 20,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderTopWidth: 0,
    borderLeftWidth: 0,
    borderBottomRightRadius: 20,
  },
  processingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  processingText: {
    marginTop: 20,
    fontSize: 16,
  },
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  controlButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
  controlText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '500',
  },
  scannerStatusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  // Scan options styles
  scanOptionsContainer: {
    padding: 15,
    marginHorizontal: 20,
    borderRadius: 10,
    marginBottom: 10,
  },
  optionsRow: {
    marginBottom: 10,
  },
  optionsLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 5,
  },
  pickerContainer: {
    borderWidth: 1,
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 40,
    width: '100%',
  },
  instructionsContainer: {
    padding: 20,
    paddingBottom: Platform.OS === 'ios' ? 40 : 20,
  },
  instructionsText: {
    fontSize: 14,
    textAlign: 'center',
  },
  permissionText: {
    fontSize: 18,
    marginBottom: 20,
    textAlign: 'center',
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default QRScannerScreen;