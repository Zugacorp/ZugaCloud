# File: frontend/components/bottom_frame.py

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

class BottomFrame(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.is_syncing = False
        self.setup_ui()

    def setup_ui(self):
        self.create_sync_button()
        self.create_progress_bar()
        self.create_status_labels()
        self.configure_grid()

    def create_sync_button(self):
        self.sync_button = ttk.Button(self, text="SYNC", command=self.toggle_sync, style='Sync.TButton')
        self.sync_button.grid(row=0, column=0, pady=10, padx=10, sticky='w')

    def create_progress_bar(self):
        self.progress = ttk.Progressbar(self, orient='horizontal', mode='determinate', length=600)
        self.progress.grid(row=0, column=1, columnspan=2, pady=10, padx=10, sticky='ew')

    def create_status_labels(self):
        self.detailed_progress_var = tk.StringVar()
        self.detailed_progress_var.set("Idle")
        self.detailed_progress_label = ttk.Label(self, textvariable=self.detailed_progress_var, font=("Segoe UI", 10))
        self.detailed_progress_label.grid(row=1, column=0, columnspan=3, pady=5, padx=10, sticky='w')

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = ttk.Label(self, textvariable=self.status_var, font=("Segoe UI", 10))
        self.status_label.grid(row=2, column=0, columnspan=3, pady=5, padx=10, sticky='w')

    def configure_grid(self):
        self.columnconfigure(1, weight=1)  # Make the progress bar expandable

    def toggle_sync(self):
        if not self.is_syncing:
            self.start_sync()
        else:
            self.stop_sync()

    def start_sync(self):
        self.is_syncing = True
        self.sync_button.config(text="STOP", style='Stop.TButton')
        self.main_window.start_sync()

    def stop_sync(self):
        self.is_syncing = False
        self.sync_button.config(text="SYNC", style='Sync.TButton')
        self.main_window.stop_sync()

    def update_progress(self, progress, current_file):
        self.progress['value'] = progress
        self.detailed_progress_var.set(f"Uploading: {current_file} - {progress:.1f}%")
        self.update_idletasks()

    def update_status(self, message):
        self.status_var.set(message)
        if message == "Synchronization completed." or message == "Synchronization stopped.":
            self.reset_ui_after_sync()
            self.main_window.refresh_contents()
        self.update_idletasks()

    def reset_ui_after_sync(self):
        self.is_syncing = False
        self.sync_button.config(text="SYNC", style='Sync.TButton')
        self.progress['value'] = 0
        self.detailed_progress_var.set("Idle")
        self.status_var.set("Ready")

    def reset_progress(self):
        self.progress['value'] = 0
        self.detailed_progress_var.set("Idle")
        self.status_var.set("Ready")