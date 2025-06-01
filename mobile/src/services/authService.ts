import axios from 'axios';
import { User } from '@types/user';
import { API_URL } from '@config/api';

interface LoginResponse {
  token: string;
  refreshToken: string;
  user: User;
}

interface RefreshTokenResponse {
  token: string;
}

class AuthService {
  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      const response = await axios.post(`${API_URL}/auth/login/`, {
        username,
        password,
      });
      
      return {
        token: response.data.token,
        refreshToken: response.data.refresh_token,
        user: {
          id: response.data.user.id,
          username: response.data.user.username,
          email: response.data.user.email,
          firstName: response.data.user.first_name,
          lastName: response.data.user.last_name,
          role: response.data.user.role,
          permissions: response.data.user.permissions || [],
          organization: response.data.user.organization ? {
            id: response.data.user.organization.id,
            name: response.data.user.organization.name,
            type: response.data.user.organization.type,
          } : undefined,
        },
      };
    } catch (error) {
      console.error('Login error:', error);
      throw new Error('Authentication failed. Please check your credentials.');
    }
  }

  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    try {
      const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
        refresh: refreshToken,
      });
      
      return {
        token: response.data.access,
      };
    } catch (error) {
      console.error('Token refresh error:', error);
      throw new Error('Failed to refresh token. Please login again.');
    }
  }

  async getCurrentUser(token: string): Promise<User> {
    try {
      const response = await axios.get(`${API_URL}/auth/me/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      return {
        id: response.data.id,
        username: response.data.username,
        email: response.data.email,
        firstName: response.data.first_name,
        lastName: response.data.last_name,
        role: response.data.role,
        permissions: response.data.permissions || [],
        organization: response.data.organization ? {
          id: response.data.organization.id,
          name: response.data.organization.name,
          type: response.data.organization.type,
        } : undefined,
      };
    } catch (error) {
      console.error('Get current user error:', error);
      throw new Error('Failed to get user information.');
    }
  }

  async register(userData: {
    username: string;
    email: string;
    password: string;
    firstName: string;
    lastName: string;
  }): Promise<{ success: boolean; message: string }> {
    try {
      await axios.post(`${API_URL}/auth/register/`, {
        username: userData.username,
        email: userData.email,
        password: userData.password,
        first_name: userData.firstName,
        last_name: userData.lastName,
      });
      
      return {
        success: true,
        message: 'Registration successful. You can now login.',
      };
    } catch (error: any) {
      console.error('Registration error:', error);
      
      if (error.response && error.response.data) {
        // Extract validation errors
        const errors = error.response.data;
        const messages = [];
        
        for (const field in errors) {
          if (Object.prototype.hasOwnProperty.call(errors, field)) {
            messages.push(`${field}: ${errors[field].join(', ')}`);
          }
        }
        
        throw new Error(messages.join('\n'));
      }
      
      throw new Error('Registration failed. Please try again later.');
    }
  }

  async forgotPassword(email: string): Promise<{ success: boolean; message: string }> {
    try {
      await axios.post(`${API_URL}/auth/password-reset/`, {
        email,
      });
      
      return {
        success: true,
        message: 'Password reset instructions have been sent to your email.',
      };
    } catch (error) {
      console.error('Forgot password error:', error);
      throw new Error('Failed to process password reset. Please try again later.');
    }
  }

  async resetPassword(token: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    try {
      await axios.post(`${API_URL}/auth/password-reset/confirm/`, {
        token,
        password: newPassword,
      });
      
      return {
        success: true,
        message: 'Your password has been reset successfully. You can now login with your new password.',
      };
    } catch (error) {
      console.error('Reset password error:', error);
      throw new Error('Failed to reset password. The token may be invalid or expired.');
    }
  }

  async logout(token: string): Promise<{ success: boolean }> {
    try {
      await axios.post(
        `${API_URL}/auth/logout/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      // Even if the server-side logout fails, we consider it successful on the client side
      return { success: true };
    }
  }
}

export const authService = new AuthService();