// Example of JWT Authentication in Kotlin for MartialComp mobile app
// Documentation de l'API d'authentification JWT pour Android

import android.content.Context
import android.os.Build
import android.provider.Settings
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import java.util.*
import java.util.concurrent.TimeUnit

/**
 * Manager for JWT authentication in the MartialComp mobile app
 */
class JWTAuthManager(private val context: Context) {
    
    companion object {
        private const val BASE_URL = "https://api.martialcomp.com/api/v1/auth/"
        private const val PREFS_FILE_NAME = "auth_prefs"
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        private const val KEY_TOKEN_EXPIRATION = "token_expiration"
    }
    
    // OkHttp client for network requests
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    // Gson for JSON parsing
    private val gson = Gson()
    
    // Device information
    private val deviceId: String
        get() = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
    
    private val deviceName: String
        get() = Build.MODEL
    
    private val deviceModel: String
        get() = Build.DEVICE
    
    private val osVersion: String
        get() = Build.VERSION.RELEASE
    
    private val appVersion: String
        get() {
            val packageInfo = context.packageManager.getPackageInfo(context.packageName, 0)
            return packageInfo.versionName
        }
    
    // Encrypted shared preferences for token storage
    private val securePreferences by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        
        EncryptedSharedPreferences.create(
            context,
            PREFS_FILE_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }
    
    // Current token values
    private var accessToken: String?
        get() = securePreferences.getString(KEY_ACCESS_TOKEN, null)
        set(value) = securePreferences.edit().putString(KEY_ACCESS_TOKEN, value).apply()
    
    private var refreshToken: String?
        get() = securePreferences.getString(KEY_REFRESH_TOKEN, null)
        set(value) = securePreferences.edit().putString(KEY_REFRESH_TOKEN, value).apply()
    
    private var tokenExpiration: Long
        get() = securePreferences.getLong(KEY_TOKEN_EXPIRATION, 0)
        set(value) = securePreferences.edit().putLong(KEY_TOKEN_EXPIRATION, value).apply()
    
