import React from 'react';
import { Button } from '../common/Button';
import { useConfig } from '../../hooks/useConfig';
import { useSync } from '../../hooks/useSync';
import { Play, RefreshCw } from 'lucide-react';

export const SyncControls: React.FC = () => {
  const { config } = useConfig();
  const { syncState, startSync, stopSync } = useSync();
  const uploading = syncState.type === 'progress';

  return (
    <div className="flex space-x-4 bg-[#112240] p-4 rounded-lg border border-[#233554]">
      <Button
        onClick={startSync}
        disabled={uploading || !config.sync_folder || !config.bucket_name}
        variant="primary"
        className="flex items-center space-x-2 bg-blue-500 hover:bg-blue-600"
        title="Upload new or modified files to S3"
      >
        <Play className="h-4 w-4" />
        <span>Upload to S3</span>
      </Button>
      <Button
        onClick={stopSync}
        disabled={!uploading}
        variant="secondary"
        className="flex items-center space-x-2 bg-[#233554] hover:bg-[#2a4065]"
      >
        <span>Stop Upload</span>
      </Button>
      <Button
        onClick={() => window.location.reload()}
        variant="ghost"
        className="flex items-center space-x-2 text-gray-400 hover:text-gray-200"
      >
        <RefreshCw className="h-4 w-4" />
        <span>Refresh</span>
      </Button>
    </div>
  );
};
