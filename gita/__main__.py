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
import sys
import csv
import argparse
import subprocess
import pkg_resources
from itertools import chain
from pathlib import Path

from . import utils, info, common


def f_add(args: argparse.Namespace):
    repos = utils.get_repos()
    paths = args.paths
    if args.main:
        # add to global and tag as main
        main_repos = utils.add_repos(repos, paths, repo_type='m')
        # add sub-repo recursively and save to local config
        for name, prop in main_repos.items():
            main_path = prop['path']
            print('Inside main repo:', name)
            sub_paths = Path(main_path).glob('**')
            utils.add_repos({}, sub_paths, root=main_path)
    else:
        if args.recursive:
            paths = chain.from_iterable(Path(p).glob('**') for p in args.paths)
        utils.add_repos(repos, paths, is_bare=args.bare)


def f_rename(args: argparse.Namespace):
    repos = utils.get_repos()
    utils.rename_repo(repos, args.repo[0], args.new_name)


def f_flags(args: argparse.Namespace):
    cmd = args.flags_cmd or 'll'
    repos = utils.get_repos()
    if cmd == 'll':
        for r, prop in repos.items():
            if prop['flags']:
                print(f"{r}: {prop['flags']}")
    elif cmd == 'set':
        # when in memory, flags are List[str], when on disk, they are space
        # delimited str
        repos[args.repo]['flags'] = args.flags
        utils.write_to_repo_file(repos, 'w')


def f_color(args: argparse.Namespace):
    cmd = args.color_cmd or 'll'
    if cmd == 'll':  # pragma: no cover
        info.show_colors()
    elif cmd == 'set':
        colors = info.get_color_encoding()
        colors[args.situation] = args.color
        csv_config = common.get_config_fname('color.csv')
        with open(csv_config, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=colors)
            writer.writeheader()
            writer.writerow(colors)


