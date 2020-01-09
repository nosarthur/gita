import os
import sys
import yaml
import subprocess
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
    info_items, to_display = get_info_items()
    return [info_items[k] for k in to_display]


def get_info_items() -> Tuple[Dict[str, Callable[[str], str]], List[str]]:
    """
    Return the available information items for display in the `gita ll`
    sub-command, and the ones to be displayed.
    It loads custom information functions and configuration if they exist.
    """
    # default settings
    info_items = {'branch': get_repo_status,
            'commit_msg': get_commit_msg,
            'path': get_path, }
    display_items = ['branch', 'commit_msg']

    # custom settings
    root = common.get_config_dir()
    src_fname = os.path.join(root, 'extra_repo_info.py')
    yml_fname = os.path.join(root, 'info.yml')
    if os.path.isfile(src_fname):
        sys.path.append(root)
        from extra_repo_info import extra_info_items
        info_items.update(extra_info_items)
    if os.path.isfile(yml_fname):
        with open(yml_fname, 'r') as stream:
            display_items = yaml.load(stream, Loader=yaml.FullLoader)
        display_items = [x for x in display_items if x in info_items]
    return info_items, display_items


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


def get_repo_status(path: str) -> str:
    head = get_head(path)
    dirty, staged, untracked, color = _get_repo_status(path)
    return f'{color}{head+" "+dirty+staged+untracked:<10}{Color.end}'


def _get_repo_status(path: str) -> Tuple[str]:
    """
    Return the status of one repo
    """
    os.chdir(path)
    dirty = '*' if run_quiet_diff([]) else ''
    staged = '+' if run_quiet_diff(['--cached']) else ''
    untracked = '_' if has_untracked() else ''

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
