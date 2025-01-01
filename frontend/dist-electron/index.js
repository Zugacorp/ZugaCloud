"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
require("./src/main.cjs/index.js");
// Handle Squirrel events for Windows
if (require('electron-squirrel-startup')) {
    electron_1.app.quit();
}
