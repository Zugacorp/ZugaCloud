# File: frontend/components/thumbnail_frame.py

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import io
import threading
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

class ThumbnailFrame(ttk.Frame):
    def __init__(self, parent, file_name, file_type, default_image, on_click, aws_integration, bucket_name, display_name):
        super().__init__(parent)
        self.file_name = file_name
        self.file_type = file_type
        self.on_click = on_click
        self.aws_integration = aws_integration
        self.bucket_name = bucket_name
        self.display_name = display_name

        self.thumbnail_label = ttk.Label(self, image=default_image, background='#F5F5F5')
        self.thumbnail_label.image = default_image
        self.thumbnail_label.pack(pady=5)

        self.name_label = ttk.Label(self, text=self.truncate_filename(display_name), wraplength=150, background='#F5F5F5')
        self.name_label.pack(pady=5)

        self.thumbnail_label.bind("<Button-1>", self.handle_click)
        self.name_label.bind("<Button-1>", self.handle_click)

        if self.file_type == 'video':
            threading.Thread(target=self.load_video_thumbnail, daemon=True).start()

    def truncate_filename(self, filename, max_length=20):
        if len(filename) > max_length:
            return filename[:max_length-3] + '...'
        return filename

    def handle_click(self, event):
        self.on_click(self.file_name, self.file_type)

    def load_video_thumbnail(self):
        try:
            # Get the first few MB of the video file
            video_data = self.aws_integration.get_object_range(self.bucket_name, self.file_name, 0, 5*1024*1024)  # First 5 MB
            if video_data is None:
                logger.error(f"Failed to retrieve video data for thumbnail: {self.file_name}")
                return

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_file.write(video_data)
                temp_file_path = temp_file.name

            # Open the video file with OpenCV
            cap = cv2.VideoCapture(temp_file_path)
            
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((150, 100), Image.LANCZOS)
                thumbnail = ImageTk.PhotoImage(image=img)
                self.thumbnail_label.configure(image=thumbnail)
                self.thumbnail_label.image = thumbnail

            cap.release()
            os.unlink(temp_file_path)  # Delete the temporary file
        except Exception as e:
            logger.error(f"Error loading video thumbnail for {self.file_name}: {e}")

    def update_image(self, new_image):
        self.thumbnail_label.configure(image=new_image)
        self.thumbnail_label.image = new_image