import sys


def get_version() -> str:
    try:
        import pkg_resources
    except ImportError:
        try:
            from importlib.metadata import version
        except ImportError:
            print("cannot determine version", sys.version_info)
        else:
            return version("gita")
    else:
        return pkg_resources.get_distribution("gita").version


__version__ = get_version()
