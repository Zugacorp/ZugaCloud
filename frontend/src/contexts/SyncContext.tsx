import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import { SyncState, SyncOperations } from '../types/sync';
import { useConfig } from '../hooks/useConfig';

interface SyncContextType extends SyncOperations {
  syncState: SyncState;
}

export const SyncContext = createContext<SyncContextType | undefined>(undefined);

export const SyncProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { config } = useConfig();
  const [syncState, setSyncState] = useState<SyncState>({
    type: 'status',
    message: 'Ready to upload files to S3'
  });

  const refreshFiles = useCallback(async () => {
    try {
      window.location.reload();
    } catch (error) {
      console.error('Error refreshing files:', error);
    }
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (syncState.type === 'progress') {
      interval = setInterval(async () => {
        try {
          const response = await fetch('/api/sync/status');
          const status = await response.json();
          
          console.log('Sync status:', status);
          
          if (status.type === 'completed') {
            setSyncState({
              type: 'completed',
              message: 'Sync completed successfully',
              progress: 100,
              details: {
                currentFile: undefined,
                progress: '100%',
                size: undefined
              }
            });
            
            clearInterval(interval);
            
            setTimeout(() => {
              setSyncState({
                type: 'status',
                message: 'Ready to upload files to S3'
              });
              window.location.reload();
            }, 2000);
            
            return;
          }
          
          if (status.type === 'progress') {
            setSyncState(status);
          }
        } catch (error) {
          console.error('Error polling sync status:', error);
        }
      }, 500);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [syncState.type]);

  const startSync = async () => {
    if (!config.sync_folder || !config.bucket_name) {
      throw new Error('Sync folder and bucket must be configured');
    }
    try {
      setSyncState({ type: 'progress', message: 'Starting sync...', progress: 0 });
      await api.startSync(config.sync_folder, config.bucket_name);
    } catch (error) {
      setSyncState({ 
        type: 'error', 
        message: error instanceof Error ? error.message : 'Failed to start sync' 
      });
      throw error;
    }
  };

  const stopSync = async () => {
    try {
      await api.stopSync();
      setSyncState({ type: 'status', message: 'Sync stopped' });
    } catch (error) {
      setSyncState({ 
        type: 'error', 
        message: error instanceof Error ? error.message : 'Failed to stop sync' 
      });
      throw error;
    }
  };

  return (
    <SyncContext.Provider value={{ syncState, startSync, stopSync }}>
      {children}
    </SyncContext.Provider>
  );
};

export const useSync = () => {
  const context = useContext(SyncContext);
  if (!context) {
    throw new Error('useSync must be used within a SyncProvider');
  }
  return context;
};
