[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
# A command-line tool to view multiple git repos

In case multiple git repos are related, it helps to see their status (branch, modification) side by side,
as in the following screenshot:

![gita screenshot](https://github.com/nosarthur/gita/raw/master/screenshot.png)

Here the color codings denote the 5 situations between local and remote branches:

* white: the local branch has no remote branch.
* green: the local branch is the same as the remote branch.
* red: the local branch has diverged from the remote branch.
* yellow: the local branch is ahead of the remote branch (good for push).
* purple: the local branch is behind the remote branch (good for merge).

And the extra symbols have the following meaning:

* `+`: staged change exists
* `*`: unstaged change exists

The supported commands are

* `gita add <repo-path>`: add repo
* `gita rm <repo-name>`: remove repo
* `gita ls`: display the status of all repos
* `gita ls <repo-name>`: display the absolute path of the specified repo
* `gita fetch`: fetch all remote updates
* `gita fetch <repo-name>`: fetch remote updates for the specified repo
* `gita merge <repo-name>`: merge remote updates for the specified repo

The repo paths are saved in `~/.gita_path`

## installation

Download the source and run `pip3 install -e <gita source folder>`.

I also put the following line in my .bashrc
```
alias gita="python3 -m gita"
```

## TODO
* auto-completion
