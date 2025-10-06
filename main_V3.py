def sanitize_filename(name, max_length=60):
    # Remove or replace problematic characters for Windows
    import re
    # Remove control characters and reserved chars
    name = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', name)
    # Remove leading/trailing whitespace and dots
    name = name.strip().strip('.')
    # Truncate to max_length
    if len(name) > max_length:
        name = name[:max_length]
    return name
# main.py
import os
import sys
import threading
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QRadioButton, QComboBox,
                             QListWidget, QProgressBar, QFileDialog, QMessageBox,
                             QScrollArea, QWidget, QGroupBox, QButtonGroup, QFrame, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
# Converter dialogs
from converter_tool import BasicConverterDialog, AdvancedConverterDialog

# from setup_helper import full_setup
# # import cc_download.main as cc

# # Only run environment setup when running in development (not a frozen executable)
# try:
#     is_frozen = getattr(sys, 'frozen', False)
# except Exception:
#     is_frozen = False

# if not is_frozen:
#     # Ensure environment is ready during development/test runs
#     full_setup()

from yt_dlp import YoutubeDL
from datetime import datetime
import logging
import re
import requests
import subprocess
import json
import sqlite3
import traceback
from history_dialog import HistoryDialog
from preferences_dialog import PreferencesDialog

# Simple translation table for English, Arabic and Japanese
TRANSLATIONS = {
    'en': {
        'file': 'File', 'edit': 'Edit', 'tools': 'Tools', 'help': 'Help',
        'convert': 'Convert', 'basic_convert': 'Basic Convert', 'advanced_converter': 'Advanced Converter',
        'settings': 'Settings', 'light_theme': 'Light Theme', 'dark_theme': 'Dark Theme', 'preferences': 'Preferences...',
        'about': 'About', 'open': 'Open', 'exit': 'Exit', 'coming_soon': 'Coming soon',
        'language': 'Language', 'english': 'English', 'arabic': 'Arabic', 'japanese': 'Japanese',

        'batch_download': 'Batch Download from File',
        'media_url': 'Media URL:',
        'fetch_playlist': 'Fetch Playlist',
        'type': 'Type',
        'video': 'Video', 'audio': 'Audio', 'captions': 'Captions',
        'convert_mkv': 'Convert MKV to MP4', 'scan_folder': 'Scan Folder\nfor mkv',
        'formats': 'Formats', 'load_formats': 'Load Formats',
        'choose_folder': 'Choose Folder', 'folder_label': 'Folder: {folder}',
        'counts_label': 'Downloaded: {s}/{t} | Errors: {f}', 'start_download': 'Start Download',
        'load_cookies': 'Load Cookies.txt (optional)',
        'convert_selected': 'Convert Selected', 'convert_all': 'Convert All',
        'download_history': 'Download History',
        'ready': 'Ready', 'preferences_title': 'Preferences', 'ok': 'OK', 'cancel': 'Cancel'
    },
    'ar': {
        'file': 'ملف', 'edit': 'تحرير', 'tools': 'أدوات', 'help': 'مساعدة',
        'convert': 'تحويل', 'basic_convert': 'تحويل أساسي', 'advanced_converter': 'محول متقدم',
        'settings': 'الإعدادات', 'light_theme': 'وضع فاتح', 'dark_theme': 'الوضع الداكن', 'preferences': 'تفضيلات...',
        'about': 'حول', 'open': 'فتح', 'exit': 'خروج', 'coming_soon': 'قريبًا',
        'language': 'اللغة', 'english': 'الإنجليزية', 'arabic': 'العربية', 'japanese': 'اليابانية',

        'batch_download': 'تنزيل دفعي من ملف',
        'media_url': 'رابط الوسائط:',
        'fetch_playlist': 'جلب القائمة',
        'type': 'النوع',
        'video': 'فيديو', 'audio': 'صوت', 'captions': 'ترجمة',
        'convert_mkv': 'تحويل MKV إلى MP4', 'scan_folder': 'مسح مجلد\nلـ mkv',
        'formats': 'الأنماط', 'load_formats': 'تحميل الأنماط',
        'choose_folder': 'اختر المجلد', 'folder_label': 'المجلد: {folder}',
        'counts_label': 'تم التنزيل: {s}/{t} | الأخطاء: {f}', 'start_download': 'ابدأ التنزيل',
        'load_cookies': 'تحميل cookies.txt (اختياري)',
        'convert_selected': 'تحويل المحدد', 'convert_all': 'تحويل الكل',
        'download_history': 'سجل التنزيلات',
        'ready': 'جاهز', 'preferences_title': 'التفضيلات', 'ok': 'موافق', 'cancel': 'إلغاء'
    },
    'ja': {
        # placeholder to keep structure; real strings are above
    },
    'ja': {
        'file': 'ファイル', 'edit': '編集', 'tools': 'ツール', 'help': 'ヘルプ',
        'convert': '変換', 'basic_convert': '基本変換', 'advanced_converter': '高度な変換',
        'settings': '設定', 'light_theme': 'ライトテーマ', 'dark_theme': 'ダークテーマ', 'preferences': '設定...',
        'about': 'アプリについて', 'open': '開く', 'exit': '終了', 'coming_soon': '近日公開',
        'language': '言語', 'english': '英語', 'arabic': 'アラビア語', 'japanese': '日本語',

        'batch_download': 'ファイルから一括ダウンロード',
        'media_url': 'メディアURL:',
        'fetch_playlist': 'プレイリスト取得',
        'type': 'タイプ',
        'video': 'ビデオ', 'audio': '音声', 'captions': 'キャプション',
        'convert_mkv': 'MKVをMP4に変換', 'scan_folder': 'フォルダをスキャン\nfor mkv',
        'formats': 'フォーマット', 'load_formats': 'フォーマットを読み込む',
        'choose_folder': 'フォルダを選択', 'folder_label': 'フォルダ: {folder}',
        'counts_label': 'ダウンロード済: {s}/{t} | エラー: {f}', 'start_download': 'ダウンロード開始',
        'load_cookies': 'Cookies.txtを読み込む(オプション)',
        'convert_selected': '選択を変換', 'convert_all': 'すべて変換',
        'download_history': 'ダウンロード履歴',
        'ready': '準備完了', 'preferences_title': '設定', 'ok': 'OK', 'cancel': 'キャンセル'
    }
}

