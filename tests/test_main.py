
from gita import __main__


def test_ls():
    __main__.main(['ls'])
#    __main__.main(['ls', 'a-repo'])


def test_add():
    __main__.main(['add', '/home/some/repo/'])


def test_update_repos():
    pass
