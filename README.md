[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
# A command-line tool to view multiple git repos

In case multiple git repos are related, it helps to see their status (branch, modification) side by side,
as in the following screenshot:

![gita screenshot](https://github.com/nosarthur/gita/raw/master/screenshot.png)

Here the color coding has the following meaning:

* red: the local branch is either behind or diverged from the remote branch.
* green: the local branch is the same as the remote branch.
* yellow: the local branch is ahead of the remote branch.

And the extra symbols have the following meaning:

* `+`: staged change exists
* `*`: unstaged change exists

The supported commands are

* `gita add <repo-path>`: add repo path
* `gita rm <repo-name>`: remove repo
* `gita ls`: display the status of all repos
* `gita ls <repo-name>`: display the absolute path of the specified repo
* `gita fetch`: fetch all remote updates
* `gita fetch <repo-name>`: fetch remote updates for the specified repo

The repo paths are saved in `~/.gita_path`

## installation

Download the source and `pip3 install -e <gita source folder>`.

I also put the following line in my .bashrc
```
alias gita="python3 -m gita"
```

## TODO
* auto-completion
