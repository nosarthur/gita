
import pytest

from gita import ls


@pytest.mark.parametrize('test_input, expected', [
    ({'abc': '/root/repo/'}, 'abc               \x1b[31mrepo *+\x1b[0m\n'),
    ])
def test_describe(test_input, expected, monkeypatch):
    monkeypatch.setattr(ls, 'get_head', lambda x: 'repo')
    monkeypatch.setattr('os.chdir', lambda x: None)
    # patching os.system causes the repo to be outdate, dirty, and staged
    monkeypatch.setattr('os.system', lambda x: True)
    print(ls.describe(test_input))
    assert expected == ls.describe(test_input)
