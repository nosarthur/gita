import os
import argparse

from . import ls


def is_git(path):
    return os.path.isdir(os.path.join(path, '.git'))


def update_repos(new_paths=None):
    """
    :type new_paths: `list` of `str` or `None`

    :rtype: `dict` of repo name to repo absolute path
    """
    path_file = os.path.join(
            os.path.expanduser('~'), '.gita_path')
    if os.path.exists(path_file):
        with open(path_file) as f:
            paths = set(f.read().split(os.pathsep))
    else:
        paths = set()
    if new_paths:
        new_paths = [os.path.abspath(p) for p in new_paths if is_git(p)]
        new_paths = set(filter(lambda p: p not in paths, new_paths))
        print(f"new repos: {new_paths}")
        paths.update(new_paths)
        with open(path_file, 'w') as f:
            f.write(os.pathsep.join(paths))
    return {os.path.basename(os.path.normpath(p)):p for p in paths}

def f_add(args):
    update_repos(args.repo)


def f_ls(args):
    repos = update_repos()
    if args.repo:
        print(repos[args.repo])
    else:
        print(ls.describe(repos))


def main(argv=None):
    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    p_ls = subparsers.add_parser('ls', description='display all repos')
    p_ls.add_argument('repo', nargs='?',
            choices=update_repos(),
            help="show the directory of the chosen repo")
    p_ls.set_defaults(func=f_ls)

    p_add = subparsers.add_parser('add')
    p_add.add_argument('repo', nargs='+',
            help="add repositories")
    p_add.set_defaults(func=f_add)

    args = p.parse_args(argv)

    if 'func' in args:
        args.func(args)
    else:
        p.print_help()


if __name__ == '__main__':
    main()
