from ..configs import Configs
from ..utils import treeview
from .base_widgets import BaseTracker


class ConfigsPage(BaseTracker):
    """Widget that shows the loaded configuration."""

    def make_input_widget(self) -> None:
        return

    def get_tags(self) -> dict[str, str]:
        return {}

    def get_default_input_text(self) -> str:
        return self.get_input()

    def get_input(self) -> str:
        return treeview(Configs.get_configs())

    def parse_input(self) -> None:
        self.print_output(self.get_input())
