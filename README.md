[![PyPi version](https://img.shields.io/pypi/v/gita.svg?color=blue)](https://pypi.org/project/gita/)
[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
[![codecov](https://codecov.io/gh/nosarthur/gita/branch/master/graph/badge.svg)](https://codecov.io/gh/nosarthur/gita)
[![licence](https://img.shields.io/pypi/l/gita.svg)](https://github.com/nosarthur/gita/blob/master/LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gita.svg)](https://pypistats.org/packages/gita)
[![Chinese](https://img.shields.io/badge/-中文-lightgrey.svg)](https://github.com/nosarthur/gita/blob/master/README_CN.md)

```
 _______________________________
(  ____ \__   __|__   __(  ___  )
| (    \/  ) (     ) (  | (   ) |
| |        | |     | |  | (___) |
| | ____   | |     | |  |  ___  |
| | \_  )  | |     | |  | (   ) |
| (___) |__) (___  | |  | )   ( |
(_______)_______/  )_(  |/     \|   v0.8
```

# Gita: a command-line tool to manage multiple git repos

This tool does two things

- display the status of multiple git repos such as branch, modification, commit message side by side
- delegate git commands/aliases from any working directory

If several repos compile together, it helps to see their status together too.
I also hate to change directories to execute git commands.

![gita screenshot](https://github.com/nosarthur/gita/raw/master/screenshot.png)

Here the branch color distinguishes 5 situations between local and remote branches:

- white: local has no remote
- green: local is the same as remote
- red: local has diverged from remote
- purple: local is ahead of remote (good for push)
- yellow: local is behind remote (good for merge)

The choice of purple for ahead and yellow for behind is motivated by
[blueshift](https://en.wikipedia.org/wiki/Blueshift) and [redshift](https://en.wikipedia.org/wiki/Redshift),
using green as baseline.

The additional status symbols denote

- `+`: staged changes
- `*`: unstaged changes
- `_`: untracked files/folders

The bookkeeping sub-commands are

- `gita add <repo-path(s)>`: add repo(s) to `gita`
- `gita rm <repo-name(s)>`: remove repo(s) from `gita` (won't remove files from disk)
- `gita ll`: display the status of all repos
- `gita ls`: display the names of all repos
- `gita ls <repo-name>`: display the absolute path of one repo
- `gita -v`: display gita version

Repo paths are saved in `$XDG_CONFIG_HOME/gita/repo_path` (most likely `~/.config/gita/repo_path`).

The delegating sub-commands are of two formats

- `gita <sub-command> [repo-name(s)]`: optional repo input, and no input means all repos.
- `gita <sub-command> <repo-name(s)>`: required repo name(s) input

By default, only `fetch` and `pull` take optional input.
Sub-commands with required input are `branch`, `clean`, `diff`, `difftool`,
`log`, `merge`, `mergetool`, `patch`, `push`, `rebase`, `reflog`, `remote`, `reset`,
`stash`, `stat`, `status`, and `tag`.

If more than one repos are specified, the git command will run asynchronously,
with the exception of `log`, `difftool` and `mergetool`, which require non-trivial user input.

## Customization

Custom delegating sub-commands can be defined in `$XDG_CONFIG_HOME/gita/cmds.yml`
(most likely `~/.config/gita/cmds.yml`).
And they shadow the default ones if name collisions exist.

Default delegating sub-commands are defined in
[cmds.yml](https://github.com/nosarthur/gita/blob/master/gita/cmds.yml).
For example, `gita stat <repo-name(s)>` is registered as

```yaml
stat:
  cmd: diff --stat
  help: show edit statistics
```

which executes `git diff --stat`.

If the delegated git command is a single word, the `cmd` tag can be omitted.
See `push` for an example.
To disable asynchronous execution, set the `disable_async` tag to be `true`.
See `difftool` for an example.

If you want a custom command to behave like `gita fetch`, i.e., to apply
command to all repos if nothing is specified,
set the `allow_all` option to be `true`.
For example, the following snippet creates a new command
`gita comaster [repo-name(s)]` with optional repo name input.

```yaml
comaster:
  cmd: checkout master
  allow_all: true
  help: checkout the master branch
```

## Superman mode

The superman mode delegates any git command/alias.
Usage:

```
gita super [repo-name(s)] <any-git-command-with-or-without-options>
```

Here `repo-name(s)` is optional, and absence means all repos.
For example,

- `gita super checkout master` puts all repos on the master branch
- `gita super frontend-repo backend-repo commit -am 'implement a new feature'`
  executes `git commit -am 'implement a new feature'` for `frontend-repo` and `backend-repo`

## Requirements

Gita requires Python 3.6 or higher, due to the use of
[f-string](https://www.python.org/dev/peps/pep-0498/)
and [asyncio module](https://docs.python.org/3.6/library/asyncio.html).

Under the hood, gita uses subprocess to run git commands/aliases.
Thus the installed git version may matter.
I have git `1.8.3.1`, `2.17.2`, and `2.20.1` on my machines, and
their results agree.

## Installation

To install the latest version, run

```
pip3 install -U gita
```

If development mode is preferred,
download the source code and run

````
pip3 install -e <gita-source-folder>
```

In either case, calling `gita` in terminal may not work,
then you can put the following line in the `.bashrc` file.

```
alias gita="python3 -m gita"
```

## Auto-completion

For auto completion, download
[.gita-completion.bash](https://github.com/nosarthur/gita/blob/master/.gita-completion.bash)
and source it in `.bashrc`.

## Contributing

To contribute, you can

- report/fix bugs
- request/implement features
- star/recommend this project

To run tests locally, simply `pytest`.
More implementation details are in
[design.md](https://github.com/nosarthur/gita/blob/master/design.md).

## Other multi-repo tools

I haven't tried them but I heard good things about them.

- [myrepos](https://myrepos.branchable.com/)
- [repo](https://source.android.com/setup/develop/repo)
````
