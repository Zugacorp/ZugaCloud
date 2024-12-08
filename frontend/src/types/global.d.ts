interface Window {
  electronAPI: {
    selectFolder: () => Promise<{ success: boolean; path: string; canceled: boolean }>;
    handleVideoPlay: (url: string) => Promise<void>;
    downloadFile: (url: string, filename: string) => Promise<{ success: boolean; path: string }>;
  };
  electron: {
    shell: {
      openExternal: (url: string) => Promise<boolean>;
    };
  };
}
