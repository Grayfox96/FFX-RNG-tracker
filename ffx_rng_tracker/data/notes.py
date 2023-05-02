import os
import shutil
from logging import getLogger

from ..configs import Configs
from ..utils import open_cp1252, stringify
from .file_functions import get_resource_path


def get_notes(file_name: str, seed: int | None = None) -> str:
    """Get notes from a file, either custom or default."""
    logger = getLogger(__name__)
    if not os.path.exists(NOTES_DIRECTORY_PATH):
        logger.warning('Notes directory not found.')
        os.mkdir(NOTES_DIRECTORY_PATH)
        logger.info(f'Created notes directory "{NOTES_DIRECTORY_PATH}".')

    category_dir = stringify(Configs.speedrun_category)
    category_dir_path = f'{NOTES_DIRECTORY_PATH}/{category_dir}'
    if not os.path.exists(category_dir_path):
        logger.warning('Notes category subdirectory not found.')
        os.mkdir(category_dir_path)
        logger.info(f'Created notes subdirectory "{category_dir_path}"')

    default_file_path = f'{category_dir_path}/{file_name}'
    if not os.path.exists(default_file_path):
        logger.warning(f'Default notes file "{file_name}" for category '
                       f'"{category_dir}" not found.')
        shutil.copyfile(
            get_resource_path(f'notes/{category_dir}/{file_name}'),
            default_file_path,
            )
        logger.info(f'Copied default notes file to "{default_file_path}".')

    file_path = f'{category_dir_path}/{seed}_{file_name}'
    if not os.path.exists(file_path):
        file_path = default_file_path
    with open_cp1252(file_path) as notes_file:
        notes = notes_file.read()

    return notes


def save_notes(file_name: str,
               seed: int,
               notes: str,
               /,
               force: bool = False,
               ) -> None:
    category_dir = stringify(Configs.speedrun_category)
    file_path = f'{NOTES_DIRECTORY_PATH}/{category_dir}/{seed}_{file_name}'
    if not force and os.path.exists(file_path):
        raise FileExistsError(file_path)
    with open_cp1252(file_path, 'w') as notes_file:
        notes_file.write(notes)
    getLogger(__name__).info(f'Saved notes file to "{file_path}".')


NOTES_DIRECTORY_PATH = 'ffx_rng_tracker_notes'
