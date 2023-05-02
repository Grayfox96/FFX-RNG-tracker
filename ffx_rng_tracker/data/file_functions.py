import os
import sys


def get_resource_path(relative_path: str,
                      file_directory: str = 'data_files',
                      ) -> str:
    """Get the absolute path to a resource, necessary for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(__file__)
    resource_path = os.path.join(base_path, file_directory, relative_path)
    return resource_path
