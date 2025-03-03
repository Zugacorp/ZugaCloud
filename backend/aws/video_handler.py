import os
import logging

logger = logging.getLogger(__name__)

class VideoHandler:
    def __init__(self, s3_client):
        self.s3_client = s3_client
        
    def is_video_file(self, file_path: str) -> bool:
        """Check if a file is a video based on its extension"""
        video_extensions = {
            '.mp4', '.mkv', '.avi', '.mov', '.wmv',
            '.m4v', '.webm', '.flv', '.mpeg', '.mpg', '.3gp'
        }
        ext = os.path.splitext(file_path)[1].lower()
        return ext in video_extensions
        
    def get_content_type(self, file_path: str) -> str:
        """Get the appropriate content type based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.mp4': 'video/mp4',
            '.mkv': 'video/x-matroska',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.m4v': 'video/x-m4v',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv',
            '.mpeg': 'video/mpeg',
            '.mpg': 'video/mpeg',
            '.3gp': 'video/3gpp'
        }
        return content_types.get(ext, 'application/octet-stream')
        
    def generate_streaming_url(self, bucket_name: str, object_key: str, expiration: int = 3600) -> str:
        """Generate a streaming URL for a video file"""
        content_type = self.get_content_type(object_key)
        return self.s3_client.generate_presigned_url(
            bucket_name,
            object_key,
            expiration,
            content_type
        ) 