import os
import shutil

from .file_functions import get_resource_path


def get_notes(file_name: str, seed: int | None = None) -> str:
    """Get notes from a file, either custom or default."""
    default_file_path = f'{_NOTES_DIRECTORY_PATH}/{file_name}'
    if not os.path.exists(default_file_path):
        shutil.copyfile(
            get_resource_path(f'data/{file_name}'), default_file_path)

    file_name = f'{_NOTES_DIRECTORY_PATH}/{seed}_{file_name}'
    try:
        with open(file_name) as notes_file:
            notes = notes_file.read()
    except FileNotFoundError:
        with open(default_file_path) as notes_file:
            notes = notes_file.read()

    return notes


_NOTES_DIRECTORY_PATH = 'ffx_rng_tracker_notes'
try:
    os.mkdir(_NOTES_DIRECTORY_PATH)
except FileExistsError:
    pass
