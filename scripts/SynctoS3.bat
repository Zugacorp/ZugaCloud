
@echo off
REM SynctoS3.bat - Automatically syncs video files to S3 bucket every 60 seconds

:loop
aws s3 sync "" "s3:///" --delete
timeout /t 60
goto loop
