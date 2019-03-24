'''
Gita manages multiple git repos. It has two functionalities

   1. display the status of multiple repos side by side
   2. delegate git commands/aliases from any working directory

Examples:
    gita ls
    gita fetch
    gita stat myrepo2
    gita super myrepo1 commit -am 'add some cool feature'

For bash auto completion, download and source
https://github.com/nosarthur/gita/blob/master/.gita-completion.bash
'''

import os
import argparse
import subprocess
import pkg_resources

from . import utils


def f_add(args: argparse.Namespace):
    utils.add_repos(args.paths)


def f_ll(args: argparse.Namespace):
    """
    Display details of all repos
    """
    repos = utils.get_repos()
    for line in utils.describe(repos):
        print(line)


def f_ls(args: argparse.Namespace):
    repos = utils.get_repos()
    if args.repo:  # one repo, show its path
        print(repos[args.repo])
    else:  # show names of all repos
        print(' '.join(repos))


def f_rm(args: argparse.Namespace):
    """
    Unregister repo(s) from gita
    """
    path_file = utils.get_path_fname()
    if os.path.isfile(path_file):
        repos = utils.get_repos()
        for repo in args.repo:
            del repos[repo]
        with open(path_file, 'w') as f:
            f.write(os.pathsep.join(repos.values()))


def f_git_cmd(args: argparse.Namespace):
    """
    Delegate git command/alias defined in `args.cmd`. Asynchronous execution is
    disabled for commands in the `args.async_blacklist`.
    """
    repos = utils.get_repos()
    if args.repo:  # with user specified repo(s)
        repos = {k: repos[k] for k in args.repo}
    cmds = ['git'] + args.cmd
    if len(repos) == 1 or cmds[1] in args.async_blacklist:
        for path in repos.values():
            subprocess.run(cmds, cwd=path)
    else:  # run concurrent subprocesses
        utils.exec_async_tasks(
            utils.run_async(path, cmds) for path in repos.values())


def f_super(args):
    """
    Delegate git command/alias defined in `args.man`, which may or may not
    contain repo names.
    """
    names = []
    repos = utils.get_repos()
    for i, word in enumerate(args.man):
        if word in repos:
            names.append(word)
        else:
            break
    args.cmd = args.man[i:]
    args.repo = names
    f_git_cmd(args)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog='gita',
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__)
    subparsers = p.add_subparsers(
        title='sub-commands', help='additional help with sub-command -h')

    version = pkg_resources.require('gita')[0].version
    p.add_argument(
        '-v', '--version', action='version', version=f'%(prog)s {version}')

    # bookkeeping sub-commands
    p_add = subparsers.add_parser('add', help='add repo(s)')
    p_add.add_argument('paths', nargs='+', help="add repo(s)")
    p_add.set_defaults(func=f_add)

    p_rm = subparsers.add_parser('rm', help='remove repo(s)')
    p_rm.add_argument(
        'repo',
        nargs='+',
        choices=utils.get_repos(),
        help="remove the chosen repo(s)")
    p_rm.set_defaults(func=f_rm)

    ll_doc = f'''  status symbols:
    +: staged changes
    *: unstaged changes
    _: untracked files/folders

  branch colors:
    {utils.Color.white}white{utils.Color.end}: local has no remote
    {utils.Color.green}green{utils.Color.end}: local is the same as remote
    {utils.Color.red}red{utils.Color.end}: local has diverged from remote
    {utils.Color.purple}purple{utils.Color.end}: local is ahead of remote (good for push)
    {utils.Color.yellow}yellow{utils.Color.end}: local is behind remote (good for merge)'''
    p_ll = subparsers.add_parser(
        'll',
        help='display summary of all repos',
        formatter_class=argparse.RawTextHelpFormatter,
        description=ll_doc)
    p_ll.set_defaults(func=f_ll)

    p_ls = subparsers.add_parser(
        'ls', help='display names of all repos, or path of a chosen repo')
    p_ls.add_argument(
        'repo',
        nargs='?',
        choices=utils.get_repos(),
        help="show path of the chosen repo")
    p_ls.set_defaults(func=f_ls)

    # superman mode
    p_super = subparsers.add_parser(
        'super',
        help=
        'superman mode: delegate any git command/alias in specified or all repo(s).\n'
        'Examples:\n \t gita super myrepo1 commit -am "fix a bug"\n'
        '\t gita super repo1 repo2 repo3 checkout new-feature')
    p_super.add_argument(
        'man',
        nargs=argparse.REMAINDER,
        help="execute arbitrary git command/alias for specified or all repos "
        "Example: gita super myrepo1 diff --name-only --staged "
        "Another: gita super checkout master ")
    p_super.set_defaults(func=f_super)

    # sub-commands that fit boilerplate
    cmds = utils.get_cmds_from_files()
    for name, data in cmds.items():
        help = data.get('help')
        cmd = data.get('cmd') or name
        if data.get('allow_all'):
            choices = utils.get_choices()
            nargs = '*'
            help += ' for all repos or'
        else:
            choices = utils.get_repos()
            nargs = '+'
        help += ' for the chosen repo(s)'
        sp = subparsers.add_parser(name, help=help)
        sp.add_argument('repo', nargs=nargs, choices=choices, help=help)
        sp.set_defaults(func=f_git_cmd, cmd=cmd.split())

    args = p.parse_args(argv)

    args.async_blacklist = {
        name
        for name, data in cmds.items() if data.get('disable_async')
    }

    if 'func' in args:
        args.func(args)
    else:
        p.print_help()  # pragma: no cover


if __name__ == '__main__':
    main()  # pragma: no cover
