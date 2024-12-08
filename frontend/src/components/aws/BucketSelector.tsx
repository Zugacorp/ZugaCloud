import React, { useState, useEffect } from 'react';
import { useConfig } from '../../hooks/useConfig';
import { api } from '../../api/client';

export const BucketSelector: React.FC = () => {
  const { config, updateConfig, loading: configLoading } = useConfig();
  const [buckets, setBuckets] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadBuckets();
  }, []);

  const loadBuckets = async () => {
    try {
      setLoading(true);
      const data = await api.listBuckets();
      console.log('Available buckets:', data);
      setBuckets(data);
      
      if (data.includes('zugaarchive') && !config.bucket_name) {
        await handleBucketChange('zugaarchive');
      }
    } catch (err) {
      console.error('Failed to load buckets:', err);
      alert('Failed to load buckets. Please check your AWS credentials in settings.');
    } finally {
      setLoading(false);
    }
  };

  const handleBucketChange = async (bucket: string) => {
    await updateConfig({ bucket_name: bucket });
  };

  return (
    <select
      className="w-full px-3 py-2 bg-[#112240] border border-[#233554] rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      value={config.bucket_name || ''}
      onChange={(e) => handleBucketChange(e.target.value)}
      disabled={loading || configLoading}
    >
      <option value="">Select bucket...</option>
      {buckets.map(bucket => (
        <option key={bucket} value={bucket} className="bg-[#0a192f]">
          {bucket}
        </option>
      ))}
    </select>
  );
};
