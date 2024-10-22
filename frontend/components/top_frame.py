# File: frontend/components/top_frame.py

import tkinter as tk
from tkinter import ttk
from ..utils.ui_utils import load_image, create_blank_icon
import os
import logging

logger = logging.getLogger(__name__)

class TopFrame(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        self.create_frames()
        self.setup_left_frame()
        self.setup_right_frame()

    def create_frames(self):
        self.left_frame = ttk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky='w', padx=20, pady=20)

        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=0, column=1, sticky='e', padx=20, pady=20)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

    def setup_left_frame(self):
        self.setup_logo()
        self.setup_back_button()
        self.setup_folder_selection()
        self.setup_bucket_selection()

    def setup_right_frame(self):
        self.setup_sort_options()
        self.setup_settings_button()
        self.setup_open_bucket_button()

    def setup_logo(self):
        logo_path = os.path.join('assets', 'logo', 'zugacloud_logo.png')
        self.logo_image = load_image(logo_path, (120, 120))
        if self.logo_image:
            self.logo_label = ttk.Label(self.left_frame, image=self.logo_image)
        else:
            blank_logo = create_blank_icon((120, 120))
            self.logo_label = ttk.Label(self.left_frame, image=blank_logo, text="ZugaCloud", 
                                        compound='center', font=("Segoe UI", 14, "bold"))
            self.logo_label.image = blank_logo
        self.logo_label.grid(row=0, column=0, rowspan=2, padx=(0, 20), sticky='w')

    def setup_back_button(self):
        self.back_button = ttk.Button(self.left_frame, text="Back", command=self.main_window.go_back)
        self.back_button.grid(row=0, column=1, padx=(0, 10), pady=(0, 5), sticky='w')
        self.back_button.config(state='disabled')

    def setup_folder_selection(self):
        self.folder_label = ttk.Label(self.left_frame, text="Sync Folder:", font=("Segoe UI", 12))
        self.folder_label.grid(row=1, column=1, padx=(0, 10), pady=(5, 0), sticky='w')

        self.folder_entry = ttk.Entry(self.left_frame, width=60, font=("Segoe UI", 12))
        self.folder_entry.grid(row=1, column=2, padx=(0, 10), pady=(5, 0), sticky='w')
        self.folder_entry.insert(0, self.main_window.config.get('sync_folder', ''))

        self.browse_button = ttk.Button(self.left_frame, text="Browse", command=self.main_window.browse_folder)
        self.browse_button.grid(row=1, column=3, padx=(0, 10), pady=(5, 0), sticky='w')

    def setup_bucket_selection(self):
        self.bucket_label = ttk.Label(self.left_frame, text="S3 Bucket:", font=("Segoe UI", 12))
        self.bucket_label.grid(row=2, column=1, padx=(0, 10), pady=(10, 0), sticky='w')

        self.bucket_combo = ttk.Combobox(self.left_frame, values=self.main_window.aws_integration.get_existing_buckets(), state='readonly', font=("Segoe UI", 12))
        self.bucket_combo.grid(row=2, column=2, padx=(0, 10), pady=(10, 0), sticky='w')
        self.bucket_combo.set(self.main_window.config.get('bucket_name', ''))
        self.bucket_combo.bind("<<ComboboxSelected>>", self.main_window.on_bucket_selected)

        self.refresh_buckets_button = ttk.Button(self.left_frame, text="Refresh Buckets", command=self.main_window.refresh_buckets)
        self.refresh_buckets_button.grid(row=2, column=3, padx=(0, 10), pady=(10, 0), sticky='w')

        self.add_bucket_button = ttk.Button(self.left_frame, text="Add Bucket", command=self.main_window.add_bucket)
        self.add_bucket_button.grid(row=2, column=4, padx=(0, 10), pady=(10, 0), sticky='w')

    def setup_sort_options(self):
        self.sort_var = tk.StringVar()
        self.sort_var.set("Alphabet")
        self.sort_label = ttk.Label(self.right_frame, text="Sort By:", font=("Segoe UI", 12))
        self.sort_label.grid(row=0, column=0, padx=(0, 10), pady=(0, 5), sticky='e')

        self.sort_menu = ttk.OptionMenu(self.right_frame, self.sort_var, "Alphabet", "Alphabet", "Date", "Last Opened", command=self.main_window.sort_contents)
        self.sort_menu.grid(row=0, column=1, padx=(0, 10), pady=(0, 5), sticky='w')

    def setup_settings_button(self):
        self.settings_button = ttk.Button(self.right_frame, text="Settings", command=self.main_window.open_settings)
        self.settings_button.grid(row=0, column=2, padx=(0, 10), pady=(0, 5), sticky='w')

    def setup_open_bucket_button(self):
        self.open_bucket_button = ttk.Button(self.right_frame, text="Open S3 Bucket", command=self.main_window.open_s3_bucket)
        self.open_bucket_button.grid(row=0, column=3, padx=(0, 10), pady=(0, 5), sticky='w')

    def update_sync_folder(self, folder):
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, folder)

    def update_bucket_list(self, buckets):
        self.bucket_combo['values'] = buckets
        if self.main_window.config.get('bucket_name') in buckets:
            self.bucket_combo.set(self.main_window.config.get('bucket_name'))

    def enable_back_button(self):
        self.back_button.config(state='normal')

    def disable_back_button(self):
        self.back_button.config(state='disabled')