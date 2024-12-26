const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            preload: path.join(__dirname, 'preload.cjs')
        }
    });

    // Function to load URL with retry
    const loadURLWithRetry = async (url, retries = 5) => {
        for (let i = 0; i < retries; i++) {
            try {
                await win.loadURL(url);
                return;
            } catch (err) {
                console.log(`Attempt ${i + 1}: Failed to load URL, retrying in 1 second...`);
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        throw new Error(`Failed to load URL after ${retries} attempts`);
    };

    // Determine the correct URL based on environment
    const isDev = process.env.NODE_ENV === 'development';
    const url = isDev 
        ? 'http://localhost:5173'  // Vite dev server
        : `file://${path.join(__dirname, 'dist', 'index.html')}`; // Production build

    loadURLWithRetry(url)
        .catch(err => {
            console.error('Failed to load application:', err);
            app.quit();
        });
    
    if (isDev) {
        win.webContents.openDevTools();
    }
}

app.whenReady().then(createWindow);

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
