import os
import re
import shutil
from configparser import ConfigParser, NoOptionError, NoSectionError
from dataclasses import dataclass
from logging import getLogger

from .data.constants import GameVersion, SpeedrunCategory, UIWidget
from .data.file_functions import get_resource_path
from .data.macros import get_macros
from .utils import get_contrasting_color


@dataclass
class UIWidgetConfigs:
    shown: bool
    windowed: bool
    tag_names: list[str]
    macros: dict[str, str]

    def __str__(self) -> str:
        return ' '.join([f'{v}: {k}' for v, k in vars(self).items()])


@dataclass
class UITagConfigs:
    regex_pattern: re.Pattern
    foreground: str | None = None
    background: str | None = None
    select_foreground: str | None = None
    select_background: str | None = None


class Configs:
    seed: int | None = None
    game_version: GameVersion = GameVersion.HD
    continue_ps2_seed_search: bool = False
    speedrun_category: SpeedrunCategory | str = SpeedrunCategory.ANYPERCENT
    default_theme: str = 'azure-light'
    font_size: int = 9
    ui_tags: dict[str, UITagConfigs] = {}
    ui_widgets: dict[UIWidget, UIWidgetConfigs] = {}
    _parser = ConfigParser()
    _configs_file = 'ffx_rng_tracker_configs.ini'
    _default_configs_file = 'default_configs.ini'

    @classmethod
    def getsection(cls,
                   section: str,
                   fallback: list[str] = None,
                   ) -> list[str]:
        try:
            return cls._parser.options(section)
        except NoSectionError:
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
        except (ValueError, NoSectionError, NoOptionError):
            if fallback is not None:
                return fallback
            return []
        values: list[str] = REGEX_LIST.findall(string)
        return [v.replace("''", "'") for v in values]

    @classmethod
    def read(cls, file_path: str) -> None:
        cls._parser.read(file_path)

    @classmethod
    def load_configs(cls) -> None:
        section = 'General'
        seed = cls.getint(section, 'seed', -1)
        if 0 <= seed <= 0xffffffff:
            cls.seed = seed
        else:
            cls.seed = None
        game_version = cls.get(section, 'game version', 'HD')
        try:
            cls.game_version = GameVersion(game_version)
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
        cls.default_theme = cls.get(section, 'default theme', 'azure-light')
        cls.font_size = cls.getint(section, 'fontsize', 9)

        section = 'Tags'
        for option in cls.getsection(section):
            tag = cls.getlist(section, option)
            while len(tag) < 3:
                tag.append('')
            pattern, fg, bg, *_ = tag
            if not pattern.startswith('\'') or not pattern.endswith('\''):
                continue
            try:
                regex_pattern = re.compile(pattern[1:-1])
            except re.error:
                regex_pattern = REGEX_NEVER_MATCH
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
            elif bg:
                select_fg = None
                select_bg = None
            else:
                continue
            cls.ui_tags[option] = UITagConfigs(
                regex_pattern, fg, bg, select_fg, select_bg)

        macros = get_macros()
        for section in UIWidget:
            cls.ui_widgets[section] = UIWidgetConfigs(
                shown=cls.getboolean(section, 'shown', True),
                windowed=cls.getboolean(section, 'windowed', False),
                tag_names=cls.getlist(section, 'tags'),
                macros=macros.get(section, {}),
                )

    @classmethod
    def get_configs(cls) -> dict[str, str | int | bool]:
        configs = {}
        for name in vars(cls):
            attr = getattr(cls, name)
            if not callable(attr) and not name.startswith('_'):
                configs[name] = attr
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


REGEX_NEVER_MATCH = re.compile(r'\A\b\Z invalid regex')
REGEX_LIST = re.compile("(?:^|,)(?: )*('(?:(?:'')*[^']*)*'|[^',]*)")
