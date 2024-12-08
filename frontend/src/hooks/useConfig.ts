import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Config } from '../types/index';

interface UseConfigReturn {
  config: Config;
  updateConfig: (newConfig: Partial<Config>) => Promise<Config>;
  loading: boolean;
  error: Error | null;
}

export const useConfig = (): UseConfigReturn => {
  const [config, setConfig] = useState<Config>({
    bucket_name: 'zugaarchive',
    aws_access_key: '',
    aws_secret_key: '',
    region: 'us-east-2',
    refresh_frequency: 300,
    sync_folder: ''
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadConfig = async () => {
    try {
      console.log('Loading config...');
      setLoading(true);
      const data = await api.getConfig();
      console.log('Config loaded:', data);
      
      // Preserve AWS credentials if they exist in current config
      setConfig(prevConfig => ({
        ...prevConfig,
        ...data,
        aws_access_key: data.aws_access_key || prevConfig.aws_access_key,
        aws_secret_key: data.aws_secret_key || prevConfig.aws_secret_key,
        bucket_name: data.bucket_name || 'zugaarchive'
      }));
    } catch (err) {
      console.error('Config load error:', err);
      setError(err instanceof Error ? err : new Error('Failed to load config'));
    } finally {
      setLoading(false);
    }
  };

  const updateConfig = async (newConfig: Partial<Config>): Promise<Config> => {
    try {
      // Preserve existing AWS credentials if not explicitly being updated
      const updatedConfig = await api.updateConfig({
        ...config,
        ...newConfig,
        aws_access_key: newConfig.aws_access_key ?? config.aws_access_key,
        aws_secret_key: newConfig.aws_secret_key ?? config.aws_secret_key
      });

      setConfig(prev => ({ 
        ...prev, 
        ...updatedConfig,
        // Ensure we don't lose AWS credentials during updates
        aws_access_key: updatedConfig.aws_access_key || prev.aws_access_key,
        aws_secret_key: updatedConfig.aws_secret_key || prev.aws_secret_key,
        sync_folder: updatedConfig.sync_folder || prev.sync_folder
      }));

      return updatedConfig;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to update config'));
      throw err;
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  return {
    config,
    updateConfig,
    loading,
    error
  };
};
