import os
import sys
import sqlite3
import subprocess
from pathlib import Path

import pytest

# ensure repo root is on sys.path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import main_V3
from main_V3 import YouTubeDownloader, SETTINGS_FILE, HISTORY_DB


def test_log_download_writes_row(tmp_path, monkeypatch, qapp, qtbot):
    # point HISTORY_DB to a temporary db file
    dbp = str(tmp_path / 'test_history.db')
    monkeypatch.setattr(main_V3, 'HISTORY_DB', dbp)

    win = YouTubeDownloader()
    qtbot.addWidget(win)

    record = {
        'url': 'http://example.com/video',
        'title': 'Test Video',
        'format': 'Video',
        'quality': 'best',
        'status': 'Completed',
        'download_date': '2025-10-06 00:00:00',
        'file_size': 1234,
        'duration': 10,
        'platform': 'example',
        'file_path': 'C:/Videos/test.mp4'
    }

    # Call the internal logger
    win._log_download(record)

    # Verify row exists
    conn = sqlite3.connect(dbp)
    cur = conn.cursor()
    cur.execute('SELECT url, title, status, file_size FROM downloads WHERE url=?', (record['url'],))
    rows = cur.fetchall()
    conn.close()
    assert rows, 'No row was written to the history DB'
    assert rows[0][0] == record['url']


def test_settings_saved_and_loaded(tmp_path, monkeypatch, qapp, qtbot):
    # redirect settings file to temporary path
    sf = str(tmp_path / 'settings.json')
    monkeypatch.setattr(main_V3, 'SETTINGS_FILE', sf)

    win = YouTubeDownloader()
    qtbot.addWidget(win)

    # Change theme and language and ensure persisted
    win._set_and_save_theme('dark')
    win._set_and_save_language('ar')

    # Read file
    import json
    with open(sf, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert data.get('theme') == 'dark'
    assert data.get('language') == 'ar'


def test_convert_to_mp4_ffmpeg_missing(tmp_path, monkeypatch):
    # Create dummy input file
    inp = tmp_path / 'video.mkv'
    inp.write_text('dummy')

    # Force subprocess.run to raise FileNotFoundError to simulate missing ffmpeg
    def _bad_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, 'run', _bad_run)

    ok, msg = main_V3.YouTubeDownloader().convert_to_mp4(str(inp))
    assert not ok
    assert 'FFmpeg' in msg or 'ffmpeg' in msg or 'not found' in msg.lower()


def test_convert_to_mp4_success(tmp_path, monkeypatch):
    # Create dummy input file and expected output
    inp = tmp_path / 'video.mkv'
    outp = tmp_path / 'video.mp4'
    inp.write_text('dummy')
    # Simulate ffmpeg creating the output file
    def _good_run(*args, **kwargs):
        # create the output file to simulate successful conversion
        outp.write_text('mp4')
        class CP:
            returncode = 0
        return CP()

    monkeypatch.setattr(subprocess, 'run', _good_run)

    ok, result = main_V3.YouTubeDownloader().convert_to_mp4(str(inp))
    assert ok
    assert str(outp) == result
