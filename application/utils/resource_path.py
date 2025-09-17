
import sys, os


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for PyInstaller.

    :param relative_path: Relative file path
    :return: Absolute path to resource
    """

    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(".."), relative_path)