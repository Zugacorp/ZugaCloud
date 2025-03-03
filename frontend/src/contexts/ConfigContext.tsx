import React, { createContext, useContext, useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import type { Config, AWSCredentials } from '../types/config'
import { api } from '../api/client'

// Error types
export class ConfigError extends Error {
  constructor(message: string, public code: string) {
    super(message)
    this.name = 'ConfigError'
  }
}

export class ValidationError extends ConfigError {
  constructor(message: string) {
    super(message, 'VALIDATION_ERROR')
  }
}

export class StorageError extends ConfigError {
  constructor(message: string) {
    super(message, 'STORAGE_ERROR')
  }
}

// Loading states
interface LoadingState {
  isLoading: boolean
  operation: string | null
}

// Context type
interface ConfigContextType {
  config: Config
  loading: LoadingState
  error: ConfigError | null
  isConfigured: boolean
  updateConfig: (newConfig: Partial<Config>) => Promise<void>
  validateConfig: (config: Partial<Config>) => Promise<boolean>
  clearError: () => void
  reloadConfig: () => Promise<void>
}

const defaultConfig: Config = {
  aws_access_key: '',
  aws_secret_key: '',
  region: 'us-east-1',
  refresh_frequency: 300,
  sync_folder: '',
  bucket_name: '',
  prefer_env_vars: false
}

const ConfigContext = createContext<ConfigContextType>({
  config: defaultConfig,
  loading: { isLoading: false, operation: null },
  error: null,
  isConfigured: false,
  updateConfig: async () => {},
  validateConfig: async () => false,
  clearError: () => {},
  reloadConfig: async () => {}
})

export const useConfig = () => useContext(ConfigContext)

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<Config>(defaultConfig)
  const [loading, setLoading] = useState<LoadingState>({ isLoading: false, operation: null })
  const [error, setError] = useState<ConfigError | null>(null)

  const clearError = () => setError(null)

  const handleConfigError = (error: unknown, customMessage?: string) => {
    console.error('Config error:', error)
    
    let configError: ConfigError
    if (error instanceof ConfigError) {
      configError = error
    } else if (error instanceof Error) {
      configError = new ConfigError(error.message, 'UNKNOWN_ERROR')
    } else {
      configError = new ConfigError(customMessage || 'An unknown error occurred', 'UNKNOWN_ERROR')
    }
    
    setError(configError)
    toast.error(configError.message)
    return configError
  }

  const validateConfig = async (configToValidate: Partial<Config>): Promise<boolean> => {
    try {
      clearError()
      setLoading({ isLoading: true, operation: 'validating' })

      // Validate sync folder
      if (configToValidate.sync_folder) {
        const folderExists = await api.checkLocalFile(configToValidate.sync_folder)
        if (!folderExists) {
          throw new ValidationError('Sync folder does not exist')
        }
      }

      // Validate AWS credentials if provided
      if (configToValidate.aws_access_key || configToValidate.aws_secret_key) {
        const credentials: AWSCredentials = {
          aws_access_key: configToValidate.aws_access_key || config.aws_access_key || '',
          aws_secret_key: configToValidate.aws_secret_key || config.aws_secret_key || '',
          aws_region: configToValidate.region || config.region || 'us-east-1'
        }
        
        const validationResult = await api.validateCredentials(credentials)
        if (!validationResult.valid) {
          throw new ValidationError(validationResult.error || 'Invalid AWS credentials')
        }
      }

      return true
    } catch (error) {
      handleConfigError(error, 'Configuration validation failed')
      return false
    } finally {
      setLoading({ isLoading: false, operation: null })
    }
  }

  const loadConfig = async () => {
    try {
      clearError()
      setLoading({ isLoading: true, operation: 'loading' })
      const data = await api.getConfig()
      setConfig(data)
    } catch (error) {
      handleConfigError(error, 'Failed to load configuration')
    } finally {
      setLoading({ isLoading: false, operation: null })
    }
  }

  const updateConfig = async (newConfig: Partial<Config>) => {
    try {
      clearError()
      setLoading({ isLoading: true, operation: 'updating' })

      // Validate new configuration
      const isValid = await validateConfig(newConfig)
      if (!isValid) {
        throw new ValidationError('Invalid configuration')
      }

      // Update configuration
      const updatedConfig = await api.updateConfig({ ...config, ...newConfig })
      setConfig(updatedConfig)
      toast.success('Configuration updated successfully')
    } catch (error) {
      const configError = handleConfigError(error, 'Failed to update configuration')
      throw configError
    } finally {
      setLoading({ isLoading: false, operation: null })
    }
  }

  // Initial load
  useEffect(() => {
    loadConfig()
  }, [])

  const isConfigured = Boolean(config.sync_folder && config.bucket_name)

  const value = {
    config,
    loading,
    error,
    isConfigured,
    updateConfig,
    validateConfig,
    clearError,
    reloadConfig: loadConfig
  }

  return (
    <ConfigContext.Provider value={value}>
      {children}
    </ConfigContext.Provider>
  )
} 