import React, { useState } from 'react';
import { FileGrid } from '../components/file/FileGrid';
import { useConfig } from '../hooks/useConfig';

export const Dashboard: React.FC = () => {
  const { loading, config } = useConfig();
  const [currentPath, setCurrentPath] = useState('/');

  console.log('Dashboard render:', { loading, config, currentPath });

  if (loading) {
    console.log('Dashboard is loading');
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#0a192f]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a192f] text-white">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <FileGrid 
          currentPath={currentPath}
          onNavigate={setCurrentPath}
          bucketName={config.bucket_name || 'zugaarchive'}
        />
      </main>
    </div>
  );
};
