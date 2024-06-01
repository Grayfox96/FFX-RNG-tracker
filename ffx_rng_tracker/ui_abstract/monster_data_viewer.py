import re
from dataclasses import dataclass, field

from ..configs import REGEX_NEVER_MATCH, UITagConfigs, UIWidgetConfigs
from ..data.monsters import get_monsters_dict
from ..ui_functions import format_monster_data
from .input_widget import InputWidget
from .output_widget import OutputWidget


@dataclass
class MonsterDataViewer:
    """Widget used to display monster's data."""

    configs: UIWidgetConfigs
    monster_selection_widget: InputWidget
    output_widget: OutputWidget
    search_bar: InputWidget
    monster_data: dict[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        monsters = get_monsters_dict()
        self.monster_data = {k: format_monster_data(v)
                             for k, v in monsters.items()}
        for name in self.configs.tag_names:
            self.output_widget.register_tag(name)
        # set input expects the selection as the first item
        monsters = '|'.join([''] + sorted(self.monster_data))
        self.monster_selection_widget.set_input(monsters)
        self.monster_selection_widget.register_callback(self.callback)
        self.output_widget.register_tag(
            '#search bar',
            UITagConfigs(REGEX_NEVER_MATCH, background='#ffff00'),
            )
        self.search_bar.register_callback(self.search_callback)

    def callback(self) -> None:
        monster_name = self.monster_selection_widget.get_input()
        monster_data = self.monster_data.get(monster_name, '')
        self.output_widget.print_output(monster_data)
        self.output_widget.seek(self.search_bar.get_input())

    def filter_monsters(self) -> None:
        old_selection = self.monster_selection_widget.get_input()
        filter = self.search_bar.get_input().lower()
        monsters_names = [name
                          for name, data in self.monster_data.items()
                          if filter in name or filter in data.lower()
                          ]
        monsters_names.sort()
        monsters_names.insert(0, old_selection)
        self.monster_selection_widget.set_input('|'.join(monsters_names))

    def search_callback(self) -> None:
        search = self.search_bar.get_input()
        tag = self.output_widget.tags['#search bar']
        self.output_widget.clean_tag('#search bar')
        if search:
            tag.regex_pattern = re.compile(
                re.escape(search), flags=re.IGNORECASE)
        else:
            tag.regex_pattern = REGEX_NEVER_MATCH
        self.filter_monsters()
