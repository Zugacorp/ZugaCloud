const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  on: (channel, callback) => {
    if (channel === 'video:load') {
      ipcRenderer.on(channel, (_, data) => callback(data));
    }
  }
}); 