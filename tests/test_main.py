
from gita import __main__
from gita import ls


def test_ls(monkeypatch, capfd):
    monkeypatch.setattr(__main__, 'update_repos',
            lambda: {'repo1':'/a/', 'repo2':'/b/'})
    monkeypatch.setattr(ls, 'describe', lambda x: x)
    __main__.main(['ls'])
    out, err = capfd.readouterr()
    assert out == "{'repo1': '/a/', 'repo2': '/b/'}\n"
    __main__.main(['ls', 'repo1'])
    out, err = capfd.readouterr()
    assert out == '/a/\n'


def test_rm(monkeypatch):
    monkeypatch.setattr(__main__, 'update_repos',
            lambda: {'repo1':'/a/', 'repo2':'/b/'})
    monkeypatch.setattr('os.path.exists', lambda x: False)  # bypass the fwrite
    __main__.main(['rm', 'repo1'])


def test_add():
    # this won't write to disk because the repo is not valid
    __main__.main(['add', '/home/some/repo/'])


def test_update_repos():
    pass
