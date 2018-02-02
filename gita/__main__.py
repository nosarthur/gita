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
    try:
        paths = set(os.environ['REPOPATH'].split(os.pathsep))
    except KeyError:
        paths = set()
        os.environ['REPOPATH'] = ''
    if new_paths:
        new_paths = [os.path.abspath(p) for p in new_paths if is_git(p)]
        new_paths = set(filter(lambda p: p not in paths, new_paths))
        for p in new_paths:
            os.environ['REPOPATH'] += (os.pathsep + p)
        print(f"export REPOPATH={os.environ['REPOPATH']}")
        paths.update(new_paths)
    return {os.path.basename(os.path.normpath(p)):p for p in paths}

def f_add(args):
    repos = update_repos(args.repo)
    print('add', repos)


def f_ls(args):
    repos = update_repos()
    ls
    print('ls', args, repos)

def f_repo(args):
    print('repo', args)


def main(argv=None):
    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    p_ls = subparsers.add_parser('ls', description='here')
    p_ls.add_argument('repo', nargs='*',
            help="repo(s) to show")
    p_ls.set_defaults(func=f_ls)

    p_add = subparsers.add_parser('add')
    p_add.add_argument('repo', nargs='+', # type=update_repos,
            help="add repositories")
    p_add.set_defaults(func=f_add)

    p.add_argument('goto', metavar='repo', nargs='?',
            # choices=update_repos(),
            default=None,
            help="go to the directory of the chosen repo")

    args = p.parse_args(argv)

    if args.goto:
        print('repos:', args.goto)
    elif 'func' in args:
        args.func(args)
    else:
        p.print_help()


main()
