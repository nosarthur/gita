import sys


def get_version() -> str:
    try:
        from importlib.metadata import version
    except ImportError:
        print("cannot determine version", sys.version_info)
    else:
        return version("gita")


__version__ = get_version()
