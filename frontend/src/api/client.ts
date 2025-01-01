export interface ApiClient {
  // Configuration methods
  getConfig: () => Promise<any>
  updateConfig: (config: any) => Promise<any>
  validateCredentials: (credentials: any) => Promise<any>
  checkCredentialSource: () => Promise<any>
  setCredentialSource: (options: { useEnvVars: boolean }) => Promise<any>

  // File system methods
  listFiles: (path: string, bucketName: string) => Promise<any>
  checkLocalFile: (path: string) => Promise<boolean>
  deleteLocalFile: (path: string) => Promise<void>
  deleteS3Object: (path: string) => Promise<void>
  getPresignedUrl: (path: string) => Promise<string>
  selectFolder: (path: string) => Promise<any>

  // AWS methods
  listBuckets: () => Promise<any>

  // Sync methods
  startSync: (syncFolder: string, bucketName: string) => Promise<void>
  stopSync: () => Promise<void>
}

// Create a mock API client for development
export const api: ApiClient = {
  getConfig: async () => ({}),
  updateConfig: async () => ({}),
  validateCredentials: async () => ({}),
  checkCredentialSource: async () => ({}),
  setCredentialSource: async () => ({}),
  listFiles: async () => ({ files: [] }),
  checkLocalFile: async () => false,
  deleteLocalFile: async () => {},
  deleteS3Object: async () => {},
  getPresignedUrl: async () => '',
  selectFolder: async () => ({}),
  listBuckets: async () => ({ buckets: [] }),
  startSync: async () => {},
  stopSync: async () => {},
}
