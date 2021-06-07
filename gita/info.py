import os
import csv
import yaml
import subprocess
from enum import Enum
from pathlib import Path
from functools import lru_cache
from typing import Tuple, List, Callable, Dict

from . import common


class Color(str, Enum):
    """
    Terminal color
    """
    black = '\x1b[30m'
    red = '\x1b[31m'  # local diverges from remote
    green = '\x1b[32m'  # local == remote
    yellow = '\x1b[33m'  # local is behind
    blue = '\x1b[34m'
    purple = '\x1b[35m'  # local is ahead
    cyan = '\x1b[36m'
    white = '\x1b[37m'  # no remote branch
    end = '\x1b[0m'
    b_black = '\x1b[30;1m'
    b_red = '\x1b[31;1m'
    b_green = '\x1b[32;1m'
    b_yellow = '\x1b[33;1m'
    b_blue = '\x1b[34;1m'
    b_purple = '\x1b[35;1m'
    b_cyan = '\x1b[36;1m'
    b_white = '\x1b[37;1m'
    underline = '\x1B[4m'


def show_colors():  # pragma: no cover
    """

    """
    for i, c in enumerate(Color, start=1):
        if c != Color.end and c != Color.underline:
            print(f'{c.value}{c.name:<8} ', end='')
        if i % 9 == 0:
            print()
    print(f'{Color.end}')
    for situation, c in sorted(get_color_encoding().items()):
        print(f'{situation:<12}: {Color[c].value}{c:<8}{Color.end} ')


@lru_cache()
def get_color_encoding() -> Dict[str, str]:
    """
    Return color scheme for different local/remote situations.
    In the format of {situation: color name}
    """
    # custom settings
    csv_config = Path(common.get_config_fname('color.csv'))
    if csv_config.is_file():
        with open(csv_config, 'r') as f:
            reader = csv.DictReader(f)
            colors = next(reader)
    else:
        colors = {
            'no-remote': Color.white.name,
            'in-sync': Color.green.name,
            'diverged': Color.red.name,
            'local-ahead': Color.purple.name,
            'remote-ahead': Color.yellow.name,
            }
    return colors


def get_info_funcs() -> List[Callable[[str], str]]:
    """
    Return the functions to generate `gita ll` information. All these functions
    take the repo path as input and return the corresponding information as str.
    See `get_path`, `get_repo_status`, `get_common_commit` for examples.
    """
    to_display = get_info_items()
    # This re-definition is to make unit test mocking to work
    all_info_items = {
            'branch': get_repo_status,
            'commit_msg': get_commit_msg,
            'commit_time': get_commit_time,
            'path': get_path,
        }
    return [all_info_items[k] for k in to_display]


def get_info_items() -> List[str]:
    """
    Return the information items to be displayed in the `gita ll` command.
    """
    # custom settings
    csv_config = Path(common.get_config_fname('info.csv'))
    if csv_config.is_file():
        with open(csv_config, 'r') as f:
            reader = csv.reader(f)
            display_items = next(reader)
        display_items = [x for x in display_items if x in ALL_INFO_ITEMS]
    else:
        # default settings
        display_items = ['branch', 'commit_msg', 'commit_time']
    return display_items


def get_path(prop: Dict[str, str]) -> str:
    return f'{Color.cyan}{prop["path"]}{Color.end}'


# TODO: do we need to add the flags here too?
def get_head(path: str) -> str:
    result = subprocess.run('git symbolic-ref -q --short HEAD || git describe --tags --exact-match',
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            universal_newlines=True,
                            cwd=path)
    return result.stdout.strip()


def run_quiet_diff(flags: List[str], args: List[str]) -> int:
    """
    Return the return code of git diff `args` in quiet mode
    """
    result = subprocess.run(
        ['git'] + flags + ['diff', '--quiet'] + args,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode


def get_common_commit() -> str:
    """
    Return the hash of the common commit of the local and upstream branches.
    """
    result = subprocess.run('git merge-base @{0} @{u}'.split(),
                            stdout=subprocess.PIPE,
                            universal_newlines=True)
    return result.stdout.strip()


def has_untracked(flags: List[str]) -> bool:
    """
    Return True if untracked file/folder exists
    """
    cmd = ['git'] + flags + 'ls-files -zo --exclude-standard'.split()
    result = subprocess.run(cmd,
                            stdout=subprocess.PIPE)
    return bool(result.stdout)


def get_commit_msg(prop: Dict[str, str]) -> str:
    """
    Return the last commit message.
    """
    # `git show-branch --no-name HEAD` is faster than `git show -s --format=%s`
    cmd = ['git'] + prop['flags'] + 'show-branch --no-name HEAD'.split()
    result = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            universal_newlines=True,
                            cwd=prop['path'])
    return result.stdout.strip()


def get_commit_time(prop: Dict[str, str]) -> str:
    """
    Return the last commit time in parenthesis.
    """
    cmd = ['git'] + prop['flags'] + 'log -1 --format=%cd --date=relative'.split()
    result = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            universal_newlines=True,
                            cwd=prop['path'])
    return f"({result.stdout.strip()})"


def get_repo_status(prop: Dict[str, str], no_colors=False) -> str:
    head = get_head(prop['path'])
    dirty, staged, untracked, color = _get_repo_status(prop, no_colors)
    if color:
        return f'{color}{head+" "+dirty+staged+untracked:<10}{Color.end}'
    return f'{head+" "+dirty+staged+untracked:<10}'


def _get_repo_status(prop: Dict[str, str], no_colors: bool) -> Tuple[str]:
    """
    Return the status of one repo
    """
    path = prop['path']
    flags = prop['flags']
    os.chdir(path)
    dirty = '*' if run_quiet_diff(flags, []) else ''
    staged = '+' if run_quiet_diff(flags, ['--cached']) else ''
    untracked = '_' if has_untracked(flags) else ''

    if no_colors:
        return dirty, staged, untracked, ''

    colors = {situ: Color[name].value
            for situ, name in get_color_encoding().items()}
    diff_returncode = run_quiet_diff(flags, ['@{u}', '@{0}'])
    has_no_remote = diff_returncode == 128
    has_no_diff = diff_returncode == 0
    if has_no_remote:
        color = colors['no-remote']
    elif has_no_diff:
        color = colors['in-sync']
    else:
        common_commit = get_common_commit()
        outdated = run_quiet_diff(flags, ['@{u}', common_commit])
        if outdated:
            diverged = run_quiet_diff(flags, ['@{0}', common_commit])
            color = colors['diverged'] if diverged else colors['remote-ahead']
        else:  # local is ahead of remote
            color = colors['local-ahead']
    return dirty, staged, untracked, color


ALL_INFO_ITEMS = {
        'branch': get_repo_status,
        'commit_msg': get_commit_msg,
        'commit_time': get_commit_time,
        'path': get_path,
        }
