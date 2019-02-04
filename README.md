[![PyPi version](https://img.shields.io/pypi/v/gita.svg)](https://pypi.org/project/gita/)
[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
[![codecov](https://codecov.io/gh/nosarthur/gita/branch/master/graph/badge.svg)](https://codecov.io/gh/nosarthur/gita)
[![licence](https://img.shields.io/pypi/l/gita.svg?style=flat)](https://github.com/nosarthur/gita/blob/master/LICENSE)

# A command-line tool to manage multiple git repos

This tool does two things

- display the status of multiple git repos such as branch, modification, commit message side by side
- delegate git commands from any working directory

![gita screenshot](https://github.com/nosarthur/gita/raw/master/screenshot.png)

Here the colors denote the 5 situations between local and remote branches:

- white: local branch has no remote branch
- green: local branch is the same as remote branch
- red: local branch has diverged from remote branch
- purple: local branch is ahead of remote branch (good for push)
- yellow: local branch is behind remote branch (good for merge)

The choice of purple for ahead and yellow for behind is motivated by
[blueshift](https://en.wikipedia.org/wiki/Blueshift) and [redshift](https://en.wikipedia.org/wiki/Redshift),
using green as baseline.

The additional status symbols denote

- `+`: staged changes
- `*`: unstaged changes
- `_`: untracked files/folders

The bookkeeping sub-commands are

- `gita add <repo-path(s)>`: add repo(s) to `gita`
- `gita rm <repo-name>`: remove repo from `gita` (won't remove repo from disk)
- `gita ls`: display the status of all repos
- `gita ls <repo-name>`: display the absolute path of one repo
- `gita --version`: display gita version

Repo paths are saved in `~/.gita/repo_path`.

The delegated git sub-commands are

- `gita branch <repo-name(s)>`: show local branches for the specified repo(s)
- `gita clean <repo-name(s)>`: remove untracked files/folders for the specified repo(s)
- `gita difftool <repo-name(s)>`: show differences for the specified repo(s)
- `gita fetch`: fetch remote updates for all repos
- `gita fetch <repo-name(s)>`: fetch remote updates for the specified repo(s)
- `gita log <repo-name(s)>`: show log of the specified repo(s)
- `gita merge <repo-name(s)>`: merge remote updates for the specified repo(s)
- `gita patch <repo-name(s)>`: make a patch for the specified repo(s)
- `gita pull <repo-name(s)>`: pull remote updates for the specified repo(s)
- `gita push <repo-name(s)>`: push local updates of the specified repo(s) to remote
- `gita remote <repo-name(s)>`: show remote settings of the specified repo(s)
- `gita reflog <repo-name(s)>`: show ref logs of the specified repo(s)
- `gita stat <repo-name(s)>`: show repo(s) edit statistics
- `gita status <repo-name(s)>`: show repo(s) status

Delegation details are specified in
[cmds.yml](https://github.com/nosarthur/gita/blob/master/gita/cmds.yml).
For example, `gita stat <repo-name(s)>` is registered as

```yaml
stat:
  cmd: diff --stat
  help: show edit statistics
```

and the delegated command is `git diff --stat`.

## customization

Custom git command aliases can be placed in `~/.gita/cmds.yml`.
And they shadow the default ones in the case of name clashes.

## installation

To install the latest version, run

```
pip3 install -U gita
```

If development mode is preferred,
download the source code and run `pip3 install -e <gita-source-folder>`.
In either case, calling `gita` in terminal may not work,
then you can put the following line in the `.bashrc` file.

```
alias gita="python3 -m gita"
```

## TODO (not tracked by issues)

- auto-completion
