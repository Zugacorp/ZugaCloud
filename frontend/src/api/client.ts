import { Config, AWSCredentials, SyncStatus } from '../types/index';
import { ValidationResponse } from './types';

const API_BASE = '/api';
const isElectron = Boolean(window.electronAPI);

// Browser-safe path normalization
function normalizePath(path: string): string {
  return path.replace(/\\/g, '/').replace(/\/+/g, '/');
}

export const api = {
  getConfig: async (): Promise<Config> => {
    try {
      const response = await fetch(`${API_BASE}/config`);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Config error response:', errorText);
        throw new Error('Failed to fetch config');
      }
      return response.json();
    } catch (error) {
      console.error('Config fetch error:', error);
      throw error;
    }
  },

  validateCredentials: async (credentials: AWSCredentials): Promise<ValidationResponse> => {
    try {
      const response = await fetch(`${API_BASE}/validate-credentials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Validation error response:', errorText);
        throw new Error(errorText || 'Failed to validate credentials');
      }
      
      return response.json();
    } catch (error) {
      console.error('Validation error:', error);
      throw error;
    }
  },

  listBuckets: async (): Promise<string[]> => {
    const response = await fetch(`${API_BASE}/buckets`);
    if (!response.ok) {
      throw new Error('Failed to list buckets');
    }
    return response.json();
  },

  listFiles: async (path: string, bucketName: string): Promise<any> => {
    try {
      const response = await fetch(
        `${API_BASE}/files?path=${encodeURIComponent(path)}&bucket=${encodeURIComponent(bucketName)}`
      );
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('List files error response:', errorText);
        throw new Error('Failed to list files');
      }
      
      return response.json();
    } catch (error) {
      console.error('List files error:', error);
      throw error;
    }
  },

  // Sync operations
  startSync: async (syncFolder: string, bucketName: string): Promise<SyncStatus> => {
    const response = await fetch(`${API_BASE}/sync/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        sync_folder: syncFolder, 
        bucket_name: bucketName 
      }),
    });
    if (!response.ok) {
      throw new Error('Failed to start sync');
    }
    return response.json();
  },

  stopSync: async (): Promise<SyncStatus> => {
    const response = await fetch(`${API_BASE}/sync/stop`, { 
      method: 'POST' 
    });
    if (!response.ok) {
      throw new Error('Failed to stop sync');
    }
    return response.json();
  },

  getSyncStatus: async (): Promise<SyncStatus> => {
    const response = await fetch(`${API_BASE}/sync/status`);
    if (!response.ok) {
      throw new Error('Failed to get sync status');
    }
    return response.json();
  },

  selectFolder: async (folderPath: string): Promise<{ success: boolean; error?: string }> => {
    console.log('Sending folder path to backend:', folderPath);
    
    try {
      const response = await fetch(`${API_BASE}/select-folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          path: folderPath,
          isElectron 
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        console.error('Select folder error:', data);
        return {
          success: false,
          error: data.error || 'Failed to set sync folder'
        };
      }
      
      await api.updateConfig({ sync_folder: folderPath });
      return { success: true };
    } catch (error) {
      console.error('Select folder error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to set sync folder'
      };
    }
  },

  updateConfig: async (config: Partial<Config>): Promise<Config> => {
    console.log('Updating config:', config);
    
    const response = await fetch(`${API_BASE}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to update config');
    }
    
    return response.json();
  },

  getPresignedUrl: async (filePath: string): Promise<string> => {
    try {
      const response = await fetch(
        `${API_BASE}/files/stream/${encodeURIComponent(filePath)}`
      );
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Streaming URL error response:', errorText);
        throw new Error('Failed to get streaming URL');
      }
      
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      
      return data.url;
    } catch (error) {
      console.error('Streaming URL error:', error);
      throw error;
    }
  },

  deleteLocalFile: async (path: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/files/local`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: encodeURIComponent(path) })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to delete local file');
    }
  },

  deleteS3Object: async (path: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/files/s3`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    });
    if (!response.ok) throw new Error('Failed to delete S3 object');
  },

  checkLocalFile: async (path: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/files/local/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      });
      const data = await response.json();
      return data.exists;
    } catch (error) {
      console.error('Error checking local file:', error);
      return false;
    }
  },

  checkCredentialSource: async (): Promise<{ usingEnvVars: boolean }> => {
    try {
        const response = await fetch(`${API_BASE}/check-credential-source`);
        if (!response.ok) {
            throw new Error('Failed to check credential source');
        }
        return response.json();
    } catch (error) {
        console.error('Error checking credential source:', error);
        throw error;
    }
  },

  setCredentialSource: async (params: { useEnvVars: boolean }): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/set-credential-source`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      
      if (!response.ok) {
        throw new Error('Failed to set credential source');
      }
    } catch (error) {
      console.error('Error setting credential source:', error);
      throw error;
    }
  }
};
