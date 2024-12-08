import { app } from 'electron';
import './src/main.cjs/index.js';

// Handle Squirrel events for Windows
if (require('electron-squirrel-startup')) {
  app.quit();
}
