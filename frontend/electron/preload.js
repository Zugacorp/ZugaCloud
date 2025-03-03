const { contextBridge, ipcRenderer } = require('electron');

// Prevent default drag and drop behavior
document.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
});

document.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
});

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
    'electron',
    {
        send: (channel, data) => {
            // whitelist channels
            let validChannels = ['toMain', 'open-external', 'select-folder'];
            if (validChannels.includes(channel)) {
                try {
                    ipcRenderer.send(channel, data);
                } catch (error) {
                    console.error('Error sending IPC message:', error);
                }
            }
        },
        receive: (channel, func) => {
            let validChannels = ['fromMain', 'folder-selected', 'error'];
            if (validChannels.includes(channel)) {
                try {
                    // Deliberately strip event as it includes `sender` 
                    ipcRenderer.on(channel, (event, ...args) => {
                        try {
                            func(...args);
                        } catch (error) {
                            console.error('Error in IPC callback:', error);
                        }
                    });
                } catch (error) {
                    console.error('Error setting up IPC listener:', error);
                }
            }
        },
        // Expose folder selection API
        selectFolder: async () => {
            try {
                const result = await ipcRenderer.invoke('select-folder');
                return result;
            } catch (error) {
                console.error('Error selecting folder:', error);
                return { success: false, error: error.message };
            }
        },
        // Expose any other APIs needed by the renderer process
        platform: process.platform
    }
); 