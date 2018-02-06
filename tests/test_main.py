
from gita import __main__


def test_ls():
    __main__.main(['ls'])
#    __main__.main(['ls', 'a-repo'])


def test_rm(monkeypatch):
    monkeypatch.setattr(__main__, 'update_repos',
            lambda: {'repo1':'/a/', 'repo2':'/b/'})
    monkeypatch.setattr('os.path.exists', lambda x: False)  # bypass the fwrite
    __main__.main(['rm', 'repo1'])


def test_add():
    __main__.main(['add', '/home/some/repo/'])


def test_update_repos():
    pass
