"""
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
"""

import os
import sys
import csv
import argparse
import subprocess
from functools import partial
import pkg_resources
from itertools import chain
from pathlib import Path
import glob

from . import utils, info, common


def _group_name(name: str, exclude_old_names=True) -> str:
    """
    Return valid group name
    """
    repos = utils.get_repos()
    if name in repos:
        print(f"Cannot use group name {name} since it's a repo name.")
        sys.exit(1)
    if exclude_old_names:
        if name in utils.get_groups():
            print(f"Cannot use group name {name} since it's already in use.")
            sys.exit(1)
    if name in {"none", "auto"}:
        print(f"Cannot use group name {name} since it's a reserved keyword.")
        sys.exit(1)
    return name


def _path_name(name: str) -> str:
    """
    Return absolute path
    """
    if name:
        return os.path.abspath(name)
    return ""


def f_add(args: argparse.Namespace):
    repos = utils.get_repos()
    paths = args.paths
    dry_run = args.dry_run
    groups = utils.get_groups()
    if args.recursive or args.auto_group:
        paths = (
            p.rstrip(os.path.sep)
            for p in chain.from_iterable(
                glob.glob(os.path.join(p, "**/"), recursive=True) for p in args.paths
            )
        )
    new_repos = utils.add_repos(
        repos,
        paths,
        include_bare=args.bare,
        exclude_submodule=args.skip_submodule,
        dry_run=dry_run,
    )
    if dry_run:
        return
    if new_repos and args.auto_group:
        new_groups = utils.auto_group(new_repos, args.paths)
        if new_groups:
            print(f"Created {len(new_groups)} new group(s).")
            utils.write_to_groups_file(new_groups, "a+")
    if new_repos and args.group:
        gname = args.group
        gname_repos = set(groups[gname]["repos"])
        gname_repos.update(new_repos)
        groups[gname]["repos"] = sorted(gname_repos)
        print(f"Added {len(new_repos)} repos to the {gname} group")
        utils.write_to_groups_file(groups, "w")


def f_rename(args: argparse.Namespace):
    repos = utils.get_repos()
    utils.rename_repo(repos, args.repo[0], args.new_name)


def f_flags(args: argparse.Namespace):
    cmd = args.flags_cmd or "ll"
    repos = utils.get_repos()
    if cmd == "ll":
        for r, prop in repos.items():
            if prop["flags"]:
                print(f"{r}: {prop['flags']}")
    elif cmd == "set":
        # when in memory, flags are List[str], when on disk, they are space
        # delimited str
        repos[args.repo]["flags"] = args.flags
        utils.write_to_repo_file(repos, "w")


def f_color(args: argparse.Namespace):
    cmd = args.color_cmd or "ll"
    if cmd == "ll":  # pragma: no cover
        info.show_colors()
    elif cmd == "set":
        colors = info.get_color_encoding()
        colors[args.situation] = args.color
        csv_config = common.get_config_fname("color.csv")
        with open(csv_config, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=colors)
            writer.writeheader()
            writer.writerow(colors)
    elif cmd == "reset":
        Path(common.get_config_fname("color.csv")).unlink(missing_ok=True)


