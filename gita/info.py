import csv
import subprocess
from enum import Enum
from pathlib import Path
from collections import namedtuple
from functools import lru_cache, partial
from typing import Tuple, List, Callable, Dict

from . import common


class Color(Enum):
    """
    Terminal color
    """

    black = "\x1b[30m"
    red = "\x1b[31m"  # local diverges from remote
    green = "\x1b[32m"  # local == remote
    yellow = "\x1b[33m"  # local is behind
    blue = "\x1b[34m"
    purple = "\x1b[35m"  # local is ahead
    cyan = "\x1b[36m"
    white = "\x1b[37m"  # no remote branch
    end = "\x1b[0m"
    b_black = "\x1b[30;1m"
    b_red = "\x1b[31;1m"
    b_green = "\x1b[32;1m"
    b_yellow = "\x1b[33;1m"
    b_blue = "\x1b[34;1m"
    b_purple = "\x1b[35;1m"
    b_cyan = "\x1b[36;1m"
    b_white = "\x1b[37;1m"
    underline = "\x1B[4m"

    # Make f"{Color.foo}" expand to Color.foo.value .
    #
    # See https://stackoverflow.com/a/24487545
    def __str__(self):
        return f"{self.value}"


default_colors = {
    "no_remote": Color.white.name,
    "in_sync": Color.green.name,
    "diverged": Color.red.name,
    "local_ahead": Color.purple.name,
    "remote_ahead": Color.yellow.name,
}


def show_colors():  # pragma: no cover
    """ """
    for i, c in enumerate(Color, start=1):
        if c != Color.end and c != Color.underline:
            print(f"{c.value}{c.name:<8} ", end="")
        if i % 9 == 0:
            print()
    print(f"{Color.end}")
    for situation, c in sorted(get_color_encoding().items()):
        print(f"{situation:<12}: {Color[c].value}{c:<8}{Color.end} ")


@lru_cache()
def get_color_encoding() -> Dict[str, str]:
    """
    Return color scheme for different local/remote situations.
    In the format of {situation: color name}
    """
    # custom settings
    csv_config = Path(common.get_config_fname("color.csv"))
    if csv_config.is_file():
        with open(csv_config, "r") as f:
            reader = csv.DictReader(f)
            colors = next(reader)
    else:
        colors = default_colors
    return colors


def get_info_funcs(no_colors=False) -> List[Callable[[str], str]]:
    """
    Return the functions to generate `gita ll` information. All these functions
    take the repo path as input and return the corresponding information as str.
    See `get_path`, `get_repo_status`, `get_common_commit` for examples.
    """
    to_display = get_info_items()
    # This re-definition is to make unit test mocking to work
    all_info_items = {
        "branch": partial(get_repo_status, no_colors=no_colors),
        "branch_name": get_repo_branch,
        "commit_msg": get_commit_msg,
        "commit_time": get_commit_time,
        "path": get_path,
    }
    return [all_info_items[k] for k in to_display]


def get_info_items() -> List[str]:
    """
    Return the information items to be displayed in the `gita ll` command.
    """
    # custom settings
    csv_config = Path(common.get_config_fname("info.csv"))
    if csv_config.is_file():
        with open(csv_config, "r") as f:
            reader = csv.reader(f)
            display_items = next(reader)
        display_items = [x for x in display_items if x in ALL_INFO_ITEMS]
    else:
        # default settings
        display_items = ["branch", "commit_msg", "commit_time"]
    return display_items


def get_path(prop: Dict[str, str]) -> str:
    return f'{Color.cyan}{prop["path"]}{Color.end}'


# TODO: do we need to add the flags here too?
def get_head(path: str) -> str:
    result = subprocess.run(
        "git symbolic-ref -q --short HEAD || git describe --tags --exact-match",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
        cwd=path,
    )
    return result.stdout.strip()


def run_quiet_diff(flags: List[str], args: List[str], path) -> int:
    """
    Return the return code of git diff `args` in quiet mode
    """
    result = subprocess.run(
        ["git"] + flags + ["diff", "--quiet"] + args,
        stderr=subprocess.DEVNULL,
        cwd=path,
    )
    return result.returncode


