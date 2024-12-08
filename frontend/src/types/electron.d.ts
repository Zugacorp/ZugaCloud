interface FolderSelectionResult {
  success: boolean;
  path?: string;
  canceled: boolean;
}

export interface ElectronAPI {
  selectFolder: () => Promise<FolderSelectionResult>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

export {};
