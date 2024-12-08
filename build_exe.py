# File: build_exe.py

import PyInstaller.__main__
import os
import sys
import tkinter
import shutil
from cryptography.fernet import Fernet

def create_readme():
    """Create the README.md file with updated instructions."""
    readme_content = """# ZugaCloud - Infinite Video Storage

A desktop application for seamless video storage and synchronization with AWS S3.

## Features

- Automatic synchronization with AWS S3
- Video thumbnail generation
- Secure credential management
- Bucket management
- File organization
- Progress tracking
- Auto-retry on failure

## Requirements

- AWS Account
- AWS S3 Bucket
- AWS CLI installed
- Windows 7 or later

## Setup Instructions

1. Install the AWS CLI from: https://aws.amazon.com/cli/
2. Configure AWS credentials in the application settings
3. Select or create an S3 bucket
4. Choose a local folder for synchronization
5. Start syncing!

## Usage

1. Launch ZugaCloud
2. Enter AWS credentials in Settings
3. Select or create a bucket
4. Choose a local folder
5. Click SYNC to start synchronization

## Troubleshooting

If you encounter permission issues:
1. Run the application as administrator
2. Ensure you have write permissions to the sync folder
3. Check AWS credentials and permissions

For more help, visit: https://aws.amazon.com/documentation/s3/
"""
    with open('README.md', 'w') as f:
        f.write(readme_content)

def create_version_file():
    """Create version information file."""
    version_info = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 1, 0, 0),
    prodvers=(1, 1, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'ZugaCloud'),
         StringStruct(u'FileDescription', u'ZugaCloud Video Storage'),
         StringStruct(u'FileVersion', u'1.1.0'),
         StringStruct(u'InternalName', u'zugacloud'),
         StringStruct(u'LegalCopyright', u'Copyright (c) 2024 ZugaCloud'),
         StringStruct(u'OriginalFilename', u'ZugaCloud.exe'),
         StringStruct(u'ProductName', u'ZugaCloud'),
         StringStruct(u'ProductVersion', u'1.1.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    with open('version_info.txt', 'w') as f:
        f.write(version_info)

def create_manifest():
    """Create the application manifest file."""
    manifest_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="X86"
    name="ZugaCloud"
    type="win32"
  />
  <description>ZugaCloud Video Storage Application</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
    </application>
  </compatibility>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
</assembly>
"""
    with open('app.manifest', 'w') as f:
        f.write(manifest_content)

def setup_encryption():
    """Generate encryption key for secure storage."""
    key = Fernet.generate_key()
    with open('backend/encryption.key', 'wb') as f:
        f.write(key)

def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        'dist',
        'build',
        'frontend/assets/thumbnails',
        'frontend/assets/icons',
        'frontend/assets/logo',
        'config'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def build_exe():
    """Build the executable with PyInstaller."""
    try:
        # Create necessary files and directories
        create_readme()
        create_version_file()
        create_manifest()
        setup_encryption()
        ensure_directories()

        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get Tkinter DLL path
        tkinter_dir = os.path.dirname(tkinter.__file__)
        
        # Define PyInstaller command
        pyinstaller_command = [
            'main.py',
            '--onefile',
            '--windowed',
            '--name=ZugaCloud',
            '--add-data=frontend:frontend',
            '--add-data=backend:backend',
            '--add-data=config:config',
            '--add-data=README.md:.',
            f'--icon={os.path.join(current_dir, "assets", "zugacloud_icon.ico")}',
            '--version-file=version_info.txt',
            '--manifest=app.manifest',
            '--clean',
            '--noconfirm',
            '--log-level=WARN',
            f'--distpath={os.path.join(current_dir, "dist")}',
            f'--workpath={os.path.join(current_dir, "build")}',
            f'--add-data={tkinter_dir};tkinter',
            '--hidden-import=tkinter',
            '--hidden-import=tkinter.filedialog',
            '--hidden-import=numpy',
            '--hidden-import=cv2',
            '--hidden-import=PIL',
            '--hidden-import=boto3',
            '--hidden-import=botocore',
            '--hidden-import=win32security',
            '--hidden-import=win32api',
            '--hidden-import=win32con',
            '--hidden-import=cryptography',
            '--uac-admin'
        ]
        
        # Add Anaconda DLL directory to PATH
        os.environ['PATH'] = os.path.join(sys.prefix, 'Library', 'bin') + os.pathsep + os.environ['PATH']
        
        # Run PyInstaller
        PyInstaller.__main__.run(pyinstaller_command)

        # Clean up temporary files
        os.remove('version_info.txt')
        os.remove('app.manifest')

        print("Build completed successfully!")
        return True

    except Exception as e:
        print(f"Error during build: {e}")
        return False

if __name__ == "__main__":
    if build_exe():
        print("Application built successfully!")
    else:
        print("Build failed. Check the error messages above.")