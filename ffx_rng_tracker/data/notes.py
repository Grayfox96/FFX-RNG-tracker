import os
import shutil

from ..configs import Configs
from ..utils import stringify
from .constants import SpeedrunCategory
from .file_functions import get_resource_path


def get_notes(file_path: str, seed: int | None = None) -> str:
    """Get notes from a file, either custom or default."""
    category_dir = stringify(Configs.speedrun_category)

    default_file_path = f'{_NOTES_DIRECTORY_PATH}/{category_dir}/{file_path}'
    # if the notes file for the current category doesn't exist
    # in the notes directory make a copy there
    if not os.path.exists(default_file_path):
        shutil.copyfile(
            get_resource_path(f'data/notes/{category_dir}/{file_path}'),
            default_file_path)

    file_path = f'{_NOTES_DIRECTORY_PATH}/{category_dir}/{seed}_{file_path}'

    # try opening the notes file for the current category and seed
    try:
        with open(file_path) as notes_file:
            notes = notes_file.read()
    # if it doesnt exist open the notes file for the current category
    except FileNotFoundError:
        with open(default_file_path) as notes_file:
            notes = notes_file.read()

    return notes


_NOTES_DIRECTORY_PATH = 'ffx_rng_tracker_notes'
try:
    os.mkdir(_NOTES_DIRECTORY_PATH)
except FileExistsError:
    pass

_NOTES_CATEGORIES_SUBDIRECTORIES = {category: stringify(category)
                                    for category in SpeedrunCategory}
for subdirectory in _NOTES_CATEGORIES_SUBDIRECTORIES.values():
    try:
        os.mkdir(f'{_NOTES_DIRECTORY_PATH}/{subdirectory}')
    except FileExistsError:
        pass
