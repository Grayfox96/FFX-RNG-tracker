from dataclasses import dataclass

from ..data.constants import Character
from .main import Event


@dataclass
class Heal(Event):
    characters: list[Character]
    amount: int

    def __post_init__(self) -> None:
        self._heal()

    def __str__(self) -> str:
        if len(self.characters) == len(tuple(Character)):
            characters = 'every Character'
        else:
            characters = ', '.join([c for c in self.characters])
        string = f'Heal: {characters} healed by {self.amount} HP and MP'
        return string

    def _heal(self) -> None:
        for character in self.characters:
            actor = self.gamestate.characters[character]
            actor.current_hp += self.amount
            actor.current_mp += self.amount
