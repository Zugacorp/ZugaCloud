import { useState, useEffect } from 'react'
import { useConfig } from '../../contexts/ConfigContext'
import { api } from '../../api/client'

interface Bucket {
  Name: string
  CreationDate: string
}

export function BucketSelector() {
  const { config } = useConfig()
  const [buckets, setBuckets] = useState<Bucket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadBuckets()
  }, [])

  const loadBuckets = async () => {
    try {
      setLoading(true)
      const data = await api.listBuckets()
      setBuckets(data.buckets)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load buckets')
    } finally {
      setLoading(false)
    }
  }

  const handleBucketSelect = async (bucketName: string) => {
    try {
      setLoading(true)
      await api.updateConfig({
        ...config,
        bucket_name: bucketName,
      })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to select bucket')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h2>Select S3 Bucket</h2>
      {error && <div className="error">{error}</div>}
      <select
        value={config.bucket_name || ''}
        onChange={(e) => handleBucketSelect(e.target.value)}
        disabled={loading}
      >
        <option value="">Select a bucket</option>
        {buckets.map((bucket) => (
          <option key={bucket.Name} value={bucket.Name}>
            {bucket.Name}
          </option>
        ))}
      </select>
    </div>
  )
}
