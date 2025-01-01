import { useState } from 'react'
import { FileInfo } from '../../types/file'

interface VideoThumbnailProps {
  file: FileInfo
  thumbnailUrl?: string
  previewUrl?: string
}

export function VideoThumbnail({ file, thumbnailUrl, previewUrl }: VideoThumbnailProps) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="relative w-full h-full"
    >
      {thumbnailUrl ? (
        <img
          src={isHovered && previewUrl ? previewUrl : thumbnailUrl}
          alt={file.name}
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full bg-gray-200 flex items-center justify-center">
          <span className="text-gray-500">No thumbnail</span>
        </div>
      )}
      <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
        <div className="text-white">▶</div>
      </div>
    </div>
  )
}
