from dataclasses import dataclass

from ..data.constants import Rarity
from ..data.items import ItemDrop
from ..data.monsters import Monster
from .main import Event


@dataclass
class Steal(Event):
    monster: Monster
    successful_steals: int

    def __post_init__(self) -> None:
        self.item = self._get_item()
        if self.item:
            self.gamestate.inventory.add(self.item.item, self.item.quantity)

    def __str__(self) -> str:
        string = f'Steal: {self.monster} | '
        if self.item:
            string += str(self.item)
        else:
            string += 'Failed'
        return string

    def _get_item(self) -> ItemDrop | None:
        rng_steal = self._advance_rng(10) % 255
        base_steal_chance = self.monster.steal.base_chance
        steal_chance = base_steal_chance // (2 ** self.successful_steals)
        if steal_chance > rng_steal:
            rng_rarity = self._advance_rng(11) & 255
            if rng_rarity < 32:
                return self.monster.steal.items[Rarity.RARE]
            else:
                return self.monster.steal.items[Rarity.COMMON]
        else:
            return None
