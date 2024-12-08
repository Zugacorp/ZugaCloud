export type SyncMessageDetails = {
  currentFile?: string;
  bucket?: string;
  progress?: string;
  size?: string;
  totalFiles?: number;
  totalSize?: string;
  filesScanned?: number;
  filesToSync?: number;
};

export type SyncMessage = {
  message: string;
  details?: SyncMessageDetails;
} | string;

export type SyncStateType = 'status' | 'progress' | 'completed' | 'error';

export type SyncState = {
  type: SyncStateType;
  message: SyncMessage;
  progress?: number;
  details?: SyncMessageDetails;
};

export type SyncStatus = {
  state?: 'idle' | 'scanning' | 'syncing' | 'completed' | 'error';
  type: SyncStateType;
  message: SyncMessage;
  progress?: number;
  details?: SyncMessageDetails;
};

export interface SyncOperations {
  startSync: () => Promise<void>;
  stopSync: () => Promise<void>;
} 