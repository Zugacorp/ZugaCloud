import { Config, AWSCredentials } from '../types/config';

export interface Credentials {
  aws_access_key: string;
  aws_secret_key: string;
  region: string;
}

export interface ValidationResponse {
  valid: boolean;
  message?: string;
  error?: {
    code: string;
    message: string;
    requestId?: string;
  };
}

export interface ApiClient {
  getConfig: () => Promise<Config>;
  updateConfig: (config: Partial<Config>) => Promise<Config>;
  validateCredentials: (credentials: AWSCredentials) => Promise<{ success: boolean; error?: string }>;
  listBuckets: () => Promise<string[]>;
  selectFolder: (folderPath: string) => Promise<{ success: boolean; error?: string }>;
  createSyncBatch: (folderPath: string) => Promise<{ success: boolean; error?: string }>;
}
