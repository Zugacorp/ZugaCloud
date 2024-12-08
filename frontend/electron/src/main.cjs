const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { enable } = require('@electron/remote/main');
const path = require('path');
const os = require('os');
const https = require('https');
const fs = require('fs');

let mainWindow = null;

function createWindow() {
  const preloadPath = path.join(__dirname, 'preload.cjs');
  console.log('Preload script path:', preloadPath);

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: preloadPath,
      sandbox: false,
      enableRemoteModule: true
    }
  });

  // Enable remote module
  enable(mainWindow.webContents);

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadURL('http://localhost:5000');
  }
}

// Initialize IPC handlers
ipcMain.handle('dialog:openFolder', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory'],
    title: 'Select Folder',
    buttonLabel: 'Select Folder'
  });
  
  console.log('Dialog result:', result);
  return {
    success: !result.canceled,
    path: result.filePaths[0],
    canceled: result.canceled
  };
});

ipcMain.handle('file:download', async (_, { url, filename }) => {
  if (!filename) {
    throw new Error('Filename is required for download');
  }

  const downloadsPath = path.join(os.homedir(), 'Downloads');
  const filePath = path.join(downloadsPath, filename);

  return new Promise((resolve, reject) => {
    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download: ${response.statusCode}`));
        return;
      }

      const file = fs.createWriteStream(filePath);
      response.pipe(file);

      file.on('finish', () => {
        file.close();
        resolve({ success: true, path: filePath });
      });

      file.on('error', (err) => {
        fs.unlink(filePath, () => {});
        reject(err);
      });
    }).on('error', (err) => {
      reject(err);
    });
  });
});

app.whenReady().then(() => {
  createWindow();
  console.log('Electron app ready');
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
}); 