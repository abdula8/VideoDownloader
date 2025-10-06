import os
import sys
import pytest
from PyQt5 import QtWidgets


@pytest.fixture(scope='session')
def qapp():
    """Ensure a QApplication exists for tests that need it."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    yield app


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    p = tmp_path / 'test_history.db'
    path = str(p)
    # ensure file exists
    open(path, 'a').close()
    return path
