# ZugaCloud Debugging Guide

This document tracks common issues encountered during development and their solutions.

## Table of Contents
- [Resolved Issues](#resolved-issues)
- [Unresolved Issues](#unresolved-issues)
- [Common Troubleshooting Steps](#common-troubleshooting-steps)
- [Current Investigation](#current-investigation)

## Current Investigation

### Electron App Startup Issue (2024-02-25)
**Issue Description:**  
Electron app fails to start properly - shows white screen and closes.

**Root Cause Analysis:**
1. Main entry point mismatch in package.json
2. Module type conflicts between Vite and Electron
3. Environment variables not properly set in development

**Solution Steps:**
1. Update package.json configuration:
```json
{
  "type": "commonjs",
  "main": "../electron_main.js",
  "scripts": {
    "electron:dev": "cross-env NODE_ENV=development concurrently \"vite\" \"wait-on tcp:5001 && electron .\""
  }
}
```

2. Install required dependencies:
```bash
npm install --save-dev cross-env
```

3. Verify file structure:
```
project_root/
├── electron_main.js
└── frontend/
    ├── electron/
    │   └── preload.js
    ├── src/
    │   └── main.tsx
    └── package.json
```

4. Start the app in development:
```powershell
# Terminal 1: Start Vite dev server
cd frontend
npm run dev

# Terminal 2: Start Electron
cd frontend
npm run electron:dev
```

**Verification Steps:**
1. Check Vite server output for:
   - Correct port (5001)
   - No compilation errors
   - Assets being served

2. Check Electron process for:
   - NODE_ENV=development
   - Correct preload script path
   - IPC communication setup

3. Monitor DevTools for:
   - Console errors
   - Network requests
   - React component mounting

**Status:** Testing solution implementation...

### Cognito Global Reference Error (2024-02-25)
**Issue Description:**  
App shows white screen with console error:
```
Uncaught ReferenceError: global is not defined
    at node_modules/amazon-cognito-identity-js/node_modules/buffer/index.js
```

**Root Cause:**  
The amazon-cognito-identity-js package expects the Node.js `global` object to be available, but it's not present in the browser environment. This is a common issue when using Node.js packages in browser/Electron environments.

**Solution Steps:**
1. Add global polyfill to index.html:
```html
<head>
    <script>
        // Polyfill for Node.js global
        if (typeof global === 'undefined') {
            window.global = window;
        }
    </script>
    <!-- other head elements -->
</head>
```

2. Alternative solution - Add Vite configuration:
```typescript
// vite.config.ts
export default defineConfig({
    // ... other config
    define: {
        global: 'window',
    },
    optimizeDeps: {
        include: ['amazon-cognito-identity-js'],
    },
})
```

3. If using TypeScript, add global to types:
```typescript
// src/types/global.d.ts
declare global {
    interface Window {
        global: Window;
    }
}
```

**Status:** Implementing solution...

### Cognito Client ID Not Found Error (2024-02-25)
**Issue Description:**  
Login fails with error:
```
ResourceNotFoundException: User pool client 2va38gqnkcrt32lspp1h8f4k11 does not exist.
```

**Root Cause:**  
The Cognito client ID in the environment files doesn't match an existing client in AWS Cognito. This can happen if:
1. The client was deleted from AWS Console
2. The client ID was changed but not updated in env files
3. The client was created in a different region
4. The user pool was recreated but client wasn't

**Solution Steps:**
1. Verify current client in AWS Console:
   - Go to AWS Cognito Console
   - Select the user pool `us-east-2_1hzrxJhtw`
   - Check App Integration > App client list
   - Note the correct client ID

2. Update environment files:
```env
# backend/.env
COGNITO_CLIENT_ID=<new_client_id>
VITE_COGNITO_CLIENT_ID=<new_client_id>

# frontend/.env
VITE_COGNITO_CLIENT_ID=<new_client_id>
```

3. If client doesn't exist:
   - Create new client in AWS Console
   - Enable required OAuth flows
   - Configure callback URLs
   - Update client ID in both .env files

4. Verify configuration:
```bash
# Check if client exists
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-2_1hzrxJhtw \
  --client-id <client_id>
```

**Status:** Awaiting AWS Cognito verification...

## Resolved Issues

### 1. White Screen on Electron App Launch
**Issue Description:**  
The Electron app shows a white screen and automatically closes after a while.

**Root Cause:**  
Multiple issues were identified:
1. Incorrect preload script path
2. Context isolation and security settings not properly configured
3. Missing type definitions for Electron API

**Solution:**  
1. Updated Electron main process configuration:
```javascript
const win = new BrowserWindow({
    webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        sandbox: true,
        preload: path.join(__dirname, 'frontend', 'electron', 'preload.js')
    }
});
```

2. Created proper preload script with context bridge:
```javascript
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('electron', {
    send: (channel, data) => {
        let validChannels = ['toMain'];
        if (validChannels.includes(channel)) {
            ipcRenderer.send(channel, data);
        }
    },
    // ... other exposed APIs
});
```

3. Added TypeScript definitions in `frontend/src/types/electron.d.ts`

### 2. Cognito Configuration Missing
**Issue Description:**  
Login fails with "Missing Cognito configuration" error.

**Root Cause:**  
Environment variables not properly loaded or missing from .env files.

**Solution:**  
1. Ensure all required variables are in frontend/.env:
```env
VITE_COGNITO_USER_POOL_ID=us-east-2_xxxxx
VITE_COGNITO_CLIENT_ID=xxxxxx
VITE_AWS_REGION=us-east-2
VITE_COGNITO_DOMAIN=xxxxx.auth.us-east-2.amazoncognito.com
VITE_IDENTITY_POOL_ID=us-east-2:xxxxx
```

2. Added validation in useConfig hook to check for required fields.

### 3. Windows PowerShell Command Separator Issue
**Issue Description:**  
Commands using && separator fail in Windows PowerShell with error:
```
The token '&&' is not a valid statement separator in this version.
```

**Solution:**  
Use semicolon (;) instead of && for command chaining in PowerShell:
```powershell
cd frontend; npm run electron:dev
```
Or use separate commands:
```powershell
cd frontend
npm run electron:dev
```

### 4. Node Process Killing During Development (2025-02-25)
**Issue Description:**  
During development, node processes were being forcibly killed, causing the application to fail during startup. The logs showed:
```
2025-02-24 20:56:49,631 - zugacloud-dev - INFO - Killing process node.exe (PID: 29536) using port 5001
[0] vite exited with code 1
```

This issue made development difficult as the application would frequently shut down unexpectedly, requiring a complete restart of the development stack.

**Root Causes:**  
After thorough investigation, we identified multiple interconnected issues:

1. **Import Error in Backend Code**:
   - The backend server failed to start due to an import error in `backend/api/routes.py`:
   ```python
   # Incorrect import
   from ..auth.auth import require_auth  # This function didn't exist
   ```
   - The correct function was `login_required`, not `require_auth`.

2. **Process Management Chain Reaction**:
   - When the backend server failed to start, the `dev.py` script detected this as an unexpected termination.
   - This triggered the `cleanup_processes()` function, which killed all processes on ports 5000 and 5001.
   - The node process running the Vite server on port 5001 was terminated as part of this cleanup.

3. **Concurrently Package Default Behavior**:
   - The `concurrently` npm package was used in both package.json files to run multiple commands in parallel.
   - By default, when one command fails, `concurrently` kills all other commands it's managing.
   - This behavior is controlled by the `--kill-others` flag, which was enabled by default.

4. **Electron Window Closing Behavior**:
   - When the Electron window was closed, it triggered the `window-all-closed` event.
   - The event handler was configured to call `app.quit()` on non-macOS platforms.
   - This sent a shutdown signal to all processes, including the Python process.
   - The Python process then cleaned up all other processes, causing the application to shut down.

**Solution Implemented:**  
We implemented a comprehensive solution addressing all identified root causes:

1. **Fixed Import Error**:
   - Changed the import in `backend/api/routes.py` from:
   ```python
   from ..auth.auth import require_auth
   ```
   - To:
   ```python
   from ..auth.auth import login_required
   ```

2. **Improved Process Management**:
   - Modified the `kill_process_on_port` function in `dev.py` to never kill node processes:
   ```python
   if 'node' in process_name or 'npm' in process_name or 'electron' in process_name:
       logger.info(f"Skipping node/npm/electron process: {process_name} (PID: {proc.pid})")
       continue
   ```
   - Enhanced logging to track which processes are being considered and why they're being skipped.

3. **Modified Concurrently Configuration**:
   - Added the `--kill-others=false` flag to the `concurrently` command in both package.json files:
   ```json
   "electron:dev": "cross-env NODE_ENV=development concurrently --kill-others=false \"vite\" \"wait-on tcp:5001 && electron .\""
   ```
   - This prevents `concurrently` from killing other processes when one process exits or fails.

4. **Prevented Electron from Quitting in Development Mode**:
   - Modified the `window-all-closed` event handler in `electron_main.js`:
   ```javascript
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
   ```
   - This ensures that in development mode, closing the Electron window doesn't terminate the application.

**Verification:**  
After implementing these changes, we verified that:
1. The backend server starts correctly on port 5000 without any import errors.
2. The frontend Vite server runs on port 5001 without being killed.
3. Electron successfully connects to the Vite server.
4. Closing the Electron window does not terminate the development environment.
5. The application can be restarted without requiring a complete restart of the development stack.

**Key Learnings:**  
1. **Process Management Complexity**: Managing multiple processes in a development environment requires careful consideration of how processes interact and terminate.
2. **Default Behaviors Matter**: Understanding the default behaviors of development tools like `concurrently` is crucial for stable development environments.
3. **Electron Lifecycle Events**: Electron's lifecycle events need special handling in development mode to prevent unexpected application termination.
4. **Comprehensive Logging**: Detailed logging of process management activities was essential for diagnosing this complex issue.

**Future Recommendations:**  
1. Implement a more robust process management system with proper dependency tracking.
2. Add automated tests for the startup sequence to catch similar issues early.
3. Consider using a more sophisticated development environment setup tool.
4. Maintain detailed documentation of process management behaviors for future developers.

## Unresolved Issues

### 1. TypeScript Electron API Type Conflict
**Issue Description:**  
Type conflict between Electron shell API and custom IPC interface:
```typescript
Subsequent property declarations must have the same type. Property 'electron' must be of type '{ shell: { openExternal: (url: string) => Promise<boolean>; }; }'
```

**Current Status:**  
- Investigating proper type merging for Electron APIs
- Temporary workaround using type assertions
- Need to resolve without compromising type safety

### 2. [Template for New Issues]
**Issue Description:**  
[Description of the issue]

**Current Status:**  
- Current understanding of the problem
- Steps taken so far
- Potential solutions being investigated

## Common Troubleshooting Steps

### 1. Development Server Issues
1. Check if Vite server is running on port 5001
2. Verify environment variables are loaded
3. Check DevTools console (Ctrl+Shift+I) for errors
4. Verify backend server is running on port 5000

### 2. Authentication Issues
1. Verify Cognito configuration in AWS Console
2. Check token storage in localStorage
3. Verify network requests in DevTools Network tab
4. Check CORS configuration in backend

### 3. Electron App Debugging
1. Enable DevTools in development mode
2. Check main process logs
3. Verify preload script is loaded
4. Check IPC communication 