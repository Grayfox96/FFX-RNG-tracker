import sys

MIN_PYTHON_VERSION_INFO = 3, 12

if sys.version_info < MIN_PYTHON_VERSION_INFO:
    MIN_PYTHON_VERSION_INFO = '.'.join(str(i) for i in MIN_PYTHON_VERSION_INFO)
    raise RuntimeError(
        f'Python ver. {MIN_PYTHON_VERSION_INFO} or higher is required')

__version__ = '24.01.15'
