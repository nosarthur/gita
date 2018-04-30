import os
import argparse

from . import utils


def f_add(args):
    utils.add_repos(args.repo)


def f_ls(args):
    repos = utils.get_repos()
    if args.repo:
        print(repos[args.repo])
    else:
        print(utils.describe(repos))


def f_rm(args):
    path_file = utils.get_path_fname()
    if os.path.exists(path_file):
        repos = utils.get_repos()
        del repos[args.repo]
        with open(path_file, 'w') as f:
            f.write(os.pathsep.join(repos.values()))


def f_git_cmd(args):
    """
    Delegate git command
    """
    repos = utils.get_repos()
    if args.repo:  # with user specified repo(s)
        repos = {k: repos[k] for k in args.repo}
    for path in repos.values():
        utils.exec_git(path, args.cmd)


def main(argv=None):
    p = argparse.ArgumentParser(prog='gita')
    subparsers = p.add_subparsers(title='sub-commands',
                                  help='additional help with sub-command -h')

    p_ls = subparsers.add_parser('ls', help='display all repos')
    p_ls.add_argument('repo', nargs='?', choices=utils.get_repos(),
            help="show path of the chosen repo")
    p_ls.set_defaults(func=f_ls)

    p_add = subparsers.add_parser('add', help='add repo(s)')
    p_add.add_argument('repo', nargs='+', help="add repo(s)")
    p_add.set_defaults(func=f_add)

    p_rm = subparsers.add_parser('rm', help='remove repo')
    p_rm.add_argument('repo', choices=utils.get_repos(),
            help="remove the chosen repo")
    p_rm.set_defaults(func=f_rm)

    p_fetch = subparsers.add_parser('fetch',
            help='fetch remote updates for all repos or the chosen repo(s)')
    p_fetch.add_argument('repo', nargs='*', choices=utils.get_choices(),
            help="fetch remote update for the chosen repo(s)")
    p_fetch.set_defaults(func=f_git_cmd, cmd='git fetch')

    p_pull = subparsers.add_parser('pull', help='pull remote updates')
    p_pull.add_argument('repo', nargs='+', choices=utils.get_repos(),
            help="pull remote update for the chosen repo(s)")
    p_pull.set_defaults(func=f_git_cmd, cmd='git pull')

    p_merge = subparsers.add_parser('merge', help='merge remote updates')
    p_merge.add_argument('repo', nargs='+', choices=utils.get_repos(),
            help="merge remote update for the chosen repo(s)")
    p_merge.set_defaults(func=f_git_cmd, cmd='git merge @{u}')

    p_push = subparsers.add_parser('push', help='push the local updates')
    p_push.add_argument('repo', nargs='+', choices=utils.get_repos(),
            help="push the local update to remote for the chosen repo(s)")
    p_push.set_defaults(func=f_git_cmd, cmd='git push')

    args = p.parse_args(argv)

    if 'func' in args:
        args.func(args)
    else:
        p.print_help()  # pragma: no cover


if __name__ == '__main__':
    main()  # pragma: no cover
