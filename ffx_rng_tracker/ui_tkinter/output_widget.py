from ..configs import Configs, UITagConfigs
from .base_widgets import ScrollableText
from .tkinter_utils import get_default_font


class TkOutputWidget(ScrollableText):

    def __init__(self, parent, *args, **kwargs) -> None:
        kwargs.setdefault('font', get_default_font())
        kwargs.setdefault('state', 'disabled')
        kwargs.setdefault('wrap', 'word')
        super().__init__(parent, *args, **kwargs)
        self.text.tag_configure('wrap margin', lmargin2='1c')
        self.tags: dict[str, UITagConfigs] = {}

    def print_output(self, output: str) -> None:
        self.text.config(state='normal')
        self.set(output)
        self.text.tag_add('wrap margin', '1.0', 'end')
        for name, tag in self.tags.items():
            self.highlight_pattern(name, tag.regex_pattern, output)
        self.text.config(state='disabled')

    def clean_tag(self, tag_name: str) -> None:
        self.text.tag_remove(tag_name, '1.0', 'end')

    def register_tag(self,
                     tag_name: str,
                     tag: UITagConfigs | None = None,
                     ) -> None:
        """Setup tag to be used in print_output.

        If tag is not provided, a tag with the name tag_name
        will be retrieved from Configs.ui_tags.
        """
        if tag is None:
            tag = Configs.ui_tags.get(tag_name)
            if tag is None:
                return
        self.tags[tag_name] = tag
        self.text.tag_configure(
            tagName=tag_name,
            foreground=tag.foreground,
            background=tag.background,
            selectforeground=tag.select_foreground,
            selectbackground=tag.select_background,
            )
