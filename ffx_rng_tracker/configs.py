import configparser
import os
import shutil
from dataclasses import dataclass
from logging import getLogger

from .data.constants import GameVersion, SpeedrunCategory
from .data.file_functions import get_resource_path
from .utils import get_contrasting_color


@dataclass
class UIWidgetConfigs:
    shown: bool
    windowed: bool

    def __str__(self) -> str:
        return ' '.join([f'{v}: {k}' for v, k in vars(self).items()])


@dataclass
class Color:
    foreground: str | None
    background: str | None
    select_foreground: str | None
    select_background: str | None


class Configs:
    seed: int | None = None
    game_version: GameVersion = GameVersion.HD
    continue_ps2_seed_search: bool = False
    speedrun_category: SpeedrunCategory | str = SpeedrunCategory.ANYPERCENT
    use_dark_mode: bool = False
    font_size: int = 9
    use_theme: bool = True
    colors: dict[str, Color] = {}
    important_monsters: list[str] = []
    ui_widgets: dict[str, UIWidgetConfigs] = {}
    _parser = configparser.ConfigParser()
    _configs_file = 'ffx_rng_tracker_configs.ini'
    _default_configs_file = 'default_configs.ini'

    @classmethod
    def getsection(cls,
                   section: str,
                   fallback: list[str] = None,
                   ) -> list[str]:
        try:
            return cls._parser.options(section)
        except configparser.NoSectionError:
            if fallback is not None:
                return fallback
            return []

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
    def getlist(cls,
                section: str,
                option: str,
                fallback: list[str] = None,
                ) -> list[str]:
        try:
            string = cls._parser.get(section, option)
        except (ValueError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            return []
        return string.replace(' ', '').split(',')

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
        try:
            cls.game_version = GameVersion(
                cls.get(section, 'game version', 'HD'))
        except ValueError:
            cls.game_version = GameVersion.HD
        cls.continue_ps2_seed_search = cls.getboolean(
            section, 'continue ps2 seed search', False)
        speedrun_category = cls.get(section, 'category', 'AnyPercent')
        try:
            speedrun_category = SpeedrunCategory(speedrun_category)
        except ValueError:
            speedrun_category = ''.join(x for x in speedrun_category
                                        if x.isalnum() or x in '._-')
        if speedrun_category:
            cls.speedrun_category = speedrun_category
        else:
            cls.speedrun_category = SpeedrunCategory.ANYPERCENT

        section = 'UI'
        cls.use_dark_mode = cls.getboolean(section, 'use dark mode', False)
        cls.font_size = cls.getint(section, 'fontsize', 9)
        cls.use_theme = cls.getboolean(section, 'use theme', True)

        section = 'Colors'
        allowed_options = (
            'preemptive', 'ambush', 'encounter', 'crit', 'party update',
            'stat update', 'equipment update', 'comment', 'advance rng',
            'equipment', 'no encounters', 'yojimbo low gil',
            'yojimbo high gil', 'compatibility update', 'error', 'status miss',
            'important monster', 'captured monster',
        )
        for option in cls.getsection(section):
            if option not in allowed_options:
                continue
            colors_list = cls.getlist(section, option)
            while len(colors_list) < 2:
                colors_list.append('')
            fg, bg, *_ = colors_list
            if len(fg) == 7 and fg[0] == '#':
                try:
                    int(fg[1:], 16)
                except ValueError:
                    fg = None
            else:
                fg = None
            if len(bg) == 7 and bg[0] == '#':
                try:
                    int(bg[1:], 16)
                except ValueError:
                    bg = None
            else:
                bg = None

            if fg and bg:
                select_fg = get_contrasting_color(fg)
                select_bg = get_contrasting_color(bg)
            elif fg:
                select_fg = get_contrasting_color(fg)
                select_bg = fg
            else:
                select_fg = None
                select_bg = None
            cls.colors[option] = Color(fg, bg, select_fg, select_bg)

        ui_widgets = (
            'Seed info', 'Drops', 'Encounters', 'Steps', 'Encounters Table',
            'Encounters Planner', 'Actions', 'Monster Targeting', 'Status',
            'Yojimbo', 'Monster Data', 'Seedfinder', 'Configs/Log',
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
    def init_configs(cls) -> None:
        if not os.path.exists(cls._configs_file):
            logger = getLogger(__name__)
            logger.warning('Configs file not found.')
            default_configs_file = get_resource_path(
                f'data_files/{cls._default_configs_file}')
            shutil.copyfile(default_configs_file, cls._configs_file)
            logger.info(
                f'Copied default configs file to "{cls._configs_file}"')
        cls.read(cls._configs_file)
        cls.load_configs()
