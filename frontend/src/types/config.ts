export interface Config {
  aws_access_key: string;
  aws_secret_key: string;
  region: string;
  refresh_frequency: number;
  sync_folder?: string;
  bucket_name: string;
  prefer_env_vars?: boolean;
}

export interface AWSCredentials {
  aws_access_key: string;
  aws_secret_key: string;
  region: string;
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
