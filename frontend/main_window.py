# File: frontend/main_window.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
from .components.top_frame import TopFrame
from .components.middle_frame import MiddleFrame
from .components.bottom_frame import BottomFrame
from backend.config_manager import ConfigManager
from backend.aws_integration import AWSIntegration
from backend.file_sync import FileSync
from .dialogs.settings_dialog import SettingsDialog
from .utils.ui_utils import create_z_icon
import ctypes
import win32gui
import win32api
import win32con
import logging
import threading
import webbrowser
import subprocess
import queue
import io
import os
import sys

logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self, root, config_manager, aws_integration, file_sync):
        self.root = root
        self.root.title("ZugaCloud - Infinite Video Storage")
        self.root.geometry('1300x900')
        self.root.resizable(True, True)

        self.config_manager = config_manager
        self.config = self.config_manager.load_config()
        self.aws_integration = aws_integration
        self.file_sync = file_sync

        self.update_queue = queue.Queue()
        self.file_sync.update_queue = self.update_queue

        self.setup_styles()
        self.setup_icons()
        self.create_frames()
        self.setup_protocol_handlers()
        self.load_initial_contents()
        self.start_update_checker()

        self.root.after(1000, self.setup_taskbar_icon)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#F5F5F5')
        self.style.configure('TLabel', background='#F5F5F5', font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10), padding=5)
        self.style.configure('Sync.TButton', font=('Segoe UI', 12, 'bold'), padding=10, background='#4CAF50', foreground='white')
        self.style.map('Sync.TButton', background=[('active', '#45a049')])
        self.style.configure('Stop.TButton', font=('Segoe UI', 12, 'bold'), padding=10, background='#f44336', foreground='white')
        self.style.map('Stop.TButton', background=[('active', '#d32f2f')])

    def setup_icons(self):
        cool_z_icon = self.create_cool_z_icon()
        self.icons = {
            'file': cool_z_icon,
            'folder': cool_z_icon,
            'video': cool_z_icon,
            'audio': cool_z_icon,
            'image': cool_z_icon,
        }

    def create_cool_z_icon(self, size=(150, 100)):
        image = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(image)

        for y in range(size[1]):
            r = int(255 * (1 - y / size[1]))
            g = int(200 * (1 - y / size[1]))
            b = 255
            draw.line([(0, y), (size[0], y)], fill=(r, g, b))

        font_size = min(size) // 2
        font = self.get_default_font(font_size)
        
        shadow_offset = font_size // 10
        draw.text((size[0]//2 + shadow_offset, size[1]//2 + shadow_offset), 'Z', fill='darkblue', font=font, anchor='mm')
        draw.text((size[0]//2, size[1]//2), 'Z', fill='white', font=font, anchor='mm')

        draw.rectangle([0, 0, size[0]-1, size[1]-1], outline='lightblue', width=2)

        return ImageTk.PhotoImage(image)

    def get_default_font(self, size):
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            return ImageFont.load_default()

    def create_frames(self):
        self.top_frame = TopFrame(self.root, self)
        self.top_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=20)

        self.middle_frame = MiddleFrame(self.root, self)
        self.middle_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=20)

        self.bottom_frame = BottomFrame(self.root, self)
        self.bottom_frame.grid(row=2, column=0, sticky='ew', padx=20, pady=20)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def setup_protocol_handlers(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_initial_contents(self):
        if self.aws_integration.is_initialized():
            self.refresh_contents()
        else:
            self.middle_frame.display_error("AWS integration not initialized. Please check your settings.")

    def start_sync(self):
        sync_folder = self.config.get('sync_folder')
        bucket_name = self.config.get('bucket_name')
        if not sync_folder or not bucket_name:
            messagebox.showerror("Error", "Please set both sync folder and bucket name before syncing.")
            return
        self.bottom_frame.reset_progress()
        threading.Thread(target=self.file_sync.start_sync, args=(sync_folder, bucket_name), daemon=True).start()

    def stop_sync(self):
        self.file_sync.stop_sync()

    def start_update_checker(self):
        self.root.after(100, self.check_updates)

    def check_updates(self):
        try:
            while True:
                update = self.update_queue.get_nowait()
                if update[0] == "status":
                    self.bottom_frame.update_status(update[1])
                elif update[0] == "progress":
                    self.bottom_frame.update_progress(update[1], update[2])
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_updates)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.file_sync.stop_sync()
            self.root.destroy()
            logger.info("Application closed by user.")

    def open_file(self, key, file_type):
        if file_type == 'folder':
            self.middle_frame.current_prefix = key
            self.middle_frame.load_s3_contents()
        else:
            threading.Thread(target=self._open_file_thread, args=(key, file_type), daemon=True).start()

    def _open_file_thread(self, key, file_type):
        try:
            if file_type == 'video':
                self._open_video(key)
            elif file_type == 'audio':
                self._open_audio(key)
            elif file_type == 'image':
                self._open_image(key)
            else:
                self.root.after(0, messagebox.showinfo, "Open File", f"Opening file: {key}")
        except Exception as e:
            logger.error(f"Error opening file {key}: {e}")
            self.root.after(0, messagebox.showerror, "Error", f"Failed to open file: {e}")

    def _open_video(self, key):
        try:
            presigned_url = self.aws_integration.generate_presigned_url(
                self.config.get('bucket_name'),
                key
            )
            if presigned_url:
                self.root.after(0, self.play_video_with_media_player, presigned_url)
            else:
                self.root.after(0, messagebox.showerror, "Error", "Failed to generate presigned URL.")
        except Exception as e:
            logger.error(f"Error opening video {key}: {e}")
            self.root.after(0, messagebox.showerror, "Error", f"Failed to open video: {e}")

    def play_video_with_media_player(self, url):
        try:
            if os.name == 'nt':  # Windows
                vlc_path = self.get_vlc_path()
                if vlc_path:
                    subprocess.Popen([vlc_path, url])
                else:
                    os.startfile(url)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', url], check=True)
            else:  # Linux and others
                subprocess.run(['xdg-open', url], check=True)
        except Exception as e:
            logger.error(f"Error playing video: {e}")
            self.root.after(0, messagebox.showerror, "Error", f"Failed to play video: {e}")
            webbrowser.open(url)

    def get_vlc_path(self):
        common_paths = [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return None

    def _open_audio(self, key):
        # Implement audio opening logic
        pass

    def _open_image(self, key):
        # Implement image opening logic
        pass

    def refresh_contents(self):
        if self.aws_integration.is_initialized():
            self.middle_frame.load_s3_contents()
        else:
            messagebox.showerror("Error", "AWS integration not initialized. Please check your settings.")

    def update_config(self, new_config):
        self.config = new_config
        self.config_manager.save_config(self.config)
        self.aws_integration.update_credentials(
            access_key=self.config.get('aws_access_key'),
            secret_key=self.config.get('aws_secret_key'),
            region=self.config.get('region')
        )
        self.file_sync.update_config(self.config)
        self.refresh_contents()

    def open_settings(self):
        SettingsDialog(self.root, self.config_manager, self.aws_integration)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.config['sync_folder'] = folder_selected
            self.config_manager.save_config(self.config)
            self.top_frame.update_sync_folder(folder_selected)
            self.file_sync.manage_syncto_s3_bat(folder_selected)

    def refresh_buckets(self):
        buckets = self.aws_integration.get_existing_buckets()
        self.top_frame.update_bucket_list(buckets)
        self.refresh_contents()

    def add_bucket(self):
        bucket_name = simpledialog.askstring("Add Bucket", "Enter new S3 bucket name:")
        if bucket_name:
            success = self.aws_integration.create_s3_bucket(bucket_name)
            if success:
                messagebox.showinfo("Success", f"Bucket '{bucket_name}' created successfully.")
                self.refresh_buckets()
            else:
                messagebox.showerror("Error", f"Failed to create bucket '{bucket_name}'.")

    def on_bucket_selected(self, event=None):
        selected_bucket = self.top_frame.bucket_combo.get()
        self.config['bucket_name'] = selected_bucket
        self.config_manager.save_config(self.config)
        self.refresh_contents()

    def open_s3_bucket(self):
        bucket_name = self.config.get('bucket_name')
        region = self.config.get('region', 'us-east-2')
        if bucket_name:
            url = f"https://s3.console.aws.amazon.com/s3/buckets/{bucket_name}?region={region}&tab=objects"
            webbrowser.open(url)
        else:
            messagebox.showerror("Error", "No S3 bucket selected.")

    def sort_contents(self, sort_type):
        self.middle_frame.sort_contents(sort_type)

    def setup_taskbar_icon(self):
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons', 'z_icon.ico'))
        logging.info(f"Attempting to set icon from: {icon_path}")
        if os.path.exists(icon_path):
            try:
                # Set the taskbar icon
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ZugaCloud.1')
                
                # Set icon using wm_iconbitmap
                self.root.wm_iconbitmap(icon_path)
                
                # Get the window handle
                hwnd = win32gui.GetParent(self.root.winfo_id())
                
                # Load the icon
                icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                hicon = win32gui.LoadImage(None, icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags)
                
                # Set the icon for the window
                win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)
                win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
                
                logging.info(f"Window handle: {hwnd}")
                logging.info(f"Icon handle: {hicon}")
                logging.info(f"Taskbar icon set successfully: {icon_path}")
            except Exception as e:
                logging.error(f"Failed to set taskbar icon: {e}", exc_info=True)
        else:
            logging.error(f"Icon file not found: {icon_path}")

    def go_back(self):
        if hasattr(self, 'middle_frame'):
            self.middle_frame.go_back()