from ffx_rng_tracker.configs import Configs
from ffx_rng_tracker.logger import setup_main_logger
from ffx_rng_tracker.ui_tkinter.encounters_tracker import TkEncountersTracker
from ffx_rng_tracker.ui_tkinter.main import main

if __name__ == '__main__':
    setup_main_logger()
    Configs.init_configs_from_user_files()
    main(title='FFX Encounters tracker', widget=TkEncountersTracker)
