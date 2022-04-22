from dataclasses import dataclass
from itertools import product

from ..configs import Configs
from ..data.seeds import (DAMAGE_VALUES_NEEDED, HD_FROM_BOOT_FRAMES,
                          PS2_FROM_BOOT_FRAMES, datetime_to_seed)
from ..events.character_action import CharacterAction
from .actions_tracker import ActionsTracker
from .input_widget import InputWidget
from .output_widget import OutputWidget


@dataclass
class SeedFinder(ActionsTracker):
    damage_values_widget: InputWidget
    popup: OutputWidget

    def get_default_input_data(self) -> str:
        input_data = ('encounter\n'
                      'auron attack sinscale\ntidus attack sinscale\n'
                      'auron attack sinscale\ntidus attack sinscale\n'
                      'auron attack sinscale\ntidus attack sinscale\n'
                      )
        return input_data

    def find_seed(self) -> None:
        input_text = self.edit_input(self.input_widget.get_input())
        events = self.parser.parse(input_text)

        indexes = []
        for index, event in enumerate(events):
            if isinstance(event, CharacterAction):
                if event.action.does_damage:
                    indexes.append(index)

        if len(indexes) < DAMAGE_VALUES_NEEDED:
            self.popup.print_output(
                f'Need {DAMAGE_VALUES_NEEDED} damaging actions.')
            return

        input_dvs = self.damage_values_widget.get_input()
        for symbol in (',', '-', '/', '\\', '.'):
            input_dvs = input_dvs.replace(symbol, ' ')
        input_dvs = input_dvs.split()
        try:
            input_dvs = [int(i) for i in input_dvs]
        except ValueError as error:
            error = str(error).split(':', 1)[1]
            self.popup.print_output(f'{error} is not a valid damage value.')
            return

        if len(input_dvs) < len(indexes):
            self.popup.print_output(f'Need {len(indexes)} damage values.')
            return

        input_dvs = input_dvs[:len(indexes)]

        damage_values = []

        if Configs.ps2:
            frames = PS2_FROM_BOOT_FRAMES
        else:
            frames = HD_FROM_BOOT_FRAMES

        for frame, dt in product(range(frames), range(256)):
            seed = datetime_to_seed(dt, frame)
            self.parser.gamestate.seed = seed
            events = self.parser.parse(input_text)
            damage_values.clear()
            for index in indexes:
                event: CharacterAction = events[index]
                damage_values.append(event.damage)
            if damage_values == input_dvs:
                self.input_widget.set_input(
                    f'# Seed number: {seed}\n{self.input_widget.get_input()}')
                self.popup.print_output(f'Seed: {seed}')
                self.callback()
                break
        else:
            self.popup.print_output('Seed not found!')