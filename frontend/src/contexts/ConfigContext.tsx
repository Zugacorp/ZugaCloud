import { createContext, useContext, useState, useEffect } from 'react'
import type { Config } from '../types/index'
import { api } from '../api/client'

interface ConfigContextType {
  config: Config
  loading: boolean
  error: Error | null
  isConfigured: boolean
  updateConfig: (newConfig: Partial<Config>) => Promise<void>
}

const ConfigContext = createContext<ConfigContextType>({
  config: { sync_folder: '', bucket_name: '' },
  loading: true,
  error: null,
  isConfigured: false,
  updateConfig: async () => {},
})

export const useConfig = () => useContext(ConfigContext)

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<Config>({ sync_folder: '', bucket_name: '' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const data = await api.getConfig()
      setConfig(data)
      setError(null)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }

  const updateConfig = async (newConfig: Partial<Config>) => {
    try {
      setLoading(true)
      const updatedConfig = await api.updateConfig({ ...config, ...newConfig })
      setConfig(updatedConfig)
      setError(null)
    } catch (err) {
      setError(err as Error)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const isConfigured = Boolean(config.sync_folder && config.bucket_name)

  return (
    <ConfigContext.Provider value={{ config, loading, error, isConfigured, updateConfig }}>
      {children}
    </ConfigContext.Provider>
  )
} 