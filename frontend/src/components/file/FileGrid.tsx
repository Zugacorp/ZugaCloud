import React from 'react';
import { FileItem as FileItemComponent } from './FileItem';
import { useFileSystem } from '../../hooks/useFileSystem';
import { FileItem as FileItemType } from '../../types/file';
import { ChevronLeft } from 'lucide-react';
import { Button } from '../common/Button';

interface FileGridProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  bucketName: string;
}

export const FileGrid: React.FC<FileGridProps> = ({ currentPath, onNavigate, bucketName }) => {
  const { files, loading, error } = useFileSystem(currentPath);

  console.log('FileGrid render:', { currentPath, bucketName, loading, filesCount: files.length });

  if (!bucketName) {
    return (
      <div className="text-center p-4 text-gray-400">
        Please select a bucket to view files
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 text-center p-4">
        Error loading files: {error}
      </div>
    );
  }

  const handleFileClick = (file: FileItemType) => {
    if (file.type === 'folder') {
      // For folders, navigate to the new path
      const newPath = file.path.endsWith('/') ? file.path : `${file.path}/`;
      onNavigate(newPath);
    }
    // Handle file clicks if needed
  };

  const handleBackClick = () => {
    const segments = currentPath.split('/').filter(Boolean);
    segments.pop(); // Remove the last segment
    const parentPath = segments.length ? `/${segments.join('/')}/` : '/';
    onNavigate(parentPath);
  };

  const renderBreadcrumbs = () => {
    const segments = currentPath.split('/').filter(Boolean);
    return (
      <div className="flex items-center space-x-2 text-sm mb-4">
        <button 
          onClick={() => onNavigate('/')}
          className="text-blue-400 hover:text-blue-300"
        >
          {bucketName}
        </button>
        {segments.map((segment, index) => (
          <React.Fragment key={index}>
            <span className="text-gray-500">/</span>
            <button
              onClick={() => {
                const newPath = '/' + segments.slice(0, index + 1).join('/') + '/';
                onNavigate(newPath);
              }}
              className="text-blue-400 hover:text-blue-300"
            >
              {segment}
            </button>
          </React.Fragment>
        ))}
      </div>
    );
  };

  return (
    <div className="relative p-4">
      {/* Back button - only show when not at root */}
      {currentPath !== '/' && (
        <Button
          variant="ghost"
          size="icon"
          onClick={handleBackClick}
          className="absolute left-4 top-4 z-10"
        >
          <ChevronLeft className="h-5 w-5" />
        </Button>
      )}

      {/* Breadcrumbs with adjusted padding to account for back button */}
      <div className={`mb-4 ${currentPath !== '/' ? 'ml-16' : ''}`}>
        {renderBreadcrumbs()}
      </div>

      {/* File grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {files.map((file, index) => (
          <FileItemComponent
            key={index}
            file={file}
            onClick={() => handleFileClick(file)}
          />
        ))}
      </div>
    </div>
  );
};
