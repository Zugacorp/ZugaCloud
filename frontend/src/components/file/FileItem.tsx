import React, { useState, useEffect } from 'react';
import { FaFolder, FaFolderOpen } from 'react-icons/fa';
import { BsFilePlayFill, BsFileFill } from 'react-icons/bs';
import { FileItem as FileItemType } from '../../types/file';
import { VideoThumbnail } from './VideoThumbnail';
import { formatFileSize, handleVideoPlay } from '../../utils/file';
import { api } from '../../api/client';
import { ContextMenu } from '../common/ContextMenu';
import { cn } from '../../utils/cn';

interface FileItemProps {
  file: FileItemType;
  onClick: () => void;
  selected?: boolean;
  onSelect?: () => void;
  viewMode?: 'grid' | 'list';
}

export const FileItem: React.FC<FileItemProps> = ({ 
  file, 
  onClick, 
  selected = false,
  onSelect,
  viewMode = 'grid' 
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasLocalCopy, setHasLocalCopy] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ isOpen: boolean; x: number; y: number }>({
    isOpen: false,
    x: 0,
    y: 0
  });

  useEffect(() => {
    const checkLocalExistence = async () => {
      if (file.type === 'file') {
        const exists = await api.checkLocalFile(file.path);
        setHasLocalCopy(exists);
      }
    };
    
    checkLocalExistence();
  }, [file]);

  const handleClick = async (e: React.MouseEvent) => {
    if (e.button === 2) return;
    
    onSelect?.();
    
    if (file.type === 'folder') {
      onClick();
    } else if (file.isVideo) {
      setIsLoading(true);
      try {
        const streamUrl = await api.getPresignedUrl(file.path);
        await handleVideoPlay(streamUrl);
      } catch (error) {
        console.error('Error playing video:', error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const getFileColor = () => {
    if (file.isVideo) return 'text-purple-400';
    switch (file.extension) {
      case 'pdf': return 'text-red-400';
      case 'doc':
      case 'docx': return 'text-blue-400';
      case 'xls':
      case 'xlsx': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onSelect?.();
    setContextMenu({
      isOpen: true,
      x: e.clientX,
      y: e.clientY
    });
  };

  const handlePlay = async () => {
    setIsLoading(true);
    try {
      const streamUrl = await api.getPresignedUrl(file.path);
      await handleVideoPlay(streamUrl);
    } catch (error) {
      console.error('Error playing video:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (type: 'local' | 's3') => {
    try {
      if (type === 'local') {
        await api.deleteLocalFile(file.path);
        setHasLocalCopy(false);
      } else {
        await api.deleteS3Object(file.path);
      }
      window.location.reload();
    } catch (error) {
      console.error(`Error deleting file (${type}):`, error);
    }
  };

  const handleDownload = async () => {
    try {
      const url = await api.getPresignedUrl(file.path);
      const filename = file.name || file.path.split('/').pop() || 'download';
      
      if (window.electronAPI?.downloadFile) {
        const result = await window.electronAPI.downloadFile(url, filename);
        if (result.success) {
          console.log(`File downloaded to: ${result.path}`);
        }
      } else {
        window.open(url, '_blank');
      }
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  const containerClasses = cn(
    "group relative cursor-pointer transition-colors",
    viewMode === 'grid' ? "p-2 rounded-lg" : "p-3 rounded-md",
    selected ? "bg-[#233554]" : "hover:bg-[#1a2942]",
    "focus:outline-none focus:ring-2 focus:ring-blue-500"
  );

  if (viewMode === 'list') {
    return (
      <div
        className={containerClasses}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        tabIndex={0}
      >
        <div className="flex items-center space-x-4">
          {file.type === 'folder' ? (
            <div className="w-10 flex justify-center">
              {isHovered ? (
                <FaFolderOpen className="w-6 h-6 text-blue-400" />
              ) : (
                <FaFolder className="w-6 h-6 text-blue-400" />
              )}
            </div>
          ) : (
            <div className="w-10 flex justify-center">
              {file.isVideo ? (
                <BsFilePlayFill className="w-6 h-6 text-purple-400" />
              ) : (
                <BsFileFill className={`w-6 h-6 ${getFileColor()}`} />
              )}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="text-sm truncate text-gray-100">{file.name}</div>
            {file.size && file.type !== 'folder' && (
              <div className="text-xs text-gray-400">{formatFileSize(file.size)}</div>
            )}
          </div>
        </div>
        <ContextMenu
          file={file}
          isOpen={contextMenu.isOpen}
          position={{ x: contextMenu.x, y: contextMenu.y }}
          onClose={() => setContextMenu({ isOpen: false, x: 0, y: 0 })}
          onPlay={handlePlay}
          onDelete={handleDelete}
          onDownload={handleDownload}
          hasLocalCopy={hasLocalCopy}
        />
      </div>
    );
  }

  // Grid view (default)
  return (
    <div
      className={containerClasses}
      onClick={handleClick}
      onContextMenu={handleContextMenu}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      tabIndex={0}
    >
      <div className="relative w-full rounded-lg overflow-hidden bg-[#112240] mb-2" style={{ aspectRatio: '16/9' }}>
        {file.isVideo ? (
          <VideoThumbnail
            file={file}
            thumbnailUrl={file.thumbnailUrl}
            previewUrl={file.previewUrl}
            onContextMenu={handleContextMenu}
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {file.type === 'folder' ? (
              <>
                {isHovered ? (
                  <FaFolderOpen className="w-16 h-16 text-blue-400 transition-transform transform scale-110" />
                ) : (
                  <FaFolder className="w-16 h-16 text-blue-400" />
                )}
                <span className="text-xs text-blue-400 mt-2">FOLDER</span>
              </>
            ) : (
              <>
                <BsFileFill className={`w-16 h-16 ${getFileColor()}`} />
                <span className={`text-xs mt-2 ${getFileColor()}`}>
                  {file.extension?.toUpperCase()}
                </span>
              </>
            )}
          </div>
        )}
      </div>
      
      <div className="text-sm truncate text-center text-gray-100">
        {file.name}
      </div>
      
      {file.size && file.type !== 'folder' && (
        <div className="text-xs text-gray-400 text-center">
          {formatFileSize(file.size)}
        </div>
      )}
    </div>
  );
};