def get_common_commit(path) -> str:
    """
    Return the hash of the common commit of the local and upstream branches.
    """
    result = subprocess.run(
        "git merge-base @{0} @{u}".split(),
        stdout=subprocess.PIPE,
        universal_newlines=True,
        cwd=path,
    )
    return result.stdout.strip()


def has_untracked(flags: List[str], path) -> bool:
    """
    Return True if untracked file/folder exists
    """
    cmd = ["git"] + flags + "ls-files -zo --exclude-standard".split()
    result = subprocess.run(cmd, stdout=subprocess.PIPE, cwd=path)
    return bool(result.stdout)


def has_stashed(flags: List[str], path) -> bool:
    """
    Return True if stashed content exists
    """
    # FIXME: this doesn't work for repos like worktrees, bare, etc
    p = Path(path) / ".git" / "logs" / "refs" / "stash"
    got = False
    try:
        got = p.is_file()
    except Exception:
        pass
    return got


def get_commit_msg(prop: Dict[str, str]) -> str:
    """
    Return the last commit message.
    """
    # `git show-branch --no-name HEAD` is faster than `git show -s --format=%s`
    cmd = ["git"] + prop["flags"] + "show-branch --no-name HEAD".split()
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
        cwd=prop["path"],
    )
    return result.stdout.strip()


def get_commit_time(prop: Dict[str, str]) -> str:
    """
    Return the last commit time in parenthesis.
    """
    cmd = ["git"] + prop["flags"] + "log -1 --format=%cd --date=relative".split()
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
        cwd=prop["path"],
    )
    return f"({result.stdout.strip()})"


default_symbols = {
    "dirty": "*",
    "staged": "+",
    "untracked": "?",
    "stashed": "$",
    "local_ahead": "↑",
    "remote_ahead": "↓",
    "diverged": "⇕",
    "in_sync": "",
    "no_remote": "∅",
    "": "",
}


@lru_cache()
def get_symbols() -> Dict[str, str]:
    """
    return status symbols with customization
    """
    custom = {}
    csv_config = Path(common.get_config_fname("symbols.csv"))
    if csv_config.is_file():
        with open(csv_config, "r") as f:
            reader = csv.DictReader(f)
            custom = next(reader)
    default_symbols.update(custom)
    return default_symbols


def get_repo_status(prop: Dict[str, str], no_colors=False) -> str:
    branch = get_head(prop["path"])
    dirty, staged, untracked, stashed, situ = _get_repo_status(prop)
    symbols = get_symbols()
    info = f"{branch:<10} [{symbols[dirty]}{symbols[staged]}{symbols[stashed]}{symbols[untracked]}{symbols[situ]}]"

    if no_colors:
        return f"{info:<18}"
    colors = {situ: Color[name].value for situ, name in get_color_encoding().items()}
    color = colors[situ]
    return f"{color}{info:<18}{Color.end}"


def get_repo_branch(prop: Dict[str, str]) -> str:
    return get_head(prop["path"])


def _get_repo_status(prop: Dict[str, str]) -> Tuple[str, str, str, str, str]:
    """
    Return the status of one repo
    """
    path = prop["path"]
    flags = prop["flags"]
    dirty = "dirty" if run_quiet_diff(flags, [], path) else ""
    staged = "staged" if run_quiet_diff(flags, ["--cached"], path) else ""
    untracked = "untracked" if has_untracked(flags, path) else ""
    stashed = "stashed" if has_stashed(flags, path) else ""

    diff_returncode = run_quiet_diff(flags, ["@{u}", "@{0}"], path)
    if diff_returncode == 128:
        situ = "no_remote"
    elif diff_returncode == 0:
        situ = "in_sync"
    else:
        common_commit = get_common_commit(path)
        outdated = run_quiet_diff(flags, ["@{u}", common_commit], path)
        if outdated:
            diverged = run_quiet_diff(flags, ["@{0}", common_commit], path)
            situ = "diverged" if diverged else "remote_ahead"
        else:  # local is ahead of remote
            situ = "local_ahead"
    return dirty, staged, untracked, stashed, situ


ALL_INFO_ITEMS = {
    "branch",
    "branch_name",
    "commit_msg",
    "commit_time",
    "path",
}
