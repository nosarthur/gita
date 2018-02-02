import os


def get_head(path):
    head = os.path.join(path, '.git/HEAD')
    with open(head) as f:
        return os.path.basename(f.read())


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
        output += f'{name}\t{green}{head}{end}'
    return output
