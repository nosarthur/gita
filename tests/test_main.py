import pytest
from unittest.mock import patch, mock_open
import argparse
import shlex

from gita import __main__
from gita import utils
from conftest import PATH_FNAME, PATH_FNAME_EMPTY, PATH_FNAME_CLASH


class TestLs:
    def test(self, monkeypatch, capfd):
        monkeypatch.setattr(utils, 'get_repos',
                lambda: {'repo1':'/a/', 'repo2':'/b/'})
        monkeypatch.setattr(utils, 'describe', lambda x: x)
        __main__.main(['ls'])
        out, err = capfd.readouterr()
        assert err == ''
        assert out == "repo1repo2"
        __main__.main(['ls', 'repo1'])
        out, err = capfd.readouterr()
        assert err == ''
        assert out == '/a/\n'

    @pytest.mark.parametrize('path_fname, expected', [
        (PATH_FNAME,
         "repo1 cmaster dsu\x1b[0m msgrepo2 cmaster dsu\x1b[0m msg"),
        (PATH_FNAME_EMPTY, ""),
        (PATH_FNAME_CLASH,
         "repo1   cmaster dsu\x1b[0m msgrepo2   cmaster dsu\x1b[0m msgx/repo1 cmaster dsu\x1b[0m msg"
         ),
    ])
    @patch('gita.utils.is_git', return_value=True)
    @patch('gita.utils.get_head', return_value="master")
    @patch('gita.utils._get_repo_status', return_value=("d", "s", "u", "c"))
    @patch('gita.utils.get_commit_msg', return_value="msg")
    @patch('gita.utils.get_path_fname')
    def testWithPathFiles(self, mock_path_fname, _0, _1, _2, _3, path_fname,
                          expected, capfd):
        mock_path_fname.return_value = path_fname
        utils.get_repos.cache_clear()
        __main__.main(['ls'])
        out, err = capfd.readouterr()
        assert err == ''
        assert out == expected


@patch('os.path.isfile', return_value=True)
@patch('gita.utils.get_path_fname', return_value='some path')
@patch('gita.utils.get_repos', return_value={'repo1': '/a/', 'repo2': '/b/'})
def test_rm(*_):
    args = argparse.Namespace()
    args.repo = 'repo1'
    with patch('builtins.open', mock_open()) as mock_file:
        __main__.f_rm(args)
    mock_file.assert_called_with('some path', 'w')
    handle = mock_file()
    handle.write.assert_called_once_with('/b/')


def test_not_add():
    # this won't write to disk because the repo is not valid
    __main__.main(['add', '/home/some/repo/'])


@patch('gita.utils.has_remote', return_value=True)
@patch(
    'gita.utils.get_repos', return_value={
        'repo1': '/a/bc',
        'repo2': '/d/efg'
    })
@patch('os.chdir')
@patch('os.system')
def test_fetch(mock_sys, mock_chdir, *_):
    __main__.main(['fetch'])
    mock_chdir.assert_any_call('/a/bc')
    mock_chdir.assert_any_call('/d/efg')
    mock_sys.assert_any_call('git fetch')
    assert mock_sys.call_count == 2


@pytest.mark.parametrize('input', [
    'diff --name-only --staged',
    "commit -am 'lala kaka'",
])
@patch('gita.utils.get_repos', return_value={'repo7': 'path7'})
@patch('gita.utils.exec_git')
def test_superman(mock_exec, _, input):
    mock_exec.reset_mock()
    args = ['super', 'repo7'] + shlex.split(input)
    __main__.main(args)
    mock_exec.assert_called_once_with('path7', input)
