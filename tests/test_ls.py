
import pytest

from gita import utils


@pytest.mark.parametrize('test_input, expected', [
    ({'abc': '/root/repo/'}, 'abc               \x1b[1;31mrepo *+\x1b[0m\n'),
    ])
def test_describe(test_input, expected, monkeypatch):
    monkeypatch.setattr(utils, 'get_head', lambda x: 'repo')
    monkeypatch.setattr('os.chdir', lambda x: None)
    # patching os.system causes the repo to be outdate, dirty, and staged
    monkeypatch.setattr('os.system', lambda x: True)
    print(utils.describe(test_input))
    assert expected == utils.describe(test_input)
