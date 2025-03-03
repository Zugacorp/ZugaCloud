import { useState } from 'react'
import { FaFolder, FaFolderOpen } from 'react-icons/fa'
import { BsFilePlayFill, BsFileFill } from 'react-icons/bs'
import { FileInfo } from '../../types/file'
import { api } from '../../api/client'
import { ContextMenu } from '../common/ContextMenu'
import { formatFileSize } from '../../utils/file'

interface FileItemProps {
  file: FileInfo
  onClick: () => void
}

export function FileItem({ file, onClick }: FileItemProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null)

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault()
    setContextMenu({ x: e.clientX, y: e.clientY })
  }

  const handleDelete = async () => {
    try {
      if (file.type === 'file') {
        await api.deleteS3Object(file.path)
      }
      setContextMenu(null)
    } catch (error) {
      console.error('Failed to delete file:', error)
    }
  }

  const handleDownload = async () => {
    try {
      if (file.type === 'file') {
        const url = await api.getPresignedUrl(file.path)
        window.open(url, '_blank')
      }
      setContextMenu(null)
    } catch (error) {
      console.error('Failed to download file:', error)
    }
  }

  const Icon = file.type === 'folder'
    ? isHovered ? FaFolderOpen : FaFolder
    : file.isVideo ? BsFilePlayFill : BsFileFill

  const iconColor = file.type === 'folder' 
    ? 'text-blue-400' 
    : file.isVideo 
      ? 'text-purple-400' 
      : 'text-gray-400'

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      onContextMenu={handleContextMenu}
      className={`
        relative p-4 rounded-lg 
        border border-[#233554] 
        bg-[#112240] 
        hover:border-blue-400 
        cursor-pointer 
        transition-colors
        group
      `}
    >
      <div className="flex items-center space-x-3">
        <Icon className={`w-8 h-8 ${iconColor}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-100 truncate">
            {file.name}
          </p>
          <div className="text-xs text-gray-400 mt-1">
            {file.type === 'folder' ? (
              <>
                {file.fileCount ? `${file.fileCount.toLocaleString()} files` : 'Empty folder'}
                {file.totalSize && ` • ${formatFileSize(file.totalSize)}`}
              </>
            ) : (
              file.size && formatFileSize(file.size)
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className={`
        absolute top-2 right-2 
        flex items-center space-x-2
        opacity-0 group-hover:opacity-100
        transition-opacity
      `}>
        {file.type === 'file' && (
          <>
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleDownload()
              }}
              className="p-1 text-gray-400 hover:text-blue-400"
              title="Download"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleDelete()
              }}
              className="p-1 text-gray-400 hover:text-red-400"
              title="Delete"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </>
        )}
      </div>

      {file.isProcessing && (
        <div className="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        </div>
      )}

      {file.error && (
        <div className="absolute bottom-2 right-2 text-red-500 text-xs">
          Error processing file
        </div>
      )}

      {contextMenu && (
        <ContextMenu
          file={file}
          x={contextMenu.x}
          y={contextMenu.y}
          onClose={() => setContextMenu(null)}
          onDelete={handleDelete}
          onDownload={handleDownload}
        />
      )}
    </div>
  )
}
