import pytest
from unittest.mock import patch
from pathlib import Path
import argparse
import shlex

from gita import __main__
from gita import utils, info
from conftest import (
    PATH_FNAME, PATH_FNAME_EMPTY, PATH_FNAME_CLASH, GROUP_FNAME,
    async_mock, TEST_DIR,
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
        assert info.Color.end in out

        # no color on branch name
        __main__.main(['ll', '-n'])
        out, err = capfd.readouterr()
        assert err == ''
        assert 'gita' in out
        assert info.Color.end not in out

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


class TestContext:

    @patch('gita.utils.get_context', return_value=None)
    def testDisplayNoContext(self, _, capfd):
        __main__.main(['context'])
        out, err = capfd.readouterr()
        assert err == ''
        assert 'Context is not set\n' == out

    @patch('gita.utils.get_context', return_value=Path('gname.context'))
    @patch('gita.utils.get_groups', return_value={'gname': ['a', 'b']})
    def testDisplayContext(self, _, __, capfd):
        __main__.main(['context'])
        out, err = capfd.readouterr()
        assert err == ''
        assert 'gname: a b\n' == out

    @patch('gita.utils.get_context')
    def testReset(self, mock_ctx):
        __main__.main(['context', 'none'])
        mock_ctx.return_value.unlink.assert_called()

    @patch('gita.utils.get_context', return_value=None)
    @patch('gita.common.get_config_dir', return_value=TEST_DIR)
    @patch('gita.utils.get_groups', return_value={'lala': ['b'], 'kaka': []})
    def testSetFirstTime(self, *_):
        ctx = TEST_DIR / 'lala.context'
        assert not ctx.is_file()
        __main__.main(['context', 'lala'])
        assert ctx.is_file()
        ctx.unlink()

    @patch('gita.common.get_config_dir', return_value=TEST_DIR)
    @patch('gita.utils.get_groups', return_value={'lala': ['b'], 'kaka': []})
    @patch('gita.utils.get_context')
    def testSetSecondTime(self, mock_ctx, *_):
        __main__.main(['context', 'kaka'])
        mock_ctx.return_value.rename.assert_called()


class TestGroupCmd:

    @patch('gita.utils.get_config_fname', return_value=GROUP_FNAME)
    def testLs(self, _, capfd):
        args = argparse.Namespace()
        args.to_group = None
        args.group_cmd = 'ls'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        out, err = capfd.readouterr()
        assert err == ''
        assert 'xx yy\n' == out

    @patch('gita.utils.get_config_fname', return_value=GROUP_FNAME)
    def testLl(self, _, capfd):
        args = argparse.Namespace()
        args.to_group = None
        args.group_cmd = None
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        out, err = capfd.readouterr()
        assert err == ''
        assert 'xx: a b\nyy: a c d\n' == out

    @patch('gita.utils.get_config_fname', return_value=GROUP_FNAME)
    @patch('gita.utils.write_to_groups_file')
    def testRename(self, mock_write, _):
        args = argparse.Namespace()
        args.gname = 'xx'
        args.new_name = 'zz'
        args.group_cmd = 'rename'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        expected = {'yy': ['a', 'c', 'd'], 'zz': ['a', 'b']}
        mock_write.assert_called_once_with(expected, 'w')

    @patch('gita.utils.get_config_fname', return_value=GROUP_FNAME)
    def testRenameError(self, *_):
        args = argparse.Namespace()
        args.gname = 'xx'
        args.new_name = 'yy'
        args.group_cmd = 'rename'
        utils.get_groups.cache_clear()
        with pytest.raises(SystemExit, match='yy already exists.'):
            __main__.f_group(args)

    @pytest.mark.parametrize('input, expected', [
        ('xx', {'yy': ['a', 'c', 'd']}),
        ("xx yy", {}),
    ])
    @patch('gita.utils.get_repos', return_value={'a': '', 'b': '', 'c': '', 'd': ''})
    @patch('gita.utils.get_config_fname', return_value=GROUP_FNAME)
    @patch('gita.utils.write_to_groups_file')
    def testRm(self, mock_write, _, __, input, expected):
        utils.get_groups.cache_clear()
        args = ['group', 'rm'] + shlex.split(input)
        __main__.main(args)
        mock_write.assert_called_once_with(expected, 'w')

    @patch('gita.utils.get_repos', return_value={'a': '', 'b': '', 'c': '', 'd': ''})
    @patch('gita.utils.get_config_fname', return_value=GROUP_FNAME)
    @patch('gita.utils.write_to_groups_file')
    def testAdd(self, mock_write, *_):
        args = argparse.Namespace()
        args.to_group =  ['a', 'c']
        args.group_cmd = 'add'
        args.gname = 'zz'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        mock_write.assert_called_once_with({'zz': ['a', 'c']}, 'a+')

    @patch('gita.utils.get_repos', return_value={'a': '', 'b': '', 'c': '', 'd': ''})
    @patch('gita.utils.get_config_fname', return_value=GROUP_FNAME)
    @patch('gita.utils.write_to_groups_file')
    def testAddToExisting(self, mock_write, *_):
        args = argparse.Namespace()
        args.to_group =  ['a', 'c']
        args.group_cmd = 'add'
        args.gname = 'xx'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        mock_write.assert_called_once_with(
                {'xx': ['a', 'b', 'c'], 'yy': ['a', 'c', 'd']}, 'w')


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
    args = argparse.Namespace()
    args.info_cmd = None
    __main__.f_info(args)
    out, err = capfd.readouterr()
    assert 'In use: branch,commit_msg\nUnused: path\n' == out
    assert err == ''
