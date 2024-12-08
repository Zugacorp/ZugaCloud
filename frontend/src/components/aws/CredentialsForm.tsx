import React, { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import { useConfig } from '../../hooks/useConfig';
import { api } from '../../api/client';

export const CredentialsForm: React.FC = () => {
  const { config, updateConfig } = useConfig();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [usingEnvVars, setUsingEnvVars] = useState(false);
  const [preferEnvVars, setPreferEnvVars] = useState(false);

  useEffect(() => {
    const checkCredentialSettings = async () => {
      try {
        const [sourceResponse, configResponse] = await Promise.all([
          api.checkCredentialSource(),
          api.getConfig()
        ]);
        
        setUsingEnvVars(sourceResponse.usingEnvVars);
        setPreferEnvVars(configResponse.prefer_env_vars || false);
      } catch (err) {
        console.error('Error checking credential settings:', err);
      }
    };
    checkCredentialSettings();
  }, []);

  const handlePreferEnvVarsChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const useEnv = e.target.checked;
    try {
      setLoading(true);
      await api.setCredentialSource({ useEnvVars: useEnv });
      setPreferEnvVars(useEnv);
      
      if (useEnv && await api.checkCredentialSource().then(r => r.usingEnvVars)) {
        window.location.reload();
      } else if (!useEnv) {
        window.location.reload();
      }
    } catch (err) {
      console.error('Error setting credential source:', err);
      setError('Failed to update credential source preference');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (preferEnvVars && usingEnvVars) {
      setError('Cannot modify credentials when using environment variables');
      return;
    }

    setError(null);
    setSuccess(false);
    setLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const credentials = {
      aws_access_key: formData.get('aws_access_key') as string,
      aws_secret_key: formData.get('aws_secret_key') as string,
      region: formData.get('region') as string || 'us-east-2'
    };

    try {
      const validationResult = await api.validateCredentials(credentials);
      
      if (!validationResult.valid) {
        throw new Error(validationResult.message || 'Invalid credentials');
      }
      
      await updateConfig(credentials);
      setSuccess(true);
      
      window.location.reload();
    } catch (err) {
      console.error('Credential update error:', err);
      setError(err instanceof Error ? err.message : 'Failed to update credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex items-center space-x-2 mb-4">
        <input
          type="checkbox"
          id="useEnvVars"
          checked={preferEnvVars}
          onChange={handlePreferEnvVarsChange}
          className="h-4 w-4 rounded border-gray-300 text-blue-500 focus:ring-blue-500"
        />
        <label htmlFor="useEnvVars" className="text-sm text-gray-300">
          Use environment variables for AWS credentials
        </label>
      </div>

      {usingEnvVars && preferEnvVars && (
        <div className="p-3 bg-blue-900/50 border border-blue-500 rounded-md text-blue-200">
          Using AWS credentials from environment variables. Form inputs are disabled.
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-900/50 border border-red-500 rounded-md text-red-200">
          {error}
        </div>
      )}
      
      {success && (
        <div className="p-3 bg-green-900/50 border border-green-500 rounded-md text-green-200">
          Credentials updated successfully!
        </div>
      )}

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">
          AWS Access Key
        </label>
        <input
          type="text"
          name="aws_access_key"
          defaultValue={config.aws_access_key || ''}
          required
          disabled={preferEnvVars && usingEnvVars}
          className="w-full px-3 py-2 bg-[#0a192f] border border-[#233554] rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">
          AWS Secret Key
        </label>
        <input
          type="password"
          name="aws_secret_key"
          defaultValue={config.aws_secret_key || ''}
          required
          disabled={preferEnvVars && usingEnvVars}
          className="w-full px-3 py-2 bg-[#0a192f] border border-[#233554] rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">
          Region
        </label>
        <input
          type="text"
          name="region"
          defaultValue={config.region || 'us-east-2'}
          required
          disabled={preferEnvVars && usingEnvVars}
          className="w-full px-3 py-2 bg-[#0a192f] border border-[#233554] rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
      </div>

      <Button
        type="submit"
        disabled={loading || (preferEnvVars && usingEnvVars)}
        className="w-full"
      >
        {loading ? 'Updating...' : 'Update Credentials'}
      </Button>
    </form>
  );
};
