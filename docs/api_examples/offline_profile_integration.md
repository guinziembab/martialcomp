# Guide d'intégration du profil hors-ligne pour les applications mobiles

Ce guide explique comment intégrer la fonctionnalité de profil hors-ligne de MartialComp dans une application mobile.

## Vue d'ensemble

La fonctionnalité de profil hors-ligne permet de :

1. Générer un QR code contenant les informations complètes d'un profil de pratiquant
2. Scanner et vérifier ce QR code sans connexion internet
3. Afficher et valider les informations du pratiquant en mode hors-ligne

## Récupération des profils hors-ligne

### Endpoints d'API

```
GET /api/v1/practitioners/{practitioner_id}/offline-profile/
```

#### Paramètres de requête
- `format` : (optionnel) "json" (défaut) ou "html"

#### Réponse
```json
{
  "success": true,
  "profile_token": "eyJhbGciOiJIUzI1...",
  "generated_at": "2025-05-21T14:00:00Z",
  "qr_image_url": "https://example.com/media/qr_codes/practitioners/profile/...",
  "expires_in_days": 30
}
```

## Vérification d'un token de profil

### Processus de vérification

1. Décoder le contenu du QR code pour obtenir le token
2. Vérifier la validité du token en utilisant la fonction `verifyOfflineProfile`
3. Afficher les informations du profil si le token est valide

### Exemple d'implémentation en JavaScript

```javascript
// Fonction de décodage et vérification d'un token de profil
function verifyOfflineProfile(token) {
  try {
    // Décodage Base64URL en JSON
    const raw = atob(token.replace(/-/g, '+').replace(/_/g, '/'));
    const profileData = JSON.parse(raw);
    
    // Vérifier l'expiration
    const now = Math.floor(Date.now() / 1000);
    if (profileData.exp < now) {
      return {
        valid: false,
        reason: "token_expired"
      };
    }
    
    // Vérifier la signature (nécessite une implémentation spécifique)
    const isValidSignature = verifySignature(profileData);
    if (!isValidSignature) {
      return {
        valid: false,
        reason: "signature_invalid"
      };
    }
    
    // Token valide
    return {
      valid: true,
      profile: profileData
    };
    
  } catch (error) {
    return {
      valid: false,
      reason: "token_malformed",
      error: error.message
    };
  }
}

// Exemple de fonction pour la vérification de signature (à adapter)
function verifySignature(profileData) {
  // Extraction de la signature
  const signature = profileData.sig;
  
  // Copie des données sans la signature pour le calcul
  const dataToVerify = { ...profileData };
  delete dataToVerify.sig;
  delete dataToVerify.jti;
  
  // Tri des clés pour obtenir un ordre canonique
  const canonicalData = JSON.stringify(Object.keys(dataToVerify).sort().reduce(
    (obj, key) => {
      obj[key] = dataToVerify[key];
      return obj;
    }, {})
  );
  
  // Calcul du hash HMAC-SHA256 (nécessite une bibliothèque cryptographique)
  const expectedSignature = calculateHmacSha256(
    canonicalData + `martialcomp_offline_secret_profile_${profileData.prac_id}`
  );
  
  // Comparaison des signatures
  return signature === expectedSignature;
}
```

### Exemple d'implémentation en React Native

```jsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Camera } from 'expo-camera';
import * as Crypto from 'expo-crypto';

export default function OfflineProfileScanner() {
  const [hasPermission, setHasPermission] = useState(null);
  const [scanned, setScanned] = useState(false);
  const [profileData, setProfileData] = useState(null);
  const [error, setError] = useState(null);

  // Demande de permission pour la caméra
  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  // Fonction de gestion du scan
  const handleBarCodeScanned = ({ data }) => {
    setScanned(true);
    verifyProfileToken(data);
  };

  // Vérification du token
  const verifyProfileToken = async (token) => {
    try {
      // Décodage Base64URL en JSON
      const raw = atob(token.replace(/-/g, '+').replace(/_/g, '/'));
      const profileData = JSON.parse(raw);
      
      // Vérifier l'expiration
      const now = Math.floor(Date.now() / 1000);
      if (profileData.exp < now) {
        setError('Ce profil a expiré');
        return;
      }
      
      // Vérifier la signature (simplifié pour l'exemple)
      const isValidSignature = true; // À remplacer par votre logique de vérification
      
      if (!isValidSignature) {
        setError('Signature invalide');
        return;
      }
      
      // Profil valide
      setProfileData(profileData);
      setError(null);
      
    } catch (error) {
      setError('Format de token invalide: ' + error.message);
    }
  };

  // Rendu de l'interface
  return (
    <View style={styles.container}>
      {hasPermission === null && <Text>Demande d'autorisation de caméra...</Text>}
      {hasPermission === false && <Text>Accès à la caméra refusé</Text>}
      
      {hasPermission && !scanned && (
        <Camera
          style={styles.camera}
          onBarCodeScanned={handleBarCodeScanned}
          barCodeScannerSettings={{
            barCodeTypes: ['qr'],
          }}
        />
      )}
      
      {scanned && (
        <View style={styles.resultContainer}>
          {error ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
              <TouchableOpacity 
                style={styles.button}
                onPress={() => setScanned(false)}
              >
                <Text style={styles.buttonText}>Scanner à nouveau</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <ProfileDisplay profile={profileData} />
          )}
        </View>
      )}
    </View>
  );
}

// Composant d'affichage du profil
function ProfileDisplay({ profile }) {
  return (
    <View style={styles.profileContainer}>
      <Text style={styles.nameText}>{profile.first_name} {profile.last_name}</Text>
      <Text style={styles.infoText}>Club: {profile.club?.name || 'Non spécifié'}</Text>
      <Text style={styles.infoText}>Licence: {profile.license_number || 'Non spécifiée'}</Text>
      <Text style={styles.infoText}>Grade: {profile.grade || 'Non spécifié'}</Text>
      
      {/* Plus d'informations de profil... */}
      
      <View style={styles.validationContainer}>
        <Text style={styles.validText}>Profil vérifié ✓</Text>
        <Text style={styles.expireText}>
          Valable jusqu'au {new Date(profile.exp * 1000).toLocaleDateString()}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'column',
  },
  camera: {
    flex: 1,
  },
  resultContainer: {
    flex: 1,
    padding: 20,
  },
  errorContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  errorText: {
    color: 'red',
    fontSize: 18,
    marginBottom: 20,
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#007BFF',
    padding: 15,
    borderRadius: 5,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
  },
  profileContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 20,
  },
  nameText: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  infoText: {
    fontSize: 16,
    marginBottom: 8,
  },
  validationContainer: {
    marginTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
    paddingTop: 15,
  },
  validText: {
    color: 'green',
    fontSize: 16,
    fontWeight: 'bold',
  },
  expireText: {
    color: '#666',
    fontSize: 14,
    marginTop: 5,
  },
});
```

### Exemple d'implémentation en Swift (iOS)

