import os


def get_head(path):
    head = os.path.join(path, '.git/HEAD')
    with open(head) as f:
        return os.path.basename(f.read()).rstrip()


def describe(repos):
    """
    :type repos: `dict` of repo name to repo absolute path

    :rtype: `str`
    """
    output = ''
    green = '\x1b[32m'
    end = '\x1b[0m'
    for name, path in repos.items():
        head = get_head(path)
        os.chdir(path)
        dirty = '*' if os.system('git diff --quiet') else ''
        staged = '+' if os.system('git diff --cached --quiet') else ''
        output += f'{name}\t{green}{head} {dirty}{staged}{end}\n'
    return output
