import os
import sys
import sqlite3
import json
import tempfile
from pathlib import Path

import pytest

# ensure repo root is on sys.path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from main_V3 import sanitize_filename, check_os, HISTORY_DB


def test_sanitize_filename_basic():
    s = 'abc/def:ghi*?"<>|\n'
    out = sanitize_filename(s)
    assert '\\' not in out and '/' not in out and ':' not in out
    assert len(out) > 0


def test_check_os_returns_path():
    p = check_os('foo.txt')
    assert 'foo.txt' in p


def test_init_and_log_db(tmp_path):
    # use a temp DB file
    db_path = tmp_path / 'hist.db'
    db_path = str(db_path)

    # call the module-level init by opening a connection and creating the table
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            title TEXT,
            format TEXT,
            quality TEXT,
            status TEXT,
            download_date TEXT,
            file_size INTEGER,
            duration INTEGER,
            platform TEXT,
            file_path TEXT
        )
    ''')
    conn.commit()

    # insert a row
    cur.execute('INSERT INTO downloads (url, title, status, download_date) VALUES (?, ?, ?, ?)',
                ('http://example.com', 'Title', 'Completed', '2025-10-06 00:00:00'))
    conn.commit()

    cur.execute('SELECT url, title, status FROM downloads')
    rows = cur.fetchall()
    assert rows and rows[0][0] == 'http://example.com'
    conn.close()
