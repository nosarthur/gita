import subprocess
import locale
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


def test_commit_message_ignores_locale_and_git_output_encoding(tmp_path, monkeypatch):
    message = "Emoji \U0001f642 and \u4e2d\u6587"
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
         "commit", "--allow-empty", "--no-gpg-sign", "-qm", message],
        cwd=tmp_path, check=True,
    )
    subprocess.run(["git", "config", "i18n.logOutputEncoding", "ISO-8859-1"],
                   cwd=tmp_path, check=True)
    monkeypatch.setattr(locale, "getpreferredencoding", lambda *args: "gbk")
    if hasattr(locale, "getencoding"):
        monkeypatch.setattr(locale, "getencoding", lambda: "gbk")
    assert info.get_commit_msg({"path": str(tmp_path), "flags": []}, info.Truncate()) == message
