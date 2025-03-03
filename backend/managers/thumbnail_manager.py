import asyncio
import aiohttp
import cv2
import os
import tempfile
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
import requests

logger = logging.getLogger(__name__)

class ThumbnailManager:
    def __init__(self, aws_integration):
        self.aws_integration = aws_integration
        self.thumbnail_cache = {}
        self.preview_cache = {}
        
        # Define base directory
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Define separate directories for static and animated thumbnails
        self.thumbnails_base = os.path.join(base_path, 'frontend', 'assets', 'thumbnails')
        self.static_dir = os.path.join(self.thumbnails_base, 'static')
        self.animated_dir = os.path.join(self.thumbnails_base, 'animated')
        
        self.ensure_thumbnail_directories()
        
    def ensure_thumbnail_directories(self):
        """Create thumbnail directories if they don't exist"""
        try:
            os.makedirs(self.static_dir, exist_ok=True)
            os.makedirs(self.animated_dir, exist_ok=True)
            logger.info(f"Thumbnail directories ensured at: {self.thumbnails_base}")
        except Exception as e:
            logger.error(f"Error creating thumbnail directories: {e}")
            
    def get_thumbnail_paths(self, video_key):
        """Get paths for both static and animated thumbnails"""
        # Create a safe filename from the video key
        safe_name = video_key.replace('/', '_').replace('\\', '_')
        return {
            'static': os.path.join(self.static_dir, f"{safe_name}.jpg"),
            'animated': os.path.join(self.animated_dir, f"{safe_name}.gif")
        }
            
    async def generate_thumbnails(self, video_key):
        """Generate both static and animated thumbnails"""
        if not self.aws_integration.bucket_name:
            logger.error("No bucket name configured")
            return None, None

        paths = self.get_thumbnail_paths(video_key)
        
        # Check if thumbnails already exist
        if os.path.exists(paths['static']) and os.path.exists(paths['animated']):
            logger.info(f"Thumbnails already exist for {video_key}")
            return paths['static'], paths['animated']
        
        try:
            url = self.aws_integration.generate_presigned_url(
                self.aws_integration.bucket_name,
                video_key
            )
            if not url:
                logger.error(f"Failed to generate URL for {video_key}")
                return None, None

            # Create a temporary directory that will be automatically cleaned up
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_video_path = os.path.join(temp_dir, f"temp_video{os.path.splitext(video_key)[1]}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        # Download first few seconds for animated preview
                        chunk = await response.content.read(1024*1024*5)  # Read 5MB
                        
                        # Write to temp file
                        with open(temp_video_path, 'wb') as f:
                            f.write(chunk)
                        
                        # Generate static thumbnail
                        cap = cv2.VideoCapture(temp_video_path)
                        ret, frame = cap.read()
                        if ret:
                            # Resize frame maintaining aspect ratio
                            height = int(400 * 9/16)
                            frame = cv2.resize(frame, (400, height), interpolation=cv2.INTER_AREA)
                            cv2.imwrite(paths['static'], frame)
                            logger.info(f"Generated static thumbnail for {video_key}")
                            
                            # Generate animated preview (GIF)
                            frames = []
                            for _ in range(30):  # Capture 30 frames
                                ret, frame = cap.read()
                                if not ret:
                                    break
                                frame = cv2.resize(frame, (400, height))
                                frames.append(frame)
                            
                            if frames:
                                # Convert frames to GIF
                                import imageio
                                imageio.mimsave(paths['animated'], frames, fps=10)
                                logger.info(f"Generated animated thumbnail for {video_key}")
                            
                            cap.release()
                            return paths['static'], paths['animated']
                        
            return None, None
                    
        except Exception as e:
            logger.error(f"Error generating thumbnails for {video_key}: {e}")
            return None, None

    def generate_thumbnail(self, video_key):
        """Generate static thumbnail synchronously"""
        if not self.aws_integration.bucket_name:
            logger.error("No bucket name configured")
            return None

        thumbnail_path = self.get_thumbnail_paths(video_key)['static']
        
        if os.path.exists(thumbnail_path):
            return thumbnail_path

        try:
            url = self.aws_integration.generate_presigned_url(
                self.aws_integration.bucket_name,
                video_key
            )
            if not url:
                return None

            # Create a temporary directory that will be automatically cleaned up
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_video_path = os.path.join(temp_dir, f"temp_video{os.path.splitext(video_key)[1]}")
                
                # Download video chunk
                response = requests.get(url, stream=True)
                chunk = next(response.iter_content(chunk_size=1024*1024))
                
                # Write to temp file
                with open(temp_video_path, 'wb') as f:
                    f.write(chunk)
                
                # Extract first frame
                cap = cv2.VideoCapture(temp_video_path)
                ret, frame = cap.read()
                if ret:
                    height = int(400 * 9/16)
                    frame = cv2.resize(frame, (400, height))
                    cv2.imwrite(thumbnail_path, frame)
                    cap.release()
                    return thumbnail_path
                
            return None
                    
        except Exception as e:
            logger.error(f"Error generating thumbnail for {video_key}: {e}")
            return None
