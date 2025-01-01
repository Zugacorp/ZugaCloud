import { useState } from 'react'
import { FaFolder, FaFolderOpen } from 'react-icons/fa'
import { BsFilePlayFill, BsFileFill } from 'react-icons/bs'
import { FileInfo } from '../../types/file'
import { api } from '../../api/client'
import { ContextMenu } from '../common/ContextMenu'

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

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      onContextMenu={handleContextMenu}
      className="relative p-4 cursor-pointer hover:bg-gray-100 rounded-md"
    >
      <div className="flex items-center space-x-2">
        <Icon className="w-6 h-6" />
        <span>{file.name}</span>
      </div>
      {file.type === 'file' && (
        <div className="text-sm text-gray-500">
          {(file.size || 0).toLocaleString()} bytes
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
