from ..errors import EventParsingError
from ..gamestate import GameState
from .comment import Comment
from .main import Event
from .parsing_functions import USAGE, ParsingFunction


class EventParser:
    """Helper class used to convert strings to events."""

    def __init__(self, gamestate: GameState) -> None:
        self.gamestate = gamestate
        self._parsing_functions: dict[str, ParsingFunction] = {}

    def register_parsing_function(self,
                                  command: str,
                                  func: ParsingFunction,
                                  ) -> None:
        self._parsing_functions[command] = func

    def parse(self, text: str) -> list[Event]:
        """Parse through the input text and returns a list of events."""
        events = []
        for line in text.splitlines():
            event = self.parse_line(line)
            events.append(event)
        return events

    def parse_line(self, line: str) -> Event:
        """Parse the input line and returns an event."""
        words = line.lower().split()
        if not words or words[0].startswith(('#', '///')):
            return Comment(self.gamestate, line)
        event_name, *params = words
        try:
            parsing_func = self._parsing_functions[event_name]
        except KeyError:
            return Comment(
                self.gamestate, f'# Error: No event called "{event_name}"')
        try:
            return parsing_func(self.gamestate, *params)
        except EventParsingError as error:
            if not str(error):
                usage = USAGE.get(parsing_func, ['No usage found'])[0]
                error = f'Usage: {usage}'
            return Comment(self.gamestate, f'# Error: {error}')
