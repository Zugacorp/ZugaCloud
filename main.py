# File: main.py

import tkinter as tk
from tkinter import ttk
import logging
import sys
import queue
import os
import subprocess

from frontend.main_window import MainWindow
from backend.config_manager import ConfigManager
from backend.aws_integration import AWSIntegration
from backend.file_sync import FileSync

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("zugacloud.log"),
                        logging.StreamHandler(sys.stdout)
                    ])

logger = logging.getLogger(__name__)

def check_aws_credentials(config):
    access_key = config.get('aws_access_key')
    secret_key = config.get('aws_secret_key')
    return bool(access_key and secret_key)

def open_readme():
    readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
    if sys.platform == "win32":
        os.startfile(readme_path)
    elif sys.platform == "darwin":
        subprocess.call(["open", readme_path])
    else:
        subprocess.call(["xdg-open", readme_path])

def show_credentials_message(config_manager):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    dialog = tk.Toplevel(root)
    dialog.title("AWS Credentials Required")
    dialog.geometry("400x150")
    dialog.protocol("WM_DELETE_WINDOW", root.quit)  # Handle window close
    
    ttk.Label(dialog, text="AWS Access Key and Secret Key are required.\nPlease follow the instructions in the README to set up your AWS account.", wraplength=350).pack(pady=10)
    
    ttk.Button(dialog, text="Open README", command=open_readme).pack(pady=10)
    
    ttk.Button(dialog, text="Close", command=root.quit).pack(pady=10)
    
    root.mainloop()

def main():
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()

        if not check_aws_credentials(config):
            show_credentials_message(config_manager)
            return  # Exit the application after showing the message

        root = tk.Tk()
        root.title("ZugaCloud - Infinite Video Storage")

        aws_integration = AWSIntegration(
            access_key=config.get('aws_access_key'),
            secret_key=config.get('aws_secret_key'),
            region=config.get('region')
        )

        update_queue = queue.Queue()
        file_sync = FileSync(aws_integration, update_queue)
        file_sync.update_config(config)

        app = MainWindow(root, config_manager, aws_integration, file_sync)

        app.middle_frame.start_auto_refresh()

        root.mainloop()
    except Exception as e:
        logger.exception("An unexpected error occurred:")
        raise

if __name__ == "__main__":
    main()