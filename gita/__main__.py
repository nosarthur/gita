import os
import argparse

from . import utils


def is_git(path):
    return os.path.isdir(os.path.join(path, '.git'))


def update_repos(new_paths=None):
    """
    :type new_paths: `list` of `str` or `None`

    :rtype: `dict` of repo name to repo absolute path
    """
    path_file = os.path.join(os.path.expanduser('~'), '.gita_path')
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
        print(utils.describe(repos))


def f_rm(args):
    repos = update_repos()
    del repos[args.repo]
    path_file = os.path.join(os.path.expanduser('~'), '.gita_path')
    if os.path.exists(path_file):
        with open(path_file, 'w') as f:
            f.write(os.pathsep.join(repos.values()))


def f_git_cmd(args):
    repos = update_repos()
    if args.repo:
        repos = repos.fromkeys([args.repo], repos[args.repo])
    for path in repos.values():
        utils.exec_git(path, args.cmd)


def main(argv=None):
    p = argparse.ArgumentParser(prog='gita')
    subparsers = p.add_subparsers(title='sub-commands',
                                  help='additional help with sub-command -h')

    p_ls = subparsers.add_parser('ls', help='display all repos')
    p_ls.add_argument('repo', nargs='?', choices=update_repos(),
            help="show path of the chosen repo")
    p_ls.set_defaults(func=f_ls)

    p_add = subparsers.add_parser('add', help='add repositories')
    p_add.add_argument('repo', nargs='+', help="add repositories")
    p_add.set_defaults(func=f_add)

    p_rm = subparsers.add_parser('rm', help='remove repository')
    p_rm.add_argument('repo', choices=update_repos(),
            help="remove the chosen repo")
    p_rm.set_defaults(func=f_rm)

    p_merge = subparsers.add_parser('merge', help='merge the remote updates')
    p_merge.add_argument('repo', choices=update_repos(),
            help="merge the remote update for the chosen repo")
    p_merge.set_defaults(func=f_git_cmd, cmd='git merge @{u}')

    p_fetch = subparsers.add_parser('fetch',
            help='fetch the remote updates for all repos or one repo')
    p_fetch.add_argument('repo', nargs='?', choices=update_repos(),
            help="fetch the remote update for the chosen repo")
    p_fetch.set_defaults(func=f_git_cmd, cmd='git fetch')

    p_push = subparsers.add_parser('push', help='push the local updates')
    p_push.add_argument('repo', choices=update_repos(),
            help="push the local update to remote for the chosen repo")
    p_push.set_defaults(func=f_git_cmd, cmd='git push')

    args = p.parse_args(argv)

    if 'func' in args:
        args.func(args)
    else:
        p.print_help()


if __name__ == '__main__':
    main()
