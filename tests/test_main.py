import os
import pytest
from unittest.mock import patch
from pathlib import Path
import argparse
import asyncio
import shlex

from gita import __main__
from gita import utils, info, common
from conftest import (
    PATH_FNAME, PATH_FNAME_EMPTY, PATH_FNAME_CLASH, GROUP_FNAME, PATH_FNAME_MAIN,
    async_mock, TEST_DIR,
)


@patch('gita.utils.get_repos', return_value={'aa'})
def test_group_name(_):
    got = __main__._group_name('xx')
    assert got == 'xx'
    with pytest.raises(SystemExit):
        __main__._group_name('aa')


class TestAdd:

    @pytest.mark.parametrize('input, expected', [
        (['add', '.'], ''),
        (['add', '-m', '.'], 'm'),
        ])
    @patch('gita.common.get_config_fname')
    def test_add(self, mock_path_fname, tmp_path, input, expected):
        def side_effect(input, _=None):
            return tmp_path / f'{input}.txt'
        mock_path_fname.side_effect = side_effect
        utils.get_repos.cache_clear()
        __main__.main(input)
        utils.get_repos.cache_clear()
        got = utils.get_repos()
        assert len(got) == 1
        assert got['gita']['type'] == expected

    @patch('gita.utils.is_git', return_value=True)
    def test_add_main(self, _, tmp_path, monkeypatch, tmpdir):
        def side_effect(root=None):
            if root is None:
                return os.path.join(tmp_path, "gita")
            else:
                return os.path.join(root, ".gita")

        def desc(repos, **_):
            print(len(repos), repos.keys())
            assert len(repos) > 0
            for r, prop in repos.items():
                if prop['type'] == 'm':
                    assert 'test_add_main' in r
                    break
            else:
                assert 0, 'no main repo found'
            return ''

        monkeypatch.setattr(common, 'get_config_dir', side_effect)
        monkeypatch.setattr(utils, 'describe', desc)

        utils.get_repos.cache_clear()

        with tmpdir.as_cwd():
            __main__.main(['add', '-m', '.'])
            utils.get_repos.cache_clear()
            __main__.main(['ll'])


@pytest.mark.parametrize('path_fname, expected', [
    (PATH_FNAME, ''),
    (PATH_FNAME_CLASH, "repo2: ['--haha', '--pp']\n"),
    ])
@patch('gita.utils.is_git', return_value=True)
@patch('gita.utils.get_groups', return_value={})
@patch('gita.common.get_config_fname')
def test_flags(mock_path_fname, _, __, path_fname, expected, capfd):
    mock_path_fname.return_value = path_fname
    utils.get_repos.cache_clear()
    __main__.main(['flags'])
    out, err = capfd.readouterr()
    assert err == ''
    assert out == expected


class TestLsLl:
    @patch('gita.common.get_config_fname')
    def test_ll(self, mock_path_fname, capfd, tmp_path):
        """
        functional test
        """
        # avoid modifying the local configuration
        def side_effect(input, _=None):
            return tmp_path / f'{input}.txt'
        mock_path_fname.side_effect = side_effect
        utils.get_repos.cache_clear()
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
        __main__.main(['ll', '-C'])
        out, err = capfd.readouterr()
        assert err == ''
        assert 'gita' in out
        assert info.Color.end not in out

        __main__.main(['ls', 'gita'])
        out, err = capfd.readouterr()
        assert err == ''
        assert out.strip() == utils.get_repos()['gita']['path']

    def test_ls(self, monkeypatch, capfd):
        monkeypatch.setattr(utils, 'get_repos',
                lambda: {'repo1': {'path': '/a/'}, 'repo2': {'path': '/b/'}})
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
         "repo1 cmaster dsu\x1b[0m msg \nrepo2 cmaster dsu\x1b[0m msg \nxxx   cmaster dsu\x1b[0m msg \n"),
        (PATH_FNAME_EMPTY, ""),
        (PATH_FNAME_MAIN,
         '\x1b[4mmain1\x1b[0m cmaster dsu\x1b[0m msg \nxx    cmaster dsu\x1b[0m msg \n'),
        (PATH_FNAME_CLASH,
         "repo1 cmaster dsu\x1b[0m msg \nrepo2 cmaster dsu\x1b[0m msg \n"
         ),
    ])
    @patch('gita.utils.is_git', return_value=True)
    @patch('gita.info.get_head', return_value="master")
    @patch('gita.info._get_repo_status', return_value=("d", "s", "u", "c"))
    @patch('gita.info.get_commit_msg', return_value="msg")
    @patch('gita.info.get_commit_time', return_value="")
    @patch('gita.common.get_config_fname')
    def test_with_path_files(self, mock_path_fname, _0, _1, _2, _3, _4, path_fname,
                          expected, capfd):
        def side_effect(input, _=None):
            if input == 'repos.csv':
                return path_fname
            return f'/{input}'
        mock_path_fname.side_effect = side_effect
        utils.get_repos.cache_clear()
        __main__.main(['ll'])
        out, err = capfd.readouterr()
        print(out)
        assert err == ''
        assert out == expected


