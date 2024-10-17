import logging
import sys
from functools import wraps
from traceback import format_exception
from types import TracebackType

from .ui_abstract.output_widget import OutputWidget


class UIHandler(logging.Handler):
    """Handler to log records into an OutputWidget."""

    def __init__(self, output_widget: OutputWidget) -> None:
        super().__init__()
        self.output_widget = output_widget
        self.log = ''

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        if not msg.endswith('\n'):
            msg += '\n'
        self.log += msg
        self.output_widget.print_output(self.log)


def log_exceptions(logger: logging.Logger | None = None):
    """Decorator used to log unhandled exceptions."""
    if logger is None:
        logger = logging.getLogger(__name__)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                issue = 'exception in ' + func.__name__ + '\n'
                logger.exception(issue)
                raise
        return wrapper
    return decorator


def setup_main_logger(use_console_handler: bool = True,
                      use_file_handler: bool = True,
                      ) -> None:
    """Setup the main logger."""
    logger = logging.getLogger(__name__.split('.')[0])

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt='{asctime} - {name} - {levelname} - {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{',
        )
    if use_console_handler:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)

    if use_file_handler:
        file_handler = logging.FileHandler('ffx_rng_tracker_log.log')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)


def log_tkinter_error(exception_type: type[BaseException],
                      exception: BaseException,
                      tb: TracebackType | None,
                      ) -> None:
    """Receives an error from Tkinter, prints it
    and logs it to the root logger.
    """
    error_message = (f'Exception in Tkinter callback\n'
                     f'{''.join(format_exception(exception))}')
    logger = logging.getLogger(__name__)
    logger.error(error_message)
