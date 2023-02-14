from tkinter import font

from ..configs import Configs
from .base_widgets import ScrollableText, get_default_font_args


class TkOutputWidget(ScrollableText):

    def __init__(self, parent, *args, **kwargs) -> None:
        kwargs.setdefault('font', font.Font(**get_default_font_args()))
        kwargs.setdefault('state', 'disabled')
        kwargs.setdefault('wrap', 'word')
        super().__init__(parent, *args, **kwargs)
        self.tag_configure('wrap margin', lmargin2='1c')
        self.regex_patterns = self.get_regex_patterns()
        self.setup_tags()

    def print_output(self, output: str) -> None:
        self.config(state='normal')
        self.set(output)
        self.tag_add('wrap margin', '1.0', 'end')
        self.highlight_patterns()
        self.config(state='disabled')

    def highlight_patterns(self) -> None:
        for tag_name, pattern in self.regex_patterns.items():
            self.highlight_pattern(pattern, tag_name)

    def get_regex_patterns(self) -> dict[str, str]:
        patterns = {
            'advance rng': '^Advanced rng.+$',
            'error': '^.*# Error: .+$',
            'comment': '^#(.+?)?$',
        }
        return patterns

    def setup_tags(self) -> None:
        """Setup tags to be used by highlight_patterns."""
        for tag_name, color in Configs.colors.items():
            self.tag_configure(
                tag_name, foreground=color.foreground,
                background=color.background,
                selectforeground=color.select_foreground,
                selectbackground=color.select_background)
