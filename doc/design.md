# design

This document explains the inner workings of this 200 LOC (excluding tests) project.

The main idea of `gita` is to run git command/alias in subprocess or
asynchronous subprocess, which enables the following features

- execute git commands/aliases from any working directory
- execute the same command for multiple repos in batch mode

In addition, the `gita ll` command runs various `git` commands to collect
information for each repo, and displays the result of all repos side by side.

## user interface

There are three types of `gita` sub-commands

- **bookkeeping**: add/remove repos from `gita`, display repo information
- **delegating**: delegate pre-configured `git` commands or aliases
- **`super`**: delegate arbitrary `git` commands or aliases

And there are only two `gita` options, i.e., the `-h` for help and `-v` for version.

The bookkeeping and delegating sub-commands all share the formats

```shell
gita <sub-command> <repo-name(s)>
gita <sub-command> [repo-name(s)]
```

The exceptions are `add`, `ll`, and `super`

```shell
gita ll
gita add <repo-path(s)>
gita super [repo-name(s)] <any-git-command-with-options>
```

The argument choices are determined by two utility functions

- `<repo-name(s)>`: `utils.get_repos() -> Dict[str, str]`
- `[repo-name(s)]`: `utils.get_choices() -> List[Union[str, None]]` which allows null input

## sub-command actions

The actions of the `gita` sub-commands are defined
in [`__main__.py`](https://github.com/nosarthur/gita/gita/__main__.py).

All delegating sub-commands call

```python
f_git_cmd(args: argparse.Namespace)
```

to run either `subprocess` or `asyncio` APIs.
`subprocess` is used if there is only one repo input or the sub-command is
not allowed to run asynchronously. Otherwise `asyncio` is used for efficiency.

The bookkeeping and `super` sub-commands have their own action functions

```python
f_<sub-command>(args: argparse.Namespace)
```

Not surprisingly, the `f_super` function calls `f_git_cmd` in the end.

## repo status information

Utility functions to extract repo status information are defined in [utils.py](https://github.com/nosarthur/gita/gita/utils.py).
For example,

| information                                                                    | API                                         | note                                    |
| ------------------------------------------------------------------------------ | ------------------------------------------- | --------------------------------------- |
| repo name and path                                                             | `get_repos() -> Dict[str, str]`             | parse `$XDG_CONFIG_HOME/gita/repo_path` |
| branch name                                                                    | `get_head(path: str) -> str`                | parse `.git/HEAD`                       |
| commit message                                                                 | `get_commit_msg() -> str`                   | run `subprocess`                        |
| loca/remote relation                                                           | `_get_repo_status(path: str) -> Tuple[str]` | run `subprocess`                        |
| edit status, i.e., unstaged change `*`, staged change `+`, untracked files `_` | `_get_repo_status(path: str) -> Tuple[str]` | run `subprocess`                        |

I notice that parsing file is faster than running `subprocess`.
One future improvement could be replacing the `subprocess` calls.
