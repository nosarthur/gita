import pytest
import asyncio
from unittest.mock import patch, mock_open

from gita import utils, info
from conftest import PATH_FNAME, PATH_FNAME_EMPTY, PATH_FNAME_CLASH


@pytest.mark.parametrize('test_input, diff_return, expected', [
    ({
        'abc': '/root/repo/'
    }, True, 'abc \x1b[31mrepo *+_  \x1b[0m msg'),
    ({
        'repo': '/root/repo2/'
    }, False, 'repo \x1b[32mrepo _    \x1b[0m msg'),
])
def test_describe(test_input, diff_return, expected, monkeypatch):
    monkeypatch.setattr(info, 'get_head', lambda x: 'repo')
    monkeypatch.setattr(info, 'run_quiet_diff', lambda _: diff_return)
    monkeypatch.setattr(info, 'get_commit_msg', lambda _: "msg")
    monkeypatch.setattr(info, 'has_untracked', lambda: True)
    monkeypatch.setattr('os.chdir', lambda x: None)
    print('expected: ', repr(expected))
    print('got:      ', repr(next(utils.describe(test_input))))
    assert expected == next(utils.describe(test_input))


@pytest.mark.parametrize('path_fname, expected', [
    (PATH_FNAME, {
        'repo1': '/a/bcd/repo1',
        'repo2': '/e/fgh/repo2',
        'xxx': '/a/b/c/repo3',
    }),
    (PATH_FNAME_EMPTY, {}),
    (PATH_FNAME_CLASH, {
        'repo1': '/a/bcd/repo1',
        'repo2': '/e/fgh/repo2',
        'x/repo1': '/root/x/repo1'
    }),
])
@patch('gita.utils.is_git', return_value=True)
@patch('gita.utils.get_path_fname')
def test_get_repos(mock_path_fname, _, path_fname, expected):
    mock_path_fname.return_value = path_fname
    utils.get_repos.cache_clear()
    repos = utils.get_repos()
    assert repos == expected


@patch('os.path.isfile', return_value=True)
def test_custom_push_cmd(_):
    with patch('builtins.open',
               mock_open(read_data='push:\n  cmd: hand\n  help: me')):
        cmds = utils.get_cmds_from_files()
    assert cmds['push'] == {'cmd': 'hand', 'help': 'me'}


@pytest.mark.parametrize(
    'path_input, expected',
    [
        (['/home/some/repo/'], '/home/some/repo,repo\n'),  # add one new
        (['/home/some/repo1', '/repo2'],
            {'/repo2,repo2\n/home/some/repo1,repo1\n',  # add two new
            '/home/some/repo1,repo1\n/repo2,repo2\n'}),  # add two new
        (['/home/some/repo1', '/nos/repo'],
         '/home/some/repo1,repo1\n'),  # add one old one new
    ])
@patch('os.makedirs')
@patch('gita.utils.is_git', return_value=True)
def test_add_repos(_0, _1, path_input, expected, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME', '/config')
    with patch('builtins.open', mock_open()) as mock_file:
        utils.add_repos({'repo': '/nos/repo'}, path_input)
    mock_file.assert_called_with('/config/gita/repo_path', 'a+')
    handle = mock_file()
    if type(expected) == str:
        handle.write.assert_called_once_with(expected)
    else:
        handle.write.assert_called_once()
        args, kwargs = handle.write.call_args
        assert args[0] in expected
        assert not kwargs


@patch('gita.utils.write_to_repo_file')
def test_rename_repo(mock_write):
    utils.rename_repo({'r1': '/a/b', 'r2': '/c/c'}, 'r2', 'xxx')
    mock_write.assert_called_once_with({'r1': '/a/b', 'xxx': '/c/c'}, 'w')


def test_async_output(capfd):
    tasks = [
        utils.run_async('.', [
            'python3', '-c',
            f"print({i});import time; time.sleep({i});print({i})"
        ]) for i in range(4)
    ]
    # I don't fully understand why a new loop is needed here. Without a new
    # loop, "pytest" fails but "pytest tests/test_utils.py" works. Maybe pytest
    # itself uses asyncio (or maybe pytest-xdist)?
    asyncio.set_event_loop(asyncio.new_event_loop())
    utils.exec_async_tasks(tasks)

    out, err = capfd.readouterr()
    assert err == ''
    assert out == "0\n0\n\n1\n1\n\n2\n2\n\n3\n3\n\n"
