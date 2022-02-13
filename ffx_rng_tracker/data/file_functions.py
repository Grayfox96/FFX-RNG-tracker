import os
import sys


def get_resource_path(relative_path: str) -> str:
    """Get the absolute path to a resource,
    necessary for https://github.com/brentvollebregt/auto-py-to-exe
    and for PyInstaller.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_version() -> tuple[int, int, int]:
    """Used to retrieve the version number from the version file."""
    absolute_file_path = get_resource_path('data/VERSION')
    with open(absolute_file_path) as file_object:
        version = file_object.read()
    return version.split('.')
