import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")


def test_selftest(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    from qlvtvl.app import selftest
    assert selftest() == 0
