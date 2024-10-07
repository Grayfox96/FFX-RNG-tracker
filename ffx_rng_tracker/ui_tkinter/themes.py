import os
import tkinter as tk
from logging import getLogger
from tkinter import ttk

from ..data.file_functions import get_resource_path


def import_themes(root: tk.Tk) -> None:
    style = ttk.Style()
    theme_names = style.theme_names()
    for theme_name, path in THEMES_PATHS.items():
        if theme_name in theme_names:
            getLogger(__name__).warning(f'Theme {theme_name} already imported')
            continue
        theme_path = get_resource_path(
            relative_path=path,
            file_directory=THEMES_DIRECTORY,
            )
        try:
            root.tk.call('source', theme_path)
        except tk.TclError as e:
            getLogger(__name__).warning(
                f'Error while importing theme {theme_name}: {e}')


THEMES_DIRECTORY = os.path.dirname(__file__)
THEMES_PATHS = {
    'azure-light': 'azure_theme/azure_light.tcl',
    'azure-dark': 'azure_theme/azure_dark.tcl',
}
