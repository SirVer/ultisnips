import platform

try:
    import unidecode
    UNIDECODE_IMPORTED = True
except ImportError:
    UNIDECODE_IMPORTED = False


def running_on_windows():
    if platform.system() == 'Windows':
        return 'Does not work on Windows.'


def no_unidecode_available():
    if not UNIDECODE_IMPORTED:
        return 'unidecode is not available.'
