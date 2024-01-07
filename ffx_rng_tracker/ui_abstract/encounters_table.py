import re
from dataclasses import dataclass

from .encounters_tracker import EncountersTracker
from .input_widget import InputWidget


@dataclass
class EncountersTable(EncountersTracker):
    search_bar: InputWidget

    def edit_output(self, output: str, padding: bool = False) -> str:
        monsters = self.search_bar.get_input()
        for symbol in (',', '-', '/', '\\', '.'):
            monsters = monsters.replace(symbol, ' ')
        pattern = fr'(?i)\m{'|'.join([re.escape(m) for m in monsters.split()])}\M'
        self.output_widget.regex_patterns['important monster'] = pattern

        # if the text contains /// it hides the lines before it
        if output.find('///') >= 0:
            output = output.split('///')[-1]
            output = output[output.find('\n') + 1:]
        if not output:
            return output
        output_lines = output.splitlines()
        zones = output_lines[0].split(' | ')[1].split('/')
        for index, line in enumerate(output_lines):
            parts = line.split(' | ')
            # remove icvs
            parts.pop()
            # replace zones with encounter condition
            # some encounters force a particular condition so it's possible
            # to get different ones in different zones
            parts[1] = ''
            if 'Ambush' in line:
                parts[1] += '$amb'
            if 'Preemptive' in line:
                if parts[1]:
                    parts[1] += '/'
                parts[1] += '$pre'
            if parts[1] and 'Normal' in line:
                parts[1] += '/$nor'
            output_lines[index] = ' | '.join(parts)
        output_lines.insert(
            0, f'Random Encounter: | Condition | {' | '.join(zones)}')
        output = ('\n'.join(output_lines)
                  .replace(' Normal', '')
                  .replace('Ambush', '')
                  .replace('Preemptive', '')
                  .replace('$nor', 'Normal')
                  .replace('$amb', 'Ambush')
                  .replace('$pre', 'Preemptive')
                  )
        output = self.pad_output(output).replace('Random Encounter: ', '')
        output_lines = output.splitlines()
        output_lines.insert(1, '=' * max(len(line) for line in output_lines))
        return '\n'.join(output_lines)
