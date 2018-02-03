# Manage multiple git repos

It occurs that multiple git repos are related and this is a tool to see their status in one shot.

```
python3 -m gita
```

* `gita add`: add repo path
* `gita ls`: display the status of all repos
* `gita goto`: go to the specified repo

The repo paths are saved in `~/.gita_path`

## installation

Download the source and take a look at the Makefile.

## TODO

* add detailed git status
* add test coverage
* travis ci
