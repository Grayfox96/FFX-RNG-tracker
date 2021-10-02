import csv
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


def get_sliders_settings(file_path: str) -> dict[str, dict[str, str]]:
    sliders_settings = {}
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        file_reader = csv.reader(
            file_object, delimiter=',')
        # skips first line
        next(file_reader)
        for line in file_reader:
            sliders_settings[line[0]] = {
                'min': line[1],
                'default': line[2],
                'max': line[3],
            }
    return sliders_settings


def get_notes(file_path: str):
    """Get notes from a file, either custom or default."""
    try:
        notes_file = open(get_resource_path(file_path))
    except FileNotFoundError:
        notes_file = open(get_resource_path(f'data/{file_path}'))
    notes = notes_file.read()
    notes_file.close()
    return notes
