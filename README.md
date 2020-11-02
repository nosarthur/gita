[![PyPi version](https://img.shields.io/pypi/v/gita.svg?color=blue)](https://pypi.org/project/gita/)
[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
[![codecov](https://codecov.io/gh/nosarthur/gita/branch/master/graph/badge.svg)](https://codecov.io/gh/nosarthur/gita)
[![licence](https://img.shields.io/pypi/l/gita.svg)](https://github.com/nosarthur/gita/blob/master/LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gita.svg)](https://pypistats.org/packages/gita)
[![Gitter](https://badges.gitter.im/nosarthur/gita.svg)](https://gitter.im/nosarthur/gita?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![Chinese](https://img.shields.io/badge/-中文-lightgrey.svg)](https://github.com/nosarthur/gita/blob/master/doc/README_CN.md)

```
 _______________________________
(  ____ \__   __|__   __(  ___  )
| (    \/  ) (     ) (  | (   ) |
| |        | |     | |  | (___) |
| | ____   | |     | |  |  ___  |
| | \_  )  | |     | |  | (   ) |
| (___) |__) (___  | |  | )   ( |
(_______)_______/  )_(  |/     \|   v0.12
```

# Gita: a command-line tool to manage multiple git repos

This tool does two things

- display the status of multiple git repos such as branch, modification, commit message side by side
- (batch) delegate git commands/aliases from any working directory

If several repos are related, it helps to see their status together.
I also hate to change directories to execute git commands.

![gita screenshot](https://github.com/nosarthur/gita/raw/master/doc/screenshot.png)

In the screenshot, the `gita remote nowhub` command translates to `git remote -v`
for the `nowhub` repo.
To see the pre-defined sub-commands, run `gita -h` or take a look at
[cmds.yml](https://github.com/nosarthur/gita/blob/master/gita/cmds.yml).
To add your own sub-commands, see the [customization section](#custom).
To run arbitrary `git` command, see the [superman mode section](#superman).

The branch color distinguishes 5 situations between local and remote branches:

- white: local has no remote
- green: local is the same as remote
- red: local has diverged from remote
- purple: local is ahead of remote (good for push)
- yellow: local is behind remote (good for merge)

The choice of purple for ahead and yellow for behind is motivated by
[blueshift](https://en.wikipedia.org/wiki/Blueshift) and [redshift](https://en.wikipedia.org/wiki/Redshift),
using green as baseline.
You can change the color schemes using the `gita color` sub-command.
See the [customization section](#custom).

The additional status symbols denote

- `+`: staged changes
- `*`: unstaged changes
- `_`: untracked files/folders

The bookkeeping sub-commands are

- `gita add <repo-path(s)>`: add repo(s) to `gita`
- `gita context`: context sub-command
    - `gita context`: show current context
    - `gita context none`: remove context
    - `gita context <group-name>`: set context to `group-name`, all operations then only apply to repos in this group
- `gita color`: color sub-command
    - `gita color [ll]`: Show available colors and the current coloring scheme
    - `gita color set <situation> <color>`: Use the specified color for the local-remote situation
- `gita group`: group sub-command
    - `gita group add <repo-name(s)> -n <group-name>`: add repo(s) to a new group or existing group
    - `gita group [ll]`: display existing groups with repos
    - `gita group ls`: display existing group names
    - `gita group rename <group-name> <new-name>`: change group name
    - `gita group rm <group-name(s)>`: delete group(s)
- `gita info`: info sub-command
    - `gita info [ll]`: display the used and unused information items
    - `gita info add <info-item>`: enable information item
    - `gita info rm <info-item>`: disable information item
- `gita ll`: display the status of all repos
- `gita ll <group-name>`: display the status of repos in a group
- `gita ls`: display the names of all repos
- `gita ls <repo-name>`: display the absolute path of one repo
- `gita rename <repo-name> <new-name>`: rename a repo
- `gita rm <repo-name(s)>`: remove repo(s) from `gita` (won't remove files from disk)
- `gita -v`: display gita version

The `git` delegating sub-commands are of two formats

- `gita <sub-command> [repo-name(s) or group-name(s)]`:
  optional repo or group input, and **no input means all repos**.
- `gita <sub-command> <repo-name(s) or groups-name(s)>`:
  required repo name(s) or group name(s) input

They translate to `git <sub-command>` for the corresponding repos.
By default, only `fetch` and `pull` take optional input. In other words,
`gita fetch` and `gita pull` apply to all repos.
To see the pre-defined sub-commands, run `gita -h` or take a look at
[cmds.yml](https://github.com/nosarthur/gita/blob/master/gita/cmds.yml).
To add your own sub-commands, see the [customization section](#custom).
To run arbitrary `git` command, see the [superman mode section](#superman).

If more than one repos are specified, the `git` command runs asynchronously,
with the exception of `log`, `difftool` and `mergetool`,
which require non-trivial user input.

Repo paths are saved in `$XDG_CONFIG_HOME/gita/repo_path` (most likely `~/.config/gita/repo_path`).

## Installation

To install the latest version, run

```
pip3 install -U gita
```

If you prefer development mode, download the source code and run

```
pip3 install -e <gita-source-folder>
```

In either case, calling `gita` in terminal may not work,
then you can put the following line in the `.bashrc` file.

```
alias gita="python3 -m gita"
```

Windows users may need to enable the ANSI escape sequence in terminal for
the branch color to work.
See [this stackoverflow post](https://stackoverflow.com/questions/51680709/colored-text-output-in-powershell-console-using-ansi-vt100-codes) for details.

## Auto-completion

Download
[.gita-completion.bash](https://github.com/nosarthur/gita/blob/master/.gita-completion.bash)
or
[.gita-completion.zsh](https://github.com/nosarthur/gita/blob/master/.gita-completion.zsh)
and source it in the .rc file.

## <a name='superman'></a> Superman mode

The superman mode delegates any `git` command or alias.
Usage:

```
gita super [repo-name(s) or group-name(s)] <any-git-command-with-or-without-options>
```

Here `repo-name(s)` or `group-name(s)` are optional, and their absence means all repos.
For example,

- `gita super checkout master` puts all repos on the master branch
- `gita super frontend-repo backend-repo commit -am 'implement a new feature'`
  executes `git commit -am 'implement a new feature'` for `frontend-repo` and `backend-repo`

## <a name='custom'></a> Customization

### user-defined sub-command using yaml file

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

which executes `git diff --stat` for the specified repo(s).

If the delegated `git` command is a single word, the `cmd` tag can be omitted.
See `push` for an example.
To disable asynchronous execution, set the `disable_async` tag to be `true`.
See `difftool` for an example.

If you want a custom command to behave like `gita fetch`, i.e., to apply the
command to all repos when no repo is specified,
set the `allow_all` option to be `true`.
For example, the following snippet creates a new command
`gita comaster [repo-name(s)]` with optional repo name input.

```yaml
comaster:
  cmd: checkout master
  allow_all: true
  help: checkout the master branch
```

### customize information displayed by the `gita ll` command

You can customize the information displayed by `gita ll`.
The used and unused information items are shown with `gita info`, and the
configuration is saved in `$XDG_CONFIG_HOME/gita/info.yml`.

For example, the default information items setting corresponds to

```yaml
- branch
- commit_msg
```

### customize the local/remote relationship coloring displayed by the `gita ll` command

You can see the default color scheme and the available colors via `gita color`.
To change the color coding, use `gita color set <situation> <color>`.

## Requirements

Gita requires Python 3.6 or higher, due to the use of
[f-string](https://www.python.org/dev/peps/pep-0498/)
and [asyncio module](https://docs.python.org/3.6/library/asyncio.html).

Under the hood, gita uses `subprocess` to run git commands/aliases.
Thus the installed git version may matter.
I have git `1.8.3.1`, `2.17.2`, and `2.20.1` on my machines, and
their results agree.

## Contributing

To contribute, you can

- report/fix bugs
- request/implement features
- star/recommend this project

Chat room is available on [![Join the chat at https://gitter.im/nosarthur/gita](https://badges.gitter.im/nosarthur/gita.svg)](https://gitter.im/nosarthur/gita?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

To run tests locally, simply `pytest`.
More implementation details are in
[design.md](https://github.com/nosarthur/gita/blob/master/doc/design.md).
A step-by-step guide to reproduce this project is [here](https://nosarthur.github.io/side%20project/2019/05/27/gita-breakdown.html).

You can also sponsor me on [GitHub](https://github.com/sponsors/nosarthur). Any amount is appreciated!

## Contributors

[![nosarthur](https://github.com/nosarthur.png?size=40 "nosarthur")](https://github.com/nosarthur)
[![mc0239](https://github.com/mc0239.png?size=40 "mc0239")](https://github.com/mc0239)
[![dgrant](https://github.com/dgrant.png?size=40 "dgrant")](https://github.com/dgrant)
[![samibh](https://github.com/github.png?size=40 "samibh")](https://github.com/samibh)
[![wbrn](https://github.com/wbrn.png?size=40 "wbrn")](https://github.com/wbrn)
[![TpOut](https://github.com/TpOut.png?size=40 "TpOut")](https://github.com/TpOut)
[![PabloCastellano](https://github.com/PabloCastellano.png?size=40 "PabloCastellano")](https://github.com/PabloCastellano)
[![cd3](https://github.com/cd3.png?size=40 "cd3")](https://github.com/cd3)
[![Steve-Xyh](https://github.com/Steve-Xyh.png?size=40 "Steve-Xyh")](https://github.com/Steve-Xyh)

## Other multi-repo tools

I haven't tried them but I heard good things about them.

- [myrepos](https://myrepos.branchable.com/)
- [repo](https://source.android.com/setup/develop/repo)

