import importlib.util
import platform

UNIDECODE_IMPORTED = importlib.util.find_spec("unidecode") is not None


def running_on_windows():
    if platform.system() == "Windows":
        return "Does not work on Windows."


def no_unidecode_available():
    if not UNIDECODE_IMPORTED:
        return "unidecode is not available."
