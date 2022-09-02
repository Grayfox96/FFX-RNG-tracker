from dataclasses import dataclass, field

from ..data.constants import Character
from .main import Event


@dataclass
class Heal(Event):
    characters: list[Character]
    amount: int
    hps: dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)
    mps: dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._heal()

    def __str__(self) -> str:
        characters = [str(c) for c in self.characters]
        string = f'Healed {", ".join(characters)} by {self.amount}'
        return string

    def _heal(self) -> None:
        for character in self.characters:
            character_state = self.gamestate.characters[character]
            self.hps[character] = character_state.current_hp
            character_state.current_hp += self.amount
            self.mps[character] = character_state.current_mp
            character_state.current_mp += self.amount

    def rollback(self) -> None:
        for character in self.characters:
            character_state = self.gamestate.characters[character]
            character_state.current_hp = self.hps[character]
            character_state.current_mp = self.mps[character]
        return super().rollback()