```swift
import UIKit
import AVFoundation
import CommonCrypto

class OfflineProfileScannerViewController: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
    
    var captureSession: AVCaptureSession!
    var previewLayer: AVCaptureVideoPreviewLayer!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Configuration de la caméra
        captureSession = AVCaptureSession()
        
        guard let videoCaptureDevice = AVCaptureDevice.default(for: .video) else { return }
        let videoInput: AVCaptureDeviceInput
        
        do {
            videoInput = try AVCaptureDeviceInput(device: videoCaptureDevice)
        } catch {
            return
        }
        
        if (captureSession.canAddInput(videoInput)) {
            captureSession.addInput(videoInput)
        } else {
            failed()
            return
        }
        
        let metadataOutput = AVCaptureMetadataOutput()
        
        if (captureSession.canAddOutput(metadataOutput)) {
            captureSession.addOutput(metadataOutput)
            
            metadataOutput.setMetadataObjectsDelegate(self, queue: DispatchQueue.main)
            metadataOutput.metadataObjectTypes = [.qr]
        } else {
            failed()
            return
        }
        
        // Configuration de la prévisualisation
        previewLayer = AVCaptureVideoPreviewLayer(session: captureSession)
        previewLayer.frame = view.layer.bounds
        previewLayer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(previewLayer)
        
        // Démarrage de la capture
        captureSession.startRunning()
    }
    
    func failed() {
        let ac = UIAlertController(title: "Échec de la numérisation", message: "Votre appareil ne prend pas en charge la numérisation de code", preferredStyle: .alert)
        ac.addAction(UIAlertAction(title: "OK", style: .default))
        present(ac, animated: true)
        captureSession = nil
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        
        if (captureSession?.isRunning == false) {
            captureSession.startRunning()
        }
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        
        if (captureSession?.isRunning == true) {
            captureSession.stopRunning()
        }
    }
    
    // Gestion de la détection des codes QR
    func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
        captureSession.stopRunning()
        
        if let metadataObject = metadataObjects.first {
            guard let readableObject = metadataObject as? AVMetadataMachineReadableCodeObject else { return }
            guard let stringValue = readableObject.stringValue else { return }
            
            // Vérification du token de profil
            verifyProfileToken(token: stringValue)
        }
    }
    
    // Vérification du token de profil
    func verifyProfileToken(token: String) {
        do {
            // Décodage de Base64URL en données
            let base64 = token.replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/")
            guard let data = Data(base64Encoded: base64) else {
                showError(message: "Format de token invalide")
                return
            }
            
            // Décodage JSON
            guard let profileData = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] else {
                showError(message: "Impossible de décoder les données du profil")
                return
            }
            
            // Vérification de l'expiration
            let now = Int(Date().timeIntervalSince1970)
            if let exp = profileData["exp"] as? Int, exp < now {
                showError(message: "Ce profil a expiré")
                return
            }
            
            // Vérification de la signature (simplifié pour l'exemple)
            let isValidSignature = true // À remplacer par votre logique de vérification
            
            if !isValidSignature {
                showError(message: "Signature invalide")
                return
            }
            
            // Profil valide - Affichage des informations
            showProfileDetails(profile: profileData)
            
        } catch {
            showError(message: "Erreur lors de la vérification: \(error.localizedDescription)")
        }
    }
    
    // Affichage des erreurs
    func showError(message: String) {
        let alert = UIAlertController(title: "Erreur", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Scanner à nouveau", style: .default) { _ in
            self.captureSession.startRunning()
        })
        present(alert, animated: true)
    }
    
    // Affichage des détails du profil
    func showProfileDetails(profile: [String: Any]) {
        // Créer et présenter un contrôleur de vue pour afficher les détails du profil
        let profileVC = ProfileDetailViewController()
        profileVC.profileData = profile
        present(profileVC, animated: true)
    }
}

// Contrôleur de vue pour l'affichage des détails de profil
class ProfileDetailViewController: UIViewController {
    
    var profileData: [String: Any]?
    
    // Interface d'affichage à implémenter selon vos besoins
    // ...
}
```

### Exemple d'implémentation en Kotlin (Android)

