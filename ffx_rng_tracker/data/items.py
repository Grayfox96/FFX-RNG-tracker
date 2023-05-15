import csv
from dataclasses import dataclass

from ..utils import open_cp1252
from .constants import Item
from .file_functions import get_resource_path


@dataclass
class InventorySlot:
    item: Item | None = None
    quantity: int = 0

    def __str__(self) -> str:
        if not self.item:
            return 'Empty'
        return f'{self.item} x{self.quantity}'

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if type(value) is property:
            return
        self._quantity = min(max(0, value), 99)
        if self._quantity == 0:
            self.item = None


@dataclass(frozen=True)
class ItemDrop:
    item: Item
    quantity: int
    rare: bool

    def __str__(self) -> str:
        string = f'{self.item} x{self.quantity}'
        if self.rare:
            string += ' (rare)'
        return string


def _get_item_prices(file_path: str) -> dict[Item, int]:
    """Retrieves the item prices."""
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        file_reader = csv.reader(file_object)
        # skips first line
        next(file_reader)
        item_prices = {}
        for line in file_reader:
            item_prices[Item(line[0])] = int(line[1])
    return item_prices


ITEMS = tuple(i for i in Item)
ITEM_PRICES = _get_item_prices('data_files/items.csv')
