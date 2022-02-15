def s32(integer: int) -> int:
    return ((integer & 0xffffffff) ^ 0x80000000) - 0x80000000


def treeview(obj, indentation: int = 0) -> str:
    string = ''
    match obj:
        case dict():
            for key, value in obj.items():
                string += ' ' * 4 * indentation
                string += f'{key}: '
                if isinstance(value, dict):
                    string += '\n'
                string += treeview(value, indentation + 1)
        case list() | tuple():
            string += f'{", ".join([str(a) for a in obj])}\n'
        case _:
            string += f'{obj}\n'
    return string
