const { contextBridge, ipcRenderer } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const os = require('os');
const fs = require('fs');

function getVlcPath() {
  if (process.platform === 'win32') {
    return path.join('C:', 'Program Files', 'VideoLAN', 'VLC', 'vlc.exe');
  } else if (process.platform === 'darwin') {
    return '/Applications/VLC.app/Contents/MacOS/VLC';
  } else {
    return '/usr/bin/vlc';
  }
}

function extractVideoInfo(url) {
  try {
    const decodedUrl = decodeURIComponent(url);
    const urlObj = new URL(decodedUrl);
    const pathParts = urlObj.pathname.split('/');
    const videoName = decodeURIComponent(pathParts[pathParts.length - 1].split('.')[0]);
    const bucketName = urlObj.hostname.split('.')[0];
    return `${videoName} (streamed from ${bucketName})`;
  } catch (error) {
    console.error('Error extracting video info:', error);
    return null;
  }
}

function getDownloadsFolder() {
  if (process.platform === 'win32') {
    return path.join(os.homedir(), 'Downloads');
  } else if (process.platform === 'darwin') {
    return path.join(os.homedir(), 'Downloads');
  } else {
    // Linux
    return path.join(os.homedir(), 'Downloads');
  }
}

contextBridge.exposeInMainWorld('electron', {
  shell: {
    openExternal: async (url) => {
      try {
        if (url.includes('video/') || url.includes('.mp4') || url.includes('.mkv')) {
          const vlcPath = getVlcPath();
          const title = extractVideoInfo(url);
          
          const vlcProcess = spawn(vlcPath, [
            url,
            '--meta-title', title,
            '--no-video-title-show'
          ], {
            stdio: 'ignore',
            detached: true
          });
          
          return true;
        }
        
        await shell.openExternal(url);
        return true;
      } catch (error) {
        console.error('Failed to open external URL:', error);
        return false;
      }
    }
  }
});

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
  'electronAPI',
  {
    selectFolder: () => ipcRenderer.invoke('dialog:openFolder'),
    handleVideoPlay: (url) => ipcRenderer.invoke('video:play', url),
    downloadFile: (url, filename) => {
      console.log('Initiating download:', { url, filename }); // Debug log
      return ipcRenderer.invoke('file:download', { url, filename });
    }
  }
);