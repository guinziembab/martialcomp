import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { offlineService } from '@services/offlineService';
import { RootState } from '@store/index';
import { OfflineProfile, PendingSyncAction } from '@types/offline';

interface OfflineState {
  isOfflineMode: boolean;
  offlineProfiles: OfflineProfile[];
  pendingSync: PendingSyncAction[];
  lastSyncTimestamp: number | null;
  isSyncing: boolean;
  error: string | null;
}

const initialState: OfflineState = {
  isOfflineMode: false,
  offlineProfiles: [],
  pendingSync: [],
  lastSyncTimestamp: null,
  isSyncing: false,
  error: null,
};

// Async thunks
export const syncOfflineData = createAsyncThunk(
  'offline/sync',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;
      const pendingActions = state.offline.pendingSync;
      
      if (!token) {
        throw new Error('No authentication token available');
      }
      
      if (pendingActions.length === 0) {
        return { 
          timestamp: Date.now(),
          syncedCount: 0
        };
      }
      
      const result = await offlineService.syncPendingActions(token, pendingActions);
      
      // Clear pending actions from storage
      await AsyncStorage.setItem('@offline_pending_sync', JSON.stringify([]));
      
      return {
        timestamp: Date.now(),
        syncedCount: result.syncedCount,
        failedCount: result.failedCount,
      };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to sync offline data');
    }
  }
);

export const downloadOfflineProfiles = createAsyncThunk(
  'offline/downloadProfiles',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;
      
      if (!token) {
        throw new Error('No authentication token available');
      }
      
      const profiles = await offlineService.getOfflineProfiles(token);
      
      // Store profiles in local storage
      await AsyncStorage.setItem('@offline_profiles', JSON.stringify(profiles));
      
      return profiles;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to download offline profiles');
    }
  }
);

export const loadOfflineState = createAsyncThunk(
  'offline/loadState',
  async (_, { rejectWithValue }) => {
    try {
      // Load offline profiles
      const profilesJson = await AsyncStorage.getItem('@offline_profiles');
      const profiles = profilesJson ? JSON.parse(profilesJson) : [];
      
      // Load pending sync actions
      const pendingSyncJson = await AsyncStorage.getItem('@offline_pending_sync');
      const pendingSync = pendingSyncJson ? JSON.parse(pendingSyncJson) : [];
      
      // Load last sync timestamp
      const lastSyncStr = await AsyncStorage.getItem('@offline_last_sync');
      const lastSync = lastSyncStr ? parseInt(lastSyncStr, 10) : null;
      
      return {
        profiles,
        pendingSync,
        lastSync,
      };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to load offline state');
    }
  }
);

export const addPendingSyncAction = createAsyncThunk(
  'offline/addPendingAction',
  async (action: PendingSyncAction, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const pendingActions = [...state.offline.pendingSync, action];
      
      // Store updated pending actions
      await AsyncStorage.setItem('@offline_pending_sync', JSON.stringify(pendingActions));
      
      return action;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to add pending sync action');
    }
  }
);

const offlineSlice = createSlice({
  name: 'offline',
  initialState,
  reducers: {
    setOfflineMode: (state, action: PayloadAction<boolean>) => {
      state.isOfflineMode = action.payload;
    },
    clearOfflineData: (state) => {
      state.offlineProfiles = [];
      state.pendingSync = [];
      state.lastSyncTimestamp = null;
    },
  },
  extraReducers: (builder) => {
    // Sync Offline Data
    builder.addCase(syncOfflineData.pending, (state) => {
      state.isSyncing = true;
      state.error = null;
    });
    builder.addCase(syncOfflineData.fulfilled, (state, action) => {
      state.isSyncing = false;
      state.lastSyncTimestamp = action.payload.timestamp;
      state.pendingSync = [];
    });
    builder.addCase(syncOfflineData.rejected, (state, action) => {
      state.isSyncing = false;
      state.error = action.payload as string;
    });
    
    // Download Offline Profiles
    builder.addCase(downloadOfflineProfiles.pending, (state) => {
      state.isSyncing = true;
      state.error = null;
    });
    builder.addCase(downloadOfflineProfiles.fulfilled, (state, action) => {
      state.isSyncing = false;
      state.offlineProfiles = action.payload;
      state.lastSyncTimestamp = Date.now();
    });
    builder.addCase(downloadOfflineProfiles.rejected, (state, action) => {
      state.isSyncing = false;
      state.error = action.payload as string;
    });
    
    // Load Offline State
    builder.addCase(loadOfflineState.fulfilled, (state, action) => {
      state.offlineProfiles = action.payload.profiles;
      state.pendingSync = action.payload.pendingSync;
      state.lastSyncTimestamp = action.payload.lastSync;
    });
    
    // Add Pending Sync Action
    builder.addCase(addPendingSyncAction.fulfilled, (state, action) => {
      state.pendingSync.push(action.payload);
    });
  },
});

export const { setOfflineMode, clearOfflineData } = offlineSlice.actions;
export default offlineSlice.reducer;