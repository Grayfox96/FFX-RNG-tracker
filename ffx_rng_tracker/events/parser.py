from typing import Callable

from ..errors import EventParsingError
from ..gamestate import GameState
from .comment import Comment
from .main import Event


class EventParser:
    """Helper class used to convert strings to events."""

    def __init__(self, gamestate: GameState) -> None:
        self._gamestate = gamestate
        self._parsing_functions: dict[Callable[..., Event]] = {}

    def register_parsing_function(self,
                                  name: str,
                                  func: Callable[..., Event],
                                  ) -> None:
        self._parsing_functions[name] = func

    def parse(self, text: str) -> list[Event]:
        """Parse through the input text and returns a list of events."""
        events = []
        for line in text.split('\n'):
            event = self.parse_line(line)
            events.append(event)
        return events

    def parse_line(self, line: str) -> Event:
        """Parse the input line and returns an event."""
        words = line.lower().split()
        if not words or words[0].startswith(('#', '///')):
            return Comment(self._gamestate, line)
        event_name, *params = words
        try:
            parsing_func = self._parsing_functions[event_name]
        except KeyError:
            return Comment(
                self._gamestate, f'# Error: No event called {event_name!r}')
        try:
            return parsing_func(self._gamestate, *params)
        except EventParsingError as error:
            return Comment(self._gamestate, f'# Error: {error}')
