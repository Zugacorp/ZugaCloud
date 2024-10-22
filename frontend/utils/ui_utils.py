# File: frontend/utils/ui_utils.py

from PIL import Image, ImageTk, ImageFont, ImageDraw
import os
import logging

logger = logging.getLogger(__name__)

def load_image(path, size=None):
    try:
        image = Image.open(path)
        if size:
            image = image.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception as e:
        logger.error(f"Error loading image at {path}: {e}")
        return None

def load_icons():
    icons = {}
    icon_folder = os.path.join('assets', 'icons')
    icon_files = {
        "folder": "folder_icon.png",
        "audio": "audio_icon.png",
        "video": "video_icon.png",
        "image": "file_icon.png",  # Changed to use file_icon.png for image
        "file": "file_icon.png",
    }

    for key, filename in icon_files.items():
        path = os.path.join(icon_folder, filename)
        icons[key] = load_image(path, (150, 100))
        if icons[key] is None:
            logger.warning(f"Failed to load icon: {filename}")
            # Use a default icon or create a blank image
            icons[key] = create_blank_icon((150, 100))

    return icons

def create_blank_icon(size):
    # Create a blank white image
    image = Image.new('RGB', size, color='white')
    return ImageTk.PhotoImage(image)

def get_file_type(file_name):
    if file_name.endswith('/'):
        return 'folder'
    _, ext = os.path.splitext(file_name)
    ext = ext.lower()

    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        return 'image'
    elif ext in ['.mp3', '.wav', '.aac', '.flac']:
        return 'audio'
    elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
        return 'video'
    else:
        return 'file'

def create_z_icon(size=(32, 32), color='#1E90FF', save_path='assets/z_icon.ico'):
    image = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a "Z"
    font = get_default_font(size[0]//2)
    draw.text((size[0]//4, size[1]//4), "Z", fill=color, font=font)
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Save as ICO
    image.save(save_path, format='ICO', sizes=[(32, 32)])
    
    return save_path

def get_default_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()