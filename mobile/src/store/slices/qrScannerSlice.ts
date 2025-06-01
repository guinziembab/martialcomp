import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { qrScannerService } from '@services/qrScannerService';
import { RootState } from '@store/index';
import { ScanResult, OfflineProfileData } from '@types/qrScanner';

interface QRScannerState {
  scannedData: string | null;
  scanHistory: ScanResult[];
  isScanning: boolean;
  isProcessing: boolean;
  error: string | null;
  lastScanResult: ScanResult | null;
  scanType: string | null;
  eventId: string | null;
  currentProfile: OfflineProfileData | null;
  pendingOfflineScans: ScanResult[];
}

const initialState: QRScannerState = {
  scannedData: null,
  scanHistory: [],
  isScanning: false,
  isProcessing: false,
  error: null,
  lastScanResult: null,
  scanType: null,
  eventId: null,
  currentProfile: null,
  pendingOfflineScans: [],
};

interface ProcessQRParams {
  qrData: string;
  scanType?: string;
  eventId?: string;
}

// Async thunks
export const processQRCode = createAsyncThunk(
  'qrScanner/process',
  async ({ qrData, scanType, eventId }: ProcessQRParams, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;
      
      if (!token) {
        throw new Error('No authentication token available');
      }
      
      const result = await qrScannerService.processQRCode(token, qrData, scanType, eventId);
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to process QR code');
    }
  }
);

export const verifyOfflineQRCode = createAsyncThunk(
  'qrScanner/verifyOffline',
  async ({ qrData, scanType, eventId }: ProcessQRParams, { rejectWithValue }) => {
    try {
      const result = await qrScannerService.verifyOfflineQRCode(qrData, scanType, eventId);
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to verify offline QR code');
    }
  }
);

export const getOfflineProfile = createAsyncThunk(
  'qrScanner/getOfflineProfile',
  async (practitionerId: string, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;
      
      if (!token) {
        throw new Error('No authentication token available');
      }
      
      const profileData = await qrScannerService.getOfflineProfile(token, practitionerId);
      return profileData;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to get offline profile');
    }
  }
);

export const verifyOfflineProfile = createAsyncThunk(
  'qrScanner/verifyOfflineProfile',
  async (profileToken: string, { rejectWithValue }) => {
    try {
      const result = await qrScannerService.verifyOfflineProfile(profileToken);
      if (!result.valid) {
        return rejectWithValue(result.reason || 'Invalid profile token');
      }
      return result.profile;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to verify offline profile');
    }
  }
);

export const syncOfflineScans = createAsyncThunk(
  'qrScanner/syncOfflineScans',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;
      
      if (!token) {
        throw new Error('No authentication token available');
      }
      
      const pendingScans = (getState() as RootState).qrScanner.pendingOfflineScans;
      if (pendingScans.length === 0) {
        return { synced: 0, ignored: 0 };
      }
      
      // Convert scans to the format expected by the API
      const scansToSync = pendingScans.map(scan => ({
        id: scan.id,
        timestamp: scan.timestamp,
        scan_type: scan.type,
        data: scan.data,
        offline_scan_id: scan.id,
      }));
      
      const result = await qrScannerService.syncOfflineScans(token, scansToSync);
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to sync offline scans');
    }
  }
);

