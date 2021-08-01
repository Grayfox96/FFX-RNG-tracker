import ffx_rng_tracker
import tkinter as tk
from tkinter import font
from ffx_rng_tracker_ui import on_ui_close, FFXMonsterDataViewerUI


class FFXInfo(ffx_rng_tracker.FFXRNGTracker):
    '''Overrides the init method of the rng tracker since
    rng tracking is not necessary.'''

    def __init__(self) -> None:
        self.abilities = self.get_ability_names('files/ffxhd-abilities.csv')
        self.items = self.get_item_names('files/ffxhd-items.csv')
        self.text_characters = self.get_text_characters(
            'files/ffxhd-characters.csv')
        self.monsters_data = self.get_monsters_data(
            'files/ffxhd-mon_data.csv')

        self._patch_monsters_dict_for_hd()


def main():
    ffx_info = FFXInfo()

    root = tk.Tk()
    root.protocol(
        'WM_DELETE_WINDOW', lambda: on_ui_close(root))
    root.title('ffx_monster_data_viewer')
    root.geometry('1280x800')

    ui = FFXMonsterDataViewerUI(root, ffx_info)

    root.mainloop()


if __name__ == '__main__':
    main()
