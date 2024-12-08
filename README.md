# ZugaCloud - Infinite Video Storage

A desktop application built with Python, Flask, React, and Electron for seamless video storage and synchronization with AWS S3.

## Complete Project Structure

```
└── 📁ZugaCloud
    └── 📁__pycache__
        └── main.cpython-311.pyc
    └── 📁backend
        └── 📁__pycache__
            └── __init__.cpython-311.pyc
            └── aws_integration.cpython-311.pyc
            └── config_manager.cpython-311.pyc
            └── file_sync.cpython-311.pyc
            └── initialization.cpython-311.pyc
            └── sync_queue.cpython-311.pyc
            └── thumbnail_manager.cpython-311.pyc
        └── 📁api
            └── 📁__pycache__
                └── __init__.cpython-311.pyc
                └── routes.cpython-311.pyc
            └── __init__.py
            └── routes.py
        └── 📁config
            └── config.json
        └── __init__.py
        └── aws_integration.py
        └── config_manager.py
        └── encryption.key
        └── file_sync.py
        └── initialization.py
        └── sync_manager.py
        └── sync_queue.py
        └── thumbnail_manager.py
        └── utils.py
    └── 📁frontend
        └── 📁assets
            └── 📁thumbnails
                └── 📁animated
                └── 📁static
                └── .gitkeep
        └── 📁electron
            └── 📁src
                └── main.cjs
                └── preload.cjs
                └── videoPlayer.html
                └── videoPreload.cjs
            └── index.ts
            └── tsconfig.json
        └── 📁scripts
            └── build-electron.cjs
        └── 📁src
            └── 📁api
                └── client.ts
                └── types.ts
            └── 📁components
                └── 📁aws
                    └── BucketSelector.tsx
                    └── CredentialsForm.tsx
                └── 📁common
                    └── Button.tsx
                    └── ContextMenu.tsx
                    └── LoadingSpinner.tsx
                    └── Progress.tsx
                └── 📁file
                    └── FileGrid.tsx
                    └── FileItem.tsx
                    └── FileList.tsx
                    └── FilePreview.tsx
                    └── VideoThumbnail.tsx
                └── 📁layout
                    └── Header.tsx
                    └── Layout.tsx
                    └── Navbar.tsx
                    └── Navigation.tsx
                    └── Sidebar.tsx
                └── 📁sync
                    └── ProgressBar.tsx
                    └── SyncControls.tsx
                    └── SyncStatus.tsx
                └── 📁ui
                    └── progress.tsx
            └── 📁contexts
                └── SyncContext.tsx
            └── 📁hooks
                └── useConfig.ts
                └── useElectronFolder.ts
                └── useFileSystem.ts
                └── useSync.ts
            └── 📁pages
                └── Dashboard.tsx
                └── FileExplorer.tsx
                └── Settings.tsx
            └── 📁styles
                └── globals.css
            └── 📁types
                └── config.ts
                └── electron.d.ts
                └── file.ts
                └── global.d.ts
                └── index.d.ts
                └── index.ts
                └── sync.ts
            └── 📁utils
                └── cn.ts
                └── file.ts
                └── format.ts
                └── formatters.tsx
                └── media.ts
                └── validators.tsx
            └── App.tsx
            └── main.tsx
            └── types.d.ts
            └── vite-env.d.ts
        └── index.html
        └── main.js
        └── package-lock.json
        └── package.json
        └── postcss.config.js
        └── tailwind.config.js
        └── tsconfig.json
        └── tsconfig.node.json
        └── vite.config.ts
    └── 📁scripts
        └── SynctoS3.bat
    └── .gitattributes
    └── .gitignore
    └── build_exe.py
    └── dev.py
    └── electron_main.js
    └── LICENSE
    └── main.py
    └── package-lock.json
    └── package.json
    └── README.md
```

## Component Details

### Backend Components
#### API Routes (`backend/api/routes.py`)
- Configuration management endpoints
- AWS/S3 operations
- Synchronization control
- File management
- Health checks

#### AWS Integration (`backend/aws_integration.py`)
- S3 bucket operations
- File upload/download
- Credential management
- Error handling

#### File Sync (`backend/file_sync.py`)
- File synchronization logic
- Progress tracking
- Batch file management
- Error recovery

### Frontend Components

#### React Components
- **Layout Components**: App structure and navigation
- **File Components**: File browsing and management
- **AWS Components**: Bucket selection and credentials
- **Sync Components**: Synchronization controls and status

#### State Management
- React Context for sync state
- Custom hooks for AWS integration
- File system operations
- Configuration management

#### Styling
- Tailwind CSS for styling
- Custom utility classes
- Responsive design
- Dark theme

### Build System

#### Development (`dev.py`)
- Concurrent Flask and Electron
- Hot reloading
- Development server configuration

#### Production Build (`build_exe.py`)
- PyInstaller configuration
- Resource bundling
- Encryption setup
- Directory management

## Configuration Files

### Frontend Configuration
- TypeScript configurations
- Electron build settings
- Package dependencies
- Tailwind CSS settings

### Backend Configuration
- Flask application settings
- AWS credentials
- Sync preferences
- Logging configuration

## Development Guidelines

### Code Organization
- Feature-based component structure
- Shared utilities and types
- Clear separation of concerns
- Consistent naming conventions

### Best Practices
- Type safety with TypeScript
- Error handling and logging
- Security considerations
- Performance optimization

## Testing

### Backend Tests
- API endpoint testing
- AWS integration tests
- Sync logic validation

### Frontend Tests
- Component testing
- Hook testing
- Integration testing

## Security Considerations

- Secure credential storage
- AWS IAM best practices
- Electron security guidelines
- Data encryption

## Performance Optimization

- Lazy loading
- Efficient file handling
- Caching strategies
- Resource management

## Future Enhancements

1. Video Processing
   - Thumbnail generation
   - Video transcoding
   - Metadata extraction

2. User Experience
   - Drag and drop interface
   - Progress visualization
   - File preview

3. Advanced Features
   - File versioning
   - Conflict resolution
   - Offline support

4. Security
   - Enhanced encryption
   - Access controls
   - Audit logging

---
## Environment Variables

For secure credential management, you can use the following environment variables:
- AWS_ACCESS_KEY: Your AWS access key
- AWS_SECRET_KEY: Your AWS secret key

These can be set in your environment or through a .env file (not tracked in git)

This is a living document and will be updated as the project evolves.