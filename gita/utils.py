import os


def get_head(path):
    head = os.path.join(path, '.git/HEAD')
    with open(head) as f:
        return os.path.basename(f.read()).rstrip()


def fetch(repos):
    """
    Update the repos
    """
    for name, path in repos.items():
        os.chdir(path)
        # os.system('git remote update')
        os.system('git fetch')


def describe(repos):
    """
    :type repos: `dict` of repo name to repo absolute path

    :rtype: `str`
    """
    output = ''
    red = '\x1b[31m'
    green = '\x1b[32m'
    yellow = '\x1b[33m'
    end = '\x1b[0m'
    for name, path in repos.items():
        head = get_head(path)
        os.chdir(path)
        # outdated = os.system('git rev-list HEAD...origin/master --count')
        # outdated = os.system('git diff --quiet remotes/origin/HEAD')
        if os.system('git diff --quiet @{u} @{0}'):
            outdated = os.system('git diff --quiet @{u} `git merge-base @{0} @{u}`')
            color = red if outdated else yellow
        else:
            color = green
        dirty = '*' if os.system('git diff --quiet') else ''
        staged = '+' if os.system('git diff --cached --quiet') else ''
        output += f'{name:<18}{color}{head} {dirty}{staged}{end}\n'
    return output
