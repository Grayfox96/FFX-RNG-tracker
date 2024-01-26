from datetime import date
from os.path import abspath

import PyInstaller.__main__ as pyinstaller

from ffx_rng_tracker import __version__

version = date.today().strftime('%y.%m.%d')
if __version__ != version:
    print(f'Update version to {version!r}')
    quit()

file_name = abspath('ffx_rng_tracker_ui.py')
name = f'FFX RNG tracker v{__version__}'
data = f'{abspath('ffx_rng_tracker/data/data_files')};data_files/'
ui_tkinter = f'{abspath('ffx_rng_tracker/ui_tkinter/azure_theme')};azure_theme/'

pyinstaller.run([
    f'{file_name}',
    '--noconfirm',
    '--onefile',
    '--windowed',
    f'--name={name}',
    '--add-data', data,
    '--add-data', ui_tkinter,
])
