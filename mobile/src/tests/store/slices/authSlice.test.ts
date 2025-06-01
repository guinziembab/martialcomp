import authReducer, {
  login,
  logout,
  refreshAuthToken,
  checkAuthStatus,
  setCredentials,
  clearCredentials,
} from '@store/slices/authSlice';
import { authService } from '@services/authService';
import * as SecureStore from 'expo-secure-store';

// Mock the auth service
jest.mock('@services/authService', () => ({
  authService: {
    login: jest.fn(),
    refreshToken: jest.fn(),
    getCurrentUser: jest.fn(),
    logout: jest.fn(),
  },
}));

// Mock SecureStore
jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

describe('authSlice', () => {
  const initialState = {
    user: null,
    token: null,
    refreshToken: null,
    isLoading: false,
    error: null,
    isAuthenticated: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('reducers', () => {
    it('should handle setCredentials', () => {
      const user = { id: '1', username: 'testuser', email: 'test@example.com', firstName: 'Test', lastName: 'User', role: 'practitioner', permissions: [] };
      const token = 'test-token';
      const refreshToken = 'test-refresh-token';
      
      const nextState = authReducer(initialState, setCredentials({ user, token, refreshToken }));
      
      expect(nextState).toEqual({
        ...initialState,
        user,
        token,
        refreshToken,
        isAuthenticated: true,
      });
    });

    it('should handle clearCredentials', () => {
      const state = {
        ...initialState,
        user: { id: '1', username: 'testuser', email: 'test@example.com', firstName: 'Test', lastName: 'User', role: 'practitioner', permissions: [] },
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        isAuthenticated: true,
      };
      
      const nextState = authReducer(state, clearCredentials());
      
      expect(nextState).toEqual(initialState);
    });
  });

  describe('extraReducers', () => {
    it('should handle login.pending', () => {
      const nextState = authReducer(initialState, { type: login.pending.type });
      
      expect(nextState).toEqual({
        ...initialState,
        isLoading: true,
        error: null,
      });
    });

    it('should handle login.fulfilled', () => {
      const user = { id: '1', username: 'testuser', email: 'test@example.com', firstName: 'Test', lastName: 'User', role: 'practitioner', permissions: [] };
      const token = 'test-token';
      const refreshToken = 'test-refresh-token';
      
      const nextState = authReducer(initialState, {
        type: login.fulfilled.type,
        payload: { user, token, refreshToken },
      });
      
      expect(nextState).toEqual({
        ...initialState,
        user,
        token,
        refreshToken,
        isAuthenticated: true,
        isLoading: false,
      });
    });

    it('should handle login.rejected', () => {
      const error = 'Invalid credentials';
      
      const nextState = authReducer(initialState, {
        type: login.rejected.type,
        payload: error,
      });
      
      expect(nextState).toEqual({
        ...initialState,
        isLoading: false,
        error,
      });
    });

    it('should handle logout.fulfilled', () => {
      const state = {
        ...initialState,
        user: { id: '1', username: 'testuser', email: 'test@example.com', firstName: 'Test', lastName: 'User', role: 'practitioner', permissions: [] },
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        isAuthenticated: true,
      };
      
      const nextState = authReducer(state, { type: logout.fulfilled.type });
      
      expect(nextState).toEqual({
        ...initialState,
        isLoading: false,
      });
    });

    it('should handle refreshAuthToken.fulfilled', () => {
      const state = {
        ...initialState,
        token: 'old-token',
        refreshToken: 'test-refresh-token',
      };
      
      const newToken = 'new-token';
      
      const nextState = authReducer(state, {
        type: refreshAuthToken.fulfilled.type,
        payload: { token: newToken },
      });
      
      expect(nextState).toEqual({
        ...state,
        token: newToken,
      });
    });

    it('should handle refreshAuthToken.rejected', () => {
      const state = {
        ...initialState,
        user: { id: '1', username: 'testuser', email: 'test@example.com', firstName: 'Test', lastName: 'User', role: 'practitioner', permissions: [] },
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        isAuthenticated: true,
      };
      
      const nextState = authReducer(state, { type: refreshAuthToken.rejected.type });
      
      expect(nextState).toEqual({
        ...initialState,
      });
    });
  });

  // Testing the thunks would require more complex setup with middleware
  // This is a simple test to ensure the thunks exist
  describe('thunks', () => {
    it('should export login thunk', () => {
      expect(login).toBeDefined();
      expect(typeof login).toBe('function');
    });

    it('should export logout thunk', () => {
      expect(logout).toBeDefined();
      expect(typeof logout).toBe('function');
    });

    it('should export refreshAuthToken thunk', () => {
      expect(refreshAuthToken).toBeDefined();
      expect(typeof refreshAuthToken).toBe('function');
    });

    it('should export checkAuthStatus thunk', () => {
      expect(checkAuthStatus).toBeDefined();
      expect(typeof checkAuthStatus).toBe('function');
    });
  });
});