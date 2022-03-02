from ..ui_functions import get_status_chance_string
from .base_widgets import BaseWidget, BetterText


class StatusTracker(BaseWidget):
    """Widget that shows status RNG rolls."""

    def make_input_widget(self) -> None:
        return

    def make_output_widget(self) -> BetterText:
        widget = super().make_output_widget()
        widget.configure(wrap='none')
        widget._add_h_scrollbar()
        return widget

    def get_tags(self) -> dict[str, str]:
        return {'status miss': '100'}

    def get_default_input_text(self) -> str:
        return self.get_input()

    def get_input(self) -> str:
        return get_status_chance_string(self.gamestate.seed)

    def parse_input(self) -> None:
        self.print_output(self.get_input())
