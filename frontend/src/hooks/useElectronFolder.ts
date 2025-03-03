import { useState } from 'react';

interface FolderSelection {
  selectFolder: () => Promise<string | null>;
  isLoading: boolean;
  error: Error | null;
}

export function useElectronFolder(): FolderSelection {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const selectFolder = async (): Promise<string | null> => {
    if (!window.electron) {
      console.error('Electron API not available');
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await window.electron.selectFolder();
      return result.success && result.path ? result.path : null;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to select folder');
      setError(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return { selectFolder, isLoading, error };
}
