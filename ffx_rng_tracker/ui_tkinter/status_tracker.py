from ..ui_functions import get_status_chance_string
from .base_widgets import BaseWidget, BetterText


class StatusTracker(BaseWidget):
    """Widget that shows status RNG rolls."""

    def make_input_widget(self):
        return

    def make_output_widget(self) -> BetterText:
        widget = super().make_output_widget()
        widget.configure(wrap='none')
        widget._add_h_scrollbar()
        return widget

    def get_input(self):
        self.text = get_status_chance_string(self.gamestate.seed)

    def get_tags(self) -> list[tuple[str, str, bool]]:
        return [('100', 'status miss', False)]

    def print_output(self):
        self.get_input()
        self.output_widget.config(state='normal')
        self.output_widget.set(self.text)
        self.output_widget.config(state='disabled')
        self.highlight_patterns()
