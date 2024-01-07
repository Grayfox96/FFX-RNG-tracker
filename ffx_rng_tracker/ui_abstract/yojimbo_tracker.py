from ..data.actions import YOJIMBO_ACTIONS
from ..events.parsing_functions import (ParsingFunction,
                                        parse_compatibility_update,
                                        parse_death, parse_roll,
                                        parse_yojimbo_action)
from .base_tracker import TrackerUI


class YojimboTracker(TrackerUI):
    """Widget used to track Yojimbo rng."""
    notes_file = 'yojimbo_notes.txt'

    def get_parsing_functions(self) -> list[ParsingFunction]:
        parsing_functions = [
            parse_roll,
            parse_death,
            parse_compatibility_update,
            parse_yojimbo_action,
        ]
        return parsing_functions

    def get_usage(self) -> str:
        usage = super().get_usage()
        usage += ('\n'
                  '# Yojimbo actions:\n'
                  '#     daigoro, kozuka, wakizashi_st,\n'
                  '#     wakizashi_mt, zanmato,\n'
                  '#     dismiss, autodismiss,\n'
                  '#     first_turn_dismiss')
        return usage

    def edit_input(self, input_text: str) -> str:
        input_lines = input_text.splitlines()
        for index, line in enumerate(input_lines):
            match line.lower().split():
                case ['death', *_]:
                    line = 'death yojimbo'
                case [action_name, *params] if action_name in YOJIMBO_ACTIONS:
                    line = ' '.join(['yojimboturn', action_name, *params])
                case ['/usage']:
                    line = self.usage
            input_lines[index] = line
        return '\n'.join(input_lines)

    def edit_output(self, output: str, padding: bool = False) -> str:
        # if the text contains /// it hides the lines before it
        if output.find('///') >= 0:
            output = output.split('///')[-1]
            output = output[output.find('\n') + 1:]
        return output
