# ZugaCloud - Infinite Video Storage

A desktop application built with Python, Flask, React, and Electron for seamless video storage and synchronization with AWS S3.

## Complete Project Structure

```
zugacloud/
├── backend/
│ ├── api/
│ │ ├── init.py
│ │ └── routes.py # API endpoints and route handlers
│ ├── config/
│ │ └── config.json # Application configuration
│ ├── aws_integration.py # AWS S3 operations
│ ├── config_manager.py # Configuration management
│ ├── file_sync.py # File synchronization logic
│ ├── sync_manager.py # Sync orchestration
│ └── init.py
├── frontend/
│ ├── electron/
│ │ ├── src/
│ │ │ ├── main.cjs # Electron main process
│ │ │ └── preload.cjs # Preload scripts
│ │ ├── index.ts # Electron entry point
│ │ └── tsconfig.json # TypeScript config for Electron
│ ├── src/
│ │ ├── api/
│ │ │ ├── client.ts # API client
│ │ │ └── types.ts # API type definitions
│ │ ├── components/
│ │ │ ├── aws/
│ │ │ │ ├── BucketSelector.tsx
│ │ │ │ └── CredentialsForm.tsx
│ │ │ ├── common/
│ │ │ │ ├── Button.tsx
│ │ │ │ ├── LoadingSpinner.tsx
│ │ │ │ └── Progress.tsx
│ │ │ ├── file/
│ │ │ │ ├── FileGrid.tsx
│ │ │ │ ├── FileItem.tsx
│ │ │ │ ├── FileList.tsx
│ │ │ │ └── FilePreview.tsx
│ │ │ ├── layout/
│ │ │ │ ├── Header.tsx
│ │ │ │ ├── Layout.tsx
│ │ │ │ ├── Navbar.tsx
│ │ │ │ ├── Navigation.tsx
│ │ │ │ └── Sidebar.tsx
│ │ │ └── sync/
│ │ │ ├── ProgressBar.tsx
│ │ │ ├── SyncControls.tsx
│ │ │ └── SyncStatus.tsx
│ │ ├── contexts/
│ │ │ └── SyncContext.tsx # Sync state management
│ │ ├── hooks/
│ │ │ ├── useConfig.ts
│ │ │ ├── useElectronFolder.ts
│ │ │ ├── useFileSystem.ts
│ │ │ └── useSync.ts
│ │ ├── pages/
│ │ │ ├── Dashboard.tsx
│ │ │ ├── FileExplorer.tsx
│ │ │ └── Settings.tsx
│ │ ├── styles/
│ │ │ └── globals.css # Global styles
│ │ ├── types/
│ │ │ ├── config.ts
│ │ │ ├── electron.d.ts
│ │ │ ├── file.ts
│ │ │ ├── global.d.ts
│ │ │ ├── index.d.ts
│ │ │ └── sync.ts
│ │ └── utils/
│ │ ├── cn.ts # Class name utilities
│ │ ├── formatters.tsx # Data formatting utilities
│ │ └── validators.tsx # Form validation utilities
│ ├── index.html # Entry HTML
│ ├── main.tsx # React entry point
│ ├── package.json # Frontend dependencies
│ ├── postcss.config.js # PostCSS configuration
│ ├── tailwind.config.js # Tailwind CSS config
│ ├── tsconfig.json # TypeScript config
│ ├── tsconfig.node.json # Node-specific TS config
│ └── vite.config.ts # Vite bundler config
├── build_exe.py # Executable builder
├── dev.py # Development server
├── electron_main.js # Electron main process
├── LICENSE # MIT License
├── main.py # Flask application
├── package.json # Root dependencies
└── README.md # Project documentation
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