def f_info(args: argparse.Namespace):
    to_display = info.get_info_items()
    cmd = args.info_cmd or "ll"
    if cmd == "ll":
        print("In use:", ",".join(to_display))
        unused = sorted(list(set(info.ALL_INFO_ITEMS) - set(to_display)))
        if unused:
            print("Unused:", ",".join(unused))
        return
    if cmd == "add" and args.info_item not in to_display:
        to_display.append(args.info_item)
        csv_config = common.get_config_fname("info.csv")
        with open(csv_config, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(to_display)
    elif cmd == "rm" and args.info_item in to_display:
        to_display.remove(args.info_item)
        csv_config = common.get_config_fname("info.csv")
        with open(csv_config, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(to_display)


def f_clone(args: argparse.Namespace):

    if args.dry_run:
        if args.from_file:
            for url, repo_name, abs_path in utils.parse_clone_config(args.clonee):
                print(f"git clone {url} {abs_path}")
        else:
            print(f"git clone {args.clonee}")
        return

    if args.directory:
        path = args.directory
    else:
        path = Path.cwd()

    if not args.from_file:
        subprocess.run(["git", "clone", args.clonee], cwd=path)
        # add the cloned repo to gita; group is also supported
        cloned_path = os.path.join(path, args.clonee.split("/")[-1].split(".")[0])
        args.paths = [cloned_path]
        args.recursive = args.auto_group = args.bare = args.skip_submodule = False
        f_add(args)
        return

    if args.preserve_path:
        utils.exec_async_tasks(
            utils.run_async(repo_name, path, ["git", "clone", url, abs_path])
            for url, repo_name, abs_path in utils.parse_clone_config(args.clonee)
        )
    else:
        utils.exec_async_tasks(
            utils.run_async(repo_name, path, ["git", "clone", url])
            for url, repo_name, _ in utils.parse_clone_config(args.clonee)
        )


def f_freeze(args):
    repos = utils.get_repos()
    ctx = utils.get_context()
    if args.group is None and ctx:
        args.group = ctx.stem
    group_repos = None
    if args.group:  # only display repos in this group
        group_repos = utils.get_groups()[args.group]["repos"]
        repos = {k: repos[k] for k in group_repos if k in repos}
    seen = {""}
    for name, prop in repos.items():
        path = prop["path"]
        url = ""
        # FIXME: capture_output is new in 3.7. Maybe drop support for 3.6
        cp = subprocess.run(
            ["git", "remote", "-v"],
            cwd=path,
            universal_newlines=True,
            capture_output=True,
        )
        lines = cp.stdout.split("\n")
        if cp.returncode == 0 and len(lines) > 0:
            parts = lines[0].split()
            if len(parts) > 1:
                url = parts[1]
        if url not in seen:
            seen.add(url)
            print(f"{url},{name},{path}")


def f_ll(args: argparse.Namespace):
    """
    Display details of all repos
    """
    repos = utils.get_repos()
    ctx = utils.get_context()
    if args.group is None and ctx:
        args.group = ctx.stem
    group_repos = None
    if args.group:  # only display repos in this group
        group_repos = utils.get_groups()[args.group]["repos"]
        repos = {k: repos[k] for k in group_repos if k in repos}
    if args.g:  # display by group
        if group_repos:
            print(f"{args.group}:")
            for line in utils.describe(repos, no_colors=args.no_colors):
                print("  ", line)
        else:
            for g, prop in utils.get_groups().items():
                print(f"{g}:")
                g_repos = {k: repos[k] for k in prop["repos"] if k in repos}
                for line in utils.describe(g_repos, no_colors=args.no_colors):
                    print("  ", line)
    else:
        for line in utils.describe(repos, no_colors=args.no_colors):
            print(line)


def f_ls(args: argparse.Namespace):
    repos = utils.get_repos()
    if args.repo:  # one repo, show its path
        print(repos[args.repo]["path"])
    else:  # show names of all repos
        print(" ".join(repos))


def f_group(args: argparse.Namespace):
    groups = utils.get_groups()
    cmd = args.group_cmd or "ll"
    if cmd == "ll":
        if "to_show" in args and args.to_show:
            gname = args.to_show
            print(" ".join(groups[gname]["repos"]))
        else:
            for group, prop in groups.items():
                print(f"{info.Color.underline}{group}{info.Color.end}: {prop['path']}")
                for r in prop["repos"]:
                    print("  -", r)
    elif cmd == "ls":
        print(" ".join(groups))
    elif cmd == "rename":
        new_name = args.new_name
        gname = args.gname
        groups[new_name] = groups[gname]
        del groups[gname]
        utils.write_to_groups_file(groups, "w")
        # change context
        ctx = utils.get_context()
        if ctx and ctx.stem == gname:
            utils.replace_context(ctx, new_name)
    elif cmd == "rm":
        ctx = utils.get_context()
        for name in args.to_ungroup:
            del groups[name]
            if ctx and str(ctx.stem) == name:
                utils.replace_context(ctx, "")
        utils.write_to_groups_file(groups, "w")
    elif cmd == "add":
        gname = args.gname
        if gname in groups:
            gname_repos = set(groups[gname]["repos"])
            gname_repos.update(args.to_group)
            groups[gname]["repos"] = sorted(gname_repos)
            if "gpath" in args:
                groups[gname]["path"] = args.gpath
            utils.write_to_groups_file(groups, "w")
        else:
            gpath = ""
            if "gpath" in args:
                gpath = args.gpath
            utils.write_to_groups_file(
                {gname: {"repos": sorted(args.to_group), "path": gpath}}, "a+"
            )
    elif cmd == "rmrepo":
        gname = args.gname
        if gname in groups:
            group = {
                gname: {"repos": groups[gname]["repos"], "path": groups[gname]["path"]}
            }
            for repo in args.to_rm:
                utils.delete_repo_from_groups(repo, group)
            groups[gname] = group[gname]
            utils.write_to_groups_file(groups, "w")


def f_context(args: argparse.Namespace):
    choice = args.choice
    ctx = utils.get_context()
    if choice is None:  # display current context
        if ctx:
            group = ctx.stem
            print(f"{group}: {' '.join(utils.get_groups()[group]['repos'])}")
        elif (Path(common.get_config_dir()) / "auto.context").exists():
            print("auto: none detected!")
        else:
            print("Context is not set")
    else:  # set context
        utils.replace_context(ctx, choice)


def f_rm(args: argparse.Namespace):
    """
    Unregister repo(s) from gita
    """
    path_file = common.get_config_fname("repos.csv")
    if os.path.isfile(path_file):
        repos = utils.get_repos()
        group_updated = False
        groups = utils.get_groups()
        for repo in args.repo:
            del repos[repo]
            up = utils.delete_repo_from_groups(repo, groups)
            group_updated = group_updated or up
        if group_updated:
            utils.write_to_groups_file(groups, "w")

        utils.write_to_repo_file(repos, "w")


def f_git_cmd(args: argparse.Namespace):
    """
    Delegate git command/alias defined in `args.cmd`. Asynchronous execution is
    disabled for commands in the `args.async_blacklist`.
    """
    if "_parsed_repos" in args:
        repos = args._parsed_repos
    else:
        repos, _ = utils.parse_repos_and_rest(args.repo)

    per_repo_cmds = []
    for prop in repos.values():
        cmds = args.cmd.copy()
        if cmds[0] == "git" and prop["flags"]:
            cmds[1:1] = prop["flags"]
        per_repo_cmds.append(cmds)

    # This async blacklist mechanism is broken if the git command name does
    # not match with the gita command name.
    if len(repos) == 1 or args.cmd[1] in args.async_blacklist:
        for prop, cmds in zip(repos.values(), per_repo_cmds):
            path = prop["path"]
            print(path)
            subprocess.run(cmds, cwd=path, shell=args.shell)
    else:  # run concurrent subprocesses
        # Async execution cannot deal with multiple repos' user name/password.
        # Here we shut off any user input in the async execution, and re-run
        # the failed ones synchronously.
        errors = utils.exec_async_tasks(
            utils.run_async(repo_name, prop["path"], cmds)
            for cmds, (repo_name, prop) in zip(per_repo_cmds, repos.items())
        )
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
    repos, cmds = utils.parse_repos_and_rest(args.man, args.quote_mode)
    if not cmds:
        print("Missing commands")
        sys.exit(2)

    cmds = " ".join(cmds)  # join the shell command into a single string
    for name, prop in repos.items():
        # TODO: pull this out as a function
        got = subprocess.run(
            cmds,
            cwd=prop["path"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(utils.format_output(got.stdout.decode(), name))


def f_super(args):
    """
    Delegate git command/alias defined in `args.man`, which may or may not
    contain repo names.
    """
    repos, cmds = utils.parse_repos_and_rest(args.man, args.quote_mode)
    if not cmds:
        print("Missing commands")
        sys.exit(2)

    args.cmd = ["git"] + cmds
    args._parsed_repos = repos
    args.shell = False
    f_git_cmd(args)


def f_clear(_):
    utils.write_to_groups_file({}, "w")
    utils.write_to_repo_file({}, "w")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="gita", formatter_class=argparse.RawTextHelpFormatter, description=__doc__
    )
    subparsers = p.add_subparsers(
        title="sub-commands", help="additional help with sub-command -h"
    )

    version = pkg_resources.require("gita")[0].version
    p.add_argument("-v", "--version", action="version", version=f"%(prog)s {version}")

    # bookkeeping sub-commands
    p_add = subparsers.add_parser("add", description="add repo(s)", help="add repo(s)")
    p_add.add_argument("paths", nargs="+", type=_path_name, help="repo(s) to add")
    p_add.add_argument("-n", "--dry-run", action="store_true", help="dry run")
    p_add.add_argument(
        "-g",
        "--group",
        choices=utils.get_groups(),
        help="add repo(s) to the specified group",
    )
    p_add.add_argument(
        "-s", "--skip-submodule", action="store_true", help="skip submodule repo(s)"
    )
    xgroup = p_add.add_mutually_exclusive_group()
    xgroup.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="recursively add repo(s) in the given path(s).",
    )
    xgroup.add_argument(
        "-a",
        "--auto-group",
        action="store_true",
        help="recursively add repo(s) in the given path(s) "
        "and create hierarchical groups based on folder structure.",
    )
    xgroup.add_argument("-b", "--bare", action="store_true", help="add bare repo(s)")
    p_add.set_defaults(func=f_add)

    p_rm = subparsers.add_parser(
        "rm", description="remove repo(s)", help="remove repo(s)"
    )
    p_rm.add_argument(
        "repo", nargs="+", choices=utils.get_repos(), help="remove the chosen repo(s)"
    )
    p_rm.set_defaults(func=f_rm)

    p_freeze = subparsers.add_parser(
        "freeze",
        description="print all repo information",
        help="print all repo information",
    )
    p_freeze.add_argument(
        "-g",
        "--group",
        choices=utils.get_groups(),
        help="freeze repos in the specified group",
    )
    p_freeze.set_defaults(func=f_freeze)

    p_clone = subparsers.add_parser(
        "clone", description="clone repos", help="clone repos"
    )
    p_clone.add_argument(
        "clonee",
        help="A URL or a config file.",
    )
    p_clone.add_argument(
        "-C",
        "--directory",
        help="Change to DIRECTORY before doing anything.",
    )
    p_clone.add_argument(
        "-p",
        "--preserve-path",
        dest="preserve_path",
        action="store_true",
        help="clone repo(s) in their original paths",
    )
    p_clone.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="If set, show command without execution",
    )
    xgroup = p_clone.add_mutually_exclusive_group()
    xgroup.add_argument(
        "-g",
        "--group",
        choices=utils.get_groups(),
        help="If set, add repo to the specified group after cloning, otherwise add to gita without group.",
    )
    xgroup.add_argument(
        "-f",
        "--from-file",
        action="store_true",
        help="If set, clone repos in a config file rendered from `gita freeze`",
    )
    p_clone.set_defaults(func=f_clone)

    p_rename = subparsers.add_parser(
        "rename", description="rename a repo", help="rename a repo"
    )
    p_rename.add_argument(
        "repo", nargs=1, choices=utils.get_repos(), help="rename the chosen repo"
    )
    p_rename.add_argument("new_name", help="new name")
    p_rename.set_defaults(func=f_rename)

    p_flags = subparsers.add_parser(
        "flags",
        description="Set custom git flags for repo.",
        help="git flags configuration",
    )
    p_flags.set_defaults(func=f_flags)
    flags_cmds = p_flags.add_subparsers(
        dest="flags_cmd", help="additional help with sub-command -h"
    )
    flags_cmds.add_parser("ll", description="display repos with custom flags")
    pf_set = flags_cmds.add_parser("set", description="Set flags for repo.")
    pf_set.add_argument("repo", choices=utils.get_repos(), help="repo name")
    pf_set.add_argument(
        "flags", nargs=argparse.REMAINDER, help="custom flags, use quotes"
    )

    p_color = subparsers.add_parser(
        "color",
        description="display and modify branch coloring of the ll sub-command.",
        help="color configuration",
    )
    p_color.set_defaults(func=f_color)
    color_cmds = p_color.add_subparsers(
        dest="color_cmd", help="additional help with sub-command -h"
    )
    color_cmds.add_parser(
        "ll",
        description="display available colors and the current branch coloring in the ll sub-command",
    )
    color_cmds.add_parser("reset", description="reset color scheme.")
    pc_set = color_cmds.add_parser(
        "set", description="Set color for local/remote situation."
    )
    pc_set.add_argument(
        "situation",
        choices=info.get_color_encoding(),
        help="5 possible local/remote situations",
    )
    pc_set.add_argument(
        "color", choices=[c.name for c in info.Color], help="available colors"
    )

    p_info = subparsers.add_parser(
        "info",
        description="list, add, or remove information items of the ll sub-command.",
        help="information setting",
    )
    p_info.set_defaults(func=f_info)
    info_cmds = p_info.add_subparsers(
        dest="info_cmd", help="additional help with sub-command -h"
    )
    info_cmds.add_parser(
        "ll", description="show used and unused information items of the ll sub-command"
    )
    info_cmds.add_parser("add", description="Enable information item.").add_argument(
        "info_item", choices=info.ALL_INFO_ITEMS, help="information item to add"
    )
    info_cmds.add_parser("rm", description="Disable information item.").add_argument(
        "info_item", choices=info.ALL_INFO_ITEMS, help="information item to delete"
    )

    ll_doc = f"""  status symbols:
    +: staged changes
    *: unstaged changes
    _: untracked files/folders

  branch colors:
    {info.Color.white}white{info.Color.end}: local has no remote
    {info.Color.green}green{info.Color.end}: local is the same as remote
    {info.Color.red}red{info.Color.end}: local has diverged from remote
    {info.Color.purple}purple{info.Color.end}: local is ahead of remote (good for push)
    {info.Color.yellow}yellow{info.Color.end}: local is behind remote (good for merge)"""
    p_ll = subparsers.add_parser(
        "ll",
        help="display summary of all repos",
        formatter_class=argparse.RawTextHelpFormatter,
        description=ll_doc,
    )
    p_ll.add_argument(
        "group",
        nargs="?",
        choices=utils.get_groups(),
        help="show repos in the chosen group",
    )
    p_ll.add_argument(
        "-C",
        "--no-colors",
        action="store_true",
        help="Disable coloring on the branch names.",
    )
    p_ll.add_argument("-g", action="store_true", help="Show repo summaries by group.")
    p_ll.set_defaults(func=f_ll)

    p_context = subparsers.add_parser(
        "context",
        help="set context",
        description="Set and remove context. A context is a group."
        " When set, all operations apply only to repos in that group.",
    )
    p_context.add_argument(
        "choice",
        nargs="?",
        choices=set().union(utils.get_groups(), {"none", "auto"}),
        help="Without this argument, show current context. "
        "Otherwise choose a group as context, or use 'auto', "
        "which sets the context/group automatically based on "
        "the current working directory. "
        "To remove context, use 'none'. ",
    )
    p_context.set_defaults(func=f_context)

    p_ls = subparsers.add_parser(
        "ls",
        help="show repo(s) or repo path",
        description="display names of all repos, or path of a chosen repo",
    )
    p_ls.add_argument(
        "repo",
        nargs="?",
        choices=utils.get_repos(),
        help="show path of the chosen repo",
    )
    p_ls.set_defaults(func=f_ls)

    p_group = subparsers.add_parser(
        "group", description="list, add, or remove repo group(s)", help="group repos"
    )
    p_group.set_defaults(func=f_group)
    group_cmds = p_group.add_subparsers(
        dest="group_cmd", help="additional help with sub-command -h"
    )
    pg_ll = group_cmds.add_parser("ll", description="List all groups with repos.")
    pg_ll.add_argument(
        "to_show", nargs="?", choices=utils.get_groups(), help="group to show"
    )
    group_cmds.add_parser("ls", description="List all group names.")
    pg_add = group_cmds.add_parser("add", description="Add repo(s) to a group.")
    pg_add.add_argument(
        "to_group",
        nargs="+",
        metavar="repo",
        choices=utils.get_repos(),
        help="repo(s) to be grouped",
    )
    pg_add.add_argument(
        "-n",
        "--name",
        dest="gname",
        type=partial(_group_name, exclude_old_names=False),
        metavar="group-name",
        required=True,
    )
    pg_add.add_argument(
        "-p", "--path", dest="gpath", type=_path_name, metavar="group-path"
    )

    pg_rmrepo = group_cmds.add_parser(
        "rmrepo", description="remove repo(s) from a group."
    )
    pg_rmrepo.add_argument(
        "to_rm",
        nargs="+",
        metavar="repo",
        choices=utils.get_repos(),
        help="repo(s) to be removed from the group",
    )
    pg_rmrepo.add_argument(
        "-n",
        "--name",
        dest="gname",
        metavar="group-name",
        required=True,
        help="group name",
    )
    pg_rename = group_cmds.add_parser("rename", description="Change group name.")
    pg_rename.add_argument(
        "gname",
        metavar="group-name",
        choices=utils.get_groups(),
        help="existing group to rename",
    )
    pg_rename.add_argument(
        "new_name", metavar="new-name", type=_group_name, help="new group name"
    )
    group_cmds.add_parser("rm", description="Remove group(s).").add_argument(
        "to_ungroup", nargs="+", choices=utils.get_groups(), help="group(s) to delete"
    )

    # superman mode
    p_super = subparsers.add_parser(
        "super",
        help="run any git command/alias",
        description="Superman mode: delegate any git command/alias in specified repo(s), group(s), or "
        "all repo(s).\n"
        'Examples:\n \t gita super myrepo1 commit -am "fix a bug"\n'
        "\t gita super repo1 repo2 repo3 checkout new-feature",
    )
    p_super.add_argument(
        "man",
        nargs=argparse.REMAINDER,
        help="execute arbitrary git command/alias for specified repo(s), group(s), or all repos.\n"
        "Example: gita super repo1 diff --name-only --staged;\n"
        "gita super checkout master ",
    )
    p_super.add_argument(
        "-q", "--quote-mode", action="store_true", help="use quote mode"
    )
    p_super.set_defaults(func=f_super)

    # shell mode
    p_shell = subparsers.add_parser(
        "shell",
        help="run any shell command",
        description="shell mode: delegate any shell command in specified repo(s), group(s), or "
        "all repo(s).\n"
        "Examples:\n \t gita shell pwd; \n"
        "\t gita shell repo1 repo2 repo3 touch xx",
    )
    p_shell.add_argument(
        "man",
        nargs=argparse.REMAINDER,
        help="execute arbitrary shell command for specified repo(s), group(s), or all repos.\n"
        "Example: gita shell myrepo1 ls\n"
        "Another: gita shell git checkout master ",
    )
    p_shell.add_argument(
        "-q", "--quote-mode", action="store_true", help="use quote mode"
    )
    p_shell.set_defaults(func=f_shell)

    # clear
    p_clear = subparsers.add_parser(
        "clear",
        description="removes all groups and repositories",
        help="removes all groups and repositories",
    )
    p_clear.set_defaults(func=f_clear)

    # sub-commands that fit boilerplate
    cmds = utils.get_cmds_from_files()
    for name, data in cmds.items():
        help = data.get("help")
        cmd = data["cmd"]
        if data.get("allow_all"):
            choices = utils.get_choices()
            nargs = "*"
            help += " for all repos or"
        else:
            choices = utils.get_repos().keys() | utils.get_groups().keys()
            nargs = "+"
        help += " for the chosen repo(s) or group(s)"
        sp = subparsers.add_parser(name, description=help)
        sp.add_argument("repo", nargs=nargs, choices=choices, help=help)
        is_shell = bool(data.get("shell"))
        sp.add_argument(
            "-s",
            "--shell",
            default=is_shell,
            type=bool,
            help="If set, run in shell mode",
        )
        if is_shell:
            cmd = [cmd]
        else:
            cmd = cmd.split()
        sp.set_defaults(func=f_git_cmd, cmd=cmd)

    args = p.parse_args(argv)

    args.async_blacklist = {
        name for name, data in cmds.items() if data.get("disable_async")
    }

    if "func" in args:
        args.func(args)
    else:
        p.print_help()  # pragma: no cover


if __name__ == "__main__":
    main()  # pragma: no cover
