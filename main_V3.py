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
                             QScrollArea, QWidget, QGroupBox, QButtonGroup, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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
                    ok += 1
                except Exception as e:
                    fail += 1
                    logging.error(f"Batch download failed for {url}: {e}")
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

        # Generic menus that currently show a 'Coming soon' message
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        tools_menu = menubar.addMenu("Tools")
        help_menu = menubar.addMenu("Help")

        # Simple actions for the generic menus
        file_action = file_menu.addAction("Open")
        file_action.triggered.connect(lambda: self._show_coming_soon('Open'))
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Settings submenu including theme selection
        settings_menu = edit_menu.addMenu("Settings")

        # Theme actions (Light / Dark)
        theme_group = QtWidgets.QActionGroup(self)
        self.light_theme_action = settings_menu.addAction("Light Theme")
        self.light_theme_action.setCheckable(True)
        self.dark_theme_action = settings_menu.addAction("Dark Theme")
        self.dark_theme_action.setCheckable(True)
        theme_group.addAction(self.light_theme_action)
        theme_group.addAction(self.dark_theme_action)

        # Connect theme actions
        self.light_theme_action.triggered.connect(lambda: self._set_and_save_theme('light'))
        self.dark_theme_action.triggered.connect(lambda: self._set_and_save_theme('dark'))

        # A simple Preferences placeholder remains for other settings
        pref_action = settings_menu.addAction("Preferences...")
        pref_action.triggered.connect(lambda: self._show_coming_soon('Preferences'))

        tools_action = tools_menu.addAction("Tools")
        tools_action.triggered.connect(lambda: self._show_coming_soon('Tools'))

        help_action = help_menu.addAction("About")
        help_action.triggered.connect(lambda: self._show_coming_soon('About'))

        # Convert menu with two real submenus that open converter dialogs
        convert_menu = menubar.addMenu("Convert")
        basic_convert_action = convert_menu.addAction("Basic Convert")
        basic_convert_action.triggered.connect(self._open_basic_converter)
        advanced_convert_action = convert_menu.addAction("Advanced Converter")
        advanced_convert_action.triggered.connect(self._open_advanced_converter)

        # Batch download button
        batch_btn = QPushButton("Batch Download from File")
        batch_btn.clicked.connect(self.batch_download_from_file)
        self.content_layout.addWidget(batch_btn)
        # URL Entry
        url_layout = QHBoxLayout()
        url_label = QLabel("Media URL:")
        self.url_entry = QLineEdit()
        self.url_entry.setMinimumWidth(500)
        fetch_btn = QPushButton("Fetch Playlist")
        fetch_btn.clicked.connect(self.fetch_videos)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_entry)
        url_layout.addWidget(fetch_btn)
        self.content_layout.addLayout(url_layout)

        # Type selection
        type_group = QGroupBox("Type")
        type_layout = QHBoxLayout(type_group)
        self.radio_group = QButtonGroup()
        self.radio_video = QRadioButton("Video")
        self.radio_audio = QRadioButton("Audio")
        self.radio_captions = QRadioButton("Captions")
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
        convert_btn = QPushButton("Convert MKV to MP4")
        convert_btn.clicked.connect(self.convert_mkv_button)
        scan_btn = QPushButton("Scan Folder\nfor mkv")
        scan_btn.clicked.connect(self.scan_folder_button)
        type_layout.addWidget(convert_btn)
        type_layout.addWidget(scan_btn)

        self.content_layout.addWidget(type_group)

        # Quality combo and formats button
        formats_layout = QHBoxLayout()
        self.q_combo = QComboBox()
        self.q_combo.addItems(self.video_qualities)
        self.q_combo.setEditable(False)
        load_formats_btn = QPushButton("Load Formats")
        load_formats_btn.clicked.connect(self.load_formats_for_selection)
        formats_layout.addWidget(self.q_combo)
        formats_layout.addWidget(load_formats_btn)
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
        self.progress_label = QLabel("")
        self.content_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.content_layout.addWidget(self.progress_bar)

        # Folder chooser
        folder_layout = QHBoxLayout()
        folder_btn = QPushButton("Choose Folder")
        folder_btn.clicked.connect(self.choose_folder)
        self.folder_label = QLabel(f"Folder: {DOWNLOAD_DIR}")
        folder_layout.addWidget(folder_btn)
        folder_layout.addWidget(self.folder_label)
        self.content_layout.addLayout(folder_layout)

        self.counts_label = QLabel("Downloaded: 0/0 | Errors: 0")
        self.content_layout.addWidget(self.counts_label)

        # Start button
        self.start_btn = QPushButton("Start Download")
        self.start_btn.setStyleSheet("background-color: green; color: white;")
        self.start_btn.clicked.connect(self.download_selected)
        self.content_layout.addWidget(self.start_btn)

        # Cookies button
        cookies_btn = QPushButton("Load Cookies.txt (optional)")
        cookies_btn.clicked.connect(self.load_cookies)
        self.content_layout.addWidget(cookies_btn)

        # Convert buttons (hidden initially)
        self.convert_selected_btn = QPushButton("Convert Selected")
        self.convert_selected_btn.clicked.connect(self.convert_selected_action_inline)
        self.convert_all_btn = QPushButton("Convert All")
        self.convert_all_btn.clicked.connect(self.convert_all_action_inline)
        self.convert_selected_btn.hide()
        self.convert_all_btn.hide()
        self.content_layout.addWidget(self.convert_selected_btn)
        self.content_layout.addWidget(self.convert_all_btn)

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
                    'outtmpl': f'%(playlist_index|NA)s - {title}.%(ext)s',
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
                        break
                    except Exception as e:
                        attempts += 1
                        logging.error(f"Download failed for '{title}' attempt {attempts}: {e}")
                        worker.progress_update.emit(f"Error: {title} (attempt {attempts}/{local_max})")
                        if attempts >= local_max:
                            self.failure_count += 1
                            worker.count_update.emit(self.success_count, self.failure_count)
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())