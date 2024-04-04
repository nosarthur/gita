import os
import csv
from typing import Tuple


def parse_clone_config(fname: str) -> Tuple:
    """
    Return the repo information (url, name, path, type) and group information
    (, name, path, repos) saved in `fname`.
    """
    repos = {}
    groups = {}
    if os.path.isfile(fname) and os.stat(fname).st_size > 0:
        with open(fname) as f:
            rows = csv.DictReader(
                f, ["url", "name", "path", "type", "flags"], restval=""
            )  # it's actually a reader
            for r in rows:
                if r["url"]:
                    repos[r["name"]] = {
                        "path": r["path"],
                        "type": r["type"],
                        "flags": r["flags"].split(),
                        "url": r["url"],
                    }
                else:
                    groups[r["name"]] = {
                        "path": r["path"],
                        "repos": [
                            repo for repo in r["type"].split("|") if repo in repos
                        ],
                    }
    return repos, groups
