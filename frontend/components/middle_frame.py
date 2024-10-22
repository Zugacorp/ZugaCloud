# File: frontend/components/middle_frame.py

import tkinter as tk
from tkinter import ttk
from .thumbnail_frame import ThumbnailFrame
from ..utils.ui_utils import get_file_type
import os
import logging
import threading
import queue

logger = logging.getLogger(__name__)

class MiddleFrame(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.thumbnail_frames = []
        self.current_prefix = ""
        self.content_queue = queue.Queue()
        self.is_loading = False
        self.initial_load_complete = False  # Initialize here
        self.setup_ui()

    def setup_ui(self):
        self.create_canvas()
        self.create_scrollbar()
        self.create_scrollable_frame()
        self.configure_scrolling()

    def create_canvas(self):
        self.content_canvas = tk.Canvas(self, bg='#F5F5F5')
        self.content_canvas.pack(side="left", fill="both", expand=True)

    def create_scrollbar(self):
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.content_canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

    def create_scrollable_frame(self):
        self.scrollable_frame = ttk.Frame(self.content_canvas)
        self.scrollable_frame_id = self.content_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

    def configure_scrolling(self):
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            )
        )
        self.content_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.content_canvas.bind('<Configure>', self.on_canvas_configure)

    def on_canvas_configure(self, event):
        self.content_canvas.itemconfig(self.scrollable_frame_id, width=event.width)

    def load_s3_contents(self):
        if self.is_loading:
            logger.info("Already loading S3 contents, skipping duplicate call.")
            return
        
        self.clear_thumbnails()
        if not self.main_window.aws_integration.is_initialized():
            self.display_error("AWS integration not initialized. Please check your settings.")
            return
        
        self.is_loading = True
        self.content_queue = queue.Queue()  # Reset the queue
        self.empty_message_displayed = False  # Reset the flag
        
        if not self.initial_load_complete:
            logger.info("Performing initial load of S3 contents.")
            self.initial_load_complete = True
        else:
            logger.info("Reloading S3 contents.")
        
        threading.Thread(target=self.fetch_s3_contents, daemon=True).start()
        self.process_content_queue()

    def fetch_s3_contents(self, continuation_token=None):
        try:
            bucket_name = self.main_window.config.get('bucket_name')
            if not bucket_name:
                self.content_queue.put(("error", "No bucket selected. Please choose a bucket in the settings."))
                return

            s3_contents, next_token = self.main_window.aws_integration.list_objects_paginated(
                bucket_name,
                self.current_prefix,
                continuation_token
            )
            
            if not s3_contents and not continuation_token:
                self.content_queue.put(("empty", f"This folder is empty: {self.current_prefix}"))
            else:
                processed_keys = set()
                for item in s3_contents:
                    key = item['Key']
                    relative_key = key[len(self.current_prefix):]
                    if '/' in relative_key:
                        # This is a subfolder
                        folder_name = relative_key.split('/')[0] + '/'
                        if folder_name not in processed_keys:
                            processed_keys.add(folder_name)
                            full_folder_key = self.current_prefix + folder_name
                            self.content_queue.put(("item", {'Key': full_folder_key, 'Type': 'folder', 'DisplayName': folder_name}))
                    elif key not in processed_keys:
                        # This is a file
                        processed_keys.add(key)
                        self.content_queue.put(("item", item))
            
            if next_token:
                # Continue fetching if there are more items
                self.fetch_s3_contents(next_token)
            else:
                self.content_queue.put(("end", None))  # Signal end of content
        except Exception as e:
            logger.error(f"Error fetching S3 contents: {e}")
            self.content_queue.put(("error", f"Error fetching S3 contents: {str(e)}"))

    def process_content_queue(self):
        try:
            while True:
                message_type, content = self.content_queue.get_nowait()
                if message_type == "item":
                    self.display_item(content)
                    self.empty_message_displayed = False  # Reset flag when content is displayed
                elif message_type == "error":
                    self.display_error(content)
                elif message_type == "empty":
                    if not self.empty_message_displayed:
                        self.display_empty_message(content)
                        self.empty_message_displayed = True
                elif message_type == "end":
                    self.is_loading = False
                    break
        except queue.Empty:
            if self.is_loading:
                self.after(100, self.process_content_queue)
        finally:
            self.update_scrollregion()

    def display_error(self, message):
        error_label = ttk.Label(
            self.scrollable_frame,
            text=message,
            font=("Segoe UI", 12),
            foreground='red',
            background='#F5F5F5'
        )
        error_label.pack(pady=20)

    def display_empty_message(self, message):
        # Clear any existing empty message before displaying a new one
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, ttk.Label) and widget.cget("text").startswith("This folder is empty:"):
                widget.destroy()

        empty_label = ttk.Label(
            self.scrollable_frame,
            text=message,
            font=("Segoe UI", 12),
            foreground='#555555',
            background='#F5F5F5'
        )
        empty_label.pack(pady=20)

    def display_item(self, item):
        file_type = 'folder' if item['Type'] == 'folder' else get_file_type(item['Key'])
        display_name = item.get('DisplayName', os.path.basename(item['Key'].rstrip('/')))
        thumbnail_frame = ThumbnailFrame(
            self.scrollable_frame,
            item['Key'],
            file_type,
            self.main_window.icons.get(file_type, self.main_window.icons['file']),
            self.on_item_click,
            self.main_window.aws_integration,
            self.main_window.config.get('bucket_name', ''),
            display_name
        )
        thumbnail_frame.pack(side=tk.LEFT, padx=10, pady=10)
        self.thumbnail_frames.append(thumbnail_frame)

    def clear_thumbnails(self):
        for frame in self.thumbnail_frames:
            frame.destroy()
        self.thumbnail_frames.clear()
        
        # Also clear any existing empty message
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, ttk.Label) and widget.cget("text").startswith("This folder is empty:"):
                widget.destroy()

    def update_scrollregion(self):
        self.scrollable_frame.update_idletasks()
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))

    def on_item_click(self, key, file_type):
        if file_type == 'folder':
            self.current_prefix = key
            self.load_s3_contents()
            self.main_window.top_frame.back_button.config(state='normal')
        else:
            self.main_window.open_file(key, file_type)

    def go_back(self):
        if self.current_prefix:
            parts = self.current_prefix.rstrip('/').split('/')
            self.current_prefix = '/'.join(parts[:-1])
            if self.current_prefix:
                self.current_prefix += '/'
            self.load_s3_contents()
            if not self.current_prefix:
                self.main_window.top_frame.back_button.config(state='disabled')

    def sort_contents(self, sort_type):
        # Implement sorting logic here
        # For now, we'll just reload the contents
        self.load_s3_contents()

    def start_auto_refresh(self):
        self.auto_refresh()

    def auto_refresh(self):
        self.load_s3_contents()
        self.after(300000, self.auto_refresh)  # 300000 ms = 5 minutes