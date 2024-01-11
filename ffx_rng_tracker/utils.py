import colorsys
import re
from dataclasses import is_dataclass
from enum import StrEnum
from functools import cache, partial
from typing import Any, overload


def s32(integer: int) -> int:
    return ((integer & 0xffffffff) ^ 0x80000000) - 0x80000000


def treeview(obj, indentation: int = 0) -> str:
    string = ''
    match obj:
        case dict():
            for key, value in obj.items():
                string += ' ' * 4 * indentation
                if isinstance(key, tuple):
                    key = ', '.join(key)
                string += f'{key}: '
                if isinstance(value, dict):
                    string += '\n'
                string += treeview(value, indentation + 1)
        case list() | tuple() | set():
            string += f'{', '.join([str(a) for a in obj])}\n'
        case dataclass if is_dataclass(dataclass):
            string += '\n' + treeview(vars(dataclass), indentation)
        case re.Pattern():
            string += f'\'{obj.pattern}\'\n'
        case _:
            string += f'{obj}\n'
    return string


def add_bytes(*values: int) -> int:
    value = 0
    for position, byte in enumerate(values):
        value += byte * (256 ** position)
    return value


@overload
def get_contrasting_color(color: str) -> str:
    ...


@overload
def get_contrasting_color(color: tuple[int, int, int]) -> tuple[int, int, int]:
    ...


@overload
def get_contrasting_color(color: tuple[float, float, float],
                          ) -> tuple[float, float, float]:
    ...


def get_contrasting_color(color):
    """Returns a color that contrasts with the one provided as input.

    Color can be a tuple of 3 integers in range 0-255,
    a tuple of floats in range 0-1
    or a string in the format #rrggbb, rrggbb, #rgb or rgb.

    The return type will match the type of color
    (string will always start with #).
    """
    return_string = False
    return_ints = False
    match color:
        case (float() as r, float() as g, float() as b):
            pass
        case (int() as r, int() as g, int() as b):
            r, g, b = r / 255, g / 255, b / 255
            return_ints = True
        case str() if len(color) in (6, 7):
            hexcode = color.strip('#')
            r = int(hexcode[0:2], 16) / 255
            g = int(hexcode[2:4], 16) / 255
            b = int(hexcode[4:6], 16) / 255
            return_string = True
        case str() if len(color) in (3, 4):
            hexcode = color.strip('#')
            r = int(hexcode[0], 16) / 15
            g = int(hexcode[1], 16) / 15
            b = int(hexcode[2], 16) / 15
            return_string = True
        case _:
            raise TypeError()

    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.1:
        if v < 0.1:
            s = 0
        if v < 0.5:
            v = 1
        else:
            v = 0
    h = (h + 0.5) % 1
    color = colorsys.hsv_to_rgb(h, s, v)
    if return_ints or return_string:
        color = [int(c * 255) for c in color]
        if return_string:
            r, g, b = color
            return f'#{r:02x}{g:02x}{b:02x}'
    r, g, b = color
    return r, g, b


def stringify(object: Any) -> str:
    string = (str(object).lower()
              .replace(' ', '_')
              .replace('(', '')
              .replace(')', '')
              .replace('\'', '')
              )
    return string


@cache
def search_strenum[S: StrEnum](stringenum: type[S], string: str) -> S:
    for instance in stringenum:
        if stringify(instance) == string:
            return instance
    raise ValueError(string)


open_cp1252 = partial(open, encoding='cp1252')
open_cp1252.__doc__ = 'Open file with encoding \'cp1252\'.'