from pathlib import Path
file_path = Path(__file__).resolve()
directory = os.path.dirname(file_path)

def check_os(name):
    if sys.platform == "linux":
        return f"{directory}/{name}"
    elif sys.platform == "win32":
        return f"{directory}\\{name}"
    else:
        print(f"This is an unsupported operating system: {sys.platform}")
        return f"{directory}/{name}"

DEFAULT_DOWNLOAD_DIR = check_os("YouTube_Downloads")
# Mutable download directory (can be changed via UI)
DOWNLOAD_DIR = DEFAULT_DOWNLOAD_DIR
AUDIO_COPY_DIR = os.path.join(DOWNLOAD_DIR, "audio_only")
LOG_FILE = check_os("youtube_downloader.log")
ARCHIVE_FILE = os.path.join(DOWNLOAD_DIR, 'downloaded_videos.txt')
SETTINGS_FILE = check_os('settings.json')
# Default history DB: put under a per-user persistent location (AppData on Windows, ~/.local/share on Linux)
from pathlib import Path as _Path
def _default_history_db_path():
    try:
        if sys.platform == 'win32':
            appdata = os.environ.get('APPDATA') or str(_Path.home())
            base = os.path.join(appdata, 'YouTubeDownloader')
        elif sys.platform == 'linux':
            base = os.path.join(str(_Path.home()), '.local', 'share', 'youtubedownloader')
        else:
            base = os.path.join(str(_Path.home()), '.youtubedownloader')
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, 'download_history.db')
    except Exception:
        return check_os('download_history.db')

HISTORY_DB = _default_history_db_path()

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_COPY_DIR, exist_ok=True)

# --- Logging Setup ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class WorkerThread(QThread):
    data_signal = pyqtSignal(object)
    count_update = pyqtSignal(int, int)
    warning_signal = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.func(self)
            self.finished_signal.emit("")
        except Exception as e:
            self.error_signal.emit(str(e))