def f_info(args: argparse.Namespace):
    to_display = info.get_info_items()
    cmd = args.info_cmd or 'll'
    if cmd == 'll':
        print('In use:', ','.join(to_display))
        unused = sorted(list(set(info.ALL_INFO_ITEMS) - set(to_display)))
        if unused:
            print('Unused:', ','.join(unused))
        return
    if cmd == 'add' and args.info_item not in to_display:
        to_display.append(args.info_item)
        csv_config = common.get_config_fname('info.csv')
        with open(csv_config, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(to_display)
    elif cmd == 'rm' and args.info_item in to_display:
        to_display.remove(args.info_item)
        csv_config = common.get_config_fname('info.csv')
        with open(csv_config, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(to_display)


def f_clone(args: argparse.Namespace):
    path = Path.cwd()
    if args.preserve_path:
        utils.exec_async_tasks(
            utils.run_async(repo_name, path, ['git', 'clone', url, abs_path])
            for url, repo_name, abs_path in utils.parse_clone_config(args.fname))
    else:
        utils.exec_async_tasks(
            utils.run_async(repo_name, path, ['git', 'clone', url])
            for url, repo_name, _ in utils.parse_clone_config(args.fname))


def f_freeze(_):
    repos = utils.get_repos()
    for name, prop in repos.items():
        path = prop['path']
        # TODO: What do we do with main repos? Maybe give an option to print
        #       their sub-repos too.
        url = ''
        cp = subprocess.run(['git', 'remote', '-v'], cwd=path, capture_output=True)
        lines = cp.stdout.decode('utf-8').split('\n')
        if cp.returncode == 0 and len(lines) > 0:
            parts = lines[0].split()
            if len(parts)>1:
                url = parts[1]
        print(f'{url},{name},{path}')


def f_ll(args: argparse.Namespace):
    """
    Display details of all repos
    """
    repos = utils.get_repos()
    ctx = utils.get_context()
    if args.group is None and ctx:
        args.group = ctx.stem
    if args.group:  # only display repos in this group
        group_repos = utils.get_groups()[args.group]
        repos = {k: repos[k] for k in group_repos if k in repos}
    for line in utils.describe(repos, no_colors=args.no_colors):
        print(line)


def f_ls(args: argparse.Namespace):
    repos = utils.get_repos()
    if args.repo:  # one repo, show its path
        print(repos[args.repo]['path'])
    else:  # show names of all repos
        print(' '.join(repos))


def f_group(args: argparse.Namespace):
    groups = utils.get_groups()
    cmd = args.group_cmd or 'll'
    if cmd == 'll':
        for group, repos in groups.items():
            print(f"{group}: {' '.join(repos)}")
    elif cmd == 'ls':
        print(' '.join(groups))
    elif cmd == 'rename':
        new_name = args.new_name
        if new_name in groups:
            sys.exit(f'{new_name} already exists.')
        gname = args.gname
        groups[new_name] = groups[gname]
        del groups[gname]
        utils.write_to_groups_file(groups, 'w')
        # change context
        ctx = utils.get_context()
        if ctx and str(ctx.stem) == gname:
            # ctx.rename(ctx.with_stem(new_name))  # only works in py3.9
            ctx.rename(ctx.with_name(f'{new_name}.context'))
    elif cmd == 'rm':
        ctx = utils.get_context()
        for name in args.to_ungroup:
            del groups[name]
            if ctx and str(ctx.stem) == name:
                ctx.unlink()
        utils.write_to_groups_file(groups, 'w')
    elif cmd == 'add':
        gname = args.gname
        if gname in groups:
            gname_repos = set(groups[gname])
            gname_repos.update(args.to_group)
            groups[gname] = sorted(gname_repos)
            utils.write_to_groups_file(groups, 'w')
        else:
            utils.write_to_groups_file({gname: sorted(args.to_group)}, 'a+')
    elif cmd == 'rmrepo':
        gname = args.gname
        if gname in groups:
            for repo in args.from_group:
                try:
                    groups[gname].remove(repo)
                except ValueError as e:
                    pass
            utils.write_to_groups_file(groups, 'w')


def f_context(args: argparse.Namespace):
    choice = args.choice
    ctx = utils.get_context()
    if choice is None:
        if ctx:
            group = ctx.stem
            print(f"{group}: {' '.join(utils.get_groups()[group])}")
        else:
            print('Context is not set')
    elif choice == 'none':  # remove context
        ctx and ctx.unlink()
    else:  # set context
        fname = Path(common.get_config_dir()) / (choice + '.context')
        if ctx:
            ctx.rename(fname)
        else:
            open(fname, 'w').close()


def f_rm(args: argparse.Namespace):
    """
    Unregister repo(s) from gita
    """
    path_file = common.get_config_fname('repos.csv')
    if os.path.isfile(path_file):
        repos = utils.get_repos()
        main_paths = [prop['path'] for prop in repos.values() if prop['type'] == 'm']
        # TODO: add test case to delete main repo from main repo
        #       only local setting should be affected instead of the global one
        for repo in args.repo:
            del repos[repo]
        # If cwd is relative to any main repo, write to local config
        cwd = os.getcwd()
        for p in main_paths:
            if utils.is_relative_to(cwd, p):
                utils.write_to_repo_file(repos, 'w', p)
                break
        else:  # global config
            utils.write_to_repo_file(repos, 'w')


def f_git_cmd(args: argparse.Namespace):
    """
    Delegate git command/alias defined in `args.cmd`. Asynchronous execution is
    disabled for commands in the `args.async_blacklist`.
    """
    repos = utils.get_repos()
    groups = utils.get_groups()
    ctx = utils.get_context()
    if not args.repo and ctx:
        args.repo = [ctx.stem]
    if args.repo:  # with user specified repo(s) or group(s)
        chosen = {}
        for k in args.repo:
            if k in repos:
                chosen[k] = repos[k]
            if k in groups:
                for r in groups[k]:
                    chosen[r] = repos[r]
        repos = chosen
    per_repo_cmds = []
    for prop in repos.values():
        cmds = args.cmd.copy()
        if cmds[0] == 'git' and prop['flags']:
            cmds[1:1] = prop['flags']
        per_repo_cmds.append(cmds)

    # This async blacklist mechanism is broken if the git command name does
    # not match with the gita command name.
    if len(repos) == 1 or args.cmd[1] in args.async_blacklist:
        for prop, cmds in zip(repos.values(), per_repo_cmds):
            path = prop['path']
            print(path)
            subprocess.run(cmds, cwd=path, shell=args.shell)
    else:  # run concurrent subprocesses
        # Async execution cannot deal with multiple repos' user name/password.
        # Here we shut off any user input in the async execution, and re-run
        # the failed ones synchronously.
        errors = utils.exec_async_tasks(
            utils.run_async(repo_name, prop['path'], cmds)
                            for cmds, (repo_name, prop) in zip(per_repo_cmds, repos.items()))
        for path in errors:
            if path:
                print(path)
                # FIXME: This is broken, flags are missing. But probably few
                #        people will use `gita flags`
                subprocess.run(args.cmd, cwd=path)


def f_shell(args):
    """
    Delegate shell command defined in `args.man`, which may or may not
    contain repo names.
    """
    names = []
    repos = utils.get_repos()
    groups = utils.get_groups()
    ctx = utils.get_context()
    for i, word in enumerate(args.man):
        if word in repos or word in groups:
            names.append(word)
        else:
            break
    args.repo = names
    # TODO: redundant with f_git_cmd
    if not args.repo and ctx:
        args.repo = [ctx.stem]
    if args.repo:  # with user specified repo(s) or group(s)
        chosen = {}
        for k in args.repo:
            if k in repos:
                chosen[k] = repos[k]
            if k in groups:
                for r in groups[k]:
                    chosen[r] = repos[r]
        repos = chosen
    cmds = ' '.join(args.man[i:])  # join the shell command into a single string
    for name, prop in repos.items():
        # TODO: pull this out as a function
        got = subprocess.run(cmds, cwd=prop['path'], check=True, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        print(utils.format_output(got.stdout.decode(), name))


def f_super(args):
    """
    Delegate git command/alias defined in `args.man`, which may or may not
    contain repo names.
    """
    names = []
    repos = utils.get_repos()
    groups = utils.get_groups()
    for i, word in enumerate(args.man):
        if word in repos or word in groups:
            names.append(word)
        else:
            break
    args.cmd = ['git'] + args.man[i:]
    args.repo = names
    args.shell = False
    f_git_cmd(args)


def main(argv=None):
    p = argparse.ArgumentParser(prog='gita',
                                formatter_class=argparse.RawTextHelpFormatter,
                                description=__doc__)
    subparsers = p.add_subparsers(title='sub-commands',
                                  help='additional help with sub-command -h')

    version = pkg_resources.require('gita')[0].version
    p.add_argument('-v',
                   '--version',
                   action='version',
                   version=f'%(prog)s {version}')

    # bookkeeping sub-commands
    p_add = subparsers.add_parser('add', description='add repo(s)',
            help='add repo(s)')
    p_add.add_argument('paths', nargs='+', help="repo(s) to add")
    xgroup = p_add.add_mutually_exclusive_group()
    xgroup.add_argument('-r', '--recursive', action='store_true',
            help="recursively add repo(s) in the given path.")
    xgroup.add_argument('-m', '--main', action='store_true',
            help="make main repo(s), sub-repos are recursively added.")
    xgroup.add_argument('-b', '--bare', action='store_true',
            help="add bare repo(s)")
    p_add.set_defaults(func=f_add)

    p_rm = subparsers.add_parser('rm', description='remove repo(s)',
            help='remove repo(s)')
    p_rm.add_argument('repo',
                      nargs='+',
                      choices=utils.get_repos(),
                      help="remove the chosen repo(s)")
    p_rm.set_defaults(func=f_rm)

    p_freeze = subparsers.add_parser('freeze',
            description='print all repo information',
            help='print all repo information')
    p_freeze.set_defaults(func=f_freeze)

    p_clone = subparsers.add_parser('clone',
            description='clone repos from config file',
            help='clone repos from config file')
    p_clone.add_argument('fname',
            help='config file. Its content should be the output of `gita freeze`.')
    p_clone.add_argument('-p', '--preserve-path', dest='preserve_path', action='store_true',
            help="clone repo(s) in their original paths")
    p_clone.set_defaults(func=f_clone)

    p_rename = subparsers.add_parser('rename', description='rename a repo',
            help='rename a repo')
    p_rename.add_argument(
        'repo',
        nargs=1,
        choices=utils.get_repos(),
        help="rename the chosen repo")
    p_rename.add_argument('new_name', help="new name")
    p_rename.set_defaults(func=f_rename)

    p_flags = subparsers.add_parser('flags',
            description='Set custom git flags for repo.',
            help='git flags configuration')
    p_flags.set_defaults(func=f_flags)
    flags_cmds = p_flags.add_subparsers(dest='flags_cmd',
            help='additional help with sub-command -h')
    flags_cmds.add_parser('ll',
            description='display repos with custom flags')
    pf_set = flags_cmds.add_parser('set',
            description='Set flags for repo.')
    pf_set.add_argument('repo', choices=utils.get_repos(),
            help="repo name")
    pf_set.add_argument('flags',
            nargs=argparse.REMAINDER,
            help="custom flags, use quotes")

    p_color = subparsers.add_parser('color',
            description='display and modify branch coloring of the ll sub-command.',
            help='color configuration')
    p_color.set_defaults(func=f_color)
    color_cmds = p_color.add_subparsers(dest='color_cmd',
            help='additional help with sub-command -h')
    color_cmds.add_parser('ll',
            description='display available colors and the current branch coloring in the ll sub-command')
    pc_set = color_cmds.add_parser('set',
                description='Set color for local/remote situation.')
    pc_set.add_argument('situation',
                    choices=info.get_color_encoding(),
                    help="5 possible local/remote situations")
    pc_set.add_argument('color',
                    choices=[c.name for c in info.Color],
                    help="available colors")

    p_info = subparsers.add_parser('info',
            description='list, add, or remove information items of the ll sub-command.',
            help='information setting')
    p_info.set_defaults(func=f_info)
    info_cmds = p_info.add_subparsers(dest='info_cmd',
            help='additional help with sub-command -h')
    info_cmds.add_parser('ll',
            description='show used and unused information items of the ll sub-command')
    info_cmds.add_parser('add', description='Enable information item.'
            ).add_argument('info_item',
                    choices=info.ALL_INFO_ITEMS,
                    help="information item to add")
    info_cmds.add_parser('rm', description='Disable information item.'
            ).add_argument('info_item',
                    choices=info.ALL_INFO_ITEMS,
                    help="information item to delete")


    ll_doc = f'''  status symbols:
    +: staged changes
    *: unstaged changes
    _: untracked files/folders

  branch colors:
    {info.Color.white}white{info.Color.end}: local has no remote
    {info.Color.green}green{info.Color.end}: local is the same as remote
    {info.Color.red}red{info.Color.end}: local has diverged from remote
    {info.Color.purple}purple{info.Color.end}: local is ahead of remote (good for push)
    {info.Color.yellow}yellow{info.Color.end}: local is behind remote (good for merge)'''
    p_ll = subparsers.add_parser('ll',
                                 help='display summary of all repos',
                                 formatter_class=argparse.RawTextHelpFormatter,
                                 description=ll_doc)
    p_ll.add_argument('group',
                      nargs='?',
                      choices=utils.get_groups(),
                      help="show repos in the chosen group")
    p_ll.add_argument('-C', '--no-colors', action='store_true',
            help='Disable coloring on the branch names.')
    p_ll.set_defaults(func=f_ll)

    p_context = subparsers.add_parser('context',
            help='set context',
            description='Set and remove context. A context is a group.'
                ' When set, all operations apply only to repos in that group.')
    p_context.add_argument('choice',
                      nargs='?',
                      choices=set().union(utils.get_groups(), {'none'}),
                      help="Without argument, show current context. Otherwise choose a group as context. To remove context, use 'none'. ")
    p_context.set_defaults(func=f_context)

    p_ls = subparsers.add_parser(
        'ls', help='show repo(s) or repo path',
        description='display names of all repos, or path of a chosen repo')
    p_ls.add_argument('repo',
                      nargs='?',
                      choices=utils.get_repos(),
                      help="show path of the chosen repo")
    p_ls.set_defaults(func=f_ls)

    p_group = subparsers.add_parser(
        'group', description='list, add, or remove repo group(s)',
        help='group repos')
    p_group.set_defaults(func=f_group)
    group_cmds = p_group.add_subparsers(dest='group_cmd',
            help='additional help with sub-command -h')
    group_cmds.add_parser('ll', description='List all groups with repos.')
    group_cmds.add_parser('ls', description='List all group names.')
    pg_add = group_cmds.add_parser('add', description='Add repo(s) to a group.')
    pg_add.add_argument('to_group',
                    nargs='+',
                    metavar='repo',
                    choices=utils.get_repos(),
                    help="repo(s) to be grouped")
    pg_add.add_argument('-n', '--name',
                    dest='gname',
                    metavar='group-name',
                    required=True,
                    help="group name")
    pg_rmrepo = group_cmds.add_parser('rmrepo', description='remove repo(s) from a group.')
    pg_rmrepo.add_argument('from_group',
                    nargs='+',
                    metavar='repo',
                    choices=utils.get_repos(),
                    help="repo(s) to be removed from the group")
    pg_rmrepo.add_argument('-n', '--name',
                    dest='gname',
                    metavar='group-name',
                    required=True,
                    help="group name")
    pg_rename = group_cmds.add_parser('rename', description='Change group name.')
    pg_rename.add_argument('gname', metavar='group-name',
                    choices=utils.get_groups(),
                    help="existing group to rename")
    pg_rename.add_argument('new_name', metavar='new-name',
                    help="new group name")
    group_cmds.add_parser('rm',
            description='Remove group(s).').add_argument('to_ungroup',
                    nargs='+',
                    choices=utils.get_groups(),
                    help="group(s) to delete")

    # superman mode
    p_super = subparsers.add_parser(
        'super',
        help='run any git command/alias',
        description='Superman mode: delegate any git command/alias in specified or '
        'all repo(s).\n'
        'Examples:\n \t gita super myrepo1 commit -am "fix a bug"\n'
        '\t gita super repo1 repo2 repo3 checkout new-feature')
    p_super.add_argument(
        'man',
        nargs=argparse.REMAINDER,
        help="execute arbitrary git command/alias for specified or all repos\n"
        "Example: gita super myrepo1 diff --name-only --staged "
        "Another: gita super checkout master ")
    p_super.set_defaults(func=f_super)

    # shell mode
    p_shell = subparsers.add_parser(
        'shell',
        help='run any shell command',
        description='shell mode: delegate any shell command in specified or '
        'all repo(s).\n'
        'Examples:\n \t gita shell pwd\n'
        '\t gita shell repo1 repo2 repo3 touch xx')
    p_shell.add_argument(
        'man',
        nargs=argparse.REMAINDER,
        help="execute arbitrary shell command for specified or all repos "
        "Example: gita shell myrepo1 ls"
        "Another: gita shell git checkout master ")
    p_shell.set_defaults(func=f_shell)

    # sub-commands that fit boilerplate
    cmds = utils.get_cmds_from_files()
    for name, data in cmds.items():
        help = data.get('help')
        cmd = data['cmd']
        if data.get('allow_all'):
            choices = utils.get_choices()
            nargs = '*'
            help += ' for all repos or'
        else:
            choices = utils.get_repos().keys() | utils.get_groups().keys()
            nargs = '+'
        help += ' for the chosen repo(s) or group(s)'
        sp = subparsers.add_parser(name, description=help)
        sp.add_argument('repo', nargs=nargs, choices=choices, help=help)
        is_shell = bool(data.get('shell'))
        sp.add_argument('-s', '--shell', default=is_shell, type=bool,
                help='If set, run in shell mode')
        if is_shell:
            cmd = [cmd]
        else:
            cmd = cmd.split()
        sp.set_defaults(func=f_git_cmd, cmd=cmd)

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
