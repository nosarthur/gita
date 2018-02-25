from unittest.mock import patch

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


def test_rm(monkeypatch):
    monkeypatch.setattr(utils, 'get_repos',
            lambda: {'repo1':'/a/', 'repo2':'/b/'})
    monkeypatch.setattr('os.path.exists', lambda x: False)  # bypass the fwrite
    __main__.main(['rm', 'repo1'])


def test_add():
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
@patch('os.system')
def test_fetch(mock_sys, mock_chdir, *_):
    __main__.main(['fetch'])
    mock_chdir.assert_any_call('/a/bc')
    mock_chdir.assert_any_call('/d/efg')
    mock_sys.assert_any_call('git fetch')
    assert mock_sys.call_count == 2
