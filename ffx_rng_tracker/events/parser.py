from ..errors import EventParsingError
from ..gamestate import GameState
from .comment import Comment
from .main import Event
from .parsing_functions import USAGE, ParsingFunction


class EventParser:
    """Helper class used to convert strings to events."""

    def __init__(self, gamestate: GameState) -> None:
        self.gamestate = gamestate
        self.parsing_functions: dict[str, ParsingFunction] = {}
        self.macros: dict[str, str] = {}

    def apply_macros(self, text: str) -> str:
        """Replace keys found in the self.macros dict with their values."""
        text = f'\n{text}\n'
        for name, macro in self.macros.items():
            text = text.replace(f'\n/macro {name}\n', f'\n{macro}\n')
        text = text[1:-1]
        return text

    def parse_to_string(self, text: str) -> str:
        return '\n'.join([str(e) for e in self.parse(text)])

    def parse(self, text: str) -> list[Event]:
        """Parse through the input text and returns a list of events."""
        text = self.apply_macros(text)

        events = []
        for line in text.splitlines():
            event = self.parse_line(line)
            events.append(event)
        return events

    def parse_line(self, line: str) -> Event:
        """Parse the input line and returns an event."""
        words = line.lower().split()
        if not words or words[0].startswith('#'):
            return Comment(self.gamestate, line)
        elif words[0] == '/macro':
            macro_names = ', '.join([f'"{m}"' for m in self.macros])
            text = f'Error: Possible macros are {macro_names}'
            return Comment(self.gamestate, text)
        elif words[0].startswith('/'):
            return Comment(self.gamestate, f'Command: {line}')
        event_name, *params = words
        try:
            parsing_func = self.parsing_functions[event_name]
        except KeyError:
            return Comment(
                self.gamestate, f'Error: No event called "{event_name}"')
        try:
            return parsing_func(self.gamestate, *params)
        except EventParsingError as error:
            if not str(error):
                usage = USAGE.get(parsing_func, ['No usage found'])[0]
                error = f'Usage: {usage}'
            return Comment(self.gamestate, f'Error: {error}')
