import configparser
import os
import shutil
from dataclasses import dataclass

from .data.file_functions import get_resource_path


@dataclass
class UIWidgetConfigs:
    shown: bool
    windowed: bool

    def __str__(self) -> str:
        return ' '.join([f'{v}: {k}' for v, k in vars(self).items()])


class Configs:
    seed: int | None
    ps2: bool
    ps2_seeds_minutes: int
    use_dark_mode: bool
    use_unicode: bool
    font_size: int
    use_theme: bool
    colors: dict[str, tuple[str, str]] = {}
    important_monsters: list[str]
    ui_widgets: dict[str, UIWidgetConfigs] = {}
    _parser = configparser.ConfigParser()
    _configs_file = 'ffx_rng_tracker_configs.ini'
    _default_configs_file = 'data/default_configs.ini'

    @classmethod
    def getboolean(cls, section: str, option: str, fallback: bool) -> bool:
        try:
            return cls._parser.getboolean(section, option, fallback=fallback)
        except ValueError:
            return fallback

    @classmethod
    def getint(cls, section: str, option: str, fallback: int) -> int:
        try:
            return cls._parser.getint(section, option, fallback=fallback)
        except ValueError:
            return fallback

    @classmethod
    def get(cls, section: str, option: str, fallback: str) -> str:
        return cls._parser.get(section, option, fallback=fallback)

    @classmethod
    def read(cls, file_path: str) -> None:
        cls._parser.read(file_path)

    @classmethod
    def load_configs(cls) -> None:
        section = 'General'
        seed = cls.getint(section, 'seed', None)
        if seed is not None and (0 <= seed <= 0xffffffff):
            cls.seed = seed
        else:
            cls.seed = None
        cls.ps2 = cls.getboolean(section, 'ps2', False)
        cls.ps2_seeds_minutes = cls.getint(section, 'ps2 seeds minutes', 3)

        section = 'UI'
        cls.use_dark_mode = cls.getboolean(section, 'use dark mode', False)
        cls.font_size = cls.getint(section, 'fontsize', 9)
        cls.use_unicode = cls.getboolean(section, 'use unicode', True)
        cls.use_theme = cls.getboolean(section, 'use theme', True)

        section = 'Colors'
        options = (
            'preemptive', 'ambush', 'encounter', 'crit', 'stat update',
            'comment', 'advance rng', 'equipment', 'no encounters',
            'yojimbo low gil', 'yojimbo high gil', 'error', 'status miss',
            'important monster',
        )
        if cls.use_dark_mode:
            fg_fallback, bg_fallback = '#ffffff', '#333333'
        else:
            fg_fallback, bg_fallback = '#000000', '#ffffff'
        for option in options:
            foreground = cls.get(section, option, fg_fallback)
            if len(foreground) == 7 and foreground[0] == '#':
                try:
                    int(foreground[1:], 16)
                except ValueError:
                    foreground = fg_fallback
            else:
                foreground = fg_fallback
            background = cls.get(section, f'{option} background', bg_fallback)
            if len(background) == 7 and background[0] == '#':
                try:
                    int(background[1:], 16)
                except ValueError:
                    background = bg_fallback
            else:
                background = bg_fallback
            cls.colors[option] = (foreground, background)

        ui_widgets = (
            'Seed info', 'Drops', 'Encounters', 'Damage/crits/escapes/misses',
            'Monster Targeting', 'Status', 'Yojimbo', 'Monster Data',
            'Configs',
        )
        for section in ui_widgets:
            shown = cls.getboolean(section, 'shown', True)
            windowed = cls.getboolean(section, 'windowed', False)
            cls.ui_widgets[section] = UIWidgetConfigs(shown, windowed)

        section = 'Encounters'
        monsters = cls.get(section, 'monsters to highlight', 'ghost')
        cls.important_monsters = [m.strip() for m in monsters.split(',')]

    @classmethod
    def get_configs(cls) -> dict[str, str | int | bool]:
        configs = {}
        for attr in dir(cls):
            if not callable(getattr(cls, attr)) and not attr.startswith('_'):
                configs[attr] = getattr(cls, attr)
        return configs

    @classmethod
    def _init_configs(cls) -> None:
        if not os.path.exists(cls._configs_file):
            shutil.copyfile(
                get_resource_path(cls._default_configs_file),
                cls._configs_file)
        Configs.read(cls._configs_file)
        Configs.load_configs()


Configs._init_configs()
