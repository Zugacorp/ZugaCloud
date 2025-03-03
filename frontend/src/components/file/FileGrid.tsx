import { useState } from 'react'
import { useFileSystem } from '../../hooks/useFileSystem'
import { FileInfo } from '../../types/file'
import { formatFileSize } from '../../utils/file'
import { FaFolder, FaFolderOpen, FaFile, FaVideo } from 'react-icons/fa'
import { FileGridSkeleton } from './FileGridSkeleton'

interface FileGridProps {
  currentPath: string
  onPathChange: (path: string) => void
}

export function FileGrid({ currentPath, onPathChange }: FileGridProps) {
  const { files, loading, error, refresh } = useFileSystem(currentPath)
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null)

  const handleFileClick = (file: FileInfo) => {
    if (file.type === 'folder') {
      onPathChange(file.path)
    } else {
      setSelectedFile(file)
    }
  }

  if (loading) {
    return <FileGridSkeleton />
  }

  if (error) {
    return (
      <div className="p-4 text-red-500 bg-red-100 rounded-lg">
        Error: {error.message}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {files.map((file) => (
        <div
          key={file.path}
          onClick={() => handleFileClick(file)}
          className={`
            relative p-4 rounded-lg border border-[#233554] bg-[#112240] 
            hover:border-blue-400 cursor-pointer transition-colors
            ${selectedFile?.path === file.path ? 'border-blue-500' : ''}
          `}
        >
          <div className="flex items-center space-x-3">
            {file.type === 'folder' ? (
              <FaFolder className="h-8 w-8 text-blue-400" />
            ) : file.isVideo ? (
              <FaVideo className="h-8 w-8 text-purple-400" />
            ) : (
              <FaFile className="h-8 w-8 text-gray-400" />
            )}
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
        </div>
      ))}
    </div>
  )
}
