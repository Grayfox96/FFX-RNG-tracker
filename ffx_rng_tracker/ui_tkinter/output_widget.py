from tkinter import font

from ..configs import Configs
from .base_widgets import DEFAULT_FONT, ScrollableText


class TkOutputWidget(ScrollableText):

    def __init__(self, parent, *args, **kwargs) -> None:
        kwargs.setdefault('font', font.Font(**DEFAULT_FONT))
        kwargs.setdefault('state', 'disabled')
        kwargs.setdefault('wrap', 'word')
        super().__init__(parent, *args, **kwargs)
        for tag_name, color in Configs.colors.items():
            self.tag_configure(
                tag_name, foreground=color.foreground,
                background=color.background,
                selectforeground=color.select_foreground,
                selectbackground=color.select_background)
        self.tag_configure('wrap margin', lmargin2='1c')
        self.tags = self.get_tags()

    def print_output(self, output: str) -> None:
        self.config(state='normal')
        if self.set(output):
            self.highlight_patterns()
        self.config(state='disabled')

    def highlight_patterns(self) -> None:
        for tag, pattern in self.tags.items():
            self.highlight_pattern(pattern, tag)

    def get_tags(self) -> dict[str, str]:
        """Setup tags to be used by highlight_patterns."""
        tags = {
            'advance rng': '^Advanced rng.+$',
            'error': '^.*# Error: .+$',
            'comment': '^#(.+?)?$',
            'wrap margin': '^.+$',
        }
        return tags
