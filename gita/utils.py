import os
from subprocess import run, PIPE
from functools import lru_cache
from typing import List, Dict, Tuple


class Color:
    red = '\x1b[31m'  # local diverges from remote
    green = '\x1b[32m'  # local == remote
    yellow = '\x1b[33m'  # local is behind
    purple = '\x1b[35m'  # local is ahead
    white = '\x1b[37m'  # no remote branch
    end = '\x1b[0m'


def get_path_fname() -> str:
    """
    """
    return os.path.join(os.path.expanduser('~'), '.gita_path')


@lru_cache()
def get_repos() -> Dict[str, str]:
    """
    :rtype: `dict` of repo name to repo absolute path
    """
    path_file = get_path_fname()
    if os.path.exists(path_file):
        with open(path_file) as f:
            paths = set(f.read().splitlines()[0].split(os.pathsep))
    else:
        paths = set()
    return {os.path.basename(os.path.normpath(p)): p for p in paths if is_git(p)}


def get_choices() -> List[str]:
    """
    Return all repo names and an additional empty list. This is a workaround of
    argparse's problem with coexisting nargs='*' and choices
    """
    repos = list(get_repos())
    repos.append([])
    return repos


def is_git(path: str) -> bool:
    return os.path.isdir(os.path.join(path, '.git'))


def add_repos(new_paths: List[str]):
    """
    Write new repo paths to file
    """
    paths = set(get_repos().values())
    new_paths = set(os.path.abspath(p) for p in new_paths if is_git(p))
    new_paths = new_paths - paths
    if new_paths:
        print(f"Found {len(new_paths)} new repo(s): {new_paths}.")
        paths.update(new_paths)
        with open(get_path_fname(), 'w') as f:
            f.write(os.pathsep.join(sorted(paths)))
    else:
        print('No new repos found!')


def get_head(path: str) -> str:
    head = os.path.join(path, '.git', 'HEAD')
    with open(head) as f:
        return os.path.basename(f.read()).rstrip()


def has_remote() -> bool:
    """
    Return `True` if remote branch exists. It should be run inside the repo
    """
    result = run('git diff --quiet @{u} @{0}', stderr=PIPE, shell=True)
    return not bool(result.stderr)


def get_commit_msg() -> str:
    """
    """
    result = run('git show -s --format=%s', stdout=PIPE, stderr=PIPE, shell=True,
                 universal_newlines=True)
    if result.stderr:  # no commit yet
        return '\n'
    return result.stdout


def exec_git(path: str, cmd: str):
    """
    Execute `cmd` in the `path` directory
    """
    os.chdir(path)
    if has_remote():
        run(cmd, shell=True)


def _get_repo_status(path: str) -> Tuple[str]:
    """
    Return repo status
    """
    os.chdir(path)
    dirty = '*' if run('git diff --quiet', shell=True).returncode else ''
    staged = '+' if run('git diff --cached --quiet', shell=True).returncode else ''

    if has_remote():
        if run('git diff --quiet @{u} @{0}', shell=True).returncode:
            merge_base = str(run('git merge-base @{0} @{u}',
                            stdout=PIPE, shell=True).stdout)
            outdated = run('git diff --quiet @{u}' + merge_base,
                           shell=True).returncode
            if outdated:
                diverged = run('git diff --quiet @{0}' + merge_base,
                               shell=True).returncode
                color = Color.red if diverged else Color.yellow
            else:  # local is ahead of remote
                color = Color.purple
        else:  # remote == local
            color = Color.green
    else:  # no remote
        color = Color.white
    return dirty, staged, color


def describe(repos: Dict[str, str]) -> str:
    """
    Return the status of all repos
    """
    output = ''
    for name in sorted(repos):
        path = repos[name]
        head = get_head(path)
        dirty, staged, color = _get_repo_status(path)
        output += f'{name:<18}{color}{head+" "+dirty+staged:<10}{Color.end} {get_commit_msg()}'
    return output
