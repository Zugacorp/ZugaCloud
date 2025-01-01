// src/hooks/useFileSystem.ts
import { useState, useEffect } from 'react';
import { useConfig } from '../contexts/ConfigContext';
import { api } from '../api/client';
import { FileInfo } from '../types/file';

export function useFileSystem(initialPath = '') {
  const [path, setPath] = useState(initialPath);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { config } = useConfig();

  useEffect(() => {
    loadFiles();
  }, [path, config.bucket_name]);

  const loadFiles = async () => {
    if (!config.bucket_name) {
      setError(new Error('No bucket selected'));
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await api.listFiles(path, config.bucket_name);
      setFiles(response.files);
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