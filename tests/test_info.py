import subprocess
from unittest.mock import patch, MagicMock

from gita import info


@patch("subprocess.run")
def test_run_quiet_diff(mock_run):
    mock_return = MagicMock()
    mock_run.return_value = mock_return
    got = info.run_quiet_diff(["--flags"], ["my", "args"], "/a/b/c")
    mock_run.assert_called_once_with(
        ["git", "--flags", "diff", "--quiet", "my", "args"],
        stderr=subprocess.DEVNULL,
        cwd="/a/b/c",
    )
    assert got == mock_return.returncode
