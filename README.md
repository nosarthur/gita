[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
# A command-line tool to view multiple git repos

In the presence of multiple related git repos, it helps to see their status (branch, modification) side by side,
as in the following screenshot:

![gita screenshot](https://github.com/nosarthur/gita/raw/master/screenshot.png)

Here the color codings denote the 5 situations between local and remote branches:

* white: the local branch has no remote branch.
* green: the local branch is the same as the remote branch.
* red: the local branch has diverged from the remote branch.
* purple: the local branch is ahead of the remote branch (good for push).
* yellow: the local branch is behind the remote branch (good for merge).

The color choices of purple for ahead and yellow for behind is motivated by [blueshift](https://en.wikipedia.org/wiki/Blueshift) and [redshift](https://en.wikipedia.org/wiki/Redshift).

The extra status symbols have the following meaning:

* `+`: staged change exists
* `*`: unstaged change exists

The supported commands are

* `gita add <repo-path>`: add repo to `gita`
* `gita rm <repo-name>`: remove repo from `gita`
* `gita ls`: display the status of all repos
* `gita ls <repo-name>`: display the absolute path of the specified repo
* `gita fetch`: fetch all remote updates
* `gita fetch <repo-name(s)>`: fetch remote updates for the specified repo(s)
* `gita pull <repo-name(s)>`: pull remote updates for the specified repo(s)
* `gita merge <repo-name(s)>`: merge remote updates for the specified repo(s)
* `gita push <repo-name(s)>`: push local updates of the specified repo(s) to remote

The repo paths are saved in `~/.gita_path`

## installation

To install, simply use pip3

```
pip3 install gita
```

Alternatively, you can download the source code and run `pip3 install -e <gita source folder>`.
This is known as the development mode.
In this case, calling `gita` in bash may not work, and you can put the following line in the .bashrc file
```
alias gita="python3 -m gita"
```

## TODO
* add versioning
* auto-completion
