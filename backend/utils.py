# File: backend/utils.py

import os
import sys
import subprocess

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def open_file_explorer(path):
    if os.name == 'nt':  # Windows
        os.startfile(path)
    elif sys.platform == 'darwin':  # macOS
        subprocess.Popen(['open', path])
    else:  # Linux and others
        subprocess.Popen(['xdg-open', path])