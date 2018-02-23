import os
import subprocess


class Color:
    red = '\x1b[31m'  # local is behind
    green = '\x1b[32m'  # local == remote
    yellow = '\x1b[33m'  # local is ahead
    purple = '\x1b[35m'  # local diverges
    white = '\x1b[37m'  # no remote
    end = '\x1b[0m'


def get_head(path):
    head = os.path.join(path, '.git/HEAD')
    with open(head) as f:
        return os.path.basename(f.read()).rstrip()


def has_remote():
    """
    Return `True` if remote branch exists. It should be run inside the repo
    """
    result = subprocess.run(
        ['git', 'checkout'], stdout=subprocess.PIPE, universal_newlines=True)
    return bool(result.stdout)


def get_commit_msg():
    """
    """
    result = subprocess.run(
        'git show -s --format=%s'.split(),
        stdout=subprocess.PIPE,
        universal_newlines=True)
    return result.stdout


def merge(path):
    """
    Merge remote changes
    """
    os.chdir(path)
    if has_remote():
        os.system('git merge @{u}')


def fetch(path):
    """
    Update the repos
    """
    os.chdir(path)
    if has_remote():
        # os.system('git remote update')
        os.system('git fetch')


def get_repo_status(path):
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
                color = Color.red if diverged else Color.purple
            else:
                color = Color.yellow
        else:  # remote == local
            color = Color.green
    else:
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
        dirty, staged, color = get_repo_status(path)
        output += f'{name:<18}{color}{head+" "+dirty+staged:<10}{Color.end} {get_commit_msg()}'
    return output
