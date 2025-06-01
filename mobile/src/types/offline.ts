import { Profile } from './profile';

export interface OfflineProfile extends Profile {
  offlineId: string;
  encryptedData?: string;
  hashedId: string;
  lastSyncTimestamp: number;
  verificationToken: string;
  expiryTimestamp: number;
}

export interface PendingSyncAction {
  id: string;
  timestamp: number;
  type: SyncActionType;
  entityId: string;
  entityType: EntityType;
  data: any;
  priority: 'high' | 'medium' | 'low';
  attempts: number;
  lastAttemptTimestamp?: number;
}

export type SyncActionType = 
  | 'create' 
  | 'update' 
  | 'delete' 
  | 'verify' 
  | 'scan' 
  | 'attendance';

export type EntityType = 
  | 'profile' 
  | 'scan' 
  | 'attendance' 
  | 'verification';