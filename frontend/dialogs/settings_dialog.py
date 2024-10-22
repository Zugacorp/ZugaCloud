# File: frontend/dialogs/settings_dialog.py

import tkinter as tk
from tkinter import ttk, messagebox

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, config_manager, aws_integration):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("500x300")
        self.resizable(False, False)
        self.config_manager = config_manager
        self.aws_integration = aws_integration
        self.config = self.config_manager.load_config()

        self.setup_ui()

    def setup_ui(self):
        self.create_widgets()
        self.load_current_settings()

    def create_widgets(self):
        # AWS Access Key
        ttk.Label(self, text="AWS Access Key:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.access_key_entry = ttk.Entry(self, width=50)
        self.access_key_entry.grid(row=0, column=1, padx=10, pady=5)

        # AWS Secret Key
        ttk.Label(self, text="AWS Secret Key:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.secret_key_entry = ttk.Entry(self, width=50, show="*")
        self.secret_key_entry.grid(row=1, column=1, padx=10, pady=5)

        # Region
        ttk.Label(self, text="Region:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.region_entry = ttk.Entry(self, width=50)
        self.region_entry.grid(row=2, column=1, padx=10, pady=5)

        # Refresh Frequency
        ttk.Label(self, text="Refresh Frequency (seconds):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.refresh_frequency_entry = ttk.Entry(self, width=50)
        self.refresh_frequency_entry.grid(row=3, column=1, padx=10, pady=5)

        # Save Button
        self.save_button = ttk.Button(self, text="Save", command=self.save_settings)
        self.save_button.grid(row=4, column=0, columnspan=2, pady=20)

    def load_current_settings(self):
        self.access_key_entry.insert(0, self.config.get('aws_access_key', ''))
        self.secret_key_entry.insert(0, self.config.get('aws_secret_key', ''))
        self.region_entry.insert(0, self.config.get('region', 'us-east-2'))
        self.refresh_frequency_entry.insert(0, str(self.config.get('refresh_frequency', 300)))

    def save_settings(self):
        new_config = {
            'aws_access_key': self.access_key_entry.get(),
            'aws_secret_key': self.secret_key_entry.get(),
            'region': self.region_entry.get(),
            'refresh_frequency': int(self.refresh_frequency_entry.get()),
            'sync_folder': self.config.get('sync_folder', ''),
            'bucket_name': self.config.get('bucket_name', '')
        }

        self.config_manager.save_config(new_config)
        self.aws_integration.__init__(
            access_key=new_config['aws_access_key'],
            secret_key=new_config['aws_secret_key'],
            region=new_config['region']
        )

        messagebox.showinfo("Settings", "Settings saved successfully.")
        self.destroy()