import tomllib
from logging import getLogger

from ..utils import open_cp1252
from .constants import UIWidget


def get_macros(file_path: str) -> dict[UIWidget, dict[str, str]]:
    logger = getLogger(__name__)
    with open_cp1252(file_path) as macros_file:
        data = macros_file.read()

    try:
        data = tomllib.loads(data)
    except tomllib.TOMLDecodeError as error:
        logger.error(f'Error while parsing "{file_path}": {error}')
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
