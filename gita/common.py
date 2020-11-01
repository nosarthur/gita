import os


def get_config_dir() -> str:
    parent = os.environ.get('XDG_CONFIG_HOME') or os.path.join(
        os.path.expanduser('~'), '.config')
    root = os.path.join(parent, "gita")
    return root


def get_config_fname(fname: str) -> str:
    """
    Return the file name that stores the repo locations.
    """
    root = get_config_dir()
    return os.path.join(root, fname)
