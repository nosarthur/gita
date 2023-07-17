import pytest
import asyncio
import subprocess
from pathlib import Path
from unittest.mock import patch, mock_open

from gita import utils, info
from conftest import (
    PATH_FNAME,
    PATH_FNAME_EMPTY,
    PATH_FNAME_CLASH,
    GROUP_FNAME,
    TEST_DIR,
)


@pytest.mark.parametrize(
    "kid, parent, expected",
    [
        ("/a/b/repo", "/a/b", ["repo"]),
        ("/a/b/repo", "/a", ["b", "repo"]),
        ("/a/b/repo", "/a/", ["b", "repo"]),
        ("/a/b/repo", "", None),
        ("/a/b/repo", "/a/b/repo", []),
    ],
)
def test_get_relative_path(kid, parent, expected):
    assert expected == utils.get_relative_path(kid, parent)


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            [],
            (
                {
                    "repo1": {"path": "/a/bcd/repo1", "type": "", "flags": []},
                    "xxx": {"path": "/a/b/c/repo3", "type": "", "flags": []},
                    "repo2": {"path": "/e/fgh/repo2", "type": "", "flags": []},
                },
                [],
            ),
        ),
        (
            ["st"],
            (
                {
                    "repo1": {"path": "/a/bcd/repo1", "type": "", "flags": []},
                    "xxx": {"path": "/a/b/c/repo3", "type": "", "flags": []},
                    "repo2": {"path": "/e/fgh/repo2", "type": "", "flags": []},
                },
                ["st"],
            ),
        ),
        (
            ["repo1", "st"],
            ({"repo1": {"flags": [], "path": "/a/bcd/repo1", "type": ""}}, ["st"]),
        ),
        (["repo1"], ({"repo1": {"flags": [], "path": "/a/bcd/repo1", "type": ""}}, [])),
    ],
)
@patch("gita.utils.is_git", return_value=True)
@patch("gita.common.get_config_fname", return_value=PATH_FNAME)
def test_parse_repos_and_rest(mock_path_fname, _, input, expected):
    got = utils.parse_repos_and_rest(input)
    assert got == expected


@pytest.mark.parametrize(
    "repo_path, paths, expected",
    [
        ("/a/b/c/repo", ["/a/b"], (("b", "c"), "/a")),
    ],
)
def test_generate_dir_hash(repo_path, paths, expected):
    got = utils._generate_dir_hash(repo_path, paths)
    assert got == expected


@pytest.mark.parametrize(
    "repos, paths, expected",
    [
        (
            {"r1": {"path": "/a/b//repo1"}, "r2": {"path": "/a/b/repo2"}},
            ["/a/b"],
            {"b": {"repos": ["r1", "r2"], "path": "/a/b"}},
        ),
        (
            {"r1": {"path": "/a/b//repo1"}, "r2": {"path": "/a/b/c/repo2"}},
            ["/a/b"],
            {
                "b": {"repos": ["r1", "r2"], "path": "/a/b"},
                "b-c": {"repos": ["r2"], "path": "/a/b/c"},
            },
        ),
        (
            {"r1": {"path": "/a/b/c/repo1"}, "r2": {"path": "/a/b/c/repo2"}},
            ["/a/b"],
            {
                "b-c": {"repos": ["r1", "r2"], "path": "/a/b/c"},
                "b": {"path": "/a/b", "repos": ["r1", "r2"]},
            },
        ),
    ],
)
def test_auto_group(repos, paths, expected):
    got = utils.auto_group(repos, paths)
    assert got == expected


@pytest.mark.parametrize(
    "test_input, diff_return, expected",
    [
        (
            [{"abc": {"path": "/root/repo/", "type": "", "flags": []}}, False],
            True,
            "abc \x1b[31mrepo       [*+?⇕] \x1b[0m msg xx",
        ),
        (
            [{"abc": {"path": "/root/repo/", "type": "", "flags": []}}, True],
            True,
            "abc repo       [*+?⇕]  msg xx",
        ),
        (
            [{"repo": {"path": "/root/repo2/", "type": "", "flags": []}}, False],
            False,
            "repo \x1b[32mrepo       [?]    \x1b[0m msg xx",
        ),
    ],
)
def test_describe(test_input, diff_return, expected, monkeypatch):
    monkeypatch.setattr(info, "get_head", lambda x: "repo")
    monkeypatch.setattr(info, "run_quiet_diff", lambda *_: diff_return)
    monkeypatch.setattr(info, "get_commit_msg", lambda *_: "msg")
    monkeypatch.setattr(info, "get_commit_time", lambda *_: "xx")
    monkeypatch.setattr(info, "has_untracked", lambda *_: True)
    monkeypatch.setattr(info, "get_common_commit", lambda x: "")

    info.get_color_encoding.cache_clear()  # avoid side effect
    assert expected == next(utils.describe(*test_input))


