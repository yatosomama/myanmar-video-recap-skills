"""Media diagnostics decode consistently in Windows and Myanmar/Chinese paths."""
import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(params=["video-cut", "video-assemble", "video-voiceover", "video-understanding"])
def media_lib(request, monkeypatch):
    path = ROOT / "skills" / request.param / "scripts/lib.py"
    spec = importlib.util.spec_from_file_location("encoding_" + request.param.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "log", lambda _message: None)
    return module


def test_real_child_utf8_and_invalid_diagnostic_bytes(media_lib):
    text = "中文路径 မြန်မာ"
    encoded = text.encode("utf-8").hex()
    code = f"import os; data=bytes.fromhex('{encoded}'); os.write(1,data); os.write(2,data+b'\\xff')"
    result = media_lib.run_cmd([sys.executable, "-c", code])
    assert result.returncode == 0
    assert result.stdout == text
    assert result.stderr == text + "\ufffd"


def test_command_encoding_can_be_explicitly_overridden(media_lib):
    code = "import os; os.write(1,bytes([233]))"
    result = media_lib.run_cmd([sys.executable, "-c", code], encoding="latin-1", errors="strict")
    assert result.returncode == 0
    assert result.stdout == "é"


def test_nonzero_exit_preserves_error_and_returncode(media_lib):
    result = media_lib.run_cmd([sys.executable, "-c", "import sys; sys.stderr.write('failure'); sys.exit(7)"])
    assert result.returncode == 7
    assert result.stderr == "failure"