@pytest.mark.parametrize('input, expected', [
    ({'repo1': {'path': '/a/'}, 'repo2': {'path': '/b/'}}, ''),
    ])
@patch('subprocess.run')
@patch('gita.utils.get_repos')
def test_freeze(mock_repos, mock_run, input, expected, capfd):
    mock_repos.return_value = input
    __main__.main(['freeze'])
    assert mock_run.call_count == 2
    out, err = capfd.readouterr()
    assert err == ''
    assert out == expected


@patch('gita.utils.parse_clone_config', return_value=[
    ['git@github.com:user/repo.git', 'repo', '/a/repo']])
@patch('gita.utils.run_async', new=async_mock())
@patch('subprocess.run')
def test_clone(*_):
    asyncio.set_event_loop(asyncio.new_event_loop())
    args = argparse.Namespace()
    args.fname = ['freeze_filename']
    args.preserve_path = None
    __main__.f_clone(args)
    mock_run = utils.run_async.mock
    assert mock_run.call_count == 1
    cmds = ['git', 'clone', 'git@github.com:user/repo.git']
    mock_run.assert_called_once_with('repo', Path.cwd(), cmds)


@patch('gita.utils.parse_clone_config', return_value=[
    ['git@github.com:user/repo.git', 'repo', '/a/repo']])
@patch('gita.utils.run_async', new=async_mock())
@patch('subprocess.run')
def test_clone_with_preserve_path(*_):
    asyncio.set_event_loop(asyncio.new_event_loop())
    args = argparse.Namespace()
    args.fname = ['freeze_filename']
    args.preserve_path = True
    __main__.f_clone(args)
    mock_run = utils.run_async.mock
    assert mock_run.call_count == 1
    cmds = ['git', 'clone', 'git@github.com:user/repo.git', '/a/repo']
    mock_run.assert_called_once_with('repo', Path.cwd(), cmds)


@patch('os.path.isfile', return_value=True)
@patch('gita.common.get_config_fname', return_value='some path')
@patch('gita.utils.get_repos', return_value={'repo1': {'path': '/a/', 'type': ''},
                                             'repo2': {'path': '/b/', 'type': ''}})
@patch('gita.utils.write_to_repo_file')
def test_rm(mock_write, *_):
    args = argparse.Namespace()
    args.repo = ['repo1']
    __main__.f_rm(args)
    mock_write.assert_called_once_with(
            {'repo2': {'path': '/b/', 'type': ''}}, 'w')


def test_not_add():
    # this won't write to disk because the repo is not valid
    __main__.main(['add', '/home/some/repo/'])


@patch('gita.utils.get_repos', return_value={'repo2': {'path': '/d/efg',
                    'flags': []}})
@patch('subprocess.run')
def test_fetch(mock_run, *_):
    asyncio.set_event_loop(asyncio.new_event_loop())
    __main__.main(['fetch'])
    mock_run.assert_called_once_with(['git', 'fetch'], cwd='/d/efg', shell=False)


