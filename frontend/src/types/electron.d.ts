interface FolderSelectionResult {
  success: boolean;
  path?: string;
  error?: string;
  canceled?: boolean;
}

interface FolderValidationResult {
  exists: boolean;
  isConfigured: boolean;
}

interface ElectronAPI {
  // App info
  getAppPath: () => string;
  getCurrentWindow: () => Electron.BrowserWindow;
  
  // Folder operations
  selectFolder: () => Promise<FolderSelectionResult>;
  validateFolder: (path: string) => Promise<FolderValidationResult>;
  
  // File operations
  openExternal: (url: string) => Promise<void>;
  
  // Window operations
  minimize: () => void;
  maximize: () => void;
  close: () => void;
}

declare global {
  interface Window {
    electron: ElectronAPI;
  }
}

export {};
