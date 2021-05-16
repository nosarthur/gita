import os


def get_config_dir(root=None) -> str:
    if root is None:
        root = os.environ.get('XDG_CONFIG_HOME') or os.path.join(
            os.path.expanduser('~'), '.config')
        return os.path.join(root, "gita")
    else:
        return os.path.join(root, ".gita")


def get_config_fname(fname: str, root=None) -> str:
    """
    Return the file name that stores the repo locations.
    """
    return os.path.join(get_config_dir(root), fname)