@patch(
    'gita.utils.get_repos', return_value={
        'repo1': {'path': '/a/bc', 'flags': []},
        'repo2': {'path': '/d/efg', 'flags': []}
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
@patch('gita.utils.get_repos', return_value={'repo7': {'path': 'path7', 'flags': []}})
@patch('subprocess.run')
def test_superman(mock_run, _, input):
    mock_run.reset_mock()
    args = ['super', 'repo7'] + shlex.split(input)
    __main__.main(args)
    expected_cmds = ['git'] + shlex.split(input)
    mock_run.assert_called_once_with(expected_cmds, cwd='path7', shell=False)


@pytest.mark.parametrize('input', [
    'diff --name-only --staged',
    "commit -am 'lala kaka'",
])
@patch('gita.utils.get_repos', return_value={'repo7': {'path': 'path7', 'flags': []}})
@patch('subprocess.run')
def test_shell(mock_run, _, input):
    mock_run.reset_mock()
    args = ['shell', 'repo7', input]
    __main__.main(args)
    expected_cmds = input
    mock_run.assert_called_once_with(expected_cmds, cwd='path7', shell=True, stderr=-2, stdout=-1)


class TestContext:

    @patch('gita.utils.get_context', return_value=None)
    def testDisplayNoContext(self, _, capfd):
        __main__.main(['context'])
        out, err = capfd.readouterr()
        assert err == ''
        assert 'Context is not set\n' == out

    @patch('gita.utils.get_context', return_value=Path('gname.context'))
    @patch('gita.utils.get_groups', return_value={'gname': ['a', 'b']})
    def test_display_context(self, _, __, capfd):
        __main__.main(['context'])
        out, err = capfd.readouterr()
        assert err == ''
        assert 'gname: a b\n' == out

    @patch('gita.utils.get_context')
    def test_reset(self, mock_ctx):
        __main__.main(['context', 'none'])
        mock_ctx.return_value.unlink.assert_called()

    @patch('gita.utils.get_context', return_value=None)
    @patch('gita.common.get_config_dir', return_value=TEST_DIR)
    @patch('gita.utils.get_groups', return_value={'lala': ['b'], 'kaka': []})
    def test_set_first_time(self, *_):
        ctx = TEST_DIR / 'lala.context'
        assert not ctx.is_file()
        __main__.main(['context', 'lala'])
        assert ctx.is_file()
        ctx.unlink()

    @patch('gita.common.get_config_dir', return_value=TEST_DIR)
    @patch('gita.utils.get_groups', return_value={'lala': ['b'], 'kaka': []})
    @patch('gita.utils.get_context')
    def test_set_second_time(self, mock_ctx, *_):
        __main__.main(['context', 'kaka'])
        mock_ctx.return_value.rename.assert_called()


class TestGroupCmd:

    @patch('gita.common.get_config_fname', return_value=GROUP_FNAME)
    def test_ls(self, _, capfd):
        args = argparse.Namespace()
        args.to_group = None
        args.group_cmd = 'ls'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        out, err = capfd.readouterr()
        assert err == ''
        assert 'xx yy\n' == out

    @patch('gita.common.get_config_fname', return_value=GROUP_FNAME)
    def test_ll(self, _, capfd):
        args = argparse.Namespace()
        args.to_group = None
        args.group_cmd = None
        args.to_show = None
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        out, err = capfd.readouterr()
        assert err == ''
        assert 'xx: a b\nyy: a c d\n' == out

    @patch('gita.common.get_config_fname', return_value=GROUP_FNAME)
    def test_ll_with_group(self, _, capfd):
        args = argparse.Namespace()
        args.to_group = None
        args.group_cmd = None
        args.to_show = 'yy'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        out, err = capfd.readouterr()
        assert err == ''
        assert 'a c d\n' == out

    @patch('gita.common.get_config_fname', return_value=GROUP_FNAME)
    @patch('gita.utils.write_to_groups_file')
    def test_rename(self, mock_write, _):
        args = argparse.Namespace()
        args.gname = 'xx'
        args.new_name = 'zz'
        args.group_cmd = 'rename'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        expected = {'yy': ['a', 'c', 'd'], 'zz': ['a', 'b']}
        mock_write.assert_called_once_with(expected, 'w')

    @patch('gita.common.get_config_fname', return_value=GROUP_FNAME)
    def test_rename_error(self, *_):
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
    @patch('gita.common.get_config_fname', return_value=GROUP_FNAME)
    @patch('gita.utils.write_to_groups_file')
    def test_rm(self, mock_write, _, __, input, expected):
        utils.get_groups.cache_clear()
        args = ['group', 'rm'] + shlex.split(input)
        __main__.main(args)
        mock_write.assert_called_once_with(expected, 'w')

    @patch('gita.utils.get_repos', return_value={'a': '', 'b': '', 'c': '', 'd': ''})
    @patch('gita.common.get_config_fname', return_value=GROUP_FNAME)
    @patch('gita.utils.write_to_groups_file')
    def test_add(self, mock_write, *_):
        args = argparse.Namespace()
        args.to_group =  ['a', 'c']
        args.group_cmd = 'add'
        args.gname = 'zz'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        mock_write.assert_called_once_with({'zz': ['a', 'c']}, 'a+')

    @patch('gita.utils.get_repos', return_value={'a': '', 'b': '', 'c': '', 'd': ''})
    @patch('gita.common.get_config_fname', return_value=GROUP_FNAME)
    @patch('gita.utils.write_to_groups_file')
    def test_add_to_existing(self, mock_write, *_):
        args = argparse.Namespace()
        args.to_group =  ['a', 'c']
        args.group_cmd = 'add'
        args.gname = 'xx'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        mock_write.assert_called_once_with(
                {'xx': ['a', 'b', 'c'], 'yy': ['a', 'c', 'd']}, 'w')

    @patch('gita.utils.get_repos', return_value={'a': '', 'b': '', 'c': '', 'd': ''})
    @patch('gita.common.get_config_fname', return_value=GROUP_FNAME)
    @patch('gita.utils.write_to_groups_file')
    def test_rm_repo(self, mock_write, *_):
        args = argparse.Namespace()
        args.from_group = ['a', 'c']
        args.group_cmd = 'rmrepo'
        args.gname = 'xx'
        utils.get_groups.cache_clear()
        __main__.f_group(args)
        mock_write.assert_called_once_with(
                {'xx': ['b'], 'yy': ['a', 'c', 'd']}, 'w')

    @patch('gita.common.get_config_fname')
    def test_integration(self, mock_path_fname, tmp_path, capfd):
        def side_effect(input, _=None):
            return tmp_path / f'{input}.csv'
        mock_path_fname.side_effect = side_effect

        __main__.main('add .'.split())
        utils.get_repos.cache_clear()
        __main__.main('group add gita -n test'.split())
        utils.get_groups.cache_clear()
        __main__.main('ll test'.split())
        out, err = capfd.readouterr()
        assert err == ''
        assert 'gita' in out


@patch('gita.utils.is_git', return_value=True)
@patch('gita.common.get_config_fname', return_value=PATH_FNAME)
@patch('gita.utils.rename_repo')
def test_rename(mock_rename, _, __):
    utils.get_repos.cache_clear()
    args = ['rename', 'repo1', 'abc']
    __main__.main(args)
    mock_rename.assert_called_once_with(
            {'repo1': {'path': '/a/bcd/repo1', 'type': '', 'flags': []},
                'xxx': {'path': '/a/b/c/repo3', 'type': '', 'flags': []},
                'repo2': {'path': '/e/fgh/repo2', 'type': '', 'flags': []}},
        'repo1', 'abc')


class TestInfo:

    @patch('gita.common.get_config_fname', return_value='')
    def test_ll(self, _, capfd):
        args = argparse.Namespace()
        args.info_cmd = None
        __main__.f_info(args)
        out, err = capfd.readouterr()
        assert 'In use: branch,commit_msg,commit_time\nUnused: path\n' == out
        assert err == ''

    @patch('gita.common.get_config_fname')
    def test_add(self, mock_get_fname, tmpdir):
        args = argparse.Namespace()
        args.info_cmd = 'add'
        args.info_item = 'path'
        with tmpdir.as_cwd():
            csv_config = Path.cwd() / 'info.csv'
            mock_get_fname.return_value = csv_config
            __main__.f_info(args)
            items = info.get_info_items()
        assert items == ['branch', 'commit_msg', 'commit_time', 'path']

    @patch('gita.common.get_config_fname')
    def test_rm(self, mock_get_fname, tmpdir):
        args = argparse.Namespace()
        args.info_cmd = 'rm'
        args.info_item = 'commit_msg'
        with tmpdir.as_cwd():
            csv_config = Path.cwd() / 'info.csv'
            mock_get_fname.return_value = csv_config
            __main__.f_info(args)
            items = info.get_info_items()
        assert items == ['branch', 'commit_time']


@patch('gita.common.get_config_fname')
def test_set_color(mock_get_fname, tmpdir):
        args = argparse.Namespace()
        args.color_cmd = 'set'
        args.color = 'redrum'  # this color doesn't exist
        args.situation = 'in-sync'
        with tmpdir.as_cwd():
            csv_config = Path.cwd() / 'colors.csv'
            mock_get_fname.return_value = csv_config
            __main__.f_color(args)
            info.get_color_encoding.cache_clear()  # avoid side effect
            items = info.get_color_encoding()
        info.get_color_encoding.cache_clear()  # avoid side effect
        assert items == {'no-remote': 'white', 'in-sync': 'redrum',
                'diverged': 'red', 'local-ahead': 'purple',
                'remote-ahead': 'yellow'}
