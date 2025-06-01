// Example of JWT Authentication in Swift for MartialComp mobile app
// Documentation de l'API d'authentification JWT pour iOS

import Foundation

// Class to manage authentication
class JWTAuthManager {
    // API Base URL
    private let baseURL = "https://api.martialcomp.com/api/v1/auth/"
    
    // User credentials
    private var accessToken: String?
    private var refreshToken: String?
    private var tokenExpiration: Date?
    
    // Device information
    private let deviceId = UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString
    private let deviceName = UIDevice.current.name
    private let deviceModel = UIDevice.current.model
    private let osVersion = UIDevice.current.systemVersion
    private let appVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
    
    // MARK: - Authentication methods
    
    // Login with username and password
    func login(username: String, password: String, completion: @escaping (Result<User, Error>) -> Void) {
        let loginURL = URL(string: baseURL + "login/")!
        var request = URLRequest(url: loginURL)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Create login payload
        let loginPayload: [String: Any] = [
            "username": username,
            "password": password,
            "device_id": deviceId,
            "device_name": deviceName,
            "device_model": deviceModel,
            "os_version": osVersion,
            "app_version": appVersion
        ]
        
        // Serialize payload to JSON
        request.httpBody = try? JSONSerialization.data(withJSONObject: loginPayload)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(NSError(domain: "No data received", code: 0)))
                return
            }
            
            do {
                let decoder = JSONDecoder()
                let authResponse = try decoder.decode(AuthResponse.self, from: data)
                
                // Store tokens
                self.accessToken = authResponse.access
                self.refreshToken = authResponse.refresh
                
                // Calculate token expiration
                if let expiresIn = authResponse.expires_in {
                    self.tokenExpiration = Date().addingTimeInterval(TimeInterval(expiresIn))
                }
                
                completion(.success(authResponse.user))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    // Refresh the access token
    func refreshAccessToken(completion: @escaping (Result<Void, Error>) -> Void) {
        guard let refreshToken = self.refreshToken else {
            completion(.failure(NSError(domain: "No refresh token available", code: 401)))
            return
        }
        
        let refreshURL = URL(string: baseURL + "refresh/")!
        var request = URLRequest(url: refreshURL)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Create refresh payload
        let refreshPayload = ["refresh": refreshToken]
        request.httpBody = try? JSONSerialization.data(withJSONObject: refreshPayload)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(NSError(domain: "No data received", code: 0)))
                return
            }
            
            do {
                let decoder = JSONDecoder()
                let authResponse = try decoder.decode(AuthResponse.self, from: data)
                
                // Update tokens
                self.accessToken = authResponse.access
                self.refreshToken = authResponse.refresh
                
                // Calculate token expiration
                if let expiresIn = authResponse.expires_in {
                    self.tokenExpiration = Date().addingTimeInterval(TimeInterval(expiresIn))
                }
                
                completion(.success(()))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    // Logout and revoke tokens
    func logout(completion: @escaping (Result<Void, Error>) -> Void) {
        guard let refreshToken = self.refreshToken else {
            // Already logged out or no token
            completion(.success(()))
            return
        }
        
        let logoutURL = URL(string: baseURL + "logout/")!
        var request = URLRequest(url: logoutURL)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Create logout payload
        let logoutPayload = ["refresh": refreshToken]
        request.httpBody = try? JSONSerialization.data(withJSONObject: logoutPayload)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            // Clear tokens regardless of the result
            self.accessToken = nil
            self.refreshToken = nil
            self.tokenExpiration = nil
            
            if let error = error {
                completion(.failure(error))
                return
            }
            
            completion(.success(()))
        }.resume()
    }
    
    // Register a new user
    func register(username: String, password: String, email: String, 
                  firstName: String, lastName: String, 
                  completion: @escaping (Result<User, Error>) -> Void) {
        
        let registerURL = URL(string: baseURL + "register/")!
        var request = URLRequest(url: registerURL)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Create registration payload
        let registerPayload: [String: Any] = [
            "username": username,
            "password": password,
            "password_confirm": password,
            "email": email,
            "first_name": firstName,
            "last_name": lastName,
            "device_id": deviceId,
            "device_name": deviceName,
            "device_model": deviceModel,
            "os_version": osVersion,
            "app_version": appVersion
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: registerPayload)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(NSError(domain: "No data received", code: 0)))
                return
            }
            
            do {
                let decoder = JSONDecoder()
                let authResponse = try decoder.decode(AuthResponse.self, from: data)
                
                // Store tokens
                self.accessToken = authResponse.access
                self.refreshToken = authResponse.refresh
                
                // Calculate token expiration
                if let expiresIn = authResponse.expires_in {
                    self.tokenExpiration = Date().addingTimeInterval(TimeInterval(expiresIn))
                }
                
                completion(.success(authResponse.user))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    // MARK: - Helper methods
    
    // Add authorization to a request
    func authorizedRequest(url: URL) -> URLRequest {
        var request = URLRequest(url: url)
        
        if let accessToken = accessToken {
            request.addValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        }
        
        return request
    }
    
    // Check if authentication token is valid
    func isAuthenticated() -> Bool {
        guard let expiration = tokenExpiration, let _ = accessToken else {
            return false
        }
        
        // Check if token is still valid (with a 5-minute buffer)
        return expiration.timeIntervalSinceNow > 300
    }
    
    // Ensure that the token is valid before making a request
    func ensureValidToken(completion: @escaping (Result<Void, Error>) -> Void) {
        // If token is still valid, return success
        if isAuthenticated() {
            completion(.success(()))
            return
        }
        
        // Otherwise, refresh the token
        refreshAccessToken(completion: completion)
    }
}

// MARK: - Data Models

struct AuthResponse: Codable {
    let access: String
    let refresh: String
    let user: User
    let expires_in: Int?
}

struct User: Codable {
    let id: Int
    let username: String
    let email: String
    let first_name: String
    let last_name: String
    let date_joined: String
    let is_active: Bool
}

// MARK: - Example Usage

class AuthExample {
    let authManager = JWTAuthManager()
    
    func demonstrateAuth() {
        // Login example
        authManager.login(username: "user123", password: "securepassword") { result in
            switch result {
            case .success(let user):
                print("Successfully logged in: \(user.username)")
                
                // Now we can make authenticated requests
                self.fetchUserProfile()
            case .failure(let error):
                print("Login failed: \(error.localizedDescription)")
            }
        }
    }
    
    func fetchUserProfile() {
        // Ensure we have a valid token before making the request
        authManager.ensureValidToken { result in
            switch result {
            case .success:
                // Token is valid, make the request
                let url = URL(string: "https://api.martialcomp.com/api/v1/auth/user/")!
                let request = self.authManager.authorizedRequest(url: url)
                
                URLSession.shared.dataTask(with: request) { data, response, error in
                    if let data = data {
                        // Process user profile data
                        print("Received user profile data: \(String(data: data, encoding: .utf8) ?? "")")
                    }
                }.resume()
                
            case .failure(let error):
                print("Failed to refresh token: \(error.localizedDescription)")
            }
        }
    }
}