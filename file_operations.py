# file_operations.py

import os


def get_dir_contents(path):
    """Gets sorted list of non-hidden files and directories."""
    items = []
    error_message = None
    try:
        for item in os.listdir(path):
            if not item.startswith("."):  # Ignore hidden files/dirs
                full_path = os.path.join(path, item)
                is_dir = os.path.isdir(full_path)
                items.append({"name": item, "is_dir": is_dir, "path": full_path})
    except PermissionError:
        error_message = "Permission Denied"
    except FileNotFoundError:
        error_message = "File Not Found"

    # Sort: directories first, then files, both alphabetically
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return items, error_message
