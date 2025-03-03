// src/hooks/useFileSystem.ts
import { useState, useEffect } from 'react';
import { useConfig } from '../contexts/ConfigContext';
import { api } from '../api/client';
import { FileInfo } from '../types/file';
import { calculateFolderStats } from '../utils/file';

export function useFileSystem(initialPath = '') {
  const [path, setPath] = useState(initialPath);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { config } = useConfig();

  useEffect(() => {
    loadFiles();
  }, [path, config.bucket_name]);

  const processFiles = (files: FileInfo[]): FileInfo[] => {
    // Group files by their parent folder
    const folderMap = new Map<string, FileInfo[]>();
    
    files.forEach(file => {
      const parts = file.path.split('/');
      parts.pop(); // Remove file name
      const parentPath = parts.join('/');
      
      if (!folderMap.has(parentPath)) {
        folderMap.set(parentPath, []);
      }
      folderMap.get(parentPath)?.push(file);
    });

    // Calculate folder stats
    return files.map(file => {
      if (file.type === 'folder') {
        const folderContents = folderMap.get(file.path) || [];
        const stats = calculateFolderStats(folderContents);
        return {
          ...file,
          totalSize: stats.totalSize,
          fileCount: stats.fileCount
        };
      }
      return file;
    });
  };

  const loadFiles = async () => {
    if (!config.bucket_name) {
      setError(new Error('No bucket selected'));
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await api.listFiles(path, config.bucket_name);
      const processedFiles = processFiles(response.files);
      setFiles(processedFiles);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  return {
    path,
    setPath,
    files,
    loading,
    error,
    refresh: loadFiles,
  };
}