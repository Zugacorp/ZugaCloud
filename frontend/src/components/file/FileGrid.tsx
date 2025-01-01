import { useState } from 'react'
import { useFileSystem } from '../../hooks/useFileSystem'
import { FileInfo } from '../../types/file'

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
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error: {error.message}</div>
  }

  return (
    <div>
      <div>
        {files.map((file) => (
          <div
            key={file.path}
            onClick={() => handleFileClick(file)}
            className={`cursor-pointer ${selectedFile?.path === file.path ? 'selected' : ''}`}
          >
            <div>{file.name}</div>
            {file.type === 'file' && <div>{file.size} bytes</div>}
          </div>
        ))}
      </div>
      <button onClick={refresh}>Refresh</button>
    </div>
  )
}
