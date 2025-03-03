@echo off
REM SynctoS3.bat - Syncs local folder to user-specified S3 bucket
REM Usage: SynctoS3.bat "local_folder_path" "s3_bucket_path"

if "%~1"=="" (
    echo Error: Please provide the local folder path
    exit /b 1
)

if "%~2"=="" (
    echo Error: Please provide the full S3 path (e.g., s3://your-bucket/path)
    exit /b 1
)

echo Starting sync from "%~1" to "%~2"

:loop
aws s3 sync "%~1" "%~2" --delete
timeout /t 60
goto loop
