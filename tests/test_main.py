import pytest
from unittest.mock import patch
import argparse
import shlex

from gita import __main__
from gita import utils
from conftest import (
    PATH_FNAME, PATH_FNAME_EMPTY, PATH_FNAME_CLASH, GROUP_FNAME,
    async_mock
)


class TestLsLl:
    @patch('gita.utils.get_config_fname')
    def testLl(self, mock_path_fname, capfd, tmp_path):
        """ functional test """
        # avoid modifying the local configuration
        mock_path_fname.return_value = tmp_path / 'path_config.txt'
        __main__.main(['add', '.'])
        out, err = capfd.readouterr()
        assert err == ''
        assert 'Found 1 new repo(s).\n' == out

        # in production this is not needed
        utils.get_repos.cache_clear()

        __main__.main(['ls'])
        out, err = capfd.readouterr()
        assert err == ''
        assert 'gita\n' == out

        __main__.main(['ll'])
        out, err = capfd.readouterr()
        assert err == ''
        assert 'gita' in out

        __main__.main(['ls', 'gita'])
        out, err = capfd.readouterr()
        assert err == ''
        assert out.strip() == utils.get_repos()['gita']

    def testLs(self, monkeypatch, capfd):
        monkeypatch.setattr(utils, 'get_repos',
                lambda: {'repo1': '/a/', 'repo2': '/b/'})
        monkeypatch.setattr(utils, 'describe', lambda x: x)
        __main__.main(['ls'])
        out, err = capfd.readouterr()
        assert err == ''
        assert out == "repo1 repo2\n"
        __main__.main(['ls', 'repo1'])
        out, err = capfd.readouterr()
        assert err == ''
        assert out == '/a/\n'

    @pytest.mark.parametrize('path_fname, expected', [
        (PATH_FNAME,
         "repo1 cmaster dsu\x1b[0m msg\nrepo2 cmaster dsu\x1b[0m msg\nxxx   cmaster dsu\x1b[0m msg\n"),
        (PATH_FNAME_EMPTY, ""),
        (PATH_FNAME_CLASH,
         "repo1   cmaster dsu\x1b[0m msg\nrepo2   cmaster dsu\x1b[0m msg\nx/repo1 cmaster dsu\x1b[0m msg\n"
         ),
    ])
    @patch('gita.utils.is_git', return_value=True)
    @patch('gita.info.get_head', return_value="master")
    @patch('gita.info._get_repo_status', return_value=("d", "s", "u", "c"))
    @patch('gita.info.get_commit_msg', return_value="msg")
    @patch('gita.utils.get_config_fname')
    def testWithPathFiles(self, mock_path_fname, _0, _1, _2, _3, path_fname,
                          expected, capfd):
        mock_path_fname.return_value = path_fname
        utils.get_repos.cache_clear()
        __main__.main(['ll'])
        out, err = capfd.readouterr()
        print(out)
        assert err == ''
        assert out == expected


@patch('os.path.isfile', return_value=True)
@patch('gita.utils.get_config_fname', return_value='some path')
@patch('gita.utils.get_repos', return_value={'repo1': '/a/', 'repo2': '/b/'})
@patch('gita.utils.write_to_repo_file')
def test_rm(mock_write, *_):
    args = argparse.Namespace()
    args.repo = ['repo1']
    __main__.f_rm(args)
    mock_write.assert_called_once_with({'repo2': '/b/'}, 'w')


def test_not_add():
    # this won't write to disk because the repo is not valid
    __main__.main(['add', '/home/some/repo/'])


@patch('gita.utils.get_repos', return_value={'repo2': '/d/efg'})
@patch('subprocess.run')
def test_fetch(mock_run, *_):
    __main__.main(['fetch'])
    mock_run.assert_called_once_with(['git', 'fetch'], cwd='/d/efg')


@patch(
    'gita.utils.get_repos', return_value={
        'repo1': '/a/bc',
        'repo2': '/d/efg'
    })
@patch('gita.utils.run_async', new=async_mock())
@patch('subprocess.run')
def test_async_fetch(*_):
    __main__.main(['fetch'])
    mock_run = utils.run_async.mock
    assert mock_run.call_count == 2
    cmds = ['git', 'fetch']
    # print(mock_run.call_args_list)
    mock_run.assert_any_call('repo1', '/a/bc', cmds)
    mock_run.assert_any_call('repo2', '/d/efg', cmds)


@pytest.mark.parametrize('input', [
    'diff --name-only --staged',
    "commit -am 'lala kaka'",
])
@patch('gita.utils.get_repos', return_value={'repo7': 'path7'})
@patch('subprocess.run')
def test_superman(mock_run, _, input):
    mock_run.reset_mock()
    args = ['super', 'repo7'] + shlex.split(input)
    __main__.main(args)
    expected_cmds = ['git'] + shlex.split(input)
    mock_run.assert_called_once_with(expected_cmds, cwd='path7')


@pytest.mark.parametrize('input, expected', [
    ('a', {'xx': ['b'], 'yy': ['c', 'd']}),
    ("c", {'xx': ['a', 'b'], 'yy': ['a', 'd']}),
    ("a b", {'yy': ['c', 'd']}),
])
@patch('gita.utils.get_repos', return_value={'a': '', 'b': '', 'c': '', 'd': ''})
@patch('gita.utils.get_config_fname', return_value=GROUP_FNAME)
@patch('gita.utils.write_to_groups_file')
def test_ungroup(mock_write, _, __, input, expected):
    utils.get_groups.cache_clear()
    args = ['ungroup'] + shlex.split(input)
    __main__.main(args)
    mock_write.assert_called_once_with(expected, 'w')


@patch('gita.utils.get_config_fname', return_value=GROUP_FNAME)
def test_group_display(_, capfd):
    args = argparse.Namespace()
    args.to_group = None
    utils.get_groups.cache_clear()
    __main__.f_group(args)
    out, err = capfd.readouterr()
    assert err == ''
    assert 'xx: a b\nyy: a c d\n' == out


@patch('gita.utils.is_git', return_value=True)
@patch('gita.utils.get_config_fname', return_value=PATH_FNAME)
@patch('gita.utils.rename_repo')
def test_rename(mock_rename, _, __):
    utils.get_repos.cache_clear()
    args = ['rename', 'repo1', 'abc']
    __main__.main(args)
    mock_rename.assert_called_once_with(
        {'repo1': '/a/bcd/repo1', 'repo2': '/e/fgh/repo2',
            'xxx': '/a/b/c/repo3'},
        'repo1', 'abc')


@patch('os.path.isfile', return_value=False)
def test_info(mock_isfile, capfd):
    __main__.f_info(None)
    out, err = capfd.readouterr()
    assert 'In use: branch,commit_msg\nUnused: path\n' == out
    assert err == ''
