import React from 'react';
import { Play, Trash2, Cloud, Download, Info } from 'lucide-react';
import { FileItem } from '../../types/file';
import { useConfig } from '../../hooks/useConfig';

interface ContextMenuProps {
  file: FileItem;
  isOpen: boolean;
  position: { x: number; y: number };
  onClose: () => void;
  onPlay?: () => Promise<void>;
  onDelete?: (type: 'local' | 's3') => Promise<void>;
  onDownload?: () => Promise<void>;
  onInfo?: () => void;
  hasLocalCopy?: boolean;
}

export const ContextMenu: React.FC<ContextMenuProps> = ({
  file,
  isOpen,
  position,
  onClose,
  onPlay,
  onDelete,
  onDownload,
  onInfo,
  hasLocalCopy = false,
}) => {
  const { config } = useConfig();
  const menuRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
      document.addEventListener('contextmenu', handleClickOutside);
      
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleEscape);
        document.removeEventListener('contextmenu', handleClickOutside);
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const menuItemClass = "flex items-center w-full px-3 py-2 text-sm text-gray-300 hover:bg-[#233554] transition-colors gap-3 outline-none";
  const dividerClass = "my-1 border-t border-[#233554]";

  // Calculate position
  const menuWidth = 224;
  const menuHeight = 200;
  const adjustedPosition = {
    x: Math.min(position.x, window.innerWidth - menuWidth),
    y: Math.min(position.y, window.innerHeight - menuHeight)
  };

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[200px] w-56 bg-[#112240] border border-[#233554] rounded-lg shadow-xl py-1 overflow-hidden"
      style={{ 
        top: adjustedPosition.y, 
        left: adjustedPosition.x,
      }}
      onClick={(e) => e.stopPropagation()}
      onContextMenu={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
    >
      {file.isVideo && onPlay && (
        <button
          onClick={onPlay}
          className={menuItemClass}
        >
          <Play className="w-4 h-4" />
          <span>Play</span>
        </button>
      )}

      {(file.isVideo || onDownload) && <div className={dividerClass} />}

      {onDelete && hasLocalCopy && (
        <button
          onClick={() => onDelete('local')}
          className={menuItemClass}
        >
          <Trash2 className="w-4 h-4" />
          <span>Delete from Local</span>
        </button>
      )}

      {onDelete && (
        <button
          onClick={() => onDelete('s3')}
          className={menuItemClass}
        >
          <Cloud className="w-4 h-4" />
          <span className="truncate">Delete from {config.bucket_name}</span>
        </button>
      )}

      {onDownload && (
        <button
          onClick={onDownload}
          className={menuItemClass}
        >
          <Download className="w-4 h-4" />
          <span>Download</span>
        </button>
      )}

      <div className={dividerClass} />

      {onInfo && (
        <button
          onClick={onInfo}
          className={menuItemClass}
        >
          <Info className="w-4 h-4" />
          <span>Info</span>
        </button>
      )}
    </div>
  );
};
