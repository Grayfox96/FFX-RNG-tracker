import tkinter as tk
from logging import getLogger
from tkinter import ttk
from typing import Protocol

from .. import __version__
from ..configs import Configs, UIWidgetConfigs
from ..data.constants import UIWidget
from ..events.parser import EventParser
from ..gamestate import GameState
from ..logger import log_exceptions, log_tkinter_error
from ..tracker import FFXRNGTracker
from ..ui_abstract.base_tracker import TrackerUI
from .actions_tracker import TkActionsTracker
from .configslog import TkConfigsLogViewer
from .drops_tracker import TkDropsTracker
from .encounters_planner import TkEncountersPlanner
from .encounters_table import TkEncountersTable
from .encounters_tracker import TkEncountersTracker
from .monster_data_viewer import TkMonsterDataViewer
from .seed_info import TkSeedInfo
from .seedfinder import TkSeedFinder
from .steps_tracker import TkStepsTracker
from .themes import cycle_theme, import_themes
from .yojimbo_tracker import TkYojimboTracker


class TkTracker(Protocol):
    tracker: TrackerUI

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        ...

    def pack(self, *args, **kwargs) -> None:
        ...


@log_exceptions()
def main(*,
         title='FFX RNG tracker',
         size='1280x830',
         widget: type[TkTracker] | None = None,
         ) -> None:
    """Creates a Tkinter main window, initializes the rng tracker
    and the root logger.
    """
    root = tk.Tk()
    # redirects errors to another function
    root.report_callback_exception = log_tkinter_error
    root.protocol('WM_DELETE_WINDOW', root.quit)
    title += (f' v{__version__}'
              f' | Game Version: {Configs.game_version}'
              f' | Category: {Configs.speedrun_category}'
              )
    root.title(title)
    root.geometry(size)

    import_themes(root)
    style = ttk.Style()
    if Configs.default_theme in style.theme_names():
        style.theme_use(Configs.default_theme)

    root.bind_all('<F8>', cycle_theme)

    if widget is not None:
        ui_configs = Configs.ui_widgets[WIDGET_NAMES[TkSeedInfo]]
        ui = TkSeedInfo(root, ui_configs)
        ui.pack(expand=True, fill='both')

        def callback_func(seed: int, _: bool) -> None:
            parser = EventParser(GameState(FFXRNGTracker(seed)))
            configs = Configs.ui_widgets[WIDGET_NAMES[widget]]
            new_ui = widget(root, parser, configs)
            ui.forget()
            new_ui.pack(expand=True, fill='both')
            root.title(f'{title} | Seed: {seed}')

        ui.register_callback(callback_func)
    else:
        ui = ttk.Notebook(root)
        ui.pack(expand=True, fill='both')

        seed_info_configs = Configs.ui_widgets[WIDGET_NAMES[TkSeedInfo]]
        seed_info = TkSeedInfo(ui, seed_info_configs)
        ui.add(seed_info, text=WIDGET_NAMES[TkSeedInfo])

        monster_data_name = WIDGET_NAMES[TkMonsterDataViewer]
        monster_data_configs = Configs.ui_widgets[monster_data_name]
        if monster_data_configs.shown:
            if monster_data_configs.windowed:
                window = tk.Toplevel()
                window.title(monster_data_name)
                window.geometry('1280x830')
                window.protocol('WM_DELETE_WINDOW', lambda: None)
                monster_data = TkMonsterDataViewer(window, monster_data_configs)
                monster_data.pack(expand=True, fill='both')
            else:
                monster_data = TkMonsterDataViewer(ui, monster_data_configs)
                ui.add(monster_data, text=monster_data_name)
        else:
            monster_data = None

        configs_log_name = WIDGET_NAMES[TkConfigsLogViewer]
        configs_log_configs = Configs.ui_widgets[configs_log_name]
        if configs_log_configs.shown:
            if configs_log_configs.windowed:
                window = tk.Toplevel()
                window.title(configs_log_name)
                window.geometry('1280x830')
                window.protocol('WM_DELETE_WINDOW', lambda: None)
                configs_log = TkConfigsLogViewer(window, configs_log_configs)
                configs_log.pack(expand=True, fill='both')
            else:
                configs_log = TkConfigsLogViewer(ui, configs_log_configs)
                ui.add(configs_log, text=configs_log_name)
        else:
            configs_log = None

        trackers: list[TkTracker] = []

        def first_seed_callback_func(seed: int, _: bool) -> None:
            root.title(f'{title} | Seed: {seed}')
            getLogger(__name__).info(f'Opened with seed {seed}.')
            for tracker_type in TRACKERS:
                tracker = add_tab(ui, tracker_type, seed)
                if tracker is not None:
                    trackers.append(tracker)
            if monster_data is not None:
                ui.insert('end', monster_data)
            if configs_log is not None:
                ui.insert('end', configs_log)
            seed_info.register_callback(reload_seed_callback_func)

        def reload_seed_callback_func(seed: int, reload_notes: bool) -> None:
            root.title(f'{title} | Seed: {seed}')
            getLogger(__name__).info(f'Changed seed to {seed}.')
            for tracker in trackers:
                tracker.tracker.change_seed(seed, reload_notes)

        if Configs.seed is None:
            seed_info.register_callback(first_seed_callback_func)
        else:
            first_seed_callback_func(Configs.seed, True)
            seed_info.print_output(Configs.seed)

    root.mainloop()


def add_tab[T: TkTracker](notebook: ttk.Notebook,
                          tracker_type: type[T],
                          seed: int,
                          ) -> T | None:
    name = WIDGET_NAMES[tracker_type]
    configs = Configs.ui_widgets[name]
    if not configs.shown:
        return
    parser = EventParser(GameState(FFXRNGTracker(seed)))
    if configs.windowed:
        window = tk.Toplevel()
        window.title(name)
        window.geometry('1280x830')
        window.protocol('WM_DELETE_WINDOW', lambda: None)
        tracker = tracker_type(window, parser, configs)
        tracker.pack(expand=True, fill='both')
    else:
        tracker = tracker_type(notebook, parser, configs)
        notebook.add(tracker, text=name)
    return tracker


WIDGET_NAMES: dict[type[tk.Widget], UIWidget] = {
    TkSeedInfo: UIWidget.SEED_INFO,
    TkDropsTracker: UIWidget.DROPS,
    TkEncountersTracker: UIWidget.ENCOUNTERS,
    TkStepsTracker: UIWidget.STEPS,
    TkEncountersPlanner: UIWidget.ENCOUNTERS_PLANNER,
    TkEncountersTable: UIWidget.ENCOUNTERS_TABLE,
    TkActionsTracker: UIWidget.ACTIONS,
    TkYojimboTracker: UIWidget.YOJIMBO,
    TkMonsterDataViewer: UIWidget.MONSTER_DATA,
    TkSeedFinder: UIWidget.SEEDFINDER,
    TkConfigsLogViewer: UIWidget.CONFIGS,
}

TRACKERS: tuple[type[TkTracker]] = (
    TkDropsTracker,
    TkEncountersTracker,
    TkStepsTracker,
    TkEncountersPlanner,
    TkEncountersTable,
    TkActionsTracker,
    TkYojimboTracker,
    TkSeedFinder,
)
