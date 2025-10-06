import os
import sys
import sqlite3
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

import pytest
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer

# ensure repo root is on sys.path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import main_V3
from main_V3 import YouTubeDownloader, HISTORY_DB
from converter_tool import BasicConverterDialog, AdvancedConverterDialog
from history_dialog import HistoryDialog


def test_basic_converter_ffmpeg_missing(qtbot, tmp_path, monkeypatch):
    dlg = BasicConverterDialog()
    qtbot.addWidget(dlg)

    # add a fake input file (no need to exist on disk for this check)
    dlg.file_list.addItem(str(tmp_path / 'in.mkv'))
    dlg.output_dir_edit.setText(str(tmp_path))

    # simulate ffmpeg missing
    def _bad_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, 'run', _bad_run)

    called = {'critical': False}

    def fake_critical(self, title, text):
        called['critical'] = True

    monkeypatch.setattr(QMessageBox, 'critical', lambda *a, **k: fake_critical(*a, **k))

    dlg._start_conversion()

    assert called['critical'] is True


def test_advanced_converter_flow(qtbot, tmp_path, monkeypatch):
    dlg = AdvancedConverterDialog()
    qtbot.addWidget(dlg)

    # create a dummy input file
    inp = tmp_path / 'sample.mkv'
    inp.write_text('dummy')
    dlg.file_list.addItem(str(inp))
    dlg.output_dir_edit.setText(str(tmp_path))

    # Make QMessageBox.question return Yes so conversion proceeds
    monkeypatch.setattr(QMessageBox, 'question', lambda *a, **k: QMessageBox.Yes)

    # simulate ffmpeg -version check success and simulate conversion by creating output file
    def fake_run(cmd, *a, **k):
        # ffmpeg -version check
        if isinstance(cmd, (list, tuple)) and '-version' in cmd:
            class R: returncode = 0
            return R()
        # conversion invocation: create output file path (last arg)
        try:
            out = cmd[-1]
            Path(out).write_text('mp4')
        except Exception:
            pass
        class R: returncode = 0
        return R()

    monkeypatch.setattr(subprocess, 'run', fake_run)

    # start conversion and wait for completion
    dlg._start_conversion()

    # wait until worker finishes (worker becomes None)
    qtbot.waitUntil(lambda: dlg.worker is None, timeout=5000)

    assert dlg.progress_label.text() in ('Conversion completed', 'Conversion process completed', 'Conversion completed')


def test_history_dialog_populates_table(tmp_path, qtbot):
    dbp = str(tmp_path / 'h.db')
    conn = sqlite3.connect(dbp)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS downloads (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, title TEXT, format TEXT, quality TEXT, status TEXT, download_date TEXT, file_size INTEGER, duration INTEGER, platform TEXT, file_path TEXT)''')
    # insert few rows
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rows = [
        ('http://a', 'Title A', 'Video', '', 'Completed', now, 100, 30, 'yt', 'c:/a.mp4'),
        ('http://b', 'Title B', 'Audio', '', 'Failed', now, 200, 0, 'yt', 'c:/b.mp3')
    ]
    for r in rows:
        cur.execute('INSERT INTO downloads (url, title, format, quality, status, download_date, file_size, duration, platform, file_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', r)
    conn.commit()
    conn.close()

    dlg = HistoryDialog(dbp)
    qtbot.addWidget(dlg)

    # table should have 2 rows
    assert dlg.history_table.rowCount() == 2
    # labels updated
    assert 'Total Downloads' in dlg.total_downloads_label.text()


def test_download_selected_integration(qtbot, tmp_path, monkeypatch):
    # prepare temp history DB
    dbp = str(tmp_path / 'hist.db')
    monkeypatch.setattr(main_V3, 'HISTORY_DB', dbp)

    # Create a fake entry and add to window
    win = YouTubeDownloader()
    qtbot.addWidget(win)

    # prepare playlist_entries with a fake entry
    entry = {'title': 'My Video', 'id': 'vid123', 'extractor': 'youtube', 'playlist': 'NA'}
    win.playlist_entries = [entry]
    win.video_listbox.addItem('001. My Video')
    win.url_entry.setText('http://example.com/watch?v=vid123')
    win.q_combo.addItem('best')
    win.q_combo.setCurrentIndex(0)

    # Monkeypatch YoutubeDL to a fake context manager
    class FakeYDL:
        def __init__(self, opts=None):
            self.opts = opts or {}
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def download(self, urls):
            # simulate creating a file in target dir
            target_dir = self.opts.get('paths', {}).get('home') or self.opts.get('outtmpl') or os.getcwd()
            # choose a filename matching outtmpl pattern (approx)
            fname = f"1 - {sanitize(title:= 'My Video')}.mp4"
            p = Path(target_dir) / fname
            os.makedirs(target_dir, exist_ok=True)
            p.write_text('x')

    # helper to sanitize similar to main_V3.sanitize_filename
    def sanitize(s):
        import re
        s = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', s)
        s = s.strip().strip('.')
        return s

    monkeypatch.setattr(main_V3, 'YoutubeDL', FakeYDL)

    # Call download_selected and wait until DB row appears
    win.video_listbox.setCurrentRow(0)
    win.start_btn.clicked.disconnect() if win.start_btn.receivers(win.start_btn.clicked) else None
    # trigger download
    win.download_selected()

    # wait until a record appears in DB
    def db_has_row():
        if not os.path.exists(dbp):
            return False
        conn = sqlite3.connect(dbp)
        cur = conn.cursor()
        try:
            cur.execute('SELECT COUNT(*) FROM downloads')
            c = cur.fetchone()[0]
        except Exception:
            c = 0
        conn.close()
        return c > 0

    qtbot.waitUntil(db_has_row, timeout=5000)

    # verify entry
    conn = sqlite3.connect(dbp)
    cur = conn.cursor()
    cur.execute('SELECT url, title, status FROM downloads')
    rows = cur.fetchall()
    conn.close()
    assert rows and rows[0][0].startswith('http')
