import os
from pathlib import Path
from functools import lru_cache
from typing import Dict


# TODO: python3.9 pathlib has is_relative_to() function
def is_relative_to(kid: str, parent: str) -> bool:
    """
    Both the `kid` and `parent` should be absolute path
    """
    return parent == os.path.commonpath((kid, parent))


@lru_cache()
def get_repos(root=None) -> Dict[str, str]:
    """
    Return a `dict` of repo name to repo absolute path

    @param config_dir: If None, use either global or local config depending on cwd.
    """
    path_file = get_config_fname('repo_path', root)
    repos = {}
    # Each line is a repo path and repo name separated by ,
    if os.path.isfile(path_file) and os.stat(path_file).st_size > 0:
        with open(path_file) as f:
            for line in f:
                line = line.rstrip()
                if not line:  # blank line
                    continue
                path, name = line.split(',')
                if not is_git(path):
                    continue
                if name not in repos:
                    repos[name] = path
                else:  # repo name collision for different paths: include parent path name
                    par_name = os.path.basename(os.path.dirname(path))
                    repos[os.path.join(par_name, name)] = path
    if root is None:  # detect if inside a main path
        cwd = os.getcwd()
        for _, path in repos.items():
            if is_relative_to(cwd, path):
                return get_repos(path)
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


def get_config_dir(root=None) -> str:
    if root is None:
        root = os.environ.get('XDG_CONFIG_HOME') or os.path.join(
            os.path.expanduser('~'), '.config')
        return os.path.join(root, "gita")
    else:
        return os.path.join(root, ".gita")


def get_config_fname(fname: str, root=None) -> str:
    """
    Return the file name that stores the repo locations.
    """
    return os.path.join(get_config_dir(root), fname)
