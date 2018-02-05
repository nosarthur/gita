# Manage multiple git repos

It occurs that multiple git repos are related and this is a tool to see their status in one shot.

```
python3 -m gita
```

* `gita add`: add repo path
* `gita ls`: display the status of all repos
* `gita ls <repo>`: display the absolute path of the specified repo. One can then enter that directory by ``cd `gita ls <repo>` ``

The repo paths are saved in `~/.gita_path`

## installation

Download the source and take a look at the Makefile. Or just `pip3 install -e .`.

## TODO

* add test coverage
* travis ci
