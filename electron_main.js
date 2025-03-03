//Import the app and BrowserWindow from the electron module
const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron'); 
const path = require('path');

// Create a function to create a new window
function createWindow() {
    //Create a new BrowserWindow
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true,
            webSecurity: true,
            preload: path.join(__dirname, 'frontend', 'electron', 'preload.js')
        }
    });

    // Prevent default drag and drop behavior
    win.webContents.on('will-navigate', (e) => {
        e.preventDefault();
    });

    // Add window event listeners for debugging
    win.on('close', (e) => {
        console.log('Window close event triggered');
    });

    win.on('crashed', (e) => {
        console.error('Window crashed:', e);
    });

    win.on('unresponsive', () => {
        console.error('Window became unresponsive');
    });

    win.webContents.on('crashed', (e, killed) => {
        console.error('WebContents crashed:', { event: e, wasKilled: killed });
    });

    win.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error('Window failed to load:', errorCode, errorDescription);
    });

    // Function to load URL with retry
    const loadURLWithRetry = async (url, retries = 5) => {
        for (let i = 0; i < retries; i++) {
            try {
                console.log(`Attempt ${i + 1}: Loading URL ${url}...`);
                await win.loadURL(url);
                console.log('URL loaded successfully');
                return;
            } catch (err) {
                console.log(`Attempt ${i + 1}: Failed to load URL, retrying in 1 second...`, err);
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        throw new Error(`Failed to load URL after ${retries} attempts`);
    };

    // Determine the correct URL based on environment
    const isDev = process.env.NODE_ENV === 'development';
    const url = isDev 
        ? 'http://localhost:5001'  // Vite dev server
        : `file://${path.join(__dirname, 'frontend/dist', 'index.html')}`;

    console.log('Environment:', process.env.NODE_ENV);
    console.log('Loading URL:', url);

    // Open DevTools in development
    if (isDev) {
        win.webContents.openDevTools();
    }

    // Load the URL
    loadURLWithRetry(url)
        .catch(err => {
            console.error('Failed to load application:', err);
            if (isDev) {
                console.log('Make sure the Vite dev server is running on port 5001');
            }
            app.quit();
        });
}

// Create window when app is ready
app.whenReady().then(() => {
    createWindow();

    // Handle macOS activation
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

// Handle IPC messages
ipcMain.on('open-external', async (event, url) => {
    try {
        await shell.openExternal(url);
    } catch (error) {
        console.error('Failed to open external URL:', error);
    }
});

ipcMain.handle('select-folder', async () => {
    try {
        const result = await dialog.showOpenDialog({
            properties: ['openDirectory']
        });
        
        return {
            success: !result.canceled,
            path: result.filePaths[0]
        };
    } catch (error) {
        console.error('Error selecting folder:', error);
        return {
            success: false,
            error: error.message
        };
    }
});

// Quit when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
    console.log('All windows closed');
    
    // Only quit the app if not in development mode
    const isDev = process.env.NODE_ENV === 'development';
    if (!isDev && process.platform !== 'darwin') {
        console.log('Quitting application');
        app.quit();
    } else {
        console.log('In development mode, not quitting application');
    }
});

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
});

process.on('unhandledRejection', (error) => {
    console.error('Unhandled rejection:', error);
});