    /**
     * Login with username and password
     */
    suspend fun login(username: String, password: String): Result<User> = withContext(Dispatchers.IO) {
        try {
            // Create login payload
            val loginPayload = mapOf(
                "username" to username,
                "password" to password,
                "device_id" to deviceId,
                "device_name" to deviceName,
                "device_model" to deviceModel,
                "os_version" to osVersion,
                "app_version" to appVersion
            )
            
            val json = gson.toJson(loginPayload)
            val body = json.toRequestBody("application/json".toMediaType())
            
            val request = Request.Builder()
                .url("${BASE_URL}login/")
                .post(body)
                .addHeader("Content-Type", "application/json")
                .build()
            
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    return@withContext Result.failure(Exception("Login failed: ${response.code}"))
                }
                
                val responseBody = response.body?.string() ?: return@withContext Result.failure(Exception("Empty response"))
                val authResponse = gson.fromJson(responseBody, AuthResponse::class.java)
                
                // Store tokens
                accessToken = authResponse.access
                refreshToken = authResponse.refresh
                
                // Calculate expiration (current time + expires_in seconds)
                tokenExpiration = System.currentTimeMillis() + (authResponse.expiresIn * 1000)
                
                return@withContext Result.success(authResponse.user)
            }
        } catch (e: Exception) {
            return@withContext Result.failure(e)
        }
    }
    
    /**
     * Register a new user
     */
    suspend fun register(
        username: String, 
        password: String, 
        email: String, 
        firstName: String, 
        lastName: String
    ): Result<User> = withContext(Dispatchers.IO) {
        try {
            // Create registration payload
            val registerPayload = mapOf(
                "username" to username,
                "password" to password,
                "password_confirm" to password,
                "email" to email,
                "first_name" to firstName,
                "last_name" to lastName,
                "device_id" to deviceId,
                "device_name" to deviceName,
                "device_model" to deviceModel,
                "os_version" to osVersion,
                "app_version" to appVersion
            )
            
            val json = gson.toJson(registerPayload)
            val body = json.toRequestBody("application/json".toMediaType())
            
            val request = Request.Builder()
                .url("${BASE_URL}register/")
                .post(body)
                .addHeader("Content-Type", "application/json")
                .build()
            
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    return@withContext Result.failure(Exception("Registration failed: ${response.code}"))
                }
                
                val responseBody = response.body?.string() ?: return@withContext Result.failure(Exception("Empty response"))
                val authResponse = gson.fromJson(responseBody, AuthResponse::class.java)
                
                // Store tokens
                accessToken = authResponse.access
                refreshToken = authResponse.refresh
                
                // Calculate expiration (current time + expires_in seconds)
                tokenExpiration = System.currentTimeMillis() + (authResponse.expiresIn * 1000)
                
                return@withContext Result.success(authResponse.user)
            }
        } catch (e: Exception) {
            return@withContext Result.failure(e)
        }
    }
    
    /**
     * Refresh the access token
     */
    suspend fun refreshAccessToken(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val currentRefreshToken = refreshToken ?: return@withContext Result.failure(Exception("No refresh token available"))
            
            // Create refresh payload
            val refreshPayload = mapOf("refresh" to currentRefreshToken)
            val json = gson.toJson(refreshPayload)
            val body = json.toRequestBody("application/json".toMediaType())
            
            val request = Request.Builder()
                .url("${BASE_URL}refresh/")
                .post(body)
                .addHeader("Content-Type", "application/json")
                .build()
            
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    return@withContext Result.failure(Exception("Token refresh failed: ${response.code}"))
                }
                
                val responseBody = response.body?.string() ?: return@withContext Result.failure(Exception("Empty response"))
                val authResponse = gson.fromJson(responseBody, AuthResponse::class.java)
                
                // Update tokens
                accessToken = authResponse.access
                refreshToken = authResponse.refresh
                
                // Calculate expiration (current time + expires_in seconds)
                tokenExpiration = System.currentTimeMillis() + (authResponse.expiresIn * 1000)
                
                return@withContext Result.success(Unit)
            }
        } catch (e: Exception) {
            return@withContext Result.failure(e)
        }
    }
    
    /**
     * Logout and revoke tokens
     */
    suspend fun logout(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val currentRefreshToken = refreshToken ?: return@withContext Result.success(Unit) // Already logged out
            
            // Create logout payload
            val logoutPayload = mapOf("refresh" to currentRefreshToken)
            val json = gson.toJson(logoutPayload)
            val body = json.toRequestBody("application/json".toMediaType())
            
            val request = Request.Builder()
                .url("${BASE_URL}logout/")
                .post(body)
                .addHeader("Content-Type", "application/json")
                .build()
            
            // Clear tokens regardless of the response
            clearTokens()
            
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    return@withContext Result.failure(Exception("Logout failed: ${response.code}"))
                }
                
                return@withContext Result.success(Unit)
            }
        } catch (e: Exception) {
            // Still clear tokens on error
            clearTokens()
            return@withContext Result.failure(e)
        }
    }
    
    /**
     * Get user profile information
     */
    suspend fun getUserProfile(): Result<User> = withContext(Dispatchers.IO) {
        ensureValidToken().fold(
            onSuccess = {
                try {
                    val request = Request.Builder()
                        .url("${BASE_URL}user/")
                        .get()
                        .addHeader("Authorization", "Bearer $accessToken")
                        .build()
                    
                    client.newCall(request).execute().use { response ->
                        if (!response.isSuccessful) {
                            return@withContext Result.failure(Exception("Failed to get user profile: ${response.code}"))
                        }
                        
                        val responseBody = response.body?.string() ?: return@withContext Result.failure(Exception("Empty response"))
                        val user = gson.fromJson(responseBody, User::class.java)
                        return@withContext Result.success(user)
                    }
                } catch (e: Exception) {
                    return@withContext Result.failure(e)
                }
            },
            onFailure = { error ->
                return@withContext Result.failure(error)
            }
        )
    }
    
    /**
     * Helper method to ensure we have a valid token
     */
    suspend fun ensureValidToken(): Result<Unit> {
        // Check if token is expired (with a 5-minute buffer)
        val currentTime = System.currentTimeMillis()
        val bufferTime = 5 * 60 * 1000 // 5 minutes in milliseconds
        
        return if (accessToken != null && tokenExpiration > (currentTime + bufferTime)) {
            Result.success(Unit) // Token is still valid
        } else if (refreshToken != null) {
            refreshAccessToken() // Token expired, try to refresh
        } else {
            Result.failure(Exception("No valid token or refresh token available")) // No tokens available
        }
    }
    
    /**
     * Clear all stored tokens
     */
    private fun clearTokens() {
        accessToken = null
        refreshToken = null
        tokenExpiration = 0
    }
    
    /**
     * Check if user is authenticated
     */
    fun isAuthenticated(): Boolean {
        return !accessToken.isNullOrEmpty() && tokenExpiration > System.currentTimeMillis()
    }
    
    /**
     * Add authorization header to any request
     */
    fun addAuthHeader(builder: Request.Builder): Request.Builder {
        accessToken?.let {
            builder.addHeader("Authorization", "Bearer $it")
        }
        return builder
    }
}

/**
 * Data models for API responses
 */
data class AuthResponse(
    val access: String,
    val refresh: String,
    val user: User,
    @SerializedName("expires_in")
    val expiresIn: Int
)

data class User(
    val id: Int,
    val username: String,
    val email: String,
    @SerializedName("first_name")
    val firstName: String,
    @SerializedName("last_name")
    val lastName: String,
    @SerializedName("date_joined")
    val dateJoined: String,
    @SerializedName("is_active")
    val isActive: Boolean
)

/**
 * Example usage in an Activity or ViewModel
 */
class AuthExample(private val context: Context) {
    private val authManager = JWTAuthManager(context)
    
    suspend fun demonstrateAuth() {
        // Login example
        authManager.login("user123", "securepassword").fold(
            onSuccess = { user ->
                println("Successfully logged in: ${user.username}")
                
                // Now we can make authenticated requests
                getUserProfile()
            },
            onFailure = { error ->
                println("Login failed: ${error.message}")
            }
        )
    }
    
    private suspend fun getUserProfile() {
        authManager.getUserProfile().fold(
            onSuccess = { user ->
                println("User profile retrieved: ${user.firstName} ${user.lastName}")
            },
            onFailure = { error ->
                println("Failed to get user profile: ${error.message}")
            }
        )
    }
}