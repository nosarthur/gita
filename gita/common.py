import os


def get_config_dir() -> str:
    root = (
        os.environ.get("GITA_PROJECT_HOME")
        or os.environ.get("XDG_CONFIG_HOME")
        or os.path.join(os.path.expanduser("~"), ".config")
    )
    return os.path.join(root, "gita")


def get_config_fname(fname: str) -> str:
    """
    Return the file name that stores the repo locations.
    """
    return os.path.join(get_config_dir(), fname)
