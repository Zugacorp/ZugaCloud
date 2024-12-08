import React from 'react';
import { Progress } from '../common/Progress';
import { useSync } from '../../hooks/useSync';
import { Button } from '../common/Button';
import { Play, StopCircle, RefreshCw } from 'lucide-react';
import { useConfig } from '../../hooks/useConfig';

export const SyncStatus: React.FC = () => {
  const { config } = useConfig();
  const { syncState, startSync, stopSync } = useSync();

  const renderStatusMessage = () => {
    if (!syncState) return 'Ready to upload files to S3';
    
    console.log('Current sync state:', syncState);
    
    if (syncState.type === 'completed') {
      return (
        <div className="flex flex-col">
          <span className="text-green-400 font-medium">
            Sync completed successfully
          </span>
        </div>
      );
    }
    
    const message = syncState.message;
    
    if (typeof message === 'object' && 'details' in message && message.details) {
      const { details } = message;
      
      if (details.currentFile) {
        return (
          <div className="flex flex-col">
            <span className="text-blue-400 font-medium">
              {message.message}
            </span>
            <span className="text-xs text-gray-400">
              {details.progress} • {details.size}
            </span>
          </div>
        );
      }
      
      return message.message;
    }
    
    return typeof message === 'string' ? message : message.message;
  };

  const getProgress = (): number => {
    if (!syncState) return 0;
    if (syncState.type === 'completed') return 100;
    if (syncState.type === 'progress') return syncState.progress || 0;
    return 0;
  };

  const isActive = syncState?.type === 'progress';
  const progress = getProgress();

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-[#112240] border-t border-[#233554]">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center p-4 space-x-4">
          <Button
            onClick={startSync}
            disabled={isActive || !config.sync_folder || !config.bucket_name}
            variant="primary"
            className="flex items-center space-x-2"
            title="Upload new or modified files to S3"
          >
            <Play className="h-4 w-4" />
            <span>Upload to S3</span>
          </Button>

          <Button
            onClick={stopSync}
            disabled={!isActive}
            variant="secondary"
            className="flex items-center space-x-2"
          >
            <StopCircle className="h-4 w-4" />
            <span>Stop</span>
          </Button>

          <div className="flex-1">
            <Progress 
              value={progress}
              className={syncState?.type === 'completed' ? 'bg-green-500' : ''}
            />
            {(isActive || syncState?.type === 'completed') && progress > 0 && (
              <div className="mt-1 text-xs text-gray-400">
                {progress.toFixed(1)}%
              </div>
            )}
          </div>

          <div className="text-sm text-gray-300 font-medium min-w-[300px]">
            {renderStatusMessage()}
          </div>

          <Button
            onClick={() => window.location.reload()}
            variant="ghost"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </Button>
        </div>
      </div>
    </div>
  );
};
