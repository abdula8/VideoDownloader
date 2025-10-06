import os
import sys
import sqlite3
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QDialog
import pytest

# ensure repo root is on sys.path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import main_V3
from main_V3 import YouTubeDownloader, HISTORY_DB


def _close_dialog_by_title(title):
    for w in QApplication.topLevelWidgets():
        if isinstance(w, QDialog) and w.windowTitle() == title:
            try:
                w.accept()
            except Exception:
                w.close()
            return True
    return False


def _trigger_tools_action(window, action_text):
    # find Tools top-level menu
    for a in window.menuBar().actions():
        if a.text() == window._tr('tools'):
            menu = a.menu()
            if not menu:
                return False
            for sa in menu.actions():
                if sa.text() == action_text:
                    sa.trigger()
                    return True
    return False


def test_open_preferences_dialog(qtbot, qapp):
    win = YouTubeDownloader()
    qtbot.addWidget(win)
    win.show()

    title = win._tr('preferences_title')

    # schedule a timer to close the dialog shortly after it opens
    QTimer.singleShot(200, lambda: _close_dialog_by_title(title))

    # trigger the Tools->Preferences action
    triggered = _trigger_tools_action(win, win._tr('preferences'))
    assert triggered, 'Preferences action not found in Tools menu'


def test_open_history_dialog(qtbot, qapp, tmp_path, monkeypatch):
    # prepare a temporary history DB with a row
    dbp = str(tmp_path / 'test_hist.db')
    conn = sqlite3.connect(dbp)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE downloads (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, title TEXT, format TEXT, quality TEXT, status TEXT, download_date TEXT, file_size INTEGER, duration INTEGER, platform TEXT, file_path TEXT)
    ''')
    cur.execute('INSERT INTO downloads (url, title, status, download_date) VALUES (?, ?, ?, ?)',
                ('http://example.com', 'Sample', 'Completed', '2025-10-06 00:00:00'))
    conn.commit()
    conn.close()

    # point the app to the temp DB
    monkeypatch.setattr(main_V3, 'HISTORY_DB', dbp)

    win = YouTubeDownloader()
    qtbot.addWidget(win)
    win.show()

    title = 'Download History'

    QTimer.singleShot(200, lambda: _close_dialog_by_title(title))

    triggered = _trigger_tools_action(win, win._tr('download_history'))
    assert triggered, 'Download History action not found in Tools menu'
