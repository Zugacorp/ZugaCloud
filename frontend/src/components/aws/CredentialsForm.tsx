import { useState, useEffect } from 'react'
import { useConfig } from '../../contexts/ConfigContext'
import { api } from '../../api/client'
import type { AWSCredentials, StorjCredentials } from '../../types/config'

interface CredentialsFormProps {
  storageProvider?: string;
}

export function CredentialsForm({ storageProvider = 'aws' }: CredentialsFormProps) {
  const { config } = useConfig()
  const [preferEnvVars, setPreferEnvVars] = useState(false)
  const [awsCredentials, setAwsCredentials] = useState<AWSCredentials>({
    aws_access_key: '',
    aws_secret_key: '',
    aws_region: '',
  })
  const [storjCredentials, setStorjCredentials] = useState<StorjCredentials>({
    storj_access_key: '',
    storj_secret_key: '',
    storj_endpoint: 'https://gateway.eu1.storjshare.io',
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const isStorj = storageProvider === 'storj'
  
  // Get provider label for UI
  const getProviderLabel = () => isStorj ? 'Storj' : 'AWS'

  useEffect(() => {
    loadCredentialSource()
  }, [storageProvider])

  const loadCredentialSource = async () => {
    try {
      setLoading(true)
      const [sourceResponse, configResponse] = await Promise.all([
        api.checkCredentialSource(),
        api.getConfig()
      ])
      setPreferEnvVars(Boolean(sourceResponse.useEnvVars))
      
      if (isStorj) {
        setStorjCredentials({
          storj_access_key: configResponse.storj_access_key || '',
          storj_secret_key: configResponse.storj_secret_key || '',
          storj_endpoint: configResponse.storj_endpoint || 'https://gateway.eu1.storjshare.io',
        })
      } else {
        setAwsCredentials({
          aws_access_key: configResponse.aws_access_key || '',
          aws_secret_key: configResponse.aws_secret_key || '',
          aws_region: configResponse.aws_region || '',
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load credential source')
    } finally {
      setLoading(false)
    }
  }

  const handleSourceChange = async (useEnv: boolean) => {
    try {
      setLoading(true)
      const response = await api.setCredentialSource({ useEnvVars: useEnv })
      setPreferEnvVars(useEnv)
      if (response.error) {
        setError(response.error)
      } else {
        setError(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update credential source')
    } finally {
      setLoading(false)
    }
  }

  const handleAwsCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      const validationResult = await api.validateCredentials(awsCredentials)
      if (!validationResult.valid) {
        setError(validationResult.error || 'Invalid credentials')
        return
      }

      const configResponse = await api.updateConfig({
        ...config,
        aws_access_key: awsCredentials.aws_access_key,
        aws_secret_key: awsCredentials.aws_secret_key,
        region: awsCredentials.aws_region,
      })

      if (configResponse.error) {
        setError(configResponse.error)
      } else {
        setError(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update credentials')
    } finally {
      setLoading(false)
    }
  }
  
  const handleStorjCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      
      // For Storj, we use a similar validation but with storj-specific params
      const validationParams = {
        storj_access_key: storjCredentials.storj_access_key,
        storj_secret_key: storjCredentials.storj_secret_key,
        storj_endpoint: storjCredentials.storj_endpoint,
        storage_provider: 'storj' // Important: tell the backend to validate as Storj
      }
      
      const validationResult = await api.validateCredentials(validationParams)
      if (!validationResult.valid) {
        setError(validationResult.error || 'Invalid Storj credentials')
        return
      }

      const configResponse = await api.updateConfig({
        ...config,
        storj_access_key: storjCredentials.storj_access_key,
        storj_secret_key: storjCredentials.storj_secret_key,
        storj_endpoint: storjCredentials.storj_endpoint,
        storage_provider: 'storj'
      })

      if (configResponse.error) {
        setError(configResponse.error)
      } else {
        setError(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update Storj credentials')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h2>{getProviderLabel()} Credentials</h2>
      <div>
        <label>
          <input
            type="radio"
            checked={!preferEnvVars}
            onChange={() => handleSourceChange(false)}
          />
          Use manual credentials
        </label>
        <label>
          <input
            type="radio"
            checked={preferEnvVars}
            onChange={() => handleSourceChange(true)}
          />
          Use environment variables
        </label>
      </div>

      {!preferEnvVars && !isStorj && (
        <form onSubmit={handleAwsCredentialsSubmit}>
          <div>
            <label>Access Key ID:</label>
            <input
              type="text"
              value={awsCredentials.aws_access_key}
              onChange={(e) =>
                setAwsCredentials({ ...awsCredentials, aws_access_key: e.target.value })
              }
            />
          </div>
          <div>
            <label>Secret Access Key:</label>
            <input
              type="password"
              value={awsCredentials.aws_secret_key}
              onChange={(e) =>
                setAwsCredentials({ ...awsCredentials, aws_secret_key: e.target.value })
              }
            />
          </div>
          <div>
            <label>Region:</label>
            <input
              type="text"
              value={awsCredentials.aws_region}
              onChange={(e) =>
                setAwsCredentials({ ...awsCredentials, aws_region: e.target.value })
              }
            />
          </div>
          <button type="submit" disabled={loading}>
            Save AWS Credentials
          </button>
        </form>
      )}
      
      {!preferEnvVars && isStorj && (
        <form onSubmit={handleStorjCredentialsSubmit}>
          <div>
            <label>Storj Access Key:</label>
            <input
              type="text"
              value={storjCredentials.storj_access_key}
              onChange={(e) =>
                setStorjCredentials({ ...storjCredentials, storj_access_key: e.target.value })
              }
            />
          </div>
          <div>
            <label>Storj Secret Key:</label>
            <input
              type="password"
              value={storjCredentials.storj_secret_key}
              onChange={(e) =>
                setStorjCredentials({ ...storjCredentials, storj_secret_key: e.target.value })
              }
            />
          </div>
          <div>
            <label>Storj Endpoint:</label>
            <input
              type="text"
              value={storjCredentials.storj_endpoint}
              onChange={(e) =>
                setStorjCredentials({ ...storjCredentials, storj_endpoint: e.target.value })
              }
            />
            <small>Default: https://gateway.eu1.storjshare.io</small>
          </div>
          <button type="submit" disabled={loading}>
            Save Storj Credentials
          </button>
        </form>
      )}

      {error && <div className="error">{error}</div>}
    </div>
  )
}
