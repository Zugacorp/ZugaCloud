
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
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

    // Load the Flask app with retry
    loadURLWithRetry('http://localhost:5000')
        .catch(err => {
            console.error('Failed to load application:', err);
            app.quit();
        });
    
    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
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
