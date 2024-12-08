import React, { useState, useRef, useEffect } from 'react';
import { FileItem } from '../../types/file';
import { formatFileSize } from '../../utils/file';

interface VideoThumbnailProps {
    file: FileItem;
    thumbnailUrl?: string;
    previewUrl?: string;
    onContextMenu: (e: React.MouseEvent) => void;
}

export const VideoThumbnail: React.FC<VideoThumbnailProps> = ({
    file,
    thumbnailUrl,
    previewUrl,
    onContextMenu
}) => {
    const [isHovered, setIsHovered] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [previewLoaded, setPreviewLoaded] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        if (isHovered && videoRef.current && previewUrl) {
            videoRef.current.play().catch(error => {
                console.error('Error playing preview:', error);
            });
        }
    }, [isHovered, previewUrl]);

    return (
        <div 
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            onContextMenu={onContextMenu}
            className="relative w-full h-full"
        >
            <div className="absolute inset-0">
                {isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#112240]">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400" />
                    </div>
                )}
                
                {thumbnailUrl && (
                    <img
                        src={thumbnailUrl}
                        alt={file.name}
                        className={`w-full h-full object-cover transition-opacity duration-300 ${
                            isHovered && previewLoaded ? 'opacity-0' : 'opacity-100'
                        }`}
                        onLoad={() => setIsLoading(false)}
                        onError={() => {
                            setIsLoading(false);
                            setError('Failed to load thumbnail');
                        }}
                    />
                )}
                
                {previewUrl && (
                    <video
                        ref={videoRef}
                        src={previewUrl}
                        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${
                            isHovered && previewLoaded ? 'opacity-100' : 'opacity-0'
                        }`}
                        muted
                        loop
                        playsInline
                        preload="auto"
                        onLoadedData={() => setPreviewLoaded(true)}
                    />
                )}
            </div>
        </div>
    );
};
