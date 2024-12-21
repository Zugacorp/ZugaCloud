import React, { useState, useEffect } from 'react';
import { FaFolder, FaFolderOpen } from 'react-icons/fa';
import { BsFilePlayFill, BsFileFill } from 'react-icons/bs';
import { FileItem as FileItemType } from '../../types/file';
import { VideoThumbnail } from './VideoThumbnail';
import { formatFileSize, handleVideoPlay } from '../../utils/file';
import { api } from '../../api/client';
import { ContextMenu } from '../common/ContextMenu';

interface FileItemProps {
  file: FileItemType;
  onClick: () => void;
}

export const FileItem: React.FC<FileItemProps> = ({ file, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasLocalCopy, setHasLocalCopy] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ isOpen: boolean; x: number; y: number }>({
    isOpen: false,
    x: 0,
    y: 0
  });
  
  useEffect(() => {
    // Check if file exists locally when component mounts
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
        if (!hasLocalCopy) {
          throw new Error('File does not exist locally');
        }
        await api.deleteLocalFile(file.path);
        setHasLocalCopy(false);
      } else {
        await api.deleteS3Object(file.path);
      }
      // Trigger refresh of the file list
      window.location.reload();
    } catch (error) {
      console.error(`Error deleting file (${type}):`, error);
      // You might want to show an error notification here
    }
  };

  const handleDownload = async () => {
    try {
      const url = await api.getPresignedUrl(file.path);
      if (!window.electronAPI?.downloadFile) {
        // Fallback to browser download if not in electron
        window.open(url, '_blank');
        return;
      }

      // Ensure we have a filename
      const filename = file.name || file.path.split('/').pop() || 'download';
      console.log('Downloading file:', { url, filename }); // Debug log

      const result = await window.electronAPI.downloadFile(url, filename);
      if (result.success) {
        console.log(`File downloaded to: ${result.path}`);
        // Optionally show a success notification
      }
    } catch (error) {
      console.error('Error downloading file:', error);
      // Optionally show an error notification
    }
  };

  const renderSize = () => {
    if (file.type === 'folder') {
      // Always show 0 B if no size is available
      const size = file.totalSize || 0;
      const count = file.fileCount || 0;
      return (
        <div className="text-xs text-gray-400 text-center">
          {formatFileSize(size)}
          {count > 0 && ` • ${count} ${count === 1 ? 'file' : 'files'}`}
        </div>
      );
    }
    
    return (
      <div className="text-xs text-gray-400 text-center">
        {formatFileSize(file.size || 0)}
      </div>
    );
  };

  return (
    <div className="group cursor-pointer">
      <div 
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className="relative group cursor-pointer p-2 rounded-lg hover:bg-[#233554] transition-colors"
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
        
        <div className="text-sm truncate text-center text-gray-100 mb-1">
          {file.name}
        </div>
        
        {renderSize()}
      </div>
      <ContextMenu
        file={file}
        isOpen={contextMenu.isOpen}
        position={{ x: contextMenu.x, y: contextMenu.y }}
        onClose={() => setContextMenu({ isOpen: false, x: 0, y: 0 })}
        onPlay={handlePlay}
        onDelete={handleDelete}
        onDownload={handleDownload}
        onInfo={() => {}}
        hasLocalCopy={hasLocalCopy}
      />
    </div>
  );
};
