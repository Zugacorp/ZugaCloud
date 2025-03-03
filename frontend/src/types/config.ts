export interface Config {
  aws_access_key: string;
  aws_secret_key: string;
  region: string;
  refresh_frequency: number;
  sync_folder?: string;
  bucket_name: string;
  prefer_env_vars?: boolean;
  storage_provider?: 'aws' | 'storj';
  
  // Storj-specific properties
  storj_access_key?: string;
  storj_secret_key?: string;
  storj_endpoint?: string;
}

export interface AWSCredentials {
  aws_access_key: string;
  aws_secret_key: string;
  aws_region: string;
}

export interface StorjCredentials {
  storj_access_key: string;
  storj_secret_key: string;
  storj_endpoint?: string;
}

export interface AWSError {
  code: string;
  message: string;
  details?: any;
}

export interface ValidationResponse {
  valid: boolean;
  message?: string;
  error?: AWSError;
}