```kotlin
import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Base64
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import kotlinx.android.synthetic.main.activity_scanner.*
import org.json.JSONObject
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class ProfileScannerActivity : AppCompatActivity() {
    
    private lateinit var cameraExecutor: ExecutorService
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_scanner)
        
        // Vérification des permissions
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(
                this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS)
        }
        
        cameraExecutor = Executors.newSingleThreadExecutor()
    }
    
    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        
        cameraProviderFuture.addListener({
            val cameraProvider: ProcessCameraProvider = cameraProviderFuture.get()
            
            val preview = Preview.Builder()
                .build()
                .also {
                    it.setSurfaceProvider(viewFinder.surfaceProvider)
                }
            
            val imageAnalyzer = ImageAnalysis.Builder()
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor, QRCodeAnalyzer { qrCode ->
                        // Analyse du QR code
                        verifyProfileToken(qrCode)
                    })
                }
            
            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this, CameraSelector.DEFAULT_BACK_CAMERA, preview, imageAnalyzer)
            } catch(exc: Exception) {
                Toast.makeText(this, "Échec de la configuration de la caméra", Toast.LENGTH_SHORT).show()
            }
            
        }, ContextCompat.getMainExecutor(this))
    }
    
    private fun verifyProfileToken(token: String) {
        try {
            // Décodage Base64URL
            val base64 = token.replace('-', '+').replace('_', '/')
            val jsonData = String(Base64.decode(base64, Base64.DEFAULT), StandardCharsets.UTF_8)
            
            // Parsing JSON
            val profileData = JSONObject(jsonData)
            
            // Vérification de l'expiration
            val now = System.currentTimeMillis() / 1000
            if (profileData.getLong("exp") < now) {
                showError("Ce profil a expiré")
                return
            }
            
            // Extraction et vérification de la signature
            val signature = profileData.getString("sig")
            
            // Copie sans la signature pour la vérification
            val dataToVerify = JSONObject(profileData.toString())
            dataToVerify.remove("sig")
            dataToVerify.remove("jti")
            
            // Calcul de la signature attendue
            val expectedSignature = calculateSignature(dataToVerify, profileData.getInt("prac_id"))
            
            if (signature != expectedSignature) {
                showError("Signature invalide")
                return
            }
            
            // Affichage du profil
            runOnUiThread {
                // Navigation vers l'écran de profil
                val intent = Intent(this, ProfileDetailActivity::class.java).apply {
                    putExtra("PROFILE_DATA", jsonData)
                }
                startActivity(intent)
                finish()
            }
            
        } catch (e: Exception) {
            showError("Erreur: ${e.message}")
        }
    }
    
    private fun calculateSignature(data: JSONObject, pracId: Int): String {
        // Tri des clés pour l'ordre canonique
        val sortedData = sortJsonObject(data)
        
        // Clé de signature
        val key = "martialcomp_offline_secret_profile_$pracId"
        
        // Calcul HMAC-SHA256
        val secretKeySpec = SecretKeySpec(key.toByteArray(), "HmacSHA256")
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(secretKeySpec)
        val bytes = mac.doFinal(sortedData.toString().toByteArray())
        
        // Conversion en hexadécimal
        return bytes.joinToString("") { "%02x".format(it) }
    }
    
    private fun sortJsonObject(jsonObject: JSONObject): JSONObject {
        val sortedJson = JSONObject()
        val keys = jsonObject.keys().asSequence().sorted().toList()
        
        for (key in keys) {
            sortedJson.put(key, jsonObject.get(key))
        }
        
        return sortedJson
    }
    
    private fun showError(message: String) {
        runOnUiThread {
            Toast.makeText(this, message, Toast.LENGTH_LONG).show()
            // Attendre un peu puis reprendre le scan
            Handler(Looper.getMainLooper()).postDelayed({
                startCamera()
            }, 3000)
        }
    }
    
    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera()
            } else {
                Toast.makeText(this, "Permissions non accordées", Toast.LENGTH_SHORT).show()
                finish()
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
    }
    
    companion object {
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
    }
}

// Activité de détail de profil
class ProfileDetailActivity : AppCompatActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_profile_detail)
        
        val profileData = intent.getStringExtra("PROFILE_DATA")
        if (profileData != null) {
            displayProfile(profileData)
        } else {
            finish()
        }
    }
    
    private fun displayProfile(profileJson: String) {
        try {
            val profile = JSONObject(profileJson)
            
            // Configuration de l'interface utilisateur avec les données du profil
            nameTextView.text = "${profile.getString("first_name")} ${profile.getString("last_name")}"
            clubTextView.text = "Club: ${profile.getJSONObject("club").getString("name")}"
            // ... et autres champs
            
            // Affichage de la date d'expiration
            val expiryDate = Date(profile.getLong("exp") * 1000)
            val dateFormat = SimpleDateFormat("dd/MM/yyyy", Locale.getDefault())
            expiryTextView.text = "Valable jusqu'au ${dateFormat.format(expiryDate)}"
            
        } catch (e: Exception) {
            Toast.makeText(this, "Erreur d'affichage du profil", Toast.LENGTH_SHORT).show()
            finish()
        }
    }
}
```

## Sécurité et bonnes pratiques

1. **Vérification de signature** : Implémentez toujours la vérification de signature dans vos applications clientes pour garantir l'authenticité des données.

2. **Vérification d'expiration** : Vérifiez toujours la date d'expiration du token avant d'afficher les informations.

3. **Stockage local** : Si vous stockez temporairement des profils hors-ligne, assurez-vous de les chiffrer et de respecter une politique d'expiration stricte.

4. **Mode hors-ligne** : Testez rigoureusement le fonctionnement de votre application en mode avion pour vous assurer qu'elle fonctionne correctement sans connexion.

5. **Gestion des erreurs** : Mettez en place une gestion claire des erreurs avec des messages explicites pour aider les utilisateurs à comprendre les problèmes.

## Ressources additionnelles

- Documentation complète de l'API : `/docs/api/reference.md`
- Guide de débogage : `/docs/troubleshooting.md`
- Exemples complets: disponibles dans le répertoire `/docs/api_examples/`