import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'

interface Config {
  bucket_name?: string
  region?: string
  identity_pool_id?: string
  user_pool_id?: string
  client_id?: string
  cognito_domain?: string
  redirect_sign_in?: string
  redirect_sign_out?: string
  api_url?: string
  [key: string]: string | undefined
}

const loadEnvConfig = () => {
  const envConfig: Config = {
    bucket_name: import.meta.env.VITE_BUCKET_NAME,
    region: import.meta.env.VITE_AWS_REGION,
    identity_pool_id: import.meta.env.VITE_IDENTITY_POOL_ID,
    user_pool_id: import.meta.env.VITE_COGNITO_USER_POOL_ID,
    client_id: import.meta.env.VITE_COGNITO_CLIENT_ID,
    cognito_domain: import.meta.env.VITE_COGNITO_DOMAIN,
    redirect_sign_in: import.meta.env.VITE_REDIRECT_SIGN_IN,
    redirect_sign_out: import.meta.env.VITE_REDIRECT_SIGN_OUT,
    api_url: import.meta.env.VITE_API_URL
  }

  return envConfig
}

export function useConfig() {
  const [config, setConfig] = useState<Config>(loadEnvConfig())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const validateConfig = async () => {
      try {
        console.log('Validating configuration...')
        
        // Log Cognito configuration
        console.log('Cognito Configuration:', {
          userPoolId: config.user_pool_id,
          clientId: config.client_id,
          domain: config.cognito_domain,
          region: config.region,
          redirectSignIn: config.redirect_sign_in,
          redirectSignOut: config.redirect_sign_out
        })

        // Validate required configuration
        const requiredFields = ['region', 'identity_pool_id', 'user_pool_id', 'client_id', 'cognito_domain'] as const
        const missingFields = requiredFields.filter(field => !config[field])

        if (missingFields.length > 0) {
          throw new Error(`Missing required configuration: ${missingFields.join(', ')}`)
        }

        setError(null)
      } catch (err) {
        console.error('Config validation error:', err)
        setError(err instanceof Error ? err : new Error('Failed to validate configuration'))
        toast.error('Failed to load application configuration')
      } finally {
        setLoading(false)
      }
    }

    validateConfig()
  }, [config])

  return {
    config,
    loading,
    error,
    isConfigured: !loading && !error && Object.keys(config).length > 0
  }
}
