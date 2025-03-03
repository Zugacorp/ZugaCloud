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
    send: (channel: string, data: any) => void;
    receive: (channel: string, func: (...args: any[]) => void) => void;
    platform: string;
  };
}

declare global {
  interface Window {
    global: Window;
  }

  // Add Node.js global compatibility
  const global: Window;
}

export {};
