from pathlib import Path
from unittest.mock import MagicMock

TEST_DIR = Path(__file__).parents[0]


def fullpath(fname: str):
    return str(TEST_DIR / fname)


PATH_FNAME = fullpath('mock_path_file')
PATH_FNAME_EMPTY = fullpath('empty_path_file')
PATH_FNAME_CLASH = fullpath('clash_path_file')
GROUP_FNAME = fullpath('mock_group_file')

def async_mock():
    """
    Mock an async function. The calling arguments are saved in a MagicMock.
    """
    m = MagicMock()

    async def coro(*args, **kwargs):
        return m(*args, **kwargs)

    coro.mock = m
    return coro
