import { useState, useEffect } from 'react'
import { useConfig } from '../../contexts/ConfigContext'
import { api } from '../../api/client'
import { Loader2, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'

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

  const handleCreateBucket = async () => {
    // This will be implemented later - for now just show an alert
    alert('Create bucket functionality coming soon!')
  }

  if (loading) {
    return (
      <div className="flex items-center h-9 space-x-2 text-gray-400">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Loading buckets...</span>
      </div>
    )
  }

  return (
    <div className="relative">
      <div className="flex space-x-2">
        <select
          value={config.bucket_name || ''}
          onChange={(e) => handleBucketSelect(e.target.value)}
          disabled={loading}
          className="
            flex-1
            h-9
            px-3 
            bg-[#0a192f] 
            border border-[#233554] 
            rounded-md 
            text-gray-100 
            text-sm
            focus:outline-none 
            focus:ring-2 
            focus:ring-blue-500 
            focus:border-transparent
            disabled:opacity-50
            disabled:cursor-not-allowed
          "
        >
          <option value="" className="bg-[#0a192f]">Select a bucket</option>
          {buckets.map((bucket) => (
            <option 
              key={bucket.Name} 
              value={bucket.Name}
              className="bg-[#0a192f]"
            >
              {bucket.Name}
            </option>
          ))}
        </select>
        <Button
          onClick={handleCreateBucket}
          variant="secondary"
          className="
            h-9 w-9
            p-0
            bg-[#233554] 
            hover:bg-[#2a4065] 
            text-white
            border border-[#233554]
          "
          title="Create new bucket"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      {!config.bucket_name && (
        <div className="absolute -bottom-5 left-0 text-xs text-red-400">
          Please select an S3 bucket first
        </div>
      )}
      {error && (
        <div className="absolute -bottom-5 left-0 text-xs text-red-400 bg-red-900/20 rounded px-2 py-1">
          {error}
        </div>
      )}
    </div>
  )
}
