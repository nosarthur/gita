import pytest
import os
from unittest.mock import patch, mock_open

from gita import utils

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PATH_FNAME = os.path.join(TEST_DIR, 'mock_path_file')
PATH_FNAME_EMPTY = os.path.join(TEST_DIR, 'empty_path_file')


@pytest.mark.parametrize('test_input, has_remote, expected', [
    ({
        'abc': '/root/repo/'
    }, True, 'abc               \x1b[31mrepo *+_  \x1b[0m msg'),
    ({
        'repo': '/root/repo2/'
    }, False, 'repo              \x1b[37mrepo *+_  \x1b[0m msg'),
])
def test_describe(test_input, has_remote, expected, monkeypatch):
    monkeypatch.setattr(utils, 'get_head', lambda x: 'repo')
    monkeypatch.setattr(utils, 'has_remote', lambda: has_remote)
    monkeypatch.setattr(utils, 'get_commit_msg', lambda: "msg")
    monkeypatch.setattr(utils, 'has_untracked', lambda: True)
    monkeypatch.setattr('os.chdir', lambda x: None)
    # Returns of os.system determine the repo status
    monkeypatch.setattr('os.system', lambda x: True)
    print('expected: ', repr(expected))
    print('got:      ', repr(next(utils.describe(test_input))))
    assert expected == next(utils.describe(test_input))


def test_get_head():
    with patch('builtins.open',
               mock_open(read_data='ref: refs/heads/snake')) as mock_file:
        head = utils.get_head('/fake')
    assert head == 'snake'
    mock_file.assert_called_once_with('/fake/.git/HEAD')


class TestGetRepos:
    @patch('gita.utils.is_git', return_value=True)
    @patch('os.path.join', return_value=PATH_FNAME)
    def test(self, *_):
        utils.get_repos.cache_clear()
        repos = utils.get_repos()
        assert repos == {'repo1': '/a/bcd/repo1', 'repo2': '/e/fgh/repo2'}

    @patch('os.path.join', return_value=PATH_FNAME_EMPTY)
    def testEmptyPath(self, *_):
        utils.get_repos.cache_clear()
        repos = utils.get_repos()
        assert repos == {}


@pytest.mark.parametrize(
    'path_input, expected',
    [
        (['/home/some/repo/'], '/home/some/repo:/nos/repo'),  # add one new
        (['/home/some/repo1', '/repo2'],
         '/home/some/repo1:/nos/repo:/repo2'),  # add two new
        (['/home/some/repo1', '/nos/repo'],
         '/home/some/repo1:/nos/repo'),  # add one old one new
    ])
@patch('os.path.expanduser', return_value='/root')
@patch('os.makedirs')
@patch('gita.utils.get_repos', return_value={'repo': '/nos/repo'})
@patch('gita.utils.is_git', return_value=True)
def test_add_repos(_0, _1, _2, _3, path_input, expected):
    with patch('builtins.open', mock_open()) as mock_file:
        utils.add_repos(path_input)
    mock_file.assert_called_with('/root/.gita/repo_path', 'w')
    handle = mock_file()
    handle.write.assert_called_once_with(expected)
