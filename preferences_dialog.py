from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QRadioButton,
                             QFileDialog, QLineEdit)

class PreferencesDialog(QDialog):
    """Preferences dialog moved out of main file. Expects a parent with methods:
    - _tr(key) -> str
    - settings dict with 'language' and 'theme' keys
    - _set_and_save_theme(theme)
    - _set_and_save_language(lang)
    - _refresh_ui_texts()
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(parent._tr('preferences_title'))
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        # Theme section
        theme_group = QGroupBox(parent._tr('settings'))
        t_layout = QVBoxLayout(theme_group)
        self.light_rb = QRadioButton(parent._tr('light_theme'))
        self.dark_rb = QRadioButton(parent._tr('dark_theme'))
        t_layout.addWidget(self.light_rb)
        t_layout.addWidget(self.dark_rb)
        layout.addWidget(theme_group)

        # Language section
        lang_group = QGroupBox(parent._tr('language'))
        l_layout = QVBoxLayout(lang_group)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([parent._tr('english'), parent._tr('arabic'), parent._tr('japanese')])
        l_layout.addWidget(self.lang_combo)
        layout.addWidget(lang_group)

        # Quick access info
        quick = QLabel(parent._tr('preferences_quick') if hasattr(parent, '_tr') else "Quick access: Theme and Language settings are available from Edit -> Settings")
        quick.setWordWrap(True)
        layout.addWidget(quick)

        # History DB path selector
        db_group = QGroupBox(parent._tr('download_history') if hasattr(parent, '_tr') else 'History DB')
        db_layout = QHBoxLayout(db_group)
        self.db_path_edit = QLineEdit()
        # Show current configured DB path if available
        cur_db = None
        try:
            cur_db = parent.settings.get('history_db') if getattr(parent, 'settings', None) else None
        except Exception:
            cur_db = None
        if not cur_db:
            try:
                cur_db = getattr(parent, 'history_db_path')
            except Exception:
                cur_db = None
        if cur_db:
            self.db_path_edit.setText(cur_db)
        browse_btn = QPushButton(parent._tr('choose_folder') if hasattr(parent, '_tr') else 'Browse...')

        def _browse():
            path, _ = QFileDialog.getSaveFileName(self, parent._tr('download_history') if hasattr(parent, '_tr') else 'History DB', cur_db or '', "SQLite DB (*.db *.sqlite);;All Files (*)")
            if path:
                self.db_path_edit.setText(path)

        browse_btn.clicked.connect(_browse)
        db_layout.addWidget(self.db_path_edit)
        db_layout.addWidget(browse_btn)
        layout.addWidget(db_group)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(parent._tr('ok'))
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn = QPushButton(parent._tr('cancel'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Set current values
        cur_lang = parent.settings.get('language', 'en') if getattr(parent, 'settings', None) else 'en'
        idx = 0 if cur_lang == 'en' else (1 if cur_lang == 'ar' else 2)
        self.lang_combo.setCurrentIndex(idx)
        if getattr(parent, 'settings', {}).get('theme', 'light') == 'dark':
            self.dark_rb.setChecked(True)
        else:
            self.light_rb.setChecked(True)

    def _on_ok(self):
        try:
            theme = 'dark' if self.dark_rb.isChecked() else 'light'
            self.parent._set_and_save_theme(theme)
            idx = self.lang_combo.currentIndex()
            lang = 'en' if idx == 0 else ('ar' if idx == 1 else 'ja')
            # Save language first
            try:
                self.parent._set_and_save_language(lang)
            except Exception:
                pass

            # Save history DB path if provided
            try:
                new_db = self.db_path_edit.text().strip()
                if new_db:
                    # Preferred: call parent's setter if exists
                    if hasattr(self.parent, '_set_and_save_history_db'):
                        try:
                            self.parent._set_and_save_history_db(new_db)
                        except Exception:
                            # fallback to storing in settings
                            self.parent.settings['history_db'] = new_db
                            self.parent._save_settings()
                    else:
                        self.parent.settings['history_db'] = new_db
                        self.parent._save_settings()
            except Exception:
                pass

            try:
                self.parent._refresh_ui_texts()
            except Exception:
                pass
            self.accept()
        except Exception:
            # Fail silently but log if parent has logging
            try:
                import logging
                logging.exception('PreferencesDialog _on_ok failed')
            except Exception:
                pass
