from ..configs import Configs
from ..utils import treeview
from .base_widgets import BaseWidget


class ConfigsPage(BaseWidget):
    """Widget that shows the loaded configuration."""

    def make_input_widget(self):
        return

    def get_input(self):
        return treeview(Configs.get_configs())

    def get_tags(self) -> list[tuple[str, str, bool]]:
        return []

    def print_output(self):
        input = self.get_input()
        self.output_widget.config(state='normal')
        self.output_widget.insert('end', input)
        self.output_widget.config(state='disabled')
