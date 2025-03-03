import { app, BrowserWindow, dialog, ipcMain } from 'electron'
import * as path from 'path'
import * as isDev from 'electron-is-dev'
import { initialize, enable } from '@electron/remote/main'
import * as fs from 'fs/promises'

// Initialize remote module
initialize()

// IPC Handlers
function setupIPC() {
  ipcMain.handle('select-folder', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory']
    })
    
    if (!result.canceled && result.filePaths.length > 0) {
      const folderPath = result.filePaths[0]
      
      // Check if folder contains video files
      try {
        const files = await fs.readdir(folderPath)
        const videoExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        const hasVideos = files.some(file => 
          videoExtensions.some(ext => file.toLowerCase().endsWith(ext))
        )
        
        if (!hasVideos) {
          throw new Error('Selected folder must contain video files')
        }
        
        // Create or update .bat file
        const batContent = `@echo off
rem ZugaCloud Video Sync Configuration
set SYNC_FOLDER="${folderPath.replace(/\\/g, '\\\\')}"
set LAST_SYNC=%date% %time%
echo Folder configured for ZugaCloud sync`
        
        await fs.writeFile(path.join(folderPath, 'zugacloud-sync.bat'), batContent)
        
        return {
          success: true,
          path: folderPath
        }
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to process folder'
        }
      }
    }
    
    return {
      success: false,
      canceled: true
    }
  })
  
  ipcMain.handle('validate-folder', async (_, folderPath: string) => {
    try {
      const stats = await fs.stat(folderPath)
      const batExists = await fs.access(path.join(folderPath, 'zugacloud-sync.bat'))
        .then(() => true)
        .catch(() => false)
      
      return {
        exists: stats.isDirectory(),
        isConfigured: batExists
      }
    } catch {
      return {
        exists: false,
        isConfigured: false
      }
    }
  })
}

function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
  })

  // Enable remote module for the window
  enable(mainWindow.webContents)

  // Load the index.html from a url in development
  // or the local file in production.
  const startUrl = isDev
    ? 'http://localhost:5173'
    : `file://${path.join(__dirname, '../dist/index.html')}`

  mainWindow.loadURL(startUrl)

  // Open the DevTools in development.
  if (isDev) {
    mainWindow.webContents.openDevTools()
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
app.whenReady().then(() => {
  setupIPC()
  createWindow()
})

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
}) 