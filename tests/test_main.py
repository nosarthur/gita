from unittest.mock import patch, mock_open
import argparse

from gita import __main__
from gita import utils


def test_ls(monkeypatch, capfd):
    monkeypatch.setattr(utils, 'get_repos',
            lambda: {'repo1':'/a/', 'repo2':'/b/'})
    monkeypatch.setattr(utils, 'describe', lambda x: x)
    __main__.main(['ls'])
    out, err = capfd.readouterr()
    assert out == "{'repo1': '/a/', 'repo2': '/b/'}\n"
    __main__.main(['ls', 'repo1'])
    out, err = capfd.readouterr()
    assert out == '/a/\n'


@patch('os.path.exists', return_value=True)
@patch('gita.utils.get_path_fname', return_value='some path')
@patch('gita.utils.get_repos', return_value={'repo1':'/a/', 'repo2':'/b/'})
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
    'gita.utils.get_repos',
    return_value={
        'repo1': '/a/bc',
        'repo2': '/d/efg'
    })
@patch('os.chdir')
@patch('subprocess.run')
def test_fetch(mock_run, mock_chdir, *_):
    __main__.main(['fetch'])
    mock_chdir.assert_any_call('/a/bc')
    mock_chdir.assert_any_call('/d/efg')
    assert mock_run.call_count == 2
    mock_run.assert_any_call('git fetch', shell=True)


def test_merge():
    pass
