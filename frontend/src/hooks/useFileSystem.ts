// src/hooks/useFileSystem.ts
import { useState, useEffect } from 'react';
import { FileItem, S3Object } from '../types/file';
import { api } from '../api/client';
import { useConfig } from '../hooks/useConfig';

function normalizePath(path: string): string {
  return path.replace(/\\/g, '/').replace(/\/+/g, '/');
}

// Add a new cache utility
const FILE_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

interface CachedData<T> {
  data: T;
  timestamp: number;
}

const fileSystemCache = new Map<string, CachedData<FileItem[]>>();

export const useFileSystem = (path: string) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { config } = useConfig();

  const getCachedData = () => {
    const cached = fileSystemCache.get(path);
    if (cached && Date.now() - cached.timestamp < FILE_CACHE_DURATION) {
      return cached.data;
    }
    return null;
  };

  const setCachedData = (data: FileItem[]) => {
    fileSystemCache.set(path, {
      data,
      timestamp: Date.now()
    });
  };

  const transformS3ObjectToFileItem = (item: S3Object): FileItem | null => {
    const key = item.Key || '';
    const normalizedPath = normalizePath(path).startsWith('/') 
      ? normalizePath(path).slice(1) 
      : normalizePath(path);
    
    // Skip SynctoS3.bat file
    if (key.endsWith('SynctoS3.bat')) {
      return null;
    }

    const isFolder = item.Type === 'prefix' || key.endsWith('/');
    
    const relativePath = key.startsWith(normalizedPath) 
      ? key.slice(normalizedPath.length) 
      : key;

    let name;
    if (isFolder) {
      const segments = relativePath.split('/').filter(Boolean);
      name = segments[0] || key.split('/').filter(Boolean).pop() || '';
    } else {
      name = key.split('/').pop() || key;
    }

    const extension = !isFolder ? name.split('.').pop()?.toLowerCase() : undefined;
    const isVideo = extension ? /^(mp4|mov|avi|wmv|flv|webm|mkv|mpeg|mpg|m4v|3gp)$/i.test(extension) : false;

    return {
      name,
      type: isFolder ? 'folder' : 'file',
      size: item.Size,
      lastModified: item.LastModified,
      path: key,
      extension,
      isVideo,
      thumbnailUrl: item.thumbnailUrl,
      previewUrl: item.previewUrl
    };
  };

  const fetchFiles = async () => {
    try {
      setLoading(true);
      console.log('Fetching files for path:', path);
      const response = await api.listFiles(path, config.bucket_name);
      console.log('Received response:', response);
      
      if (response.error) {
        setError(response.error);
        setFiles([]);
        return;
      }
      
      const processedItems = response.files
        .map(transformS3ObjectToFileItem)
        .filter((item): item is FileItem => item !== null) // Filter out null items
        .sort((a: FileItem, b: FileItem) => {
          if (a.type === 'folder' && b.type !== 'folder') return -1;
          if (a.type !== 'folder' && b.type === 'folder') return 1;
          return a.name.localeCompare(b.name);
        });

      console.log('Processed items:', processedItems);
      setFiles(processedItems);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch files:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch files');
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const cachedFiles = getCachedData();
    if (cachedFiles) {
      setFiles(cachedFiles);
    } else {
      fetchFiles();
    }
  }, [path]);

  return { files, loading, error, refreshFiles: fetchFiles };
};