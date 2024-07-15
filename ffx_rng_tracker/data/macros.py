import os
import shutil
import tomllib
from logging import getLogger

from ..utils import open_cp1252
from .constants import UIWidget
from .file_functions import get_resource_path


def get_macros() -> dict[UIWidget, dict[str, str]]:
    logger = getLogger(__name__)
    if not os.path.exists(MACROS_FILE):
        logger.warning('Macros file not found.')
        default_macros_file = get_resource_path(
            f'data_files/{DEFAULT_MACROS_FILE}')
        shutil.copyfile(default_macros_file, MACROS_FILE)
        logger.info(f'Copied default macros file to "{MACROS_FILE}"')
    with open_cp1252(MACROS_FILE) as macros_file:
        data = macros_file.read()

    try:
        data = tomllib.loads(data)
    except tomllib.TOMLDecodeError as error:
        logger.error(f'Error while parsing "{MACROS_FILE}": {error}')
        return {}

    if 'General' in data:
        general_macros = data.pop('General')
        if isinstance(general_macros, dict):
            general_macros = {k: v.strip('\n')
                              for k, v in general_macros.items()
                              if isinstance(v, str)}
        else:
            general_macros = {}
    else:
        general_macros = {}

    macros: dict[UIWidget, dict[str, str]] = {}
    for section, section_dict in data.items():
        try:
            widget = UIWidget(section)
        except ValueError:
            continue
        macros_dict = dict(general_macros)
        if isinstance(section_dict, dict):
            for k, v in section_dict.items():
                if not isinstance(v, str):
                    continue
                # necessary to put this key as the last inserted
                # if k was already in the dict
                macros_dict.pop(k, '')
                macros_dict[k] = v.strip('\n')
        macros[widget] = macros_dict
    return macros


MACROS_FILE = 'ffx_rng_tracker_macros.toml'
DEFAULT_MACROS_FILE = 'default_macros.toml'
