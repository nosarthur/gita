import os
import subprocess
from functools import lru_cache


class Color:
    red = '\x1b[31m'  # local diverges
    green = '\x1b[32m'  # local == remote
    yellow = '\x1b[33m'  # local is behind
    purple = '\x1b[35m'  # local is ahead
    white = '\x1b[37m'  # no remote
    end = '\x1b[0m'


def get_path_fname():
    """
    """
    return os.path.join(os.path.expanduser('~'), '.gita_path')


@lru_cache()
def get_repos():
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


def get_choices():
    """
    Return all repo names and an empty list. This is a workaround of argparse's
    problem with coexisting nargs='*' and choices

    :rtype: `list`
    """
    repos = list(get_repos())
    repos.append([])
    return repos


def is_git(path):
    """
    :type path: `str`
    """
    return os.path.isdir(os.path.join(path, '.git'))


def add_repos(new_paths):
    """
    :type new_paths: `list` of `str`
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


def get_head(path):
    head = os.path.join(path, '.git', 'HEAD')
    with open(head) as f:
        return os.path.basename(f.read()).rstrip()


def has_remote():
    """
    Return `True` if remote branch exists. It should be run inside the repo
    """
    result = subprocess.run(
        'git diff --quiet @{u} @{0}'.split(), stderr=subprocess.PIPE)
    return not bool(result.stderr)


def get_commit_msg():
    """
    """
    result = subprocess.run(
        'git show -s --format=%s'.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)
    if result.stderr:
        # no commit yet
        return '\n'
    return result.stdout


def exec_git(path, cmd):
    """
    Execute `cmd` in the `path` directory
    """
    os.chdir(path)
    if has_remote():
        os.system(cmd)


def _get_repo_status(path):
    """
    :param path: path to the repo

    :return: status of the repo
    """
    os.chdir(path)
    dirty = '*' if os.system('git diff --quiet') else ''
    staged = '+' if os.system('git diff --cached --quiet') else ''

    if has_remote():
        if os.system('git diff --quiet @{u} @{0}'):
            outdated = os.system(
                'git diff --quiet @{u} `git merge-base @{0} @{u}`')
            if outdated:
                diverged = os.system(
                    'git diff --quiet @{0} `git merge-base @{0} @{u}`')
                color = Color.red if diverged else Color.yellow
            else:  # local is ahead of remote
                color = Color.purple
        else:  # remote == local
            color = Color.green
    else:  # no remote
        color = Color.white
    return dirty, staged, color


def describe(repos):
    """
    :type repos: `dict` of repo name to repo absolute path

    :rtype: `str`
    """
    output = ''
    for name, path in repos.items():
        head = get_head(path)
        dirty, staged, color = _get_repo_status(path)
        output += f'{name:<18}{color}{head+" "+dirty+staged:<10}{Color.end} {get_commit_msg()}'
    return output
