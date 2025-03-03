import { contextBridge, ipcRenderer } from 'electron'
import * as remote from '@electron/remote'

interface FolderSelectionResult {
  success: boolean
  path?: string
  error?: string
  canceled?: boolean
}

interface FolderValidationResult {
  exists: boolean
  isConfigured: boolean
}

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // App info
  getAppPath: () => remote.app.getAppPath(),
  getCurrentWindow: () => remote.getCurrentWindow(),
  
  // Folder operations
  selectFolder: async (): Promise<FolderSelectionResult> => {
    return await ipcRenderer.invoke('select-folder')
  },
  
  validateFolder: async (path: string): Promise<FolderValidationResult> => {
    return await ipcRenderer.invoke('validate-folder', path)
  },
  
  // File operations
  openExternal: async (url: string): Promise<void> => {
    await remote.shell.openExternal(url)
  },
  
  // Window operations
  minimize: () => remote.getCurrentWindow().minimize(),
  maximize: () => {
    const win = remote.getCurrentWindow()
    if (win.isMaximized()) {
      win.unmaximize()
    } else {
      win.maximize()
    }
  },
  close: () => remote.getCurrentWindow().close()
}) 