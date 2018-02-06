[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
# A commandline tool to view multiple git repos

Often times multiple git repos are related and it helps to see their status (branch, modification) side by side.

```
python3 -m gita
```

* `gita add`: add repo path
* `gita ls`: display the status of all repos
* `gita ls <repo>`: display the absolute path of the specified repo. One can then enter that directory using ``cd `gita ls <repo>` ``

A screenshot is below

![gita screenshot](https://github.com/nosarthur/gita/raw/master/screenshot.png)


The repo paths are saved in `~/.gita_path`

## installation

Download the source and take a look at the Makefile. Or just `pip3 install -e .`.

## TODO
