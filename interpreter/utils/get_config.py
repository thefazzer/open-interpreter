import os
import shutil

import yaml

from .local_storage_path import get_storage_path

config_filename = "config.yaml"

user_config_path = os.path.join(get_storage_path(), config_filename)


def get_config_path(path=user_config_path):
    """
    This function checks if the given path exists. If it doesn't, it creates a new file at the path.
    If the path is a filename that exists in the config directory or the current directory, it updates the path.
    If the path doesn't exist, it creates the necessary directories and a new file at the path.
    If the user's config doesn't exist, it copies the default config from the package to the path.

    Args:
        path (str): The path to check or create.

    Returns:
        str: The final path after checking or creating.
    """
    if not os.path.exists(path):
        path = (
            os.path.join(get_storage_path(), path)
            if os.path.exists(os.path.join(get_storage_path(), path))
            else os.path.join(os.path.curdir, path)
            if os.path.exists(os.path.join(os.getcwd(), path))
            else path
        )
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(
            path
        ) and not os.path.exists(os.path.dirname(path)) else os.makedirs(
            get_storage_path(), exist_ok=True
        )
        shutil.copy(
            os.path.join(
                os.path.dirname(os.path.abspath(os.path.dirname(__file__))),
                "config.yaml",
            ),
            path,
        ) if not os.path.exists(path) else None
    return path


def get_config(path=user_config_path):
    """
    This function reads the config file at the given path and returns its content.

    Args:
        path (str): The path of the config file to read.

    Returns:
        dict: The content of the config file.
    """
    with open(get_config_path(path), "r") as file:
        return yaml.safe_load(file)