const qrScannerSlice = createSlice({
  name: 'qrScanner',
  initialState,
  reducers: {
    setScanning: (state, action: PayloadAction<boolean>) => {
      state.isScanning = action.payload;
    },
    setScannedData: (state, action: PayloadAction<string | null>) => {
      state.scannedData = action.payload;
    },
    setScanType: (state, action: PayloadAction<string | null>) => {
      state.scanType = action.payload;
    },
    setEventId: (state, action: PayloadAction<string | null>) => {
      state.eventId = action.payload;
    },
    clearScanResult: (state) => {
      state.scannedData = null;
      state.lastScanResult = null;
      state.error = null;
    },
    clearScanHistory: (state) => {
      state.scanHistory = [];
    },
    addOfflineScan: (state, action: PayloadAction<ScanResult>) => {
      // Add to pending offline scans
      state.pendingOfflineScans.push(action.payload);
      
      // Also add to scan history
      state.scanHistory.unshift(action.payload);
      
      // Keep history limited to last 50 scans
      if (state.scanHistory.length > 50) {
        state.scanHistory = state.scanHistory.slice(0, 50);
      }
    },
    clearPendingOfflineScans: (state) => {
      state.pendingOfflineScans = [];
    },
    removePendingOfflineScan: (state, action: PayloadAction<string>) => {
      state.pendingOfflineScans = state.pendingOfflineScans.filter(scan => scan.id !== action.payload);
    },
  },
  extraReducers: (builder) => {
    // Process QR Code
    builder.addCase(processQRCode.pending, (state) => {
      state.isProcessing = true;
      state.error = null;
    });
    builder.addCase(processQRCode.fulfilled, (state, action: PayloadAction<ScanResult>) => {
      state.isProcessing = false;
      state.lastScanResult = action.payload;
      state.scanHistory.unshift(action.payload);
      
      // Keep history limited to last 50 scans
      if (state.scanHistory.length > 50) {
        state.scanHistory = state.scanHistory.slice(0, 50);
      }
    });
    builder.addCase(processQRCode.rejected, (state, action) => {
      state.isProcessing = false;
      state.error = action.payload as string;
    });
    
    // Verify Offline QR Code
    builder.addCase(verifyOfflineQRCode.pending, (state) => {
      state.isProcessing = true;
      state.error = null;
    });
    builder.addCase(verifyOfflineQRCode.fulfilled, (state, action: PayloadAction<ScanResult>) => {
      state.isProcessing = false;
      state.lastScanResult = action.payload;
      
      // Add to scan history
      state.scanHistory.unshift({
        ...action.payload,
        isOffline: true,
      });
      
      // Also add to pending offline scans for later sync
      state.pendingOfflineScans.push({
        ...action.payload,
        isOffline: true,
      });
      
      // Keep history limited to last 50 scans
      if (state.scanHistory.length > 50) {
        state.scanHistory = state.scanHistory.slice(0, 50);
      }
    });
    builder.addCase(verifyOfflineQRCode.rejected, (state, action) => {
      state.isProcessing = false;
      state.error = action.payload as string;
    });
    
    // Get Offline Profile
    builder.addCase(getOfflineProfile.pending, (state) => {
      state.isProcessing = true;
      state.error = null;
    });
    builder.addCase(getOfflineProfile.fulfilled, (state, action: PayloadAction<OfflineProfileData>) => {
      state.isProcessing = false;
      state.currentProfile = action.payload;
    });
    builder.addCase(getOfflineProfile.rejected, (state, action) => {
      state.isProcessing = false;
      state.error = action.payload as string;
    });
    
    // Verify Offline Profile
    builder.addCase(verifyOfflineProfile.pending, (state) => {
      state.isProcessing = true;
      state.error = null;
    });
    builder.addCase(verifyOfflineProfile.fulfilled, (state, action: PayloadAction<OfflineProfileData>) => {
      state.isProcessing = false;
      state.currentProfile = action.payload;
    });
    builder.addCase(verifyOfflineProfile.rejected, (state, action) => {
      state.isProcessing = false;
      state.error = action.payload as string;
    });
    
    // Sync Offline Scans
    builder.addCase(syncOfflineScans.pending, (state) => {
      state.isProcessing = true;
      state.error = null;
    });
    builder.addCase(syncOfflineScans.fulfilled, (state) => {
      state.isProcessing = false;
      state.pendingOfflineScans = [];
    });
    builder.addCase(syncOfflineScans.rejected, (state, action) => {
      state.isProcessing = false;
      state.error = action.payload as string;
    });
  },
});

export const { 
  setScanning, 
  setScannedData, 
  setScanType,
  setEventId,
  clearScanResult, 
  clearScanHistory,
  addOfflineScan,
  clearPendingOfflineScans,
  removePendingOfflineScan
} = qrScannerSlice.actions;

export default qrScannerSlice.reducer;