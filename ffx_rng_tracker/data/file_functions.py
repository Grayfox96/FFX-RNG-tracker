import os
import sys

from ..utils import add_bytes


def get_resource_path(relative_path: str,
                      file_directory: str = None,
                      ) -> str:
    """Get the absolute path to a resource, necessary for PyInstaller."""
    try:
        file_directory = sys._MEIPASS
    except AttributeError:
        if file_directory is None:
            file_directory = os.path.dirname(__file__)
    resource_path = os.path.join(file_directory, relative_path)

    return resource_path


def parse_bin_file(file_path: str) -> tuple[list[list[int]], list[int]]:
    """returns a list of lists of bytes that represent the items in
    the file and a list of bytes that represents the string data
    """
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path, mode='rb') as file_object:
        data = file_object.read()
    first_item_index = add_bytes(*data[8:10])
    last_item_index = add_bytes(*data[10:12])
    n_of_items = last_item_index - first_item_index + 1
    item_length = add_bytes(*data[12:14])
    total_length = add_bytes(*data[14:16])
    data_bytes = data[20:20 + total_length]
    string_bytes = list(data[20 + total_length:])
    items: list[list[int]] = []
    for i in range(n_of_items):
        start = i * item_length
        stop = start + item_length
        items.append(list(data_bytes[start:stop]))
    return items, string_bytes
