import { contextBridge } from 'electron'
import * as remote from '@electron/remote'

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  getAppPath: () => remote.app.getAppPath(),
  getCurrentWindow: () => remote.getCurrentWindow(),
}) 