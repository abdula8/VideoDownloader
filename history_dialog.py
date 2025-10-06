#!/usr/bin/env python3
"""
Download History Dialog for Enhanced YouTube Downloader
"""

import os
import sqlite3
import subprocess
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QMessageBox, QHeaderView, QMenu, QAbstractItemView)

class HistoryDialog(QDialog):
    """Dialog for viewing and managing download history"""
    
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle("Download History")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self):
        """Setup the user interface"""
        main_layout = QHBoxLayout(self)
        
        # Left panel for filters and statistics
        left_panel = QtWidgets.QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)
        
        # Search/Filter section
        filter_group = QtWidgets.QGroupBox("Search & Filter")
        filter_layout = QVBoxLayout(filter_group)
        
        # Title search
        filter_layout.addWidget(QLabel("Title:"))
        self.title_filter = QtWidgets.QLineEdit()
        self.title_filter.setPlaceholderText("Search by title...")
        self.title_filter.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.title_filter)
        
        # URL search
        filter_layout.addWidget(QLabel("URL:"))
        self.url_filter = QtWidgets.QLineEdit()
        self.url_filter.setPlaceholderText("Search by URL...")
        self.url_filter.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.url_filter)
        
        # Status filter
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QtWidgets.QComboBox()
        self.status_filter.addItems(["All", "Completed", "Failed", "In Progress"])
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.status_filter)
        
        # Format filter
        filter_layout.addWidget(QLabel("Format:"))
        self.format_filter = QtWidgets.QComboBox()
        self.format_filter.addItems(["All", "Video", "Audio"])
        self.format_filter.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.format_filter)
        
        # Date range
        filter_layout.addWidget(QLabel("From:"))
        self.date_from = QtWidgets.QDateEdit()
        self.date_from.setDate(QtCore.QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel("To:"))
        self.date_to = QtWidgets.QDateEdit()
        self.date_to.setDate(QtCore.QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.date_to)
        
        # Filter buttons
        filter_btn_layout = QHBoxLayout()
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._apply_filters)
        clear_filters_btn = QPushButton("Clear Filters")
        clear_filters_btn.clicked.connect(self._clear_filters)
        filter_btn_layout.addWidget(search_btn)
        filter_btn_layout.addWidget(clear_filters_btn)
        filter_layout.addLayout(filter_btn_layout)
        
        left_layout.addWidget(filter_group)
        
        # Statistics section
        stats_group = QtWidgets.QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.total_downloads_label = QLabel("Total Downloads: 0")
        self.successful_downloads_label = QLabel("Successful: 0")
        self.failed_downloads_label = QLabel("Failed: 0")
        self.total_size_label = QLabel("Total Size: 0 B")
        self.total_duration_label = QLabel("Total Duration: 00:00:00")
        
        for label in [self.total_downloads_label, self.successful_downloads_label, 
                     self.failed_downloads_label, self.total_size_label, self.total_duration_label]:
            label.setStyleSheet("QLabel { font-weight: bold; margin: 2px; }")
            stats_layout.addWidget(label)
        
        left_layout.addWidget(stats_group)
        
        # Format breakdown
        format_group = QtWidgets.QGroupBox("Format Breakdown")
        format_layout = QVBoxLayout(format_group)
        
        self.format_table = QtWidgets.QTableWidget()
        self.format_table.setColumnCount(3)
        self.format_table.setHorizontalHeaderLabels(["Format", "Count", "Size"])
        self.format_table.horizontalHeader().setStretchLastSection(True)
        self.format_table.setMaximumHeight(150)
        format_layout.addWidget(self.format_table)
        
        left_layout.addWidget(format_group)
        
        # Action buttons
        button_group = QtWidgets.QGroupBox("Actions")
        button_layout = QVBoxLayout(button_group)
        
        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self._export_csv)
        export_csv_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        button_layout.addWidget(export_csv_btn)
        
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self._clear_history)
        clear_history_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        button_layout.addWidget(clear_history_btn)
        
        left_layout.addWidget(button_group)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # Right panel for table
        right_panel = QtWidgets.QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Header for right panel
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Download History")
        title_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        header_layout.addWidget(title_label)
        
        self.found_label = QLabel("Found 0 downloads")
        header_layout.addWidget(self.found_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_history)
        header_layout.addWidget(refresh_btn)
        
        right_layout.addLayout(header_layout)
        
        # History table
        self.history_table = QTableWidget()
        # There are 9 columns: Title, URL, Format, Quality, Status, File Size, Duration, Download Date, Platform
        self.history_table.setColumnCount(9)
        self.history_table.setHorizontalHeaderLabels([
            "Title", "URL", "Format", "Quality", "Status", "File Size", "Duration", "Download Date", "Platform"
        ])
        
        # Configure table
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Title column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self._show_context_menu)
        
        right_layout.addWidget(self.history_table)
        
        # Status label
        self.status_label = QLabel("Loading history...")
        right_layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        redownload_btn = QPushButton("Re-download Selected")
        redownload_btn.clicked.connect(self._redownload_selected)
        button_layout.addWidget(redownload_btn)
        
        open_location_btn = QPushButton("Open File Location")
        open_location_btn.clicked.connect(self._open_file_location)
        button_layout.addWidget(open_location_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        right_layout.addLayout(button_layout)
        
        main_layout.addWidget(right_panel)
        
        # Store all history data for filtering
        self.all_history_data = []
    
    def _load_history(self):
        """Load download history from database"""
        try:
            if not os.path.exists(self.db_path):
                self.status_label.setText("No history database found.")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, url, title, format, quality, status, download_date, 
                       file_size, duration, platform, file_path
                FROM downloads 
                ORDER BY download_date DESC 
                LIMIT 1000
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # Store all data for filtering
            self.all_history_data = []
            
            for row in rows:
                (id_, url, title, format_, quality, status, download_date, 
                 file_size, duration, platform, file_path) = row
                
                # Format date for storage
                formatted_date = download_date or ""
                if download_date:
                    try:
                        # Handle different date formats
                        if isinstance(download_date, str):
                            formatted_date = download_date
                        else:
                            formatted_date = str(download_date)
                    except:
                        formatted_date = download_date or ""
                
                item_data = {
                    'id': id_,
                    'url': url or '',
                    'title': title or 'Unknown Title',
                    'format': format_ or 'Unknown',
                    'quality': quality or 'Unknown',
                    'file_path': file_path or '',
                    'file_size': file_size or 0,
                    'duration': duration or 0,
                    'status': status or 'Unknown',
                    'platform': platform or 'Unknown',
                    'download_date': formatted_date
                }
                
                self.all_history_data.append(item_data)
            
            # Populate table with all data initially
            self._populate_table(self.all_history_data)
            self.status_label.setText(f"Showing {len(rows)} download(s)")
            
        except Exception as e:
            self.status_label.setText(f"Error loading history: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load history:\n{e}")
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _format_duration(self, duration_seconds):
        """Format duration in HH:MM:SS format"""
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _show_context_menu(self, position):
        """Show context menu for table items"""
        item = self.history_table.itemAt(position)
        if item is None:
            return
        
        menu = QMenu(self)
        
        redownload_action = menu.addAction("Re-download")
        redownload_action.triggered.connect(self._redownload_selected)
        
        open_location_action = menu.addAction("Open File Location")
        open_location_action.triggered.connect(self._open_file_location)
        
        menu.addSeparator()
        
        copy_url_action = menu.addAction("Copy URL")
        copy_url_action.triggered.connect(self._copy_url)
        
        delete_action = menu.addAction("Delete from History")
        delete_action.triggered.connect(self._delete_selected)
        
        menu.exec_(self.history_table.mapToGlobal(position))
    
    def _redownload_selected(self):
        """Re-download selected items"""
        selected_rows = set()
        for item in self.history_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select items to re-download.")
            return
        
        urls = []
        for row in selected_rows:
            title_item = self.history_table.item(row, 0)
            if title_item:
                data = title_item.data(QtCore.Qt.UserRole)
                if data and data.get('url'):
                    urls.append(data['url'])
        
        if urls:
            QMessageBox.information(
                self, 
                "Re-download", 
                f"Selected {len(urls)} item(s) for re-download.\n\n"
                "The URLs will be added to the main download queue."
            )
            # Here you would signal the main window to add these URLs
            # For now, just show the URLs
            url_text = '\n'.join(urls)
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(url_text)
            QMessageBox.information(self, "URLs Copied", "URLs have been copied to clipboard.")
    
    def _open_file_location(self):
        """Open file location in explorer"""
        selected_rows = set()
        for item in self.history_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select an item to open its location.")
            return
        
        row = list(selected_rows)[0]  # Take first selected row
        title_item = self.history_table.item(row, 0)
        
        if title_item:
            data = title_item.data(QtCore.Qt.UserRole)
            if data and data.get('file_path'):
                file_path = data['file_path']
                if os.path.exists(file_path):
                    try:
                        if os.name == 'nt':  # Windows
                            subprocess.run(['explorer', '/select,', file_path])
                        elif os.name == 'posix':  # macOS/Linux
                            if 'darwin' in os.sys.platform:  # macOS
                                subprocess.run(['open', '-R', file_path])
                            else:  # Linux
                                subprocess.run(['xdg-open', os.path.dirname(file_path)])
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Could not open file location:\n{e}")
                else:
                    QMessageBox.warning(self, "File Not Found", "The downloaded file no longer exists.")
            else:
                QMessageBox.warning(self, "No File Path", "No file path information available.")
    
    def _copy_url(self):
        """Copy URL to clipboard"""
        selected_rows = set()
        for item in self.history_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            return
        
        row = list(selected_rows)[0]
        title_item = self.history_table.item(row, 0)
        
        if title_item:
            data = title_item.data(QtCore.Qt.UserRole)
            if data and data.get('url'):
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setText(data['url'])
                self.status_label.setText("URL copied to clipboard")
    
    def _delete_selected(self):
        """Delete selected items from history"""
        selected_rows = set()
        for item in self.history_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select items to delete.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected_rows)} item(s) from history?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for row in selected_rows:
                    title_item = self.history_table.item(row, 0)
                    if title_item:
                        data = title_item.data(QtCore.Qt.UserRole)
                        if data and data.get('id'):
                            cursor.execute('DELETE FROM downloads WHERE id = ?', (data['id'],))
                
                conn.commit()
                conn.close()
                
                self._load_history()  # Refresh the table
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete items:\n{e}")
    
    def _clear_history(self):
        """Clear all download history"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear History",
            "Are you sure you want to clear all download history?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM downloads')
                conn.commit()
                conn.close()
                
                self._load_history()  # Refresh the table
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to clear history:\n{e}")

    def _apply_filters(self):
        """Apply search and filter criteria"""
        try:
            title_filter = self.title_filter.text().lower()
            url_filter = self.url_filter.text().lower()
            status_filter = self.status_filter.currentText()
            format_filter = self.format_filter.currentText()
            date_from = self.date_from.date().toPyDate()
            date_to = self.date_to.date().toPyDate()
            
            filtered_data = []
            
            for item in self.all_history_data:
                # Apply filters
                if title_filter and title_filter not in item.get('title', '').lower():
                    continue
                if url_filter and url_filter not in item.get('url', '').lower():
                    continue
                if status_filter != "All" and item.get('status', '').lower() != status_filter.lower():
                    continue
                if format_filter != "All" and item.get('format', '').lower() != format_filter.lower():
                    continue
                
                # Date filter
                try:
                    item_date = datetime.strptime(item.get('download_date', ''), '%Y-%m-%d %H:%M:%S').date()
                    if item_date < date_from or item_date > date_to:
                        continue
                except:
                    pass  # Skip date filtering if parsing fails
                
                filtered_data.append(item)
            
            self._populate_table(filtered_data)
            self.found_label.setText(f"Found {len(filtered_data)} downloads")
            
        except Exception as e:
            print(f"Filter error: {e}")
    
    def _clear_filters(self):
        """Clear all filters"""
        self.title_filter.clear()
        self.url_filter.clear()
        self.status_filter.setCurrentText("All")
        self.format_filter.setCurrentText("All")
        self.date_from.setDate(QtCore.QDate.currentDate().addDays(-30))
        self.date_to.setDate(QtCore.QDate.currentDate())
        self._apply_filters()
    
    def _export_csv(self):
        """Export history to CSV file"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export History", "download_history.csv", "CSV Files (*.csv)"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow([
                        "Title", "URL", "Format", "Quality", "Status", 
                        "File Size", "Duration", "Download Date", "Platform"
                    ])
                    
                    # Write data
                    for item in self.all_history_data:
                        writer.writerow([
                            item.get('title', ''),
                            item.get('url', ''),
                            item.get('format', ''),
                            item.get('quality', ''),
                            item.get('status', ''),
                            item.get('file_size', 0),
                            item.get('duration', 0),
                            item.get('download_date', ''),
                            item.get('platform', '')
                        ])
                
                QMessageBox.information(self, "Export Complete", f"History exported to {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export history:\n{str(e)}")

    def _populate_table(self, data: list):
        """Populate the main history table from a list of record dicts.

        Each record is expected to be a dict with keys: id, url, title, format, quality, status,
        download_date, file_size, duration, platform, file_path
        """
        try:
            # Normalize
            rows = data or []

            # Clear existing table
            self.history_table.setRowCount(0)

            for i, item in enumerate(rows):
                self.history_table.insertRow(i)
                cols = [
                    item.get('title', ''),
                    item.get('url', ''),
                    item.get('format', ''),
                    item.get('quality', ''),
                    item.get('status', ''),
                    self._format_file_size(int(item.get('file_size', 0) or 0)),
                    self._format_duration(int(item.get('duration', 0) or 0)),
                    item.get('download_date', ''),
                    item.get('platform', ''),
                ]

                for j, val in enumerate(cols):
                    twi = QTableWidgetItem(str(val))
                    # Attach the full item dict to the title column for context menu actions
                    if j == 0:
                        twi.setData(QtCore.Qt.UserRole, item)
                    self.history_table.setItem(i, j, twi)

            # Update summary labels based on all_history_data (not filtered subset)
            total = len(self.all_history_data)
            successful = sum(1 for it in self.all_history_data if str(it.get('status', '')).lower() in ('completed', 'success'))
            failed = sum(1 for it in self.all_history_data if str(it.get('status', '')).lower() == 'failed')
            total_size = sum(int(it.get('file_size', 0) or 0) for it in self.all_history_data)
            total_duration = sum(int(it.get('duration', 0) or 0) for it in self.all_history_data)

            self.total_downloads_label.setText(f"Total Downloads: {total}")
            self.successful_downloads_label.setText(f"Successful: {successful}")
            self.failed_downloads_label.setText(f"Failed: {failed}")
            self.total_size_label.setText(f"Total Size: {self._format_file_size(total_size)}")
            self.total_duration_label.setText(f"Total Duration: {self._format_duration(total_duration)}")

            # Populate format breakdown
            self.format_table.setRowCount(0)
            format_counts = {}
            for it in self.all_history_data:
                fmt = it.get('format') or 'Unknown'
                entry = format_counts.setdefault(fmt, {'count': 0, 'size': 0})
                entry['count'] += 1
                try:
                    entry['size'] += int(it.get('file_size', 0) or 0)
                except Exception:
                    pass

            for r, (fmt, info) in enumerate(sorted(format_counts.items(), key=lambda x: x[0])):
                self.format_table.insertRow(r)
                self.format_table.setItem(r, 0, QTableWidgetItem(str(fmt)))
                self.format_table.setItem(r, 1, QTableWidgetItem(str(info['count'])))
                self.format_table.setItem(r, 2, QTableWidgetItem(self._format_file_size(info['size'])))

            # Update found label
            self.found_label.setText(f"Found {len(rows)} downloads")

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to populate table:\n{e}")

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create a test database
    test_db = "test_history.db"
    dialog = HistoryDialog(test_db)
    dialog.show()
    
    sys.exit(app.exec_())