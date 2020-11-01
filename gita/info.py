import os
import sys
import yaml
import subprocess
from pathlib import Path
from typing import Tuple, List, Callable, Dict

from . import common


class Color:
    """
    Terminal color
    """
    red = '\x1b[31m'  # local diverges from remote
    green = '\x1b[32m'  # local == remote
    yellow = '\x1b[33m'  # local is behind
    blue = '\x1b[34m'
    purple = '\x1b[35m'  # local is ahead
    cyan = '\x1b[36m'
    white = '\x1b[37m'  # no remote branch
    end = '\x1b[0m'


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
            'path': get_path,
        }
    return [all_info_items[k] for k in to_display]


def get_info_items() -> List[str]:
    """
    Return the information items to be displayed in the `gita ll` command.
    """
    # default settings
    display_items = ['branch', 'commit_msg']

    # custom settings
    yml_config = Path(common.get_config_fname('info.yml'))
    if yml_config.is_file():
        with open(yml_config, 'r') as stream:
            display_items = yaml.load(stream, Loader=yaml.FullLoader)
        display_items = [x for x in display_items if x in ALL_INFO_ITEMS]
    return display_items


def get_path(path):
    return Color.cyan + path + Color.end


def get_head(path: str) -> str:
    result = subprocess.run('git rev-parse --abbrev-ref HEAD'.split(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            universal_newlines=True,
                            cwd=path)
    return result.stdout.strip()


def run_quiet_diff(args: List[str]) -> bool:
    """
    Return the return code of git diff `args` in quiet mode
    """
    result = subprocess.run(
        ['git', 'diff', '--quiet'] + args,
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


def has_untracked() -> bool:
    """
    Return True if untracked file/folder exists
    """
    result = subprocess.run('git ls-files -zo --exclude-standard'.split(),
                            stdout=subprocess.PIPE)
    return bool(result.stdout)


def get_commit_msg(path: str) -> str:
    """
    Return the last commit message.
    """
    # `git show-branch --no-name HEAD` is faster than `git show -s --format=%s`
    result = subprocess.run('git show-branch --no-name HEAD'.split(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            universal_newlines=True,
                            cwd=path)
    return result.stdout.strip()


def get_repo_status(path: str, no_colors=False) -> str:
    head = get_head(path)
    dirty, staged, untracked, color = _get_repo_status(path, no_colors)
    if color:
        return f'{color}{head+" "+dirty+staged+untracked:<10}{Color.end}'
    return f'{head+" "+dirty+staged+untracked:<10}'


def _get_repo_status(path: str, no_colors: bool) -> Tuple[str]:
    """
    Return the status of one repo
    """
    os.chdir(path)
    dirty = '*' if run_quiet_diff([]) else ''
    staged = '+' if run_quiet_diff(['--cached']) else ''
    untracked = '_' if has_untracked() else ''

    if no_colors:
        return dirty, staged, untracked, ''

    diff_returncode = run_quiet_diff(['@{u}', '@{0}'])
    has_no_remote = diff_returncode == 128
    has_no_diff = diff_returncode == 0
    if has_no_remote:
        color = Color.white
    elif has_no_diff:
        color = Color.green
    else:
        common_commit = get_common_commit()
        outdated = run_quiet_diff(['@{u}', common_commit])
        if outdated:
            diverged = run_quiet_diff(['@{0}', common_commit])
            color = Color.red if diverged else Color.yellow
        else:  # local is ahead of remote
            color = Color.purple
    return dirty, staged, untracked, color


ALL_INFO_ITEMS = {
        'branch': get_repo_status,
        'commit_msg': get_commit_msg,
        'path': get_path,
        }
