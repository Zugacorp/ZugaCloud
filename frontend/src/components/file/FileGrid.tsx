import React, { useState, useEffect } from 'react';
import { FileItem as FileItemComponent } from './FileItem';
import { useFileSystem } from '../../hooks/useFileSystem';
import { FileItem as FileItemType } from '../../types/file';
import { ChevronLeft, Grid, List, RefreshCw } from 'lucide-react';
import { Button } from '../common/Button';
import { FileGridSkeleton } from './FileGridSkeleton';

interface FileGridProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  bucketName: string;
}

export const FileGrid: React.FC<FileGridProps> = ({ currentPath, onNavigate, bucketName }) => {
  const { files, loading, error, refreshFiles } = useFileSystem(currentPath);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedFile, setSelectedFile] = useState<number | null>(null);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (selectedFile === null) return;

      switch (e.key) {
        case 'ArrowRight':
          setSelectedFile(prev => Math.min((prev || 0) + 1, files.length - 1));
          break;
        case 'ArrowLeft':
          setSelectedFile(prev => Math.max((prev || 0) - 1, 0));
          break;
        case 'Enter':
          if (files[selectedFile]) {
            handleFileClick(files[selectedFile]);
          }
          break;
        case 'Escape':
          setSelectedFile(null);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedFile, files]);

  if (!bucketName) {
    return (
      <div className="text-center p-4 text-gray-400">
        Please select a bucket to view files
      </div>
    );
  }

  if (loading) {
    return <FileGridSkeleton />;
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
      const newPath = file.path.endsWith('/') ? file.path : `${file.path}/`;
      onNavigate(newPath);
    }
  };

  const handleBackClick = () => {
    const segments = currentPath.split('/').filter(Boolean);
    segments.pop();
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
