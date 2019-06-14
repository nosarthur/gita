import os
import yaml
import asyncio
import platform
import subprocess
from functools import lru_cache
from typing import List, Dict, Tuple, Coroutine, Union


class Color:
    """
    Terminal color
    """
    red = '\x1b[31m'  # local diverges from remote
    green = '\x1b[32m'  # local == remote
    yellow = '\x1b[33m'  # local is behind
    purple = '\x1b[35m'  # local is ahead
    white = '\x1b[37m'  # no remote branch
    end = '\x1b[0m'


def get_path_fname() -> str:
    """
    Return the file name that stores the repo locations.
    """
    root = os.environ.get('XDG_CONFIG_HOME') or os.path.join(
        os.path.expanduser('~'), '.config')
    return os.path.join(root, 'gita', 'repo_path')


@lru_cache()
def get_repos() -> Dict[str, str]:
    """
    Return a `dict` of repo name to repo absolute path
    """
    path_file = get_path_fname()
    data = []
    if os.path.isfile(path_file) and os.stat(path_file).st_size > 0:
        with open(path_file) as f:
            # TODO: read lines one by one
            #   for line in f:
            data = f.read().splitlines()
    # The file content is repos separated by :
    # For each repo, there are path and repo name separated by ,
    # If repo name is not provided, the basename of the path is used as name.
    # For example, "/a/b/c,xx:/a/b/d:/c/e/f" corresponds to
    # {xx: /a/b/c, d: /a/b/d, f: /c/e/f}
    repos = {}
    for d in data:
        if not d:  # blank line
            continue
        path, name = d.split(',')
        if not is_git(path):
            continue
        if name not in repos:
            repos[name] = path
        else:  # repo name collision for different paths: include parent path name
            par_name = os.path.basename(os.path.dirname(path))
            repos[os.path.join(par_name, name)] = path
    return repos


def get_choices() -> List[Union[str, None]]:
    """
    Return all repo names and an additional empty list. This is a workaround of
    argparse's problem with coexisting nargs='*' and choices.
    See https://utcc.utoronto.ca/~cks/space/blog/python/ArgparseNargsChoicesLimitation
    and
    https://bugs.python.org/issue27227
    """
    repos = list(get_repos())
    repos.append([])
    return repos


def is_git(path: str) -> bool:
    """
    Return True if the path is a git repo.
    """
    # An alternative is to call `git rev-parse --is-inside-work-tree`
    # I don't see why that one is better yet.
    # For a regular git repo, .git is a folder, for a worktree repo, .git is a file.
    # However, git submodule repo also has .git as a file.
    # A more reliable way to differentiable regular and worktree repos is to
    # compare the result of `git rev-parse --git-dir` and
    # `git rev-parse --git-common-dir`
    loc = os.path.join(path, '.git')
    # TODO: we can display the worktree repos in a different font.
    return os.path.exists(loc)


def rename_repo(repos: Dict[str, str], repo: str, new_name: str):
    """
    Write new repo name to file
    """
    path = repos[repo]
    del repos[repo]
    repos[new_name] = path
    _write_to_repo_file(repos, 'w')


def _write_to_repo_file(repos: Dict[str, str], mode: str):
    """
    """
    data = ''.join(f'{path},{name}\n' for name, path in repos.items())
    fname = get_path_fname()
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    with open(fname, mode) as f:
        f.write(data)


def add_repos(repos: Dict[str, str], new_paths: List[str]):
    """
    Write new repo paths to file
    """
    existing_paths = set(repos.values())
    new_paths = set(os.path.abspath(p) for p in new_paths if is_git(p))
    new_paths = new_paths - existing_paths
    if new_paths:
        print(f"Found {len(new_paths)} new repo(s).")
        new_repos = {
                os.path.basename(os.path.normpath(path)): path
                for path in new_paths}
        _write_to_repo_file(new_repos, 'a+')
    else:
        print('No new repos found!')


def get_head(path: str) -> str:
    result = subprocess.run(
        'git rev-parse --abbrev-ref HEAD'.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
        cwd=path)
    return result.stdout.strip()


def run_quiet_diff(args: List[str]) -> bool:
    """
    Return the return code of git diff `args` in quiet mode
    """
    result = subprocess.run(
        ['git', 'diff', '--quiet'] + args,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode


def has_untracked() -> bool:
    """
    Return True if untracked file/folder exists
    """
    result = subprocess.run(
        'git ls-files -zo --exclude-standard'.split(), stdout=subprocess.PIPE)
    return bool(result.stdout)


def get_commit_msg() -> str:
    """
    Return the last commit message.
    """
    # `git show-branch --no-name HEAD` is faster than `git show -s --format=%s`
    result = subprocess.run(
        'git show-branch --no-name HEAD'.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True)
    return result.stdout.strip()


async def run_async(path: str, cmds: List[str]) -> Union[None, str]:
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
    stdout and print(stdout.decode())
    stderr and print(stderr.decode())
    # The existence of stderr is not good indicator since git sometimes write
    # to stderr even if the execution is successful, e.g. git fetch
    if process.returncode != 0:
        return path


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


def get_common_commit() -> str:
    """
    Return the hash of the common commit of the local and upstream branches.
    """
    result = subprocess.run(
        'git merge-base @{0} @{u}'.split(),
        stdout=subprocess.PIPE,
        universal_newlines=True)
    return result.stdout.strip()


def _get_repo_status(path: str) -> Tuple[str]:
    """
    Return the status of one repo
    """
    os.chdir(path)
    dirty = '*' if run_quiet_diff([]) else ''
    staged = '+' if run_quiet_diff(['--cached']) else ''
    untracked = '_' if has_untracked() else ''

    diff_returncode = run_quiet_diff(['@{u}', '@{0}'])
    has_no_remote = diff_returncode == 128
    has_no_diff = diff_returncode == 0
    if has_no_remote:
        color = Color.white
    elif has_no_diff:
        color = Color.green
    else:
        common_commit = get_common_commit()
        outdated = run_quiet_diff(['@{u}', common_commit])
        if outdated:
            diverged = run_quiet_diff(['@{0}', common_commit])
            color = Color.red if diverged else Color.yellow
        else:  # local is ahead of remote
            color = Color.purple
    return dirty, staged, untracked, color


def describe(repos: Dict[str, str]) -> str:
    """
    Return the status of all repos
    """
    if repos:
        name_width = max(len(n) for n in repos) + 1
    for name in sorted(repos):
        path = repos[name]
        head = get_head(path)
        dirty, staged, untracked, color = _get_repo_status(path)
        yield f'{name:<{name_width}}{color}{head+" "+dirty+staged+untracked:<10}{Color.end} {get_commit_msg()}'


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
        cmds = yaml.load(stream, Loader=yaml.FullLoader)

    # custom config file
    root = os.environ.get('XDG_CONFIG_HOME') or os.path.join(
        os.path.expanduser('~'), '.config')
    fname = os.path.join(root, 'gita', 'cmds.yml')
    custom_cmds = {}
    if os.path.isfile(fname):
        with open(fname, 'r') as stream:
            custom_cmds = yaml.load(stream, Loader=yaml.FullLoader)

    # custom commands shadow default ones
    cmds.update(custom_cmds)
    return cmds
