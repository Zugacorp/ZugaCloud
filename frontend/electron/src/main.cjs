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
      nodeIntegration: true,
      contextIsolation: true,
      preload: preloadPath,
      sandbox: false,
      enableRemoteModule: true
    }
  });

  enable(mainWindow.webContents);

  // Load the development server URL in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5001');
    // Open DevTools if needed
    // mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../dist/index.html'));
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
  console.log('Electron app ready');
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
}); 