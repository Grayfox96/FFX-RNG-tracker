import csv
from collections.abc import Iterator
from dataclasses import dataclass

from ..utils import open_cp1252
from .constants import Item
from .file_functions import get_resource_path


class Inventory:
    def __init__(self) -> None:
        self._n_of_items = len(tuple(Item))
        self._quantities: list[int] = [0] * self._n_of_items
        self._items: list[Item | None] = [None] * self._n_of_items

    def __len__(self) -> int:
        return self._n_of_items

    def __contains__(self, item: Item) -> bool:
        return item in self._items

    def __getitem__(self, key: int) -> tuple[Item | None, int]:
        if not (0 <= key < self._n_of_items):
            raise IndexError(key)
        return self._items[key], self._quantities[key]

    def __iter__(self) -> Iterator[tuple[Item | None, int]]:
        yield from zip(self._items, self._quantities)

    def reset(self) -> None:
        self._quantities.clear()
        self._quantities.extend(0 for _ in range(self._n_of_items))
        self._items.clear()
        self._items.extend(None for _ in range(self._n_of_items))

    def add(self, item: Item, amount: int) -> None:
        try:
            index = self._items.index(item)
        except ValueError:
            index = self._items.index(None)
            self._items[index] = item
        self._quantities[index] += max(0, amount)

    def remove(self, item: Item, amount: int) -> None:
        if item not in self._items:
            raise ValueError(f'{item} is not in the inventory')
        index = self._items.index(item)
        quantity = self._quantities[index]
        if amount > quantity:
            raise ValueError(f'Not enough {item} in inventory')
        elif amount == quantity:
            self._quantities[index] = 0
            self._items[index] = None
        else:
            self._quantities[index] = quantity - amount

    def switch(self, index_1: int, index_2: int) -> None:
        if (min(index_1, index_2) < 0
                or max(index_1, index_2) > (self._n_of_items - 1)):
            raise ValueError('Inventory slot needs to be between'
                             f' 0 and {self._n_of_items - 1}')
        q = self._quantities
        q[index_1], q[index_2] = q[index_2], q[index_1]
        i = self._items
        i[index_1], i[index_2] = i[index_2], i[index_1]

    def autosort(self) -> None:
        new_items = []
        new_quantities = []
        # TODO
        # autosort order is not by index
        items_in_order = tuple(ITEMS)
        for item in items_in_order:
            try:
                index = self._items.index(item)
            except ValueError:
                continue
            new_items.append(self._items[index])
            new_quantities.append(self._quantities[index])
        empty_slots = self._n_of_items - len(new_items)
        self._items.clear()
        self._items.extend(new_items)
        self._items.extend(None for _ in range(empty_slots))
        self._quantities.clear()
        self._quantities.extend(new_quantities)
        self._quantities.extend(0 for _ in range(empty_slots))

    def to_string(self) -> str:
        left = True
        left_padding = 0
        right_padding = 0
        for item, quantity in self:
            padding = len(f'{item} {quantity}')
            if left:
                left_padding = max(left_padding, padding)
            else:
                right_padding = max(right_padding, padding)
            left = not left

        left = True
        rows = []
        for item, quantity in self:
            if left:
                row = '|'
                padding = left_padding
            else:
                padding = right_padding
            if item:
                row += f' {item}{quantity:{padding - len(item)}} |'
            else:
                row += f' {'-':{padding}} |'
            if not left:
                rows.append(row)
            left = not left

        empty_row = f'| {'-':{left_padding}} | {'-':{right_padding}} |'
        while rows[-1] == empty_row:
            rows.pop()

        text = f'+-{'-' * left_padding}-+-{'-' * right_padding}-+\n'
        text += '\n'.join(rows)
        text += f'\n+-{'-' * left_padding}-+-{'-' * right_padding}-+'
        return text


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
