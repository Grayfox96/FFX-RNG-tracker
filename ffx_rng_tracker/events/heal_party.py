from dataclasses import dataclass, field

from ..data.constants import Character
from .main import Event


@dataclass
class Heal(Event):
    characters: list[Character]
    amount: int
    _old_hps: dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)
    _old_mps: dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._heal()

    def __str__(self) -> str:
        if len(self.characters) == len(tuple(Character)):
            characters = 'every Character'
        else:
            characters = ', '.join([str(c) for c in self.characters])
        string = f'Healed {characters} by {self.amount} HP and MP'
        return string

    def _heal(self) -> None:
        for character in self.characters:
            character_state = self.gamestate.characters[character]
            self._old_hps[character] = character_state.current_hp
            character_state.current_hp += self.amount
            self._old_mps[character] = character_state.current_mp
            character_state.current_mp += self.amount

    def rollback(self) -> None:
        for character in self.characters:
            character_state = self.gamestate.characters[character]
            character_state.current_hp = self._old_hps[character]
            character_state.current_mp = self._old_mps[character]
        return super().rollback()