@pytest.mark.parametrize(
    "path_fname, expected",
    [
        (
            PATH_FNAME,
            {
                "repo1": {"path": "/a/bcd/repo1", "type": "", "flags": []},
                "repo2": {"path": "/e/fgh/repo2", "type": "", "flags": []},
                "xxx": {"path": "/a/b/c/repo3", "type": "", "flags": []},
            },
        ),
        (PATH_FNAME_EMPTY, {}),
        (
            PATH_FNAME_CLASH,
            {
                "repo2": {
                    "path": "/e/fgh/repo2",
                    "type": "",
                    "flags": ["--haha", "--pp"],
                },
                "repo1": {"path": "/root/x/repo1", "type": "", "flags": []},
            },
        ),
    ],
)
@patch("gita.utils.is_git", return_value=True)
@patch("gita.common.get_config_fname")
def test_get_repos(mock_path_fname, _, path_fname, expected):
    mock_path_fname.return_value = path_fname
    utils.get_repos.cache_clear()
    assert utils.get_repos() == expected


@patch("gita.common.get_config_dir")
def test_get_context(mock_config_dir):
    mock_config_dir.return_value = TEST_DIR
    utils.get_context.cache_clear()
    assert utils.get_context() == TEST_DIR / "xx.context"

    mock_config_dir.return_value = "/"
    utils.get_context.cache_clear()
    assert utils.get_context() == None


@pytest.mark.parametrize(
    "group_fname, expected",
    [
        (
            GROUP_FNAME,
            {
                "xx": {"repos": ["a", "b"], "path": ""},
                "yy": {"repos": ["a", "c", "d"], "path": ""},
            },
        ),
    ],
)
@patch("gita.common.get_config_fname")
@patch("gita.utils.get_repos", return_value={"a": "", "b": "", "c": "", "d": ""})
def test_get_groups(_, mock_group_fname, group_fname, expected):
    mock_group_fname.return_value = group_fname
    utils.get_groups.cache_clear()
    assert utils.get_groups() == expected


@patch("os.path.isfile", return_value=True)
@patch("os.path.getsize", return_value=True)
def test_custom_push_cmd(*_):
    with patch(
        "builtins.open",
        mock_open(read_data='{"push":{"cmd":"hand","help":"me","allow_all":true}}'),
    ):
        cmds = utils.get_cmds_from_files()
    assert cmds["push"] == {"cmd": "hand", "help": "me", "allow_all": True}


@pytest.mark.parametrize(
    "path_input, expected",
    [
        (["/home/some/repo"], "/home/some/repo,some/repo,,\r\n"),  # add one new
        (
            ["/home/some/repo1", "/repo2"],
            {"/repo2,repo2,,\r\n", "/home/some/repo1,repo1,,\r\n"},  # add two new
        ),  # add two new
        (
            ["/home/some/repo1", "/nos/repo"],
            "/home/some/repo1,repo1,,\r\n",
        ),  # add one old one new
    ],
)
@patch("os.makedirs")
@patch("gita.utils.is_git", return_value=True)
def test_add_repos(_0, _1, path_input, expected, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/config")
    with patch("builtins.open", mock_open()) as mock_file:
        utils.add_repos({"repo": {"path": "/nos/repo"}}, path_input)
    mock_file.assert_called_with("/config/gita/repos.csv", "a+", newline="")
    handle = mock_file()
    if type(expected) == str:
        handle.write.assert_called_once_with(expected)
    else:
        # the write order is random
        assert handle.write.call_count == 2
        args, kwargs = handle.write.call_args
        assert args[0] in expected
        assert not kwargs


@patch("gita.utils.write_to_groups_file")
@patch("gita.utils.write_to_repo_file")
def test_rename_repo(mock_write, _):
    repos = {"r1": {"path": "/a/b", "type": None}, "r2": {"path": "/c/c", "type": None}}
    utils.rename_repo(repos, "r2", "xxx")
    mock_write.assert_called_once_with(repos, "w")


def test_async_output(capfd):
    tasks = [
        utils.run_async(
            "myrepo",
            ".",
            ["python3", "-c", f"print({i});import time; time.sleep({i});print({i})"],
        )
        for i in range(4)
    ]
    # I don't fully understand why a new loop is needed here. Without a new
    # loop, "pytest" fails but "pytest tests/test_utils.py" works. Maybe pytest
    # itself uses asyncio (or maybe pytest-xdist)?
    asyncio.set_event_loop(asyncio.new_event_loop())
    utils.exec_async_tasks(tasks)

    out, err = capfd.readouterr()
    assert err == ""
    assert (
        out
        == "myrepo: 0\nmyrepo: 0\n\nmyrepo: 1\nmyrepo: 1\n\nmyrepo: 2\nmyrepo: 2\n\nmyrepo: 3\nmyrepo: 3\n\n"
    )


def test_is_git(tmpdir):
    with tmpdir.as_cwd():
        subprocess.run("git init --bare .".split())
        assert utils.is_git(Path.cwd()) is False
        assert utils.is_git(Path.cwd(), include_bare=True) is True
