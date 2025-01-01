import { useState, useEffect } from 'react'
import { useConfig } from '../../contexts/ConfigContext'
import { api } from '../../api/client'
import type { AWSCredentials } from '../../types/index'

export function CredentialsForm() {
  const { config } = useConfig()
  const [preferEnvVars, setPreferEnvVars] = useState(false)
  const [credentials, setCredentials] = useState<AWSCredentials>({
    aws_access_key_id: '',
    aws_secret_access_key: '',
    aws_region: '',
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadCredentialSource()
  }, [])

  const loadCredentialSource = async () => {
    try {
      setLoading(true)
      const [sourceResponse, configResponse] = await Promise.all([
        api.checkCredentialSource(),
        api.getConfig()
      ])
      setPreferEnvVars(Boolean(sourceResponse.useEnvVars))
      setCredentials({
        aws_access_key_id: configResponse.aws_access_key_id || '',
        aws_secret_access_key: configResponse.aws_secret_access_key || '',
        aws_region: configResponse.aws_region || '',
      })
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

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      const validationResult = await api.validateCredentials(credentials)
      if (!validationResult.valid) {
        setError(validationResult.error || 'Invalid credentials')
        return
      }

      const configResponse = await api.updateConfig({
        ...config,
        ...credentials,
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

  if (loading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h2>AWS Credentials</h2>
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

      {!preferEnvVars && (
        <form onSubmit={handleCredentialsSubmit}>
          <div>
            <label>Access Key ID:</label>
            <input
              type="text"
              value={credentials.aws_access_key_id}
              onChange={(e) =>
                setCredentials({ ...credentials, aws_access_key_id: e.target.value })
              }
            />
          </div>
          <div>
            <label>Secret Access Key:</label>
            <input
              type="password"
              value={credentials.aws_secret_access_key}
              onChange={(e) =>
                setCredentials({ ...credentials, aws_secret_access_key: e.target.value })
              }
            />
          </div>
          <div>
            <label>Region:</label>
            <input
              type="text"
              value={credentials.aws_region}
              onChange={(e) =>
                setCredentials({ ...credentials, aws_region: e.target.value })
              }
            />
          </div>
          <button type="submit" disabled={loading}>
            Save Credentials
          </button>
        </form>
      )}

      {error && <div className="error">{error}</div>}
    </div>
  )
}
