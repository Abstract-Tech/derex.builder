# -*- coding: utf-8 -*-
import os

import pkg_resources


def get_test_path(resource_path: str) -> str:
    """Returns a path to a file in the tests folder.

    :param resource_path:str: A path relative to the tests/ directory

    :raises: FileNotFoundError if the given `resource_path` does not point to an existing file.
    """
    if pkg_resources.resource_isdir(__name__, resource_path):
        # There's no way to ask the path of a directory AFAICT
        filename = pkg_resources.resource_listdir(__name__, resource_path)[0]
        path = pkg_resources.resource_filename(__name__, f"{resource_path}/{filename}")
        return os.path.dirname(path)
    return pkg_resources.resource_filename(__name__, resource_path)


def get_builder_path(resource_path: str) -> str:
    """Returns a path to a builder folder inside the `tests/builders` directory.

    :param resource_path:str: A path relative to the tests/builders directory

    :raises: FileNotFoundError if the given `resource_path` does not point to an existing file.
    """
    return get_test_path(f"builders/{resource_path}")
