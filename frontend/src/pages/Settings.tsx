import { useState, useEffect } from 'react'
import { useConfig } from '../contexts/ConfigContext'
import { CredentialsForm } from '../components/aws/CredentialsForm'
import { BucketSelector } from '../components/aws/BucketSelector'
import { api } from '../api/client'

type StorageProviderType = 'aws' | 'storj';

export function Settings() {
  const { config, updateConfig } = useConfig()
  const [storageProvider, setStorageProvider] = useState<StorageProviderType>(
    (config.storage_provider as StorageProviderType) || 'aws'
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Initialize storage provider state from config
    if (config.storage_provider) {
      setStorageProvider(config.storage_provider as StorageProviderType)
    }
  }, [config.storage_provider])

  const handleStorageProviderChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newProvider = e.target.value as StorageProviderType
    setStorageProvider(newProvider)
    
    try {
      setLoading(true)
      setError(null)
      
      // Update the config with the new storage provider
      const updatedConfig = {
        ...config,
        storage_provider: newProvider
      }
      
      const response = await api.updateConfig(updatedConfig)
      
      if (response.error) {
        setError(response.error)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update storage provider')
    } finally {
      setLoading(false)
    }
  }

  const getProviderLabel = () => {
    return storageProvider === 'storj' ? 'Storj' : 'AWS'
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Storage Provider</h2>
        <div className="flex items-center space-x-4 mb-4">
          <label className="w-32 font-medium" htmlFor="storage-provider">Provider:</label>
          <select 
            id="storage-provider"
            value={storageProvider}
            onChange={handleStorageProviderChange}
            className="px-3 py-2 border rounded-md w-64"
            disabled={loading}
          >
            <option value="aws">Amazon S3</option>
            <option value="storj">Storj DCS</option>
          </select>
          {loading && <span className="ml-2">Updating...</span>}
        </div>
        {error && <div className="text-red-500 mt-2">{error}</div>}
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">{getProviderLabel()} Configuration</h2>
        <CredentialsForm storageProvider={storageProvider} />
      </div>
    </div>
  )
}
