import { useEffect, useRef } from 'react'
import { FileInfo } from '../../types/file'

interface ContextMenuProps {
  file: FileInfo
  x: number
  y: number
  onClose: () => void
  onDelete: () => void
  onDownload: () => void
}

export function ContextMenu({ file, x, y, onClose, onDelete, onDownload }: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  return (
    <div
      ref={menuRef}
      style={{ top: y, left: x }}
      className="absolute bg-white shadow-lg rounded-md py-1 min-w-[150px]"
    >
      {file.type === 'file' && (
        <>
          <button
            onClick={onDownload}
            className="w-full text-left px-4 py-2 hover:bg-gray-100"
          >
            Download {file.name}
          </button>
          <button
            onClick={onDelete}
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-red-600"
          >
            Delete {file.name}
          </button>
        </>
      )}
    </div>
  )
}