class YouTubeDownloader(QMainWindow):
    def batch_download_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select URL list text file", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        import re
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            urls = [line.strip() for line in f if line.strip() and re.match(r'^https?://', line.strip())]
        if not urls:
            self.show_message("Batch Download", "No valid URLs found in the file.")
            return

        def _run(worker):
            total = len(urls)
            ok, fail = 0, 0
            # Ensure download directory exists
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            for idx, url in enumerate(urls, 1):
                self.progress_label.setText(f"Batch: {idx}/{total} - {url[:60]}")
                ydl_opts = {
                    'quiet': True,
                    'progress_hooks': [lambda d: None],
                    'paths': {'home': DOWNLOAD_DIR, 'temp': DOWNLOAD_DIR},
                    # Flat, safe output template: title (truncated), id, ext
                    'outtmpl': {'default': '%(title).60s [%(id)s].%(ext)s'},
                    'restrictfilenames': True,
                    'windowsfilenames': True,
                }
                if self.cookies_path:
                    ydl_opts['cookiefile'] = self.cookies_path
                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)

                    # Best-effort file detection in DOWNLOAD_DIR using title or id
                    title = sanitize_filename(info.get('title') or info.get('id') or 'Unknown')
                    video_id = info.get('id') or ''
                    file_path = ''
                    file_size = 0
                    try:
                        candidates = []
                        for root, _, files in os.walk(DOWNLOAD_DIR):
                            for fn in files:
                                if title.lower() in fn.lower() or (video_id and video_id in fn):
                                    full = os.path.join(root, fn)
                                    try:
                                        m = os.path.getmtime(full)
                                    except Exception:
                                        m = 0
                                    candidates.append((m, full))
                        if candidates:
                            candidates.sort(reverse=True)
                            file_path = candidates[0][1]
                            try:
                                file_size = os.path.getsize(file_path)
                            except Exception:
                                file_size = 0
                    except Exception:
                        logging.exception('Error locating batch downloaded file')

                    ok += 1

                    try:
                        rec = {
                            'url': url,
                            'title': info.get('title') or '',
                            'format': 'Video',
                            'quality': '',
                            'status': 'Completed',
                            'download_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'file_size': file_size,
                            'duration': int(info.get('duration') or 0),
                            'platform': info.get('extractor') or 'Unknown',
                            'file_path': file_path
                        }
                        self._log_download(rec)
                    except Exception:
                        logging.exception('Failed to log batch download')

                except Exception as e:
                    fail += 1
                    logging.error(f"Batch download failed for {url}: {e}")
                    try:
                        rec = {
                            'url': url,
                            'title': '',
                            'format': 'Video',
                            'quality': '',
                            'status': 'Failed',
                            'download_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'file_size': 0,
                            'duration': 0,
                            'platform': 'Unknown',
                            'file_path': ''
                        }
                        self._log_download(rec)
                    except Exception:
                        logging.exception('Failed to log batch failure')
            msg = f"Batch complete. Downloaded: {ok}, Failed: {fail}"
            if fail:
                msg += "\nCheck log for details."
            worker.finished_signal.emit(msg)

        worker = WorkerThread(_run)
        worker.finished_signal.connect(lambda msg: self.show_message("Batch Download", msg))
        self._track_thread(worker)
        worker.start()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Playlist Downloader")
        self.setGeometry(100, 100, 750, 600)


        self.playlist_entries = []
        self.current_formats = []  # populated by Load Formats per selected item
        self.cookies_path = None   # optional cookies file for sites like Facebook
        self.success_count = 0
        self.failure_count = 0
        self.total_items = 0

        # Track running threads to prevent premature destruction
        self.threads = set()

        # UI/theme settings
        self.settings = {}
        self._load_settings()

        # history DB path used by this instance (can be overridden in settings)
        # default to module-level HISTORY_DB (may be monkeypatched in tests)
        try:
            self.history_db_path = self.settings.get('history_db', HISTORY_DB)
        except Exception:
            self.history_db_path = HISTORY_DB

        # Initialize history DB and a UI heartbeat timer for safe UI updates
        try:
            self._init_history_db()
        except Exception:
            logging.exception('Failed to initialize history DB')

        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(1000)
        self._heartbeat_timer.timeout.connect(self._heartbeat)
        self._heartbeat_timer.start()

        # Video qualities and audio
        self.video_qualities = ['best', 'bestvideo[height<=1080]+bestaudio', 'bestvideo[height<=720]+bestaudio', 'worst']
        self.audio_qualities = ['bestaudio', 'bestaudio[ext=mp3]', 'bestaudio/best']

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Scroll area
        scroll = QScrollArea()
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        scroll.setWidget(self.content_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        self.setup_ui()

    def _load_settings(self):
        """Load user settings (JSON) if present."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {'theme': 'light'}
        except Exception:
            self.settings = {'theme': 'light'}
        # Apply the theme now if setup_ui has not yet created actions, apply later in setup_ui
        try:
            self._apply_theme(self.settings.get('theme', 'light'))
        except Exception:
            pass

        # If settings specify a custom history DB path, use it for this session
        try:
            if isinstance(self.settings, dict) and self.settings.get('history_db'):
                self.history_db_path = self.settings.get('history_db')
            else:
                # ensure attribute exists
                if not hasattr(self, 'history_db_path'):
                    self.history_db_path = HISTORY_DB
        except Exception:
            self.history_db_path = HISTORY_DB

    # Preferences dialog implementation has been moved to the end of the file to keep
    # the YouTubeDownloader class definition contiguous.


    def _save_settings(self):
        """Persist settings to disk."""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings or {}, f, indent=2)
        except Exception:
            logging.exception('Failed to save settings')

    def _set_and_save_theme(self, theme_name: str):
        """Set theme in memory, persist it, and apply immediately."""
        if theme_name not in ('light', 'dark'):
            return
        self.settings['theme'] = theme_name
        self._save_settings()
        self._apply_theme(theme_name)

    def _apply_theme(self, theme_name: str):
        """Apply a basic light/dark stylesheet to the application and update menu checks."""
        if theme_name == 'dark':
            dark_qss = """
            QWidget { background-color: #2e2e2e; color: #e0e0e0; }
            QLineEdit, QTextEdit, QListWidget, QComboBox, QSpinBox { background-color: #3a3a3a; color: #e0e0e0; }
            QPushButton { background-color: #4b6eaf; color: white; }
            QProgressBar { background-color: #444; color: #e0e0e0; }
            """
            QApplication.instance().setStyleSheet(dark_qss)
            # Update action checks if available
            try:
                self.dark_theme_action.setChecked(True)
                self.light_theme_action.setChecked(False)
            except Exception:
                pass
        else:
            # Light theme: clear stylesheet
            QApplication.instance().setStyleSheet("")
            try:
                self.light_theme_action.setChecked(True)
                self.dark_theme_action.setChecked(False)
            except Exception:
                pass

    def _tr(self, key: str) -> str:
        """Translate a label key according to current language setting."""
        lang = self.settings.get('language', 'en') if isinstance(self.settings, dict) else 'en'
        return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

    def _set_and_save_language(self, lang_code: str):
        if lang_code not in TRANSLATIONS:
            return
        self.settings['language'] = lang_code
        self._save_settings()
        self._apply_language(lang_code)

    def _apply_language(self, lang_code: str):
        """Update visible menu labels to the selected language."""
        # Update top-level menus and menu items that were created in setup_ui
        try:
            menubar = self.menuBar()
            # Map top-level menu labels
            for action in menubar.actions():
                txt = action.text()
                if txt in ('File', 'ملف', 'ファイル'):
                    action.setText(self._tr('file'))
                elif txt in ('Edit', 'تحرير', '編集'):
                    action.setText(self._tr('edit'))
                elif txt in ('Tools', 'أدوات', 'ツール'):
                    action.setText(self._tr('tools'))
                elif txt in ('Help', 'مساعدة', 'ヘルプ'):
                    action.setText(self._tr('help'))

            # Update Settings and Convert labels inside menus
            for top_action in menubar.actions():
                menu = top_action.menu()
                if not menu:
                    continue
                for sub in menu.actions():
                    st = sub.text()
                    if st in ('Settings', 'الإعدادات', '設定'):
                        sub.setText(self._tr('settings'))
                    if st in ('Convert', 'تحويل', '変換'):
                        sub.setText(self._tr('convert'))
        except Exception:
            pass

    def _init_history_db(self):
        """Create history database and table if missing. Use file-level sqlite (safe across threads if using separate connections)."""
        try:
            conn = sqlite3.connect(self.history_db_path, timeout=5)
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
            conn.close()
        except Exception:
            logging.exception('Could not create or access history DB')

    def _log_download(self, record: dict):
        """Insert a download record into history DB. This opens a fresh sqlite connection per-call for thread-safety."""
        try:
            conn = sqlite3.connect(self.history_db_path, timeout=5)
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO downloads (url, title, format, quality, status, download_date, file_size, duration, platform, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.get('url'),
                record.get('title'),
                record.get('format'),
                record.get('quality'),
                record.get('status'),
                record.get('download_date'),
                record.get('file_size'),
                record.get('duration'),
                record.get('platform'),
                record.get('file_path')
            ))
            conn.commit()
            conn.close()
        except Exception:
            logging.exception('Failed to log download record: %s', traceback.format_exc())

    def _open_history(self):
        try:
            dlg = HistoryDialog(self.history_db_path, self)
            dlg.exec_()
        except Exception as e:
            logging.exception('Failed to open history dialog: %s', e)
            self.show_message('Error', f'Could not open history:\n{e}', QMessageBox.Critical)

    def _set_and_save_history_db(self, path: str):
        """Set a new history DB path, persist it to settings, and initialize the DB file."""
        try:
            path = os.path.expanduser(path)
            # ensure directory exists
            d = os.path.dirname(path)
            if d:
                os.makedirs(d, exist_ok=True)
            self.history_db_path = path
            # persist
            try:
                self.settings['history_db'] = path
                self._save_settings()
            except Exception:
                logging.exception('Failed to persist history_db to settings')
            # initialize DB file and tables
            try:
                conn = sqlite3.connect(self.history_db_path, timeout=5)
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
                conn.close()
            except Exception:
                logging.exception('Failed to initialize new history DB at %s', self.history_db_path)
        except Exception:
            logging.exception('Invalid path provided for history DB: %s', path)

    def _heartbeat(self):
        # Minimal heartbeat to keep UI responsive and allow thread cleanup
        try:
            # no-op currently; placeholder for periodic UI updates if needed
            pass
        except Exception:
            logging.exception('Heartbeat error')

        # Update language action checks
        try:
            lc = self.settings.get('language', 'en')
            self.lang_en_action.setChecked(lc == 'en')
            self.lang_ar_action.setChecked(lc == 'ar')
            self.lang_ja_action.setChecked(lc == 'ja')
        except Exception:
            pass

    def _track_thread(self, worker):
        self.threads.add(worker)
        worker.finished_signal.connect(lambda *_: self.threads.discard(worker))
        worker.finished.connect(lambda: self.threads.discard(worker))

    def closeEvent(self, event):
        # Wait for all threads to finish before closing
        for thread in list(self.threads):
            if thread.isRunning():
                thread.quit()
                thread.wait(3000)  # Wait up to 3 seconds per thread
        event.accept()

    def setup_ui(self):
        # --- Menu Bar ---
        menubar = self.menuBar()

        # Top-level menus
        file_menu = menubar.addMenu(self._tr('file'))
        edit_menu = menubar.addMenu(self._tr('edit'))
        tools_menu = menubar.addMenu(self._tr('tools'))
        help_menu = menubar.addMenu(self._tr('help'))

        # File actions
        file_action = file_menu.addAction(self._tr('open'))
        file_action.triggered.connect(lambda: self._show_coming_soon(self._tr('open')))
        exit_action = file_menu.addAction(self._tr('exit'))
        exit_action.triggered.connect(self.close)

        # Settings submenu including theme selection
        settings_menu = edit_menu.addMenu(self._tr('settings'))

        # Theme actions (Light / Dark)
        theme_group = QtWidgets.QActionGroup(self)
        self.light_theme_action = settings_menu.addAction(self._tr('light_theme'))
        self.light_theme_action.setCheckable(True)
        self.dark_theme_action = settings_menu.addAction(self._tr('dark_theme'))
        self.dark_theme_action.setCheckable(True)
        theme_group.addAction(self.light_theme_action)
        theme_group.addAction(self.dark_theme_action)
        self.light_theme_action.triggered.connect(lambda: self._set_and_save_theme('light'))
        self.dark_theme_action.triggered.connect(lambda: self._set_and_save_theme('dark'))

        # Language submenu (English, Arabic, Japanese)
        lang_menu = settings_menu.addMenu(self._tr('language'))
        lang_group = QtWidgets.QActionGroup(self)
        self.lang_en_action = lang_menu.addAction(self._tr('english'))
        self.lang_en_action.setCheckable(True)
        self.lang_ar_action = lang_menu.addAction(self._tr('arabic'))
        self.lang_ar_action.setCheckable(True)
        self.lang_ja_action = lang_menu.addAction(self._tr('japanese'))
        self.lang_ja_action.setCheckable(True)
        lang_group.addAction(self.lang_en_action)
        lang_group.addAction(self.lang_ar_action)
        lang_group.addAction(self.lang_ja_action)
        self.lang_en_action.triggered.connect(lambda: self._set_and_save_language('en'))
        self.lang_ar_action.triggered.connect(lambda: self._set_and_save_language('ar'))
        self.lang_ja_action.triggered.connect(lambda: self._set_and_save_language('ja'))

    # (Preferences moved to Tools menu; Settings keeps theme & language only)

    # Tools menu: Convert (submenu), Download History, Preferences
        convert_menu = tools_menu.addMenu(self._tr('convert'))
        basic_convert_action = convert_menu.addAction(self._tr('basic_convert'))
        basic_convert_action.triggered.connect(self._open_basic_converter)
        advanced_convert_action = convert_menu.addAction(self._tr('advanced_converter'))
        advanced_convert_action.triggered.connect(self._open_advanced_converter)

        history_action = tools_menu.addAction(self._tr('download_history'))
        history_action.triggered.connect(self._open_history)

        pref_action = tools_menu.addAction(self._tr('preferences'))
        pref_action.triggered.connect(self._open_preferences)

        # Help
        help_action = help_menu.addAction(self._tr('about'))
        help_action.triggered.connect(lambda: self._show_coming_soon(self._tr('about')))

        # Batch download button
        self.batch_btn = QPushButton(self._tr('batch_download'))
        self.batch_btn.clicked.connect(self.batch_download_from_file)
        self.content_layout.addWidget(self.batch_btn)

        # URL Entry
        url_layout = QHBoxLayout()
        self.url_label = QLabel(self._tr('media_url'))
        self.url_entry = QLineEdit()
        self.url_entry.setMinimumWidth(500)
        self.fetch_btn = QPushButton(self._tr('fetch_playlist'))
        self.fetch_btn.clicked.connect(self.fetch_videos)
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url_entry)
        url_layout.addWidget(self.fetch_btn)
        self.content_layout.addLayout(url_layout)

        # Type selection
        type_group = QGroupBox(self._tr('type'))
        type_layout = QHBoxLayout(type_group)
        self.radio_group = QButtonGroup()
        self.radio_video = QRadioButton(self._tr('video'))
        self.radio_audio = QRadioButton(self._tr('audio'))
        self.radio_captions = QRadioButton(self._tr('captions'))
        self.radio_video.toggled.connect(self.update_quality_options)
        self.radio_audio.toggled.connect(self.update_quality_options)
        self.radio_captions.toggled.connect(self.update_quality_options)
        self.radio_group.addButton(self.radio_video)
        self.radio_group.addButton(self.radio_audio)
        self.radio_group.addButton(self.radio_captions)
        self.radio_video.setChecked(True)
        type_layout.addWidget(self.radio_video)
        type_layout.addWidget(self.radio_audio)
        type_layout.addWidget(self.radio_captions)

        # Captions language
        self.captions_lang_combo = QComboBox()
        self.captions_lang_combo.addItems(["en", "ar"])
        self.captions_lang_combo.setCurrentText("en")
        self.captions_lang_combo.hide()
        type_layout.addWidget(self.captions_lang_combo)

        # Convert and Scan buttons
        self.convert_btn_mkv = QPushButton(self._tr('convert_mkv'))
        self.convert_btn_mkv.clicked.connect(self.convert_mkv_button)
        self.scan_btn = QPushButton(self._tr('scan_folder'))
        self.scan_btn.clicked.connect(self.scan_folder_button)
        type_layout.addWidget(self.convert_btn_mkv)
        type_layout.addWidget(self.scan_btn)

        self.content_layout.addWidget(type_group)

        # Quality combo and formats button
        formats_layout = QHBoxLayout()
        self.q_combo = QComboBox()
        self.q_combo.addItems(self.video_qualities)
        self.q_combo.setEditable(False)
        self.load_formats_btn = QPushButton(self._tr('load_formats'))
        self.load_formats_btn.clicked.connect(self.load_formats_for_selection)
        formats_layout.addWidget(self.q_combo)
        formats_layout.addWidget(self.load_formats_btn)
        self.formats_widget = QWidget()
        self.formats_widget.setLayout(formats_layout)
        self.content_layout.addWidget(self.formats_widget)

        # Video list
        list_layout = QHBoxLayout()
        self.video_listbox = QListWidget()
        self.video_listbox.setSelectionMode(QListWidget.ExtendedSelection)
        list_layout.addWidget(self.video_listbox)
        self.content_layout.addLayout(list_layout)

        # Progress
        self.progress_label = QLabel(self._tr('ready'))
        self.content_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.content_layout.addWidget(self.progress_bar)

        # Folder chooser
        folder_layout = QHBoxLayout()
        self.folder_btn = QPushButton(self._tr('choose_folder'))
        self.folder_btn.clicked.connect(self.choose_folder)
        self.folder_label = QLabel(self._tr('folder_label').format(folder=DOWNLOAD_DIR))
        folder_layout.addWidget(self.folder_btn)
        folder_layout.addWidget(self.folder_label)
        self.content_layout.addLayout(folder_layout)

        # Counts label
        self.counts_label = QLabel(self._tr('counts_label').format(s=0, t=0, f=0))
        self.content_layout.addWidget(self.counts_label)

        # Start button
        self.start_btn = QPushButton(self._tr('start_download'))
        self.start_btn.setStyleSheet("background-color: green; color: white;")
        self.start_btn.clicked.connect(self.download_selected)
        self.content_layout.addWidget(self.start_btn)

        # Cookies button
        self.cookies_btn = QPushButton(self._tr('load_cookies'))
        self.cookies_btn.clicked.connect(self.load_cookies)
        self.content_layout.addWidget(self.cookies_btn)

        # Convert buttons (hidden initially)
        self.convert_selected_btn = QPushButton(self._tr('convert_selected'))
        self.convert_selected_btn.clicked.connect(self.convert_selected_action_inline)
        self.convert_all_btn = QPushButton(self._tr('convert_all'))
        self.convert_all_btn.clicked.connect(self.convert_all_action_inline)
        self.convert_selected_btn.hide()
        self.convert_all_btn.hide()
        self.content_layout.addWidget(self.convert_selected_btn)
        self.content_layout.addWidget(self.convert_all_btn)

        # Refresh text to ensure translations are applied
        try:
            self._refresh_ui_texts()
        except Exception:
            pass

    def _show_coming_soon(self, name: str):
        """Show a standardized 'Coming soon' message for placeholder menu items."""
        self.show_message(name, f"{name} - Coming soon.")

    def _open_basic_converter(self):
        """Open the basic converter dialog from converter_tool.py"""
        try:
            dlg = BasicConverterDialog(self)
            dlg.exec_()
        except Exception as e:
            logging.exception('Failed to open BasicConverterDialog: %s', e)
            self.show_message('Error', f'Could not open Basic Converter:\n{e}', QMessageBox.Critical)

    def _open_advanced_converter(self):
        """Open the advanced converter dialog from converter_tool.py"""
        try:
            dlg = AdvancedConverterDialog(self)
            dlg.exec_()
        except Exception as e:
            logging.exception('Failed to open AdvancedConverterDialog: %s', e)
            self.show_message('Error', f'Could not open Advanced Converter:\n{e}', QMessageBox.Critical)

    def _refresh_ui_texts(self):
        """Update UI strings to current language (best-effort)."""
        try:
            # Menus are updated by _apply_language, but update buttons/labels here
            self.batch_btn.setText(self._tr('batch_download'))
            self.url_label.setText(self._tr('media_url'))
            self.fetch_btn.setText(self._tr('fetch_playlist'))
            self.radio_video.setText(self._tr('video'))
            self.radio_audio.setText(self._tr('audio'))
            self.radio_captions.setText(self._tr('captions'))
            self.convert_btn_mkv.setText(self._tr('convert_mkv'))
            self.scan_btn.setText(self._tr('scan_folder'))
            self.load_formats_btn.setText(self._tr('load_formats'))
            self.folder_btn.setText(self._tr('choose_folder'))
            self.folder_label.setText(self._tr('folder_label').format(folder=DOWNLOAD_DIR))
            self.counts_label.setText(self._tr('counts_label').format(s=0, t=0, f=0))
            self.start_btn.setText(self._tr('start_download'))
            self.cookies_btn.setText(self._tr('load_cookies'))
            self.convert_selected_btn.setText(self._tr('convert_selected'))
            self.convert_all_btn.setText(self._tr('convert_all'))
        except Exception:
            pass

    def _open_preferences(self):
        """Open Preferences dialog (created at runtime so class definition order doesn't matter)."""
        try:
            dlg = PreferencesDialog(self)
            dlg.exec_()
        except NameError:
            # PreferencesDialog may be defined later in the file; import it dynamically
            try:
                # reload module to ensure class is available
                import importlib
                importlib.reload(sys.modules[__name__])
                dlg = PreferencesDialog(self)
                dlg.exec_()
            except Exception as e:
                logging.exception('Failed to open Preferences dialog: %s', e)
                self.show_message('Error', f'Could not open Preferences:\n{e}', QMessageBox.Critical)
        except Exception as e:
            logging.exception('Failed to open Preferences dialog: %s', e)
            self.show_message('Error', f'Could not open Preferences:\n{e}', QMessageBox.Critical)

    def _populate_videos(self, data):
        titles, entries = data
        self.playlist_entries = entries
        self.video_listbox.clear()
        for t in titles:
            self.video_listbox.addItem(t)

    def _populate_scan(self, files):
        self.video_listbox.clear()
        for p in files:
            self.video_listbox.addItem(p)

    def _update_quality_combo(self, choices):
        self.current_formats = choices
        self.q_combo.clear()
        for _, label in choices:
            self.q_combo.addItem(label)
        self.progress_label.setText("Formats loaded.")

    def _update_counts(self, s, f):
        self.counts_label.setText(f"Downloaded: {s}/{self.total_items} | Errors: {f}")

    def update_quality_options(self):
        checked = self.radio_group.checkedButton()
        if not checked:
            return
        mode = checked.text()
        if not hasattr(self, 'q_combo') or self.q_combo is None:
            logging.warning('q_combo does not exist when update_quality_options called')
            return
        if mode == 'Video':
            self.q_combo.clear()
            self.q_combo.addItems(self.video_qualities)
            self.formats_widget.show()
            self.captions_lang_combo.hide()
        elif mode == 'Audio':
            self.q_combo.clear()
            self.q_combo.addItems(self.audio_qualities)
            self.formats_widget.show()
            self.captions_lang_combo.hide()
        else:
            # Captions mode
            self.formats_widget.hide()
            self.captions_lang_combo.show()

    def resolve_final_url(self, input_url: str) -> str:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            }
            resp = requests.get(input_url, headers=headers, allow_redirects=True, timeout=15)
            if resp.url:
                return resp.url
            return input_url
        except Exception:
            return input_url

    def find_video_files(self, folder_path: str):
        video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        matches = []
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                if any(filename.lower().endswith(ext) for ext in video_extensions):
                    matches.append(os.path.join(dirpath, filename))
        return matches

    def convert_to_mp4(self, input_file: str):
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}.mp4"
        if os.path.normpath(input_file).lower() == os.path.normpath(output_file).lower():
            return True, "Already MP4"
        cmd = ['ffmpeg', '-y', '-i', input_file, '-c:v', 'copy', '-c:a', 'copy', output_file]
        try:
            proc = subprocess.run(cmd, check=True, text=True, capture_output=True, encoding='utf-8')
            return True, output_file
        except FileNotFoundError:
            return False, "FFmpeg not found. Install and add to PATH."
        except subprocess.CalledProcessError as e:
            return False, e.stderr or str(e)
        except Exception as e:
            return False, str(e)

    def show_message(self, title, message, icon=QMessageBox.Information):
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

    def fetch_videos(self):
        self.playlist_entries = []
        self.video_listbox.clear()
        # Reset action buttons to download mode
        self.start_btn.show()
        self.convert_selected_btn.hide()
        self.convert_all_btn.hide()

        url = self.url_entry.text().strip()
        url = self.resolve_final_url(url)

        if not url:
            self.show_message("Input Error", "Please enter a playlist URL.")
            return

        self.progress_label.setText("Fetching videos...")

        def _fetch(worker):
            ydl_opts = {
                'extract_flat': True,
                'quiet': True,
                'skip_download': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                    'Referer': url,
                },
            }
            if self.cookies_path:
                ydl_opts['cookiefile'] = self.cookies_path
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    # Handle playlists and generic post pages with multiple entries
                    titles = []
                    entries = []
                    if isinstance(info, dict) and 'entries' in info and info['entries'] is not None:
                        playlist_entries = info['entries']
                        for i, entry in enumerate(playlist_entries):
                            if not isinstance(entry, dict):
                                continue
                            title = entry.get('title') or entry.get('id', 'Unknown')
                            titles.append(f"{i+1:03d}. {title}")
                            entries.append(entry)
                        if not entries:
                            worker.error_signal.emit("No videos found at the provided URL.")
                            return
                    elif isinstance(info, dict):
                        # Single media item
                        title = info.get('title') or info.get('id', 'Unknown')
                        titles.append(f"001. {title}")
                        entries.append(info)
                    else:
                        worker.error_signal.emit("No downloadable media found at the provided URL.")
                        return
                worker.data_signal.emit((titles, entries))
            except Exception as e:
                worker.error_signal.emit(f"Could not fetch info from URL. If this is Facebook, try loading cookies.txt and retry.\n\n{e}")

        worker = WorkerThread(_fetch)
        worker.data_signal.connect(self._populate_videos)
        worker.error_signal.connect(lambda msg: self.show_message("Error", msg, QMessageBox.Critical))
        self._track_thread(worker)
        worker.start()

    def load_formats_for_selection(self):
        selected = self.video_listbox.selectedIndexes()
        if not selected:
            self.show_message("Selection Error", "Please select a video to load formats.")
            return
        # Use the first selected index to discover formats
        idx = selected[0].row()
        url = self.url_entry.text().strip()
        url = self.resolve_final_url(url)
        if not url:
            self.show_message("Input Error", "Please enter a URL first.")
            return

        self.progress_label.setText("Loading formats...")

        def _load(worker):
            try:
                base_opts = {
                    'quiet': True,
                    'playlist_items': str(idx + 1),
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                        'Referer': url,
                    }
                }
                if self.cookies_path:
                    base_opts['cookiefile'] = self.cookies_path
                with YoutubeDL(base_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            except Exception as e:
                worker.error_signal.emit(f"Failed to load formats:\n{e}")
                return

            # info may be playlist entry or a single video dict
            # Ensure we have a dict with 'formats'
            if isinstance(info, dict) and 'formats' in info:
                formats = info['formats']
            elif isinstance(info, list) and info:
                candidate = info[0]
                formats = candidate.get('formats', [])
            else:
                formats = []

            # Build human-friendly choices, focusing on video heights
            heights = []
            for f in formats:
                vcodec = f.get('vcodec')
                height = f.get('height')
                if vcodec and vcodec != 'none' and height:
                    heights.append(height)
            heights = sorted(set(h for h in heights if isinstance(h, int)), reverse=True)

            choices = []
            choices.append(('best', 'best (auto)'))
            for h in heights:
                selector = f"bestvideo[height<={h}]+bestaudio/best"
                label = f"<= {h}p (video+bestaudio)"
                choices.append((selector, label))

            # Fallback if no heights found
            if len(choices) == 1:
                choices.extend([
                    ('best', 'best'),
                    ('worst', 'worst')
                ])

            worker.data_signal.emit(choices)

        worker = WorkerThread(_load)
        worker.data_signal.connect(self._update_quality_combo)
        worker.error_signal.connect(lambda msg: self.show_message("Error", msg, QMessageBox.Critical))
        self._track_thread(worker)
        worker.start()

    def is_in_archive(self, video_id: str) -> bool:
        try:
            if not os.path.exists(ARCHIVE_FILE):
                return False
            with open(ARCHIVE_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return video_id in content
        except Exception:
            return False

    def download_selected(self):
        selected = self.video_listbox.selectedIndexes()
        if not selected:
            self.show_message("Selection Error", "Please select at least one video.")
            return

        url = self.url_entry.text().strip()
        mode = self.radio_group.checkedButton().text()
        # Resolve selected quality when in Video/Audio mode
        selected_label = self.q_combo.currentText()
        quality = None
        if mode in ('Video', 'Audio'):
            for selector, label in self.current_formats:
                if label == selected_label:
                    quality = selector
                    break
            if not quality:
                quality = selected_label
        selected_indices = [i.row() for i in selected]

        self.total_items = len(selected_indices)
        self.success_count = 0
        self.failure_count = 0
        self.counts_label.setText(f"Downloaded: 0/{self.total_items} | Errors: 0")

        self.progress_label.setText("Starting download...")

        def run_download(worker):
            # Captions mode: use a streamlined captions flow
            if mode == 'Captions':
                lang = self.captions_lang_combo.currentText() or 'en'
                target_dir = os.path.join(DOWNLOAD_DIR, 'captions')
                os.makedirs(target_dir, exist_ok=True)
                try:
                    opts = {
                        'skip_download': True,
                        'writeautomaticsub': True,
                        'writesubtitles': True,
                        'subtitleslangs': [lang],
                        'outtmpl': os.path.join(target_dir, '%(title)s.%(ext)s'),
                        'subtitle_format': 'vtt',
                        'quiet': False,
                        'ignoreerrors': True,
                    }
                    with YoutubeDL(opts) as ydl:
                        ydl.download([url])
                    worker.finished_signal.emit(f"Captions downloaded to:\n{target_dir}")
                except Exception as e:
                    logging.error(f"Captions download failed: {e}")
                    worker.error_signal.emit(f"Failed to download captions:\n{e}")
                return

            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', '').strip()
                    worker.progress_update.emit(f"Downloading: {percent}")
                    try:
                        p_val = int(float(percent.rstrip('%')))
                        worker.progress_value.emit(p_val)
                    except:
                        worker.progress_value.emit(0)
                elif d['status'] == 'finished':
                    worker.progress_update.emit(f"Finished: {d.get('filename')}")
                    worker.progress_value.emit(100)

            for offset, idx in enumerate(selected_indices, start=1):
                try:
                    entry = self.playlist_entries[idx]
                except Exception:
                    self.failure_count += 1
                    worker.count_update.emit(self.success_count, self.failure_count)
                    continue


                # Sanitize title and subdir for safe Windows paths
                title = sanitize_filename(entry.get('title', 'Unknown Title'))
                video_id = entry.get('id') or ''
                use_archive = True
                if video_id and self.is_in_archive(video_id):
                    use_archive = False

                raw_subdir = entry.get('playlist') or 'NA'
                safe_subdir = sanitize_filename(str(raw_subdir)) or 'NA'
                target_dir = os.path.join(DOWNLOAD_DIR, safe_subdir)
                os.makedirs(target_dir, exist_ok=True)

                # Use sanitized title in outtmpl
                ydl_opts_item = {
                    'format': quality,
                    # Use sanitized title only (avoid 'NA - ' prefix when playlist_index is missing)
                    'outtmpl': f'{title}.%(ext)s',
                    'paths': {
                        'home': target_dir,
                        'temp': target_dir,
                    },
                    'ignoreerrors': False,
                    'progress_hooks': [progress_hook],
                    'playlist_items': str(idx + 1),
                    'retries': 10,
                    'fragment_retries': 10,
                    'concurrent_fragment_downloads': 3,
                    'windowsfilenames': False,
                    'restrictfilenames': False,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                        'Referer': url,
                    }
                }
                if self.cookies_path:
                    ydl_opts_item['cookiefile'] = self.cookies_path
                if use_archive:
                    ydl_opts_item['download_archive'] = ARCHIVE_FILE

                if mode == 'Audio':
                    ydl_opts_item['extractaudio'] = True
                    ydl_opts_item['postprocessors'] = [
                        {
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }
                    ]
                else:  # Video
                    ydl_opts_item['postprocessors'] = [
                        {
                            'key': 'FFmpegVideoRemuxer',
                            'preferedformat': 'mkv'
                        }
                    ]

                attempts = 0
                local_max = 5
                while True:
                    try:
                        worker.progress_value.emit(0)
                        worker.progress_update.emit(f"Starting: {title} ({offset}/{self.total_items})")
                        with YoutubeDL(ydl_opts_item) as ydl:
                            ydl.download([url])
                        self.success_count += 1
                        worker.count_update.emit(self.success_count, self.failure_count)
                        # Attempt to find the downloaded file in target_dir (best-effort)
                        try:
                            file_path = ''
                            file_size = 0
                            candidates = []
                            for root, _, files in os.walk(target_dir):
                                for fn in files:
                                    # match by title or video id if present
                                    if title.lower() in fn.lower() or (video_id and video_id in fn):
                                        full = os.path.join(root, fn)
                                        candidates.append((os.path.getmtime(full), full))
                            if candidates:
                                # choose most recently modified match
                                candidates.sort(reverse=True)
                                file_path = candidates[0][1]
                                try:
                                    file_size = os.path.getsize(file_path)
                                except Exception:
                                    file_size = 0
                        except Exception:
                            logging.exception('Failed to locate downloaded file')

                        # Log successful download (non-blocking safe sqlite write)
                        try:
                            rec = {
                                'url': url,
                                'title': title,
                                'format': 'Audio' if mode == 'Audio' else 'Video' if mode == 'Video' else 'Captions',
                                'quality': quality or '',
                                'status': 'Completed',
                                'download_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'file_size': file_size,
                                'duration': 0,
                                'platform': entry.get('extractor') or entry.get('webpage_url') or 'Unknown',
                                'file_path': file_path
                            }
                            self._log_download(rec)
                        except Exception:
                            logging.exception('Failed to log success record')

                        break
                    except Exception as e:
                        attempts += 1
                        logging.error(f"Download failed for '{title}' attempt {attempts}: {e}")
                        worker.progress_update.emit(f"Error: {title} (attempt {attempts}/{local_max})")
                        if attempts >= local_max:
                            self.failure_count += 1
                            worker.count_update.emit(self.success_count, self.failure_count)
                            # Log failed record
                            try:
                                rec = {
                                    'url': url,
                                    'title': title,
                                    'format': 'Audio' if mode == 'Audio' else 'Video' if mode == 'Video' else 'Captions',
                                    'quality': quality or '',
                                    'status': 'Failed',
                                    'download_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'file_size': 0,
                                    'duration': 0,
                                    'platform': entry.get('extractor') or entry.get('webpage_url') or 'Unknown',
                                    'file_path': ''
                                }
                                self._log_download(rec)
                            except Exception:
                                logging.exception('Failed to log failure record')
                            break

            if self.failure_count == 0:
                worker.finished_signal.emit(f"All {self.success_count} items downloaded successfully.")
            else:
                worker.warning_signal.emit(f"Downloaded {self.success_count} items with {self.failure_count} error(s). Check logs.")

        worker = WorkerThread(run_download)
        worker.progress_update.connect(self.progress_label.setText)
        worker.progress_value.connect(self.progress_bar.setValue)
        worker.count_update.connect(self._update_counts)
        worker.finished_signal.connect(lambda msg: self.show_message("Done", msg))
        worker.warning_signal.connect(lambda msg: self.show_message("Done with errors", msg, QMessageBox.Warning))
        worker.error_signal.connect(lambda msg: self.show_message("Error", msg, QMessageBox.Critical))
        self._track_thread(worker)
        worker.start()

    def choose_folder(self):
        global DOWNLOAD_DIR, AUDIO_COPY_DIR, ARCHIVE_FILE
        chosen = QFileDialog.getExistingDirectory(self, "Choose download folder", DOWNLOAD_DIR)
        if chosen:
            DOWNLOAD_DIR = chosen
            AUDIO_COPY_DIR = os.path.join(DOWNLOAD_DIR, "audio_only")
            ARCHIVE_FILE = os.path.join(DOWNLOAD_DIR, 'downloaded_videos.txt')
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            os.makedirs(AUDIO_COPY_DIR, exist_ok=True)
            self.folder_label.setText(f"Folder: {DOWNLOAD_DIR}")

    def load_cookies(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select cookies.txt",
                                              "", "Text Files (*.txt);;All Files (*)")
        if path:
            self.cookies_path = path
            self.show_message("Cookies Loaded", f"Using cookies from:\n{self.cookies_path}")

    def convert_mkv_button(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose MKV/Video files",
                                                "", "Video Files (*.mkv *.mp4 *.avi *.mov *.wmv *.flv *.webm);;All Files (*)")
        if not paths:
            return

        def _run(worker):
            ok, fail = 0, 0
            for f in paths:
                success, msg = self.convert_to_mp4(f)
                if success:
                    ok += 1
                else:
                    fail += 1
                    logging.error(f"Convert failed for {f}: {msg}")
            message = f"Converted: {ok}, Failed: {fail}"
            if fail:
                message += "\nCheck log for details."
            worker.finished_signal.emit(message)

        worker = WorkerThread(_run)
        worker.finished_signal.connect(lambda msg: self.show_message("Convert", msg))
        self._track_thread(worker)
        worker.start()

    def scan_folder_button(self):
        path = QFileDialog.getExistingDirectory(self, "Choose folder to scan for videos", DOWNLOAD_DIR)
        if not path:
            return

        def _post():
            self.start_btn.hide()
            self.convert_selected_btn.show()
            self.convert_all_btn.show()

        def _scan(worker):
            files = self.find_video_files(path)
            if not files:
                worker.error_signal.emit("No videos found in the selected folder.")
                return
            worker.data_signal.emit(files)

        worker = WorkerThread(_scan)
        worker.error_signal.connect(lambda msg: self.show_message("Scan", msg))
        worker.data_signal.connect(self._populate_scan)
        self._track_thread(worker)
        worker.start()
        _post()

    def convert_selected_action_inline(self):
        sel = self.video_listbox.selectedIndexes()
        if not sel:
            self.show_message("Convert", "Select one or more files to convert.")
            return
        files = [self.video_listbox.item(i.row()).text() for i in sel]

        def _run(worker):
            ok, fail = 0, 0
            for f in files:
                success, msg = self.convert_to_mp4(f)
                if success:
                    ok += 1
                else:
                    fail += 1
                    logging.error(f"Convert failed for {f}: {msg}")
            message = f"Converted: {ok}, Failed: {fail}"
            if fail:
                message += "\nCheck log for details."
            worker.finished_signal.emit(message)

        worker = WorkerThread(_run)
        worker.finished_signal.connect(lambda msg: self.show_message("Convert Selected", msg))
        self._track_thread(worker)
        worker.start()

    def convert_all_action_inline(self):
        count = self.video_listbox.count()
        if count == 0:
            self.show_message("Convert", "No files to convert. Run Scan first.")
            return
        files = [self.video_listbox.item(i).text() for i in range(count)]

        def _run(worker):
            ok, fail = 0, 0
            for f in files:
                success, msg = self.convert_to_mp4(f)
                if success:
                    ok += 1
                else:
                    fail += 1
                    logging.error(f"Convert failed for {f}: {msg}")
            message = f"Converted: {ok}, Failed: {fail}"
            if fail:
                message += "\nCheck log for details."
            worker.finished_signal.emit(message)

        worker = WorkerThread(_run)
        worker.finished_signal.connect(lambda msg: self.show_message("Convert All", msg))
        self._track_thread(worker)
        worker.start()
        worker = WorkerThread(_run)
        worker.finished_signal.connect(lambda msg: self.show_message("Convert All", msg))
        self._track_thread(worker)
        worker.start()


# PreferencesDialog moved to preferences_dialog.py

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())