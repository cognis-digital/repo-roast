"""Tests for hardened error-handling and edge cases."""
import json
from io import StringIO
from unittest.mock import patch

import pytest

from repo_roast.cli import main
from repo_roast.core import _canned, heuristic_score, roast, signals


# ---------------------------------------------------------------------------
# core.signals — path validation
# ---------------------------------------------------------------------------

class TestSignals:
    def test_missing_path_raises(self, tmp_path):
        missing = str(tmp_path / "does_not_exist")
        with pytest.raises(FileNotFoundError, match="does not exist"):
            signals(missing)

    def test_file_not_dir_raises(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        with pytest.raises(NotADirectoryError, match="not a directory"):
            signals(str(f))

    def test_empty_repo_returns_all_false(self, tmp_path):
        s = signals(str(tmp_path))
        assert s["has_readme"] is False
        assert s["readme_len"] == 0
        assert s["has_tests"] is False
        assert s["has_ci"] is False
        assert s["has_license"] is False
        assert s["has_docker"] is False


# ---------------------------------------------------------------------------
# core.heuristic_score — never exceeds 100
# ---------------------------------------------------------------------------

class TestHeuristicScore:
    def test_max_score_capped_at_100(self):
        s = {
            "has_readme": True,
            "readme_len": 1000,
            "has_tests": True,
            "has_ci": True,
            "has_license": True,
            "has_docker": True,
        }
        assert heuristic_score(s) <= 100

    def test_empty_signals_returns_zero(self):
        assert heuristic_score({}) == 0

    def test_partial_signals_handled(self):
        # Only some keys present — should not raise
        score = heuristic_score({"has_readme": True, "readme_len": 500})
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# core._canned — edge cases
# ---------------------------------------------------------------------------

class TestCanned:
    def test_empty_signals_dict_no_crash(self):
        msg = _canned({})
        assert isinstance(msg, str) and len(msg) > 0

    def test_full_signals_returns_clean_message(self):
        s = {
            "has_readme": True,
            "readme_len": 1000,
            "has_tests": True,
            "has_ci": True,
            "has_license": True,
            "has_docker": True,
        }
        msg = _canned(s)
        assert "clean" in msg.lower()


# ---------------------------------------------------------------------------
# core.roast — LLM response edge cases
# ---------------------------------------------------------------------------

class TestRoastLLMEdgeCases:
    def _make_llm_response(self, choices):
        return json.dumps({"choices": choices}).encode()

    def test_empty_choices_falls_back_to_canned(self, tmp_path):
        (tmp_path / "README.md").write_text("hi")
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = mock_urlopen.return_value.__enter__.return_value
            mock_response.read.return_value = json.dumps({"choices": []}).encode()
            result = roast(str(tmp_path), use_llm=True)
        assert result["roast"]  # got a canned message, not empty

    def test_malformed_json_from_llm_falls_back(self, tmp_path):
        (tmp_path / "README.md").write_text("hi")
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = mock_urlopen.return_value.__enter__.return_value
            mock_response.read.return_value = b"not-json!!!"
            result = roast(str(tmp_path), use_llm=True)
        assert result["roast"]  # canned fallback

    def test_network_error_falls_back(self, tmp_path):
        import urllib.error

        (tmp_path / "README.md").write_text("hi")
        with patch(
            "urllib.request.urlopen", side_effect=urllib.error.URLError("refused")
        ):
            result = roast(str(tmp_path), use_llm=True)
        assert result["roast"]


# ---------------------------------------------------------------------------
# cli.main — exit codes
# ---------------------------------------------------------------------------

class TestCLIExitCodes:
    def test_missing_repo_exits_2(self, tmp_path):
        missing = str(tmp_path / "ghost")
        rc = main([missing, "--no-llm"])
        assert rc == 2

    def test_file_instead_of_dir_exits_2(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("hello")
        rc = main([str(f), "--no-llm"])
        assert rc == 2

    def test_valid_repo_exits_0(self, tmp_path):
        rc = main([str(tmp_path), "--no-llm"])
        assert rc == 0

    def test_json_format_exits_0_and_is_valid_json(self, tmp_path, capsys):
        rc = main([str(tmp_path), "--no-llm", "--format", "json"])
        assert rc == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "score" in data and "roast" in data

    def test_error_goes_to_stderr_not_stdout(self, tmp_path, capsys):
        missing = str(tmp_path / "ghost")
        main([missing, "--no-llm"])
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "error" in captured.err.lower()


# ---------------------------------------------------------------------------
# integrations/webhook — header and stdin validation
# ---------------------------------------------------------------------------

class TestWebhook:
    def _run_main(self, args, stdin_text):
        """Import and run webhook main with patched stdin."""
        import integrations.webhook as wh

        with patch("sys.stdin", StringIO(stdin_text)):
            return wh.main(args if False else None), wh  # need to call via argv

    def test_empty_stdin_exits_2(self, capsys, monkeypatch):
        import integrations.webhook as wh

        monkeypatch.setattr("sys.stdin", StringIO(""))
        monkeypatch.setattr("sys.argv", ["webhook.py", "--url", "http://example.com"])
        rc = wh.main()
        assert rc == 2
        captured = capsys.readouterr()
        assert "empty" in captured.err.lower()

    def test_non_json_stdin_exits_2(self, capsys, monkeypatch):
        import integrations.webhook as wh

        monkeypatch.setattr("sys.stdin", StringIO("not json at all"))
        monkeypatch.setattr("sys.argv", ["webhook.py", "--url", "http://example.com"])
        rc = wh.main()
        assert rc == 2
        assert "json" in capsys.readouterr().err.lower()

    def test_bad_header_format_exits_2(self, capsys, monkeypatch):
        import integrations.webhook as wh

        monkeypatch.setattr("sys.stdin", StringIO('{"ok": true}'))
        monkeypatch.setattr(
            "sys.argv",
            ["webhook.py", "--url", "http://example.com", "--header", "BadHeader"],
        )
        rc = wh.main()
        assert rc == 2
        assert "colon" in capsys.readouterr().err.lower()
