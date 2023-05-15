import os
import sys


def get_resource_path(relative_path: str,
                      file_directory: str = None,
                      ) -> str:
    """Get the absolute path to a resource, necessary for PyInstaller."""
    try:
        file_directory = sys._MEIPASS
    except AttributeError:
        if file_directory is None:
            file_directory = os.path.dirname(__file__)
    resource_path = os.path.join(file_directory, relative_path)

    return resource_path
