[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
# A command-line tool to view multiple git repos

Often times multiple git repos are related and it helps to see their status (branch, modification) side by side,
as in the following screenshot:

![gita screenshot](https://github.com/nosarthur/gita/raw/master/screenshot.png)

The supported commands are

* `gita add <repo-path>`: add repo path
* `gita rm <repo-name>`: remove repo
* `gita ls`: display the status of all repos
* `gita ls <repo-name>`: display the absolute path of the specified repo. One can then enter that directory using ``cd `gita ls <repo>` ``

The repo paths are saved in `~/.gita_path`

## installation

Download the source and take a look at the Makefile. Or just `pip3 install -e .`.

I also put the following line in my .bashrc
```
alias gita="python3 -m gita"
```

## TODO
