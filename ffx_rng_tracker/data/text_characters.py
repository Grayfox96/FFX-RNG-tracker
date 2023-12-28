import csv

from ..utils import open_cp1252
from .file_functions import get_resource_path


def get_text_characters(file_path: str) -> dict[int, str]:
    """Retrieves the character encoding chart used in prize structs."""
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        file_reader = csv.reader(file_object)
        # skips first line
        next(file_reader)
        text_characters = {}
        for line in file_reader:
            text_characters[int(line[0])] = line[2]
    return text_characters


def bytes_to_string(data: list[int], offset: int) -> str:
    string = ''
    for i in range(offset, len(data)):
        byte = data[i]
        if byte == 0:
            break
        string += TEXT_CHARACTERS.get(byte, '')
    return string


TEXT_CHARACTERS = get_text_characters('data_files/text_characters.csv')
