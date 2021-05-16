import os
import yaml
import asyncio
import platform
from functools import lru_cache, partial
from pathlib import Path
from typing import List, Dict, Coroutine, Union, Iterator

from . import info
from . import common


@lru_cache()
def get_context() -> Union[Path, None]:
    """
    Return the context: either a group name or 'none'
    """
    config_dir = Path(common.get_config_dir())
    matches = list(config_dir.glob('*.context'))
    assert len(matches) < 2, "Cannot have multiple .context file"
    return matches[0] if matches else None


@lru_cache()
def get_groups() -> Dict[str, List[str]]:
    """
    Return a `dict` of group name to repo names.
    """
    fname = common.get_config_fname('groups.yml')
    groups = {}
    # Each line is a repo path and repo name separated by ,
    if os.path.isfile(fname) and os.stat(fname).st_size > 0:
        with open(fname, 'r') as f:
            groups = yaml.load(f, Loader=yaml.SafeLoader)
    return groups


def get_choices() -> List[Union[str, None]]:
    """
    Return all repo names, group names, and an additional empty list. The empty
    list is added as a workaround of
    argparse's problem with coexisting nargs='*' and choices.
    See https://utcc.utoronto.ca/~cks/space/blog/python/ArgparseNargsChoicesLimitation
    and
    https://bugs.python.org/issue27227
    """
    choices = list(common.get_repos())
    choices.extend(get_groups())
    choices.append([])
    return choices


def rename_repo(repos: Dict[str, str], repo: str, new_name: str):
    """
    Write new repo name to file
    """
    # FIXME: We should check the new name is not in use
    path = repos[repo]
    del repos[repo]
    repos[new_name] = path
    write_to_repo_file(repos, 'w')
    # update groups
    groups = get_groups()
    for g, members in groups.items():
        if repo in members:
            members.remove(repo)
            members.append(new_name)
            groups[g] = sorted(members)
    write_to_groups_file(groups, 'w')


def write_to_repo_file(repos: Dict[str, str], mode: str, root=None):
    """
    """
    data = ''.join(f'{path},{name}\n' for name, path in repos.items())
    fname = common.get_config_fname('repo_path', root)
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    with open(fname, mode) as f:
        f.write(data)


def write_to_groups_file(groups: Dict[str, List[str]], mode: str):
    """

    """
    fname = common.get_config_fname('groups.yml')
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    if not groups:  # all groups are deleted
        open(fname, 'w').close()
    else:
        with open(fname, mode) as f:
            yaml.dump(groups, f, default_flow_style=None)


def add_repos(repos: Dict[str, str], new_paths: List[str],
        repo_type=0, root=None) -> Dict[str, str]:
    """
    Write new repo paths to file; return the added repos.

    @param repos: name -> path
    """
    existing_paths = set(repos.values())
    new_paths = set(os.path.abspath(p) for p in new_paths if is_git(p))
    new_paths = new_paths - existing_paths
    new_repos = {}
    if new_paths:
        print(f"Found {len(new_paths)} new repo(s).")
        new_repos = {
                os.path.basename(os.path.normpath(path)): path
                for path in new_paths}
        write_to_repo_file(new_repos, 'a+', root)
    else:
        print('No new repos found!')
    return new_repos


def parse_clone_config(fname: str) -> Iterator[List[str]]:
    """
    Return the url, name, and path of all repos in `fname`.
    """
    with open(fname) as f:
        for line in f:
            yield line.strip().split(',')


async def run_async(repo_name: str, path: str, cmds: List[str]) -> Union[None, str]:
    """
    Run `cmds` asynchronously in `path` directory. Return the `path` if
    execution fails.
    """
    process = await asyncio.create_subprocess_exec(
        *cmds,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
        cwd=path)
    stdout, stderr = await process.communicate()
    for pipe in (stdout, stderr):
        if pipe:
            print(format_output(pipe.decode(), repo_name))
    # The existence of stderr is not good indicator since git sometimes write
    # to stderr even if the execution is successful, e.g. git fetch
    if process.returncode != 0:
        return path


def format_output(s: str, prefix: str):
    """
    Prepends every line in given string with the given prefix.
    """
    return ''.join([f'{prefix}: {line}' for line in s.splitlines(keepends=True)])


def exec_async_tasks(tasks: List[Coroutine]) -> List[Union[None, str]]:
    """
    Execute tasks asynchronously
    """
    # TODO: asyncio API is nicer in python 3.7
    if platform.system() == 'Windows':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    try:
        errors = loop.run_until_complete(asyncio.gather(*tasks))
    finally:
        loop.close()
    return errors


def describe(repos: Dict[str, str], no_colors: bool=False) -> str:
    """
    Return the status of all repos
    """
    if repos:
        name_width = max(len(n) for n in repos) + 1
    funcs = info.get_info_funcs()

    get_repo_status = info.get_repo_status
    if get_repo_status in funcs and no_colors:
        idx = funcs.index(get_repo_status)
        funcs[idx] = partial(get_repo_status, no_colors=True)

    for name in sorted(repos):
        path = repos[name]
        info_items = ' '.join(f(path) for f in funcs)
        yield f'{name:<{name_width}}{info_items}'


def get_cmds_from_files() -> Dict[str, Dict[str, str]]:
    """
    Parse delegated git commands from default config file
    and custom config file.

    Example return
    {
      'branch': {'help': 'show local branches'},
      'clean': {'cmd': 'clean -dfx',
                'help': 'remove all untracked files/folders'},
    }
    """
    # default config file
    fname = os.path.join(os.path.dirname(__file__), "cmds.yml")
    with open(fname, 'r') as stream:
        cmds = yaml.load(stream, Loader=yaml.SafeLoader)

    # custom config file
    root = common.get_config_dir()
    fname = os.path.join(root, 'cmds.yml')
    custom_cmds = {}
    if os.path.isfile(fname) and os.path.getsize(fname):
        with open(fname, 'r') as stream:
            custom_cmds = yaml.load(stream, Loader=yaml.SafeLoader)

    # custom commands shadow default ones
    cmds.update(custom_cmds)
    return cmds
