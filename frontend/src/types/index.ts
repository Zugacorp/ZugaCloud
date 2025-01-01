export * from './config';
export * from './file';
export * from './sync';

export interface Config {
  sync_folder: string
  bucket_name: string
  prefer_env_vars?: boolean
  aws_access_key_id?: string
  aws_secret_access_key?: string
  aws_region?: string
}

export interface AWSCredentials {
  aws_access_key_id: string
  aws_secret_access_key: string
  aws_region: string
}

export interface SyncStatus {
  is_syncing: boolean
  last_sync: string | null
  error: string | null
}

export interface ValidationResponse {
  valid: boolean
  error?: string
}
