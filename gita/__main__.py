import os
import yaml
import argparse
import pkg_resources

from . import utils


def f_add(args):
    utils.add_repos(args.repo)


def f_ls(args):
    repos = utils.get_repos()
    if args.repo:  # one repo, show its path
        print(repos[args.repo])
    else:
        for line in utils.describe(repos):
            print(line, end='')


def f_rm(args):
    path_file = utils.get_path_fname()
    if os.path.isfile(path_file):
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
    subparsers = p.add_subparsers(
        title='sub-commands', help='additional help with sub-command -h')

    version = pkg_resources.require('gita')[0].version
    p.add_argument(
        '--version', action='version', version=f'%(prog)s {version}')

    # delegate git sub-commands
    p_add = subparsers.add_parser('add', help='add repo(s)')
    p_add.add_argument('repo', nargs='+', help="add repo(s)")
    p_add.set_defaults(func=f_add)

    p_rm = subparsers.add_parser('rm', help='remove repo')
    p_rm.add_argument(
        'repo', choices=utils.get_repos(), help="remove the chosen repo")
    p_rm.set_defaults(func=f_rm)

    p_fetch = subparsers.add_parser(
        'fetch',
        help='fetch remote updates for all repos or the chosen repo(s)')
    p_fetch.add_argument(
        'repo',
        nargs='*',
        choices=utils.get_choices(),
        help="fetch remote update for the chosen repo(s)")
    p_fetch.set_defaults(func=f_git_cmd, cmd='git fetch')

    p_ls = subparsers.add_parser('ls', help='display summaries of all repos')
    p_ls.add_argument(
        'repo',
        nargs='?',
        choices=utils.get_repos(),
        help="show path of the chosen repo")
    p_ls.set_defaults(func=f_ls)

    # sub-commands that fit boilerplate
    fname = os.path.join(os.path.dirname(__file__), "cmds.yml")
    with open(fname, 'r') as stream:
        cmds = yaml.load(stream)

    fname = os.path.join(os.path.expanduser('~'), '.gita', 'cmds.yml')
    custom_cmds = {}
    if os.path.isfile(fname):
        with open(fname, 'r') as stream:
            custom_cmds = yaml.load(stream)

    cmds.update(custom_cmds)
    for name, data in cmds.items():
        help = data.get('help')
        cmd = data['cmd'] if 'cmd' in data else name
        sp = subparsers.add_parser(name, help=help)
        sp.add_argument(
            'repo',
            nargs='+',
            choices=utils.get_repos(),
            help=help and help + 'of the chosen repo(s)')
        sp.set_defaults(func=f_git_cmd, cmd='git ' + cmd)

    args = p.parse_args(argv)

    if 'func' in args:
        args.func(args)
    else:
        p.print_help()  # pragma: no cover


if __name__ == '__main__':
    main()  # pragma: no cover
