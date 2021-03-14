"""This module provides some helper functions for file system use."""

from contextlib import contextmanager
from pathlib import Path


@contextmanager
def open_file(path: str, mode="w"):
    """Open a file on the file system in a context.

    Besides providing a path to the file to be opened, a mode can also be
    provided, which is analogous to the mode used in builtin open function.
    Any intermediate directories that don't already exist are automatically
    created. When exiting the context, the opened file is automatically closed.

    Args:
        path (str): path to the file to be opened
        mode (str, optional): mode to open the file in. Defaults to "w".
    """
    path = Path(path)
    if len(path.parts) > 1:
        path.parent.mkdir(parents=True, exist_ok=True)

    f = open(path, mode)

    try:
        yield f
    finally:
        f.close()


def empty_file(path: str):
    """Create an empty file on the given path.

    Any intermediate directories that don't already exist are automatically
    created. If a file already exists at the given path, it is overwritten.

    Args:
        path (str): path at which the empty file is to be created
    """
    with open_file(path, mode="w") as _:
        pass
