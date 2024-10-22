# frontend/gui.py

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import threading
from backend.file_sync import FileSync
from backend.config_manager import ConfigManager
from backend.aws_integration import AWSIntegration
import cv2
import webbrowser
import boto3
from io import BytesIO
import logging
from botocore.exceptions import ClientError
import tempfile
import shutil
import subprocess
from frontend.components.thumbnail_frame import ThumbnailFrame  # Import the ThumbnailFrame
import tkinter.font as tkFont

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZugaCloudGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZugaCloud - Infinite Video Storage")
        self.root.geometry('1300x900')  # Increased size for better layout
        self.root.resizable(True, True)  # Allow resizing for better accessibility
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.aws_integration = AWSIntegration(
            access_key=self.config.get('aws_access_key'),
            secret_key=self.config.get('aws_secret_key'),
            region=self.config.get('region')
        )
        self.file_sync = FileSync(
            progress_callback=self.update_progress_threadsafe,
            status_callback=self.update_status_threadsafe
        )
        self.thumbnail_frames = []  # List to hold ThumbnailFrame instances
        self.current_prefix = ""    # Initialize current prefix to root
        self.setup_ui()
        self.load_buckets()
        self.load_thumbnails()
        self.load_s3_contents()

    def setup_ui(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use a modern theme

        # Configure custom styles
        self.style.configure('Sync.TButton',
                             font=('Orbitron', 14, 'bold'),
                             foreground='white',
                             background='#1E90FF',
                             borderwidth=0,
                             focusthickness=3,
                             focuscolor='none')
        self.style.map('Sync.TButton',
                       foreground=[('active', 'white')],
                       background=[('active', '#1C86EE')])

        self.style.configure('TButton',
                             font=('Segoe UI', 12),
                             foreground='black',
                             background='#E0E0E0')
        self.style.map('TButton',
                       foreground=[('active', 'black')],
                       background=[('active', '#B0B0B0')])

        self.style.configure('TLabel',
                             font=('Segoe UI', 12),
                             foreground='black')

        # Load Icons
        self.load_icons()

        # Define Fonts
        self.title_font = tkFont.Font(family="Orbitron", size=24, weight="bold")
        self.label_font = tkFont.Font(family="Segoe UI", size=12)
        self.button_font = tkFont.Font(family="Segoe UI", size=12, weight="bold")

        # Create main frames
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=20)

        self.middle_frame = ttk.Frame(self.root)
        self.middle_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=20)

        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.grid(row=2, column=0, sticky='ew', padx=20, pady=20)

        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create sub-frames within top_frame
        self.left_top_frame = ttk.Frame(self.top_frame)
        self.left_top_frame.grid(row=0, column=0, sticky='w')

        self.right_top_frame = ttk.Frame(self.top_frame)
        self.right_top_frame.grid(row=0, column=1, sticky='e')

        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=0)

        # Add Logo to left_top_frame
        logo_path = os.path.join('frontend', 'assets', 'logo', 'zugacloud_logo.png')
        if os.path.exists(logo_path):
            try:
                self.logo_image = Image.open(logo_path)
                self.logo_image = self.logo_image.resize((120, 120), resample=self.get_resample_filter())
                self.logo_photo = ImageTk.PhotoImage(self.logo_image)
                self.logo_label = ttk.Label(self.left_top_frame, image=self.logo_photo)
                self.logo_label.grid(row=0, column=0, rowspan=2, padx=(0, 20), sticky='w')
                logger.info("Logo loaded successfully.")
            except Exception as e:
                logger.warning(f"Error loading logo image: {e}")
                self.logo_label = ttk.Label(self.left_top_frame, text="ZugaCloud", font=self.title_font, foreground='#1E90FF')
                self.logo_label.grid(row=0, column=0, rowspan=2, padx=(0, 20), sticky='w')
        else:
            logger.warning(f"Logo file not found at {logo_path}. Using default icon.")
            self.logo_label = ttk.Label(self.left_top_frame, text="ZugaCloud", font=self.title_font, foreground='#1E90FF')
            self.logo_label.grid(row=0, column=0, rowspan=2, padx=(0, 20), sticky='w')

        # Add Back Button
        self.back_button = ttk.Button(self.left_top_frame, text="Back", command=self.go_back, style='TButton')
        self.back_button.grid(row=0, column=1, padx=(0, 5), sticky='w')
        self.back_button.config(state='disabled')  # Initially disabled
        logger.info("Back button created and packed.")

        # Top Frame Widgets (Left Side)
        self.folder_label = ttk.Label(self.left_top_frame, text="Sync Folder:", font=self.label_font)
        self.folder_label.grid(row=1, column=1, padx=(0, 5), sticky='w')
        logger.info("Sync Folder label created and packed.")

        self.folder_entry = ttk.Entry(self.left_top_frame, width=60, font=self.label_font)
        self.folder_entry.grid(row=1, column=2, padx=(0, 5), sticky='w')
        self.folder_entry.insert(0, self.config.get('sync_folder'))
        logger.info("Sync Folder entry created and packed.")

        self.browse_button = ttk.Button(self.left_top_frame, text="Browse", command=self.browse_folder, style='TButton')
        self.browse_button.grid(row=1, column=3, padx=(0, 5), sticky='w')
        logger.info("Browse button created and packed.")

        # AWS Bucket Selection (Left Side)
        self.bucket_label = ttk.Label(self.left_top_frame, text="S3 Bucket:", font=self.label_font)
        self.bucket_label.grid(row=2, column=0, padx=(20, 5), sticky='w')
        logger.info("S3 Bucket label created and packed.")

        self.bucket_combo = ttk.Combobox(self.left_top_frame, values=self.aws_integration.get_existing_buckets(), state='readonly', font=self.label_font)
        self.bucket_combo.grid(row=2, column=1, columnspan=2, padx=(0, 5), sticky='w')
        self.bucket_combo.set(self.config.get('bucket_name'))
        logger.info("S3 Bucket combobox created and packed.")

        # Bind the selection event to update self.bucket_name
        self.bucket_combo.bind("<<ComboboxSelected>>", self.on_bucket_selected)

        self.refresh_buckets_button = ttk.Button(self.left_top_frame, text="Refresh Buckets", command=self.load_buckets, style='TButton')
        self.refresh_buckets_button.grid(row=2, column=3, padx=(0, 5), sticky='w')
        logger.info("Refresh Buckets button created and packed.")

        self.add_bucket_button = ttk.Button(self.left_top_frame, text="Add Bucket", command=self.add_bucket, style='TButton')
        self.add_bucket_button.grid(row=2, column=4, padx=(0, 5), sticky='w')
        logger.info("Add Bucket button created and packed.")

        # SYNC Button (Bottom Frame)
        self.sync_button = ttk.Button(self.bottom_frame, text="SYNC", command=self.start_sync, style='Sync.TButton')
        self.sync_button.grid(row=0, column=0, pady=10, sticky='w')
        logger.info("SYNC button created and packed.")

        # Progress Bar (Bottom Frame)
        self.progress = ttk.Progressbar(self.bottom_frame, orient='horizontal', mode='determinate', length=600)
        self.progress.grid(row=0, column=1, pady=10, padx=(10, 0), sticky='w')
        logger.info("Progress bar created and packed.")

        # Detailed Progress Label (Bottom Frame)
        self.detailed_progress_var = tk.StringVar()
        self.detailed_progress_var.set("Idle")
        self.detailed_progress_label = ttk.Label(self.bottom_frame, textvariable=self.detailed_progress_var, font=self.label_font)
        self.detailed_progress_label.grid(row=1, column=0, columnspan=2, pady=5, sticky='w')
        logger.info("Detailed Progress label created and packed.")

        # Status Label (Bottom Frame)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = ttk.Label(self.bottom_frame, textvariable=self.status_var, font=self.label_font)
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5, sticky='w')
        logger.info("Status label created and packed.")

        # Thumbnail Display Area (Scrollable Canvas for Grid Layout)
        self.content_canvas = tk.Canvas(self.middle_frame, bg='#F5F5F5')
        self.scrollbar = ttk.Scrollbar(self.middle_frame, orient="vertical", command=self.content_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.content_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            )
        )

        self.content_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.content_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content_canvas.grid(row=0, column=0, sticky='nsew')
        self.scrollbar.grid(row=0, column=1, sticky='ns')

        self.middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        logger.info("Thumbnail display area created and packed.")

        # Setup Sorting Options (Right Side)
        self.sort_var = tk.StringVar()
        self.sort_var.set("Alphabet")
        self.sort_label = ttk.Label(self.right_top_frame, text="Sort By:", font=self.label_font)
        self.sort_label.grid(row=0, column=0, padx=(5, 5), sticky='e')
        logger.info("Sort label created and packed.")

        self.sort_menu = ttk.OptionMenu(self.right_top_frame, self.sort_var, "Alphabet", "Alphabet", "Date", "Last Opened", command=self.sort_contents)
        self.sort_menu.grid(row=0, column=1, padx=(0, 5), sticky='w')
        logger.info("Sort menu created and packed.")

        # Settings Button (Right Side)
        self.settings_button = ttk.Button(self.right_top_frame, text="Settings", command=self.open_settings, style='TButton')
        self.settings_button.grid(row=0, column=2, padx=(5, 5), sticky='w')
        logger.info("Settings button created and packed.")

        # Open S3 Bucket Link Button (Right Side)
        self.open_bucket_button = ttk.Button(self.right_top_frame, text="Open S3 Bucket", command=self.open_s3_bucket, style='TButton')
        self.open_bucket_button.grid(row=0, column=3, padx=(5, 5), sticky='w')
        logger.info("Open S3 Bucket button created and packed.")

        # Initialize bucket_name
        self.bucket_name = self.config.get('bucket_name')
        logger.info(f"Initialized bucket_name: {self.bucket_name}")

    def load_icons(self):
        """Load and cache all necessary icons."""
        self.icons = {}
        icon_folder = os.path.join('frontend', 'assets', 'icons')

        # Define icon filenames
        icon_files = {
            "folder": "folder_icon.png",
            "audio": "audio_icon.png",
            "video": "video_icon.png",
            "file": "file_icon.png",
            "image": "file_icon.png",  # Using file_icon for images as well
        }

        for key, filename in icon_files.items():
            path = os.path.join(icon_folder, filename)
            if os.path.exists(path):
                try:
                    image = Image.open(path)
                    image = image.resize((150, 100), resample=self.get_resample_filter())  # Resize for grid thumbnails
                    photo = ImageTk.PhotoImage(image)
                    self.icons[key] = photo
                    logger.info(f"Loaded icon: {filename}")
                except Exception as e:
                    logger.error(f"Error loading icon {filename}: {e}")
                    self.icons[key] = None
            else:
                logger.warning(f"Icon file not found: {path}. Using default icon.")
                self.icons[key] = self.icons.get('file')  # Fallback to 'file' icon if available

    def get_resample_filter(self):
        """Get the appropriate resampling filter."""
        try:
            return Image.Resampling.LANCZOS
        except AttributeError:
            return Image.LANCZOS

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_selected)
            self.config['sync_folder'] = folder_selected
            self.config_manager.save_config(self.config)
            self.manage_syncto_s3_bat(folder_selected)
            self.load_thumbnails()

    def manage_syncto_s3_bat(self, folder):
        bat_path = os.path.join(folder, 'SynctoS3.bat')
        if not os.path.exists(bat_path):
            bucket_name = self.config.get('bucket_name', 'zugaarchive')
            access_key = self.config.get('aws_access_key')
            secret_key = self.config.get('aws_secret_key')
            region = self.config.get('region', 'us-east-2')
            bat_content = f"""@echo off

aws s3 sync "{folder}" s3://{bucket_name} --region {region}

"""
            with open(bat_path, 'w') as f:
                f.write(bat_content)
            # Hide the file
            if os.name == 'nt':
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(bat_path, FILE_ATTRIBUTE_HIDDEN)
            logger.info(f"Created and hid SynctoS3.bat at {bat_path}")
        else:
            logger.info(f"SynctoS3.bat already exists at {bat_path}")

    def load_buckets(self):
        buckets = self.aws_integration.get_existing_buckets()
        self.bucket_combo['values'] = buckets
        if self.config.get('bucket_name') in buckets:
            self.bucket_combo.set(self.config.get('bucket_name'))
            self.bucket_name = self.config.get('bucket_name')
        else:
            if buckets:
                self.bucket_combo.current(0)
                self.bucket_name = buckets[0]
                self.config['bucket_name'] = buckets[0]
                self.config_manager.save_config(self.config)
            else:
                self.bucket_combo.set('')
                self.bucket_name = None

    def add_bucket(self):
        bucket_name = simpledialog.askstring("Add Bucket", "Enter new S3 bucket name:")
        if bucket_name:
            if not self.config.get('aws_access_key') or not self.config.get('aws_secret_key'):
                messagebox.showerror("AWS Credentials Missing", "Please set your AWS Access Key and Secret Key in Settings before adding a bucket.")
                return
            success = self.aws_integration.create_s3_bucket(bucket_name)
            if success:
                messagebox.showinfo("Success", f"Bucket '{bucket_name}' created successfully.")
                self.load_buckets()
            else:
                messagebox.showerror("Error", f"Failed to create bucket '{bucket_name}'.")

    def start_sync(self):
        self.config['sync_folder'] = self.folder_entry.get()
        self.config['bucket_name'] = self.bucket_combo.get()
        self.config_manager.save_config(self.config)
        self.progress['value'] = 0
        self.detailed_progress_var.set("Starting synchronization...")

        aws_access_key = self.config.get('aws_access_key')
        aws_secret_key = self.config.get('aws_secret_key')

        if (aws_access_key and not aws_secret_key) or (aws_secret_key and not aws_access_key):
            messagebox.showerror("AWS Credentials Error", "Both AWS Access Key and Secret Key must be provided.")
            return

        self.file_sync.sync_folder = self.config.get('sync_folder')
        self.file_sync.bucket_name = self.config.get('bucket_name')
        self.file_sync.region = self.config.get('region')
        self.file_sync.aws_access_key = aws_access_key
        self.file_sync.aws_secret_key = secret_key = aws_secret_key

        # Initialize or update S3 client in FileSync
        self.file_sync.s3_client = self.file_sync.initialize_s3_client()

        # Calculate total files for progress bar
        if self.file_sync.sync_folder and os.path.isdir(self.file_sync.sync_folder):
            total_files = sum([len(files) for r, d, files in os.walk(self.file_sync.sync_folder)])
        else:
            total_files = 0
        self.progress['maximum'] = total_files if total_files > 0 else 1

        # Start synchronization in a separate thread to prevent UI blocking
        threading.Thread(target=self.file_sync.start_sync, daemon=True).start()
        messagebox.showinfo("Sync", "Synchronization started!")

    def update_progress_threadsafe(self, increment, current_file=None):
        """Thread-safe update for progress."""
        self.root.after(0, self.update_progress, increment, current_file)

    def update_status_threadsafe(self, message):
        """Thread-safe update for status."""
        self.root.after(0, self.update_status, message)

    def update_progress(self, increment, current_file=None):
        self.progress['value'] += increment
        if current_file:
            self.detailed_progress_var.set(f"Uploading: {current_file}")
        else:
            # When no current file, it means completion
            if self.progress['value'] >= self.progress['maximum']:
                self.detailed_progress_var.set("Synchronization completed.")
            else:
                self.detailed_progress_var.set(f"Progress: {self.progress['value']}/{self.progress['maximum']}")
        self.root.update_idletasks()

    def update_status(self, message):
        self.status_var.set(message)
        if message == "Synchronization completed.":
            self.detailed_progress_var.set("Synchronization completed.")
            self.load_s3_contents()
        elif message == "Synchronization stopped.":
            self.detailed_progress_var.set("Synchronization stopped.")

    def load_thumbnails(self):
        """Generate thumbnails for all videos and images in the sync folder."""
        sync_folder = self.config.get('sync_folder')
        if not sync_folder or not os.path.isdir(sync_folder):
            logger.warning("No sync folder selected or folder does not exist.")
            return

        # Traverse the folder and generate thumbnails
        for root_dir, dirs, files in os.walk(sync_folder):
            for file in files:
                file_path = os.path.join(root_dir, file)
                relative_path = os.path.relpath(file_path, sync_folder)
                file_ext = os.path.splitext(file)[1].lower()
                file_type = self.get_file_type(file_ext)

                if file_type in ['video', 'image']:
                    thumbnail_path = self.get_thumbnail_path(relative_path, file_type, is_s3=False)
                    # Ensure the directory exists
                    thumbnail_dir = os.path.dirname(thumbnail_path)
                    os.makedirs(thumbnail_dir, exist_ok=True)
                    if not os.path.exists(thumbnail_path):
                        self.generate_thumbnail(file_path, thumbnail_path, file_type, is_s3=False)

    def load_s3_contents(self):
        """Load and display contents from the S3 bucket."""
        threading.Thread(target=self.fetch_and_display_s3_contents_thread, daemon=True).start()

    def fetch_and_display_s3_contents_thread(self):
        if not self.bucket_name:
            logger.warning("No bucket selected to fetch contents.")
            self.display_placeholder()
            return

        self.update_status_threadsafe("Fetching S3 bucket contents...")

        aws_access_key = self.config.get('aws_access_key')
        aws_secret_key = self.config.get('aws_secret_key')
        region = self.config.get('region')

        # Determine if both credentials are provided
        if aws_access_key and aws_secret_key:
            s3 = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=region
            )
        else:
            # Do not pass credentials explicitly; use default credential chain
            s3 = boto3.client(
                's3',
                region_name=region
            )

        paginator = s3.get_paginator('list_objects_v2')
        try:
            # Use the current_prefix to list objects within the folder
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.current_prefix, Delimiter='/')
            self.s3_contents = []
            for page in pages:
                # Add sub-folders
                if 'CommonPrefixes' in page:
                    for cp in page['CommonPrefixes']:
                        folder_name = os.path.basename(cp['Prefix'].rstrip('/'))
                        self.s3_contents.append({'Key': folder_name, 'Type': 'folder'})
                # Add files
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if not obj['Key'].endswith('/'):  # Exclude folder markers
                            file_key = obj['Key'][len(self.current_prefix):] if self.current_prefix else obj['Key']
                            self.s3_contents.append({'Key': file_key, 'Type': 'file'})

            if not self.s3_contents:
                # If bucket/folder is empty, display a placeholder
                self.display_placeholder()
            else:
                self.display_s3_contents()
            self.update_status_threadsafe("S3 bucket contents loaded.")
        except ClientError as e:
            logger.error(f"Error fetching S3 contents: {e}")
            self.update_status_threadsafe(f"Error fetching S3 contents: {e}")
            # As a fallback, display local folder contents
            self.display_placeholder()

    def display_s3_contents(self):
        """Display the contents in the UI using a grid layout with folder hierarchy."""
        # Clear existing thumbnails
        for frame in self.thumbnail_frames:
            frame.destroy()
        self.thumbnail_frames.clear()

        # Separate folders and files
        folders = [obj for obj in self.s3_contents if obj.get('Type') == 'folder']
        files = [obj for obj in self.s3_contents if obj.get('Type') == 'file']

        # Sort folders and files
        folders_sorted = sorted(folders, key=lambda x: x['Key'].lower())
        files_sorted = sorted(files, key=lambda x: x['Key'].lower())

        # Combine sorted folders and files
        sorted_contents = folders_sorted + files_sorted

        # Display folders and files
        self.display_folder_contents(sorted_contents, parent_row=0, indent=0)

    def display_folder_contents(self, sorted_contents, parent_row, indent):
        """Display folders and files in a grid layout."""
        columns = 5  # Increased columns for better use of space
        current_row = parent_row

        for obj in sorted_contents:
            name = obj['Key']
            file_type = obj['Type']

            if file_type == 'folder':
                # Display folder thumbnail
                folder_thumbnail = self.icons.get('folder', self.icons.get('file'))
                folder_frame = ThumbnailFrame(
                    self.scrollable_frame,
                    file_name=name,
                    file_type='folder',
                    image=folder_thumbnail,
                    on_click=self.open_folder,
                    on_hover=None  # No hover functionality
                )
                folder_frame.grid(row=current_row, column=indent % columns, padx=10, pady=10, sticky='n')
                self.thumbnail_frames.append(folder_frame)
                current_row += 1
            elif file_type == 'file':
                # It's a file
                file_key = name
                file_ext = os.path.splitext(file_key)[1].lower()
                file_type_detected = self.get_file_type(file_ext)
                thumbnail_path = self.get_thumbnail_path(file_key, file_type_detected, is_s3=True)
                # Ensure the directory exists
                thumbnail_dir = os.path.dirname(thumbnail_path)
                os.makedirs(thumbnail_dir, exist_ok=True)
                if not os.path.exists(thumbnail_path):
                    # Generate thumbnail if not exists
                    self.generate_thumbnail(file_key, thumbnail_path, file_type_detected, is_s3=True)
                thumbnail_image = self.load_thumbnail_image(thumbnail_path, file_type_detected)

                file_frame = ThumbnailFrame(
                    self.scrollable_frame,
                    file_name=file_key,
                    file_type=file_type_detected,
                    image=thumbnail_image,
                    on_click=self.open_selected_file,
                    on_hover=None  # No hover functionality
                )
                file_frame.grid(row=current_row, column=indent % columns, padx=10, pady=10, sticky='n')
                self.thumbnail_frames.append(file_frame)
                current_row += 1

        return current_row

    def sort_folder_dict(self, folder_dict):
        """Sort folders and files alphabetically."""
        sorted_dict = {}
        for key in sorted(folder_dict.keys(), key=lambda s: s.lower()):
            if isinstance(folder_dict[key], dict):
                sorted_dict[key] = self.sort_folder_dict(folder_dict[key])
            else:
                sorted_dict[key] = folder_dict[key]
        return sorted_dict

    def display_placeholder(self):
        """Display a placeholder message when the bucket is empty or fetch failed."""
        # Clear existing thumbnails
        for frame in self.thumbnail_frames:
            frame.destroy()
        self.thumbnail_frames.clear()

        placeholder_label = ttk.Label(self.scrollable_frame, text="No content available.", font=("Segoe UI", 16), foreground='#555555')
        placeholder_label.pack(pady=20)

        # Optionally, display local folder contents
        if self.config.get('sync_folder') and os.path.isdir(self.config.get('sync_folder')):
            self.display_local_contents()
        else:
            no_sync_label = ttk.Label(self.scrollable_frame, text="No sync folder selected.", font=("Segoe UI", 16), foreground='#555555')
            no_sync_label.pack(pady=20)

    def display_local_contents(self):
        """Display the contents of the local sync folder using a grid layout with folder hierarchy."""
        sync_folder = self.config.get('sync_folder')
        if not sync_folder or not os.path.isdir(sync_folder):
            placeholder_label = ttk.Label(self.scrollable_frame, text="No sync folder selected.", font=("Segoe UI", 16), foreground='#555555')
            placeholder_label.pack(pady=20)
            return

        # Clear existing thumbnails
        for frame in self.thumbnail_frames:
            frame.destroy()
        self.thumbnail_frames.clear()

        # Build a nested dictionary to represent folder hierarchy
        folder_dict = {}
        for root_dir, dirs, files in os.walk(sync_folder):
            for file in files:
                file_path = os.path.join(root_dir, file)
                relative_path = os.path.relpath(file_path, sync_folder)
                parts = relative_path.split('/')
                current_level = folder_dict
                for part in parts[:-1]:
                    current_level = current_level.setdefault(part, {})
                current_level[parts[-1]] = None  # File

        # Sort the folder_dict
        sorted_folder_dict = self.sort_folder_dict(folder_dict)

        # Display folders and files
        self.display_folder_contents(sorted_folder_dict, parent_row=0, indent=0)

    def get_thumbnail_path(self, file_key, file_type, is_s3=False):
        """Get the path for the cached thumbnail."""
        if is_s3:
            # For S3, organize thumbnails in a similar folder structure
            thumbnail_filename = f"{os.path.splitext(file_key)[0]}_thumbnail.jpg"
            thumbnail_path = os.path.join('frontend', 'assets', 'thumbnails', thumbnail_filename)
        else:
            # For local files, organize thumbnails in a similar folder structure
            thumbnail_filename = f"{os.path.splitext(file_key)[0]}_thumbnail.jpg"
            thumbnail_path = os.path.join('frontend', 'assets', 'thumbnails', thumbnail_filename)
        return thumbnail_path

    def generate_thumbnail(self, file_key, thumbnail_path, file_type, is_s3=False):
        """Generate a thumbnail for a video or image."""
        try:
            if file_type == 'video':
                if is_s3:
                    # Download the video to a temporary location
                    temp_dir = tempfile.mkdtemp()
                    temp_video_path = os.path.join(temp_dir, os.path.basename(file_key))
                    self.aws_integration.s3.download_file(self.bucket_name, file_key, temp_video_path)
                else:
                    sync_folder = self.config.get('sync_folder')
                    temp_video_path = os.path.join(sync_folder, file_key)

                cap = cv2.VideoCapture(temp_video_path)
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame)
                    image = image.resize((150, 100), resample=self.get_resample_filter())
                    # Ensure the thumbnail directory exists
                    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                    image.save(thumbnail_path, format='JPEG')
                    logger.info(f"Generated thumbnail for {file_key}")
                cap.release()

                if is_s3:
                    shutil.rmtree(temp_dir, ignore_errors=True)

            elif file_type == 'image':
                if is_s3:
                    # Download the image to a temporary location
                    temp_dir = tempfile.mkdtemp()
                    temp_image_path = os.path.join(temp_dir, os.path.basename(file_key))
                    self.aws_integration.s3.download_file(self.bucket_name, file_key, temp_image_path)
                    image = Image.open(temp_image_path)
                    image = image.resize((150, 100), resample=self.get_resample_filter())
                    # Ensure the thumbnail directory exists
                    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                    image.save(thumbnail_path, format='JPEG')
                    shutil.rmtree(temp_dir, ignore_errors=True)
                else:
                    sync_folder = self.config.get('sync_folder')
                    image_path = os.path.join(sync_folder, file_key)
                    image = Image.open(image_path)
                    image = image.resize((150, 100), resample=self.get_resample_filter())
                    # Ensure the thumbnail directory exists
                    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                    image.save(thumbnail_path, format='JPEG')
                    logger.info(f"Generated thumbnail for {file_key}")
        except Exception as e:
            logger.error(f"Error generating thumbnail for {file_key}: {e}")

    def load_thumbnail_image(self, thumbnail_path, file_type):
        """Load the thumbnail image."""
        if os.path.exists(thumbnail_path):
            try:
                image = Image.open(thumbnail_path)
                image = image.resize((150, 100), resample=self.get_resample_filter())
                thumbnail_image = ImageTk.PhotoImage(image)
            except Exception as e:
                logger.error(f"Error loading thumbnail image at {thumbnail_path}: {e}")
                thumbnail_image = self.icons.get('file', self.icons.get('file'))
        else:
            thumbnail_image = self.icons.get('file', self.icons.get('file'))
        return thumbnail_image

    def get_file_type(self, extension):
        """Determine the file type based on extension."""
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        audio_exts = ['.mp3', '.wav', '.aac', '.flac']
        video_exts = ['.mp4', '.avi', '.mov', '.mkv']
        if extension in image_exts:
            return 'image'
        elif extension in audio_exts:
            return 'audio'
        elif extension in video_exts:
            return 'video'
        else:
            return 'other'

    def open_selected_file(self, file_name, file_type):
        """Open the selected file with Windows Media Player."""
        if file_type == 'video':
            # Open video using presigned URL if in S3, else open locally
            is_s3 = self.bucket_name and self.bucket_name in self.aws_integration.get_existing_buckets()
            if is_s3:
                threading.Thread(target=self.generate_presigned_url_and_open_media_player, args=(file_name,), daemon=True).start()
            else:
                sync_folder = self.config.get('sync_folder')
                file_path = os.path.join(sync_folder, file_name)
                if os.path.exists(file_path):
                    try:
                        # Open with Windows Media Player
                        wmplayer_path = self.get_windows_media_player_path()
                        if wmplayer_path:
                            subprocess.Popen([wmplayer_path, file_path], shell=False)
                        else:
                            messagebox.showerror("Error", "Windows Media Player not found.")
                    except Exception as e:
                        logger.error(f"Error opening file {file_path}: {e}")
                        messagebox.showerror("Error", f"Failed to open video: {e}")
                else:
                    messagebox.showerror("Error", f"File not found: {file_path}")
        elif file_type == 'folder':
            # Navigate into the folder
            self.open_folder(file_name, file_type)
        else:
            # Implement for other file types as needed
            messagebox.showinfo("Info", f"Opening file: {file_name}")

    def generate_presigned_url_and_open_media_player(self, file_name):
        """Generate a presigned URL for the S3 video and open it with Windows Media Player."""
        try:
            # Construct the full object key with current prefix
            object_key = f"{self.current_prefix}{file_name}" if self.current_prefix else file_name
            presigned_url = self.aws_integration.generate_presigned_url(self.bucket_name, object_key)

            if presigned_url:
                logger.info(f"Presigned URL for {object_key}: {presigned_url}")  # Log the URL for debugging

                # Path to Windows Media Player executable
                wmplayer_path = self.get_windows_media_player_path()
                if wmplayer_path:
                    # Prepare Windows Media Player command-line arguments as a list
                    wmp_args = [
                        wmplayer_path,
                        presigned_url  # Presigned URL as the media to play
                    ]

                    # Execute Windows Media Player without invoking the shell
                    subprocess.Popen(wmp_args, shell=False)

                    logger.info(f"Windows Media Player started with command: {' '.join(wmp_args)}")
                else:
                    messagebox.showerror("Error", "Windows Media Player not found. Please ensure it is installed.")
            else:
                messagebox.showerror("Error", "Failed to generate presigned URL.")
        except Exception as e:
            logger.error(f"Error generating presigned URL for {file_name}: {e}")
            messagebox.showerror("Error", f"Failed to open video: {e}")

    def get_windows_media_player_path(self):
        """Get the path to the Windows Media Player executable."""
        # Common installation paths for Windows Media Player
        possible_paths = [
            r"C:\Program Files\Windows Media Player\wmplayer.exe",
            r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        # Attempt to locate via environment variables or registry if necessary
        logger.error("Windows Media Player executable not found in common paths.")
        return None

    def open_folder(self, folder_name, file_type):
        """Handle folder click events by navigating into the folder."""
        if file_type == 'folder':
            # Update the current prefix to include the clicked folder
            new_prefix = f"{self.current_prefix}{folder_name}/"
            self.current_prefix = new_prefix

            # Enable the Back button
            self.back_button.config(state='normal')

            # Reload S3 contents with the new prefix
            self.fetch_and_display_s3_contents_thread()

    def sort_contents(self, criteria):
        """Sort the contents based on the selected criteria."""
        # Implement sorting logic based on criteria
        # For simplicity, currently only supports alphabetical sorting
        self.load_s3_contents()

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.grab_set()  # Make the settings window modal

        # AWS Credentials
        ttk.Label(settings_window, text="AWS Access Key:", font=self.label_font).pack(pady=5, anchor='w', padx=20)
        access_key_entry = ttk.Entry(settings_window, width=50, show="*", font=self.label_font)
        access_key_entry.pack(pady=5, padx=20)
        access_key_entry.insert(0, self.config.get('aws_access_key'))

        ttk.Label(settings_window, text="AWS Secret Key:", font=self.label_font).pack(pady=5, anchor='w', padx=20)
        secret_key_entry = ttk.Entry(settings_window, width=50, show="*", font=self.label_font)
        secret_key_entry.pack(pady=5, padx=20)
        secret_key_entry.insert(0, self.config.get('aws_secret_key'))

        ttk.Label(settings_window, text="Region:", font=self.label_font).pack(pady=5, anchor='w', padx=20)
        region_entry = ttk.Entry(settings_window, width=50, font=self.label_font)
        region_entry.pack(pady=5, padx=20)
        region_entry.insert(0, self.config.get('region'))

        # Save Button
        def save_settings():
            access_key = access_key_entry.get().strip()
            secret_key = secret_key_entry.get().strip()
            region = region_entry.get().strip()

            if not region:
                messagebox.showerror("Error", "Region cannot be empty.")
                return

            self.config['aws_access_key'] = access_key
            self.config['aws_secret_key'] = secret_key
            self.config['region'] = region
            self.config_manager.save_config(self.config)

            # Update AWSIntegration with new credentials
            self.aws_integration = AWSIntegration(
                access_key=access_key if access_key else None,
                secret_key=secret_key if secret_key else None,
                region=region
            )
            # Update FileSync with new credentials
            self.file_sync.aws_access_key = access_key
            self.file_sync.aws_secret_key = secret_key
            self.file_sync.region = region
            self.file_sync.s3_client = self.file_sync.initialize_s3_client()

            messagebox.showinfo("Settings", "Settings saved successfully.")
            settings_window.destroy()
            self.load_buckets()  # Refresh bucket list after saving settings

        save_button = ttk.Button(settings_window, text="Save", command=save_settings, style='Sync.TButton')
        save_button.pack(pady=20)
        logger.info("Settings window created.")

    def open_s3_bucket(self):
        """Open the S3 bucket in the default web browser."""
        region = self.config.get('region') or 'us-east-2'
        bucket_name = self.config.get('bucket_name')
        if not bucket_name:
            messagebox.showerror("Error", "No S3 bucket selected.")
            return
        # Corrected the URL format for AWS S3 console
        url = f"https://s3.console.aws.amazon.com/s3/buckets/{bucket_name}?region={region}&tab=objects"
        webbrowser.open(url)
        logger.info(f"Opened S3 bucket in browser: {url}")

    def on_closing(self):
        """Handle the application closing."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.file_sync.stop_sync()
            self.root.destroy()
            logger.info("Application closed by user.")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_bucket_selected(self, event):
        """Update the bucket_name when a new bucket is selected."""
        selected_bucket = self.bucket_combo.get()
        self.bucket_name = selected_bucket
        self.config['bucket_name'] = selected_bucket
        self.config_manager.save_config(self.config)
        logger.info(f"Selected bucket: {self.bucket_name}")
        self.current_prefix = ""  # Reset to root when changing buckets
        self.back_button.config(state='disabled')  # Disable Back button at root
        self.load_s3_contents()

    def go_back(self):
        """Navigate to the parent directory."""
        if self.current_prefix:
            # Remove the last folder from the current prefix
            parts = self.current_prefix.rstrip('/').split('/')
            parts = parts[:-1]  # Remove last part
            self.current_prefix = '/'.join(parts) + '/' if parts else ''

            # Reload S3 contents
            self.fetch_and_display_s3_contents_thread()

        # Disable back button if at root
        if not self.current_prefix:
            self.back_button.config(state='disabled')
        else:
            self.back_button.config(state='normal')