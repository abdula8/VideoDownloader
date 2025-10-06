#!/usr/bin/env python3
"""
Enhanced Video Converter Tool for Enhanced YouTube Downloader
Supports both basic and advanced conversion options
"""

import os
import subprocess
import threading
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QComboBox, QGroupBox,
                            QFormLayout, QFileDialog, QMessageBox, QProgressBar,
                            QTextEdit, QListWidget, QListWidgetItem, QTabWidget,
                            QWidget, QCheckBox, QSpinBox, QSlider, QFrame)

class AdvancedConverterWorker(QtCore.QThread):
    """Enhanced worker thread for video conversion with advanced options"""
    
    progress_updated = QtCore.pyqtSignal(str, int)  # message, percentage
    conversion_completed = QtCore.pyqtSignal(str, str)  # input_file, output_file
    conversion_failed = QtCore.pyqtSignal(str, str)  # input_file, error
    
    def __init__(self, input_files, conversion_settings):
        super().__init__()
        self.input_files = input_files
        self.conversion_settings = conversion_settings
        self.is_cancelled = False
    
    def run(self):
        """Run the conversion process"""
        total_files = len(self.input_files)
        
        for i, input_file in enumerate(self.input_files, 1):
            if self.is_cancelled:
                break
            
            try:
                file_progress = int((i - 1) / total_files * 100)
                self.progress_updated.emit(
                    f"Converting {i}/{total_files}: {os.path.basename(input_file)}", 
                    file_progress
                )
                
                # Generate output filename
                base_name = os.path.splitext(os.path.basename(input_file))[0]
                output_format = self.conversion_settings['output_format']
                output_dir = self.conversion_settings['output_dir']
                output_file = os.path.join(output_dir, f"{base_name}.{output_format}")
                
                # Build FFmpeg command
                cmd = self._build_ffmpeg_command(input_file, output_file)
                
                # Run conversion
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                if result.returncode == 0:
                    self.conversion_completed.emit(input_file, output_file)
                else:
                    error_msg = result.stderr or "Unknown error"
                    self.conversion_failed.emit(input_file, error_msg)
                    
            except Exception as e:
                self.conversion_failed.emit(input_file, str(e))
        
        final_progress = 100 if not self.is_cancelled else 0
        self.progress_updated.emit("Conversion process completed", final_progress)
    
    def _build_ffmpeg_command(self, input_file, output_file):
        """Build advanced FFmpeg command based on settings"""
        settings = self.conversion_settings
        cmd = ['ffmpeg', '-i', input_file, '-y']  # -y to overwrite existing files
        
        output_format = settings['output_format']
        
        # Video settings
        if output_format in ['mp4', 'avi', 'mkv', 'webm', 'mov']:
            # Video codec
            if settings.get('video_codec') == 'h264':
                cmd.extend(['-codec:v', 'libx264'])
            elif settings.get('video_codec') == 'h265':
                cmd.extend(['-codec:v', 'libx265'])
            elif settings.get('video_codec') == 'vp9':
                cmd.extend(['-codec:v', 'libvpx-vp9'])
            elif settings.get('video_codec') == 'copy':
                cmd.extend(['-codec:v', 'copy'])
            
            # Video bitrate
            if settings.get('video_bitrate') and settings.get('video_codec') != 'copy':
                cmd.extend(['-b:v', f"{settings['video_bitrate']}k"])
            
            # Resolution
            if settings.get('resolution') and settings.get('video_codec') != 'copy':
                cmd.extend(['-vf', f"scale={settings['resolution']}"])
            
            # Frame rate
            if settings.get('framerate') and settings.get('video_codec') != 'copy':
                cmd.extend(['-r', str(settings['framerate'])])
            
            # Audio codec for video files
            if settings.get('audio_codec') == 'aac':
                cmd.extend(['-codec:a', 'aac'])
            elif settings.get('audio_codec') == 'mp3':
                cmd.extend(['-codec:a', 'libmp3lame'])
            elif settings.get('audio_codec') == 'copy':
                cmd.extend(['-codec:a', 'copy'])
            
            # Audio bitrate
            if settings.get('audio_bitrate') and settings.get('audio_codec') != 'copy':
                cmd.extend(['-b:a', f"{settings['audio_bitrate']}k"])
        
        # Audio-only settings
        elif output_format in ['mp3', 'wav', 'm4a', 'aac', 'ogg']:
            cmd.extend(['-vn'])  # No video
            
            if output_format == 'mp3':
                cmd.extend(['-codec:a', 'libmp3lame'])
                if settings.get('audio_bitrate'):
                    cmd.extend(['-b:a', f"{settings['audio_bitrate']}k"])
            elif output_format == 'wav':
                cmd.extend(['-codec:a', 'pcm_s16le'])
            elif output_format == 'm4a':
                cmd.extend(['-codec:a', 'aac'])
                if settings.get('audio_bitrate'):
                    cmd.extend(['-b:a', f"{settings['audio_bitrate']}k"])
            elif output_format == 'aac':
                cmd.extend(['-codec:a', 'aac'])
                if settings.get('audio_bitrate'):
                    cmd.extend(['-b:a', f"{settings['audio_bitrate']}k"])
            elif output_format == 'ogg':
                cmd.extend(['-codec:a', 'libvorbis'])
                if settings.get('audio_bitrate'):
                    cmd.extend(['-b:a', f"{settings['audio_bitrate']}k"])
            
            # Audio sample rate
            if settings.get('sample_rate'):
                cmd.extend(['-ar', str(settings['sample_rate'])])
        
        # Quality preset
        if settings.get('quality_preset') and settings.get('video_codec') in ['h264', 'h265']:
            cmd.extend(['-preset', settings['quality_preset']])
        
        # CRF (Constant Rate Factor) for quality
        if settings.get('crf') and settings.get('video_codec') in ['h264', 'h265']:
            cmd.extend(['-crf', str(settings['crf'])])
        
        cmd.append(output_file)
        return cmd
    
    def cancel(self):
        """Cancel the conversion process"""
        self.is_cancelled = True

class BasicConverterDialog(QDialog):
    """Basic converter dialog with simple options"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Basic Video Converter")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)
        
        self.worker = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the basic converter UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Simple video conversion tool. Select files and choose output format."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
        layout.addWidget(instructions)
        
        # Input files section
        input_group = QGroupBox("Input Files")
        input_layout = QVBoxLayout(input_group)
        
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(120)
        input_layout.addWidget(self.file_list)
        
        # File buttons
        file_buttons = QHBoxLayout()
        
        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self._add_files)
        file_buttons.addWidget(add_files_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.file_list.clear)
        file_buttons.addWidget(clear_btn)
        
        file_buttons.addStretch()
        input_layout.addLayout(file_buttons)
        
        layout.addWidget(input_group)
        
        # Output settings section
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout(output_group)
        
        # Output format
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            'mp4', 'avi', 'mkv', 'webm', 'mov',  # Video formats
            'mp3', 'wav', 'm4a', 'aac'           # Audio formats
        ])
        output_layout.addRow("Output Format:", self.format_combo)
        
        # Quality preset
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['High Quality', 'Medium Quality', 'Low Quality', 'Custom'])
        output_layout.addRow("Quality:", self.quality_combo)
        
        # Output directory
        dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(os.path.expanduser("~/Desktop"))
        dir_layout.addWidget(self.output_dir_edit)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(browse_btn)
        
        output_layout.addRow("Output Directory:", dir_layout)
        
        layout.addWidget(output_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_label = QLabel("Ready to convert")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.convert_btn = QPushButton("Start Conversion")
        self.convert_btn.clicked.connect(self._start_conversion)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.convert_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_conversion)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _add_files(self):
        """Add files to conversion list"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video/Audio Files",
            "",
            "Media Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mp3 *.wav *.m4a *.aac *.ogg);;All Files (*)"
        )
        
        for file_path in files:
            if file_path not in [self.file_list.item(i).text() for i in range(self.file_list.count())]:
                self.file_list.addItem(file_path)
    
    def _browse_output_dir(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory", 
            self.output_dir_edit.text()
        )
        if directory:
            self.output_dir_edit.setText(directory)
    
    def _start_conversion(self):
        """Start the basic conversion process"""
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "No Files", "Please add files to convert.")
            return
        
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir or not os.path.exists(output_dir):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid output directory.")
            return
        
        # Check if FFmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            QMessageBox.critical(
                self, 
                "FFmpeg Not Found", 
                "FFmpeg is required for conversion but was not found.\n\n"
                "Please install FFmpeg and make sure it's in your system PATH."
            )
            return
        
        # Get input files
        input_files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        
        # Build basic conversion settings
        settings = {
            'output_format': self.format_combo.currentText(),
            'output_dir': output_dir,
            'quality_preset': self._get_quality_preset()
        }
        
        # Add basic quality settings based on preset
        quality = self.quality_combo.currentText()
        if quality == 'High Quality':
            if settings['output_format'] in ['mp4', 'avi', 'mkv', 'webm', 'mov']:
                settings.update({
                    'video_codec': 'h264',
                    'video_bitrate': 5000,
                    'audio_codec': 'aac',
                    'audio_bitrate': 192
                })
            else:
                settings.update({
                    'audio_bitrate': 320
                })
        elif quality == 'Medium Quality':
            if settings['output_format'] in ['mp4', 'avi', 'mkv', 'webm', 'mov']:
                settings.update({
                    'video_codec': 'h264',
                    'video_bitrate': 2500,
                    'audio_codec': 'aac',
                    'audio_bitrate': 128
                })
            else:
                settings.update({
                    'audio_bitrate': 192
                })
        elif quality == 'Low Quality':
            if settings['output_format'] in ['mp4', 'avi', 'mkv', 'webm', 'mov']:
                settings.update({
                    'video_codec': 'h264',
                    'video_bitrate': 1000,
                    'audio_codec': 'aac',
                    'audio_bitrate': 96
                })
            else:
                settings.update({
                    'audio_bitrate': 128
                })
        
        # Start conversion
        self.worker = AdvancedConverterWorker(input_files, settings)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.conversion_completed.connect(self._on_conversion_completed)
        self.worker.conversion_failed.connect(self._on_conversion_failed)
        self.worker.finished.connect(self._on_worker_finished)
        
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        
        self.worker.start()
    
    def _get_quality_preset(self):
        """Get FFmpeg quality preset"""
        quality = self.quality_combo.currentText()
        if quality == 'High Quality':
            return 'slow'
        elif quality == 'Medium Quality':
            return 'medium'
        elif quality == 'Low Quality':
            return 'fast'
        else:
            return 'medium'
    
    def _cancel_conversion(self):
        """Cancel the conversion process"""
        if self.worker:
            self.worker.cancel()
            self.worker.quit()
            self.worker.wait()
        
        self._on_worker_finished()
    
    def _on_progress_updated(self, message, percentage):
        """Handle progress updates"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(percentage)
    
    def _on_conversion_completed(self, input_file, output_file):
        """Handle successful conversion"""
        pass  # Progress is handled by progress_updated
    
    def _on_conversion_failed(self, input_file, error):
        """Handle conversion failure"""
        QMessageBox.warning(self, "Conversion Error", f"Failed to convert {os.path.basename(input_file)}:\n{error}")
    
    def _on_worker_finished(self):
        """Handle worker completion"""
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText("Conversion completed")
        self.worker = None

class AdvancedConverterDialog(QDialog):
    """Advanced converter dialog with detailed options"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Video Converter & Audio Extractor")
        self.setMinimumSize(800, 700)
        self.resize(900, 800)
        
        self.worker = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the advanced converter UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Advanced video conversion tool with detailed codec and quality options.\n"
            "Configure all aspects of video and audio encoding for professional results."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
        layout.addWidget(instructions)
        
        # Create tab widget for organized settings
        self.tab_widget = QTabWidget()
        
        # Input/Output tab
        self.io_tab = self._create_io_tab()
        self.tab_widget.addTab(self.io_tab, "Input/Output")
        
        # Video settings tab
        self.video_tab = self._create_video_tab()
        self.tab_widget.addTab(self.video_tab, "Video Settings")
        
        # Audio settings tab
        self.audio_tab = self._create_audio_tab()
        self.tab_widget.addTab(self.audio_tab, "Audio Settings")
        
        # Advanced tab
        self.advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "Advanced")
        
        layout.addWidget(self.tab_widget)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_label = QLabel("Ready to convert")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        # Log area
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(80)
        self.log_text.setReadOnly(True)
        progress_layout.addWidget(self.log_text)
        
        layout.addWidget(progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.convert_btn = QPushButton("Start Advanced Conversion")
        self.convert_btn.clicked.connect(self._start_conversion)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(self.convert_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_conversion)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_io_tab(self):
        """Create input/output tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Input files section
        input_group = QGroupBox("Input Files")
        input_layout = QVBoxLayout(input_group)
        
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(150)
        input_layout.addWidget(self.file_list)
        
        # File buttons
        file_buttons = QHBoxLayout()
        
        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self._add_files)
        file_buttons.addWidget(add_files_btn)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        file_buttons.addWidget(add_folder_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        file_buttons.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.file_list.clear)
        file_buttons.addWidget(clear_btn)
        
        file_buttons.addStretch()
        input_layout.addLayout(file_buttons)
        
        layout.addWidget(input_group)
        
        # Output settings section
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout(output_group)
        
        # Output format
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            'mp4', 'avi', 'mkv', 'webm', 'mov', 'flv',  # Video formats
            'mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac'   # Audio formats
        ])
        output_layout.addRow("Output Format:", self.format_combo)
        
        # Output directory
        dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(os.path.expanduser("~/Desktop"))
        dir_layout.addWidget(self.output_dir_edit)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(browse_btn)
        
        output_layout.addRow("Output Directory:", dir_layout)
        
        layout.addWidget(output_group)
        
        return tab
    
    def _create_video_tab(self):
        """Create video settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Video codec section
        codec_group = QGroupBox("Video Codec Settings")
        codec_layout = QFormLayout(codec_group)
        
        self.video_codec_combo = QComboBox()
        self.video_codec_combo.addItems(['h264', 'h265', 'vp9', 'copy'])
        codec_layout.addRow("Video Codec:", self.video_codec_combo)
        
        # Video bitrate
        self.video_bitrate_spin = QSpinBox()
        self.video_bitrate_spin.setRange(100, 50000)
        self.video_bitrate_spin.setValue(2500)
        self.video_bitrate_spin.setSuffix(" kbps")
        codec_layout.addRow("Video Bitrate:", self.video_bitrate_spin)
        
        # CRF (Constant Rate Factor)
        self.crf_spin = QSpinBox()
        self.crf_spin.setRange(0, 51)
        self.crf_spin.setValue(23)
        codec_layout.addRow("CRF (Quality):", self.crf_spin)
        
        # Quality preset
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'])
        self.preset_combo.setCurrentText('medium')
        codec_layout.addRow("Encoding Preset:", self.preset_combo)
        
        layout.addWidget(codec_group)
        
        # Video properties section
        props_group = QGroupBox("Video Properties")
        props_layout = QFormLayout(props_group)
        
        # Resolution
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['Original', '1920x1080', '1280x720', '854x480', '640x360', 'Custom'])
        props_layout.addRow("Resolution:", self.resolution_combo)
        
        # Custom resolution
        res_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 7680)
        self.width_spin.setValue(1920)
        res_layout.addWidget(self.width_spin)
        
        res_layout.addWidget(QLabel("x"))
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 4320)
        self.height_spin.setValue(1080)
        res_layout.addWidget(self.height_spin)
        
        res_layout.addStretch()
        props_layout.addRow("Custom Resolution:", res_layout)
        
        # Frame rate
        self.framerate_spin = QSpinBox()
        self.framerate_spin.setRange(1, 120)
        self.framerate_spin.setValue(30)
        props_layout.addRow("Frame Rate:", self.framerate_spin)
        
        layout.addWidget(props_group)
        
        layout.addStretch()
        return tab
    
    def _create_audio_tab(self):
        """Create audio settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Audio codec section
        codec_group = QGroupBox("Audio Codec Settings")
        codec_layout = QFormLayout(codec_group)
        
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(['aac', 'mp3', 'vorbis', 'copy'])
        codec_layout.addRow("Audio Codec:", self.audio_codec_combo)
        
        # Audio bitrate
        self.audio_bitrate_spin = QSpinBox()
        self.audio_bitrate_spin.setRange(32, 512)
        self.audio_bitrate_spin.setValue(192)
        self.audio_bitrate_spin.setSuffix(" kbps")
        codec_layout.addRow("Audio Bitrate:", self.audio_bitrate_spin)
        
        # Sample rate
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(['Original', '48000', '44100', '32000', '22050', '16000'])
        codec_layout.addRow("Sample Rate:", self.sample_rate_combo)
        
        # Channels
        self.channels_combo = QComboBox()
        self.channels_combo.addItems(['Original', 'Stereo (2)', 'Mono (1)', '5.1 (6)'])
        codec_layout.addRow("Channels:", self.channels_combo)
        
        layout.addWidget(codec_group)
        
        # Audio filters section
        filters_group = QGroupBox("Audio Filters")
        filters_layout = QVBoxLayout(filters_group)
        
        # Volume adjustment
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        
        self.volume_slider = QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(100)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("100%")
        self.volume_slider.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        volume_layout.addWidget(self.volume_label)
        
        filters_layout.addLayout(volume_layout)
        
        # Normalize audio
        self.normalize_check = QCheckBox("Normalize Audio")
        filters_layout.addWidget(self.normalize_check)
        
        layout.addWidget(filters_group)
        
        layout.addStretch()
        return tab
    
    def _create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Advanced options section
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Two-pass encoding
        self.two_pass_check = QCheckBox("Two-pass encoding (better quality)")
        advanced_layout.addWidget(self.two_pass_check)
        
        # Hardware acceleration
        self.hw_accel_check = QCheckBox("Hardware acceleration (if available)")
        advanced_layout.addWidget(self.hw_accel_check)
        
        # Custom FFmpeg options
        custom_layout = QFormLayout()
        self.custom_options_edit = QLineEdit()
        self.custom_options_edit.setPlaceholderText("e.g., -tune film -profile:v high")
        custom_layout.addRow("Custom FFmpeg Options:", self.custom_options_edit)
        
        advanced_layout.addLayout(custom_layout)
        
        layout.addWidget(advanced_group)
        
        # Batch processing section
        batch_group = QGroupBox("Batch Processing")
        batch_layout = QFormLayout(batch_group)
        
        # Thread count
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 16)
        self.threads_spin.setValue(4)
        batch_layout.addRow("Processing Threads:", self.threads_spin)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['Low', 'Normal', 'High'])
        self.priority_combo.setCurrentText('Normal')
        batch_layout.addRow("Process Priority:", self.priority_combo)
        
        layout.addWidget(batch_group)
        
        layout.addStretch()
        return tab
    
    def _add_files(self):
        """Add files to conversion list"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video/Audio Files",
            "",
            "Media Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mp3 *.wav *.m4a *.aac *.ogg *.flac);;All Files (*)"
        )
        
        for file_path in files:
            if file_path not in [self.file_list.item(i).text() for i in range(self.file_list.count())]:
                self.file_list.addItem(file_path)
    
    def _add_folder(self):
        """Add all media files from a folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            media_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
                              '.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in media_extensions):
                        file_path = os.path.join(root, file)
                        if file_path not in [self.file_list.item(i).text() for i in range(self.file_list.count())]:
                            self.file_list.addItem(file_path)
    
    def _remove_selected(self):
        """Remove selected files from the list"""
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
    
    def _browse_output_dir(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory", 
            self.output_dir_edit.text()
        )
        if directory:
            self.output_dir_edit.setText(directory)
    
    def _start_conversion(self):
        """Start the advanced conversion process"""
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "No Files", "Please add files to convert.")
            return
        
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir or not os.path.exists(output_dir):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid output directory.")
            return
        
        # Check if FFmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            QMessageBox.critical(
                self, 
                "FFmpeg Not Found", 
                "FFmpeg is required for conversion but was not found.\n\n"
                "Please install FFmpeg and make sure it's in your system PATH."
            )
            return
        
        # Get input files
        input_files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        
        # Build advanced conversion settings
        settings = {
            'output_format': self.format_combo.currentText(),
            'output_dir': output_dir,
            'video_codec': self.video_codec_combo.currentText(),
            'video_bitrate': self.video_bitrate_spin.value(),
            'crf': self.crf_spin.value(),
            'quality_preset': self.preset_combo.currentText(),
            'audio_codec': self.audio_codec_combo.currentText(),
            'audio_bitrate': self.audio_bitrate_spin.value(),
        }
        
        # Resolution settings
        if self.resolution_combo.currentText() != 'Original':
            if self.resolution_combo.currentText() == 'Custom':
                settings['resolution'] = f"{self.width_spin.value()}x{self.height_spin.value()}"
            else:
                settings['resolution'] = self.resolution_combo.currentText()
        
        # Frame rate
        settings['framerate'] = self.framerate_spin.value()
        
        # Sample rate
        if self.sample_rate_combo.currentText() != 'Original':
            settings['sample_rate'] = int(self.sample_rate_combo.currentText())
        
        # Advanced options
        if self.two_pass_check.isChecked():
            settings['two_pass'] = True
        
        if self.hw_accel_check.isChecked():
            settings['hw_accel'] = True
        
        if self.custom_options_edit.text().strip():
            settings['custom_options'] = self.custom_options_edit.text().strip()
        
        # Confirm conversion
        reply = QMessageBox.question(
            self,
            "Confirm Advanced Conversion",
            f"Convert {len(input_files)} file(s) with advanced settings?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Start conversion
            self.worker = AdvancedConverterWorker(input_files, settings)
            self.worker.progress_updated.connect(self._on_progress_updated)
            self.worker.conversion_completed.connect(self._on_conversion_completed)
            self.worker.conversion_failed.connect(self._on_conversion_failed)
            self.worker.finished.connect(self._on_worker_finished)
            
            self.convert_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.progress_bar.setValue(0)
            
            self.log_text.clear()
            self.worker.start()
    
    def _cancel_conversion(self):
        """Cancel the conversion process"""
        if self.worker:
            self.worker.cancel()
            self.worker.quit()
            self.worker.wait()
        
        self._on_worker_finished()
    
    def _on_progress_updated(self, message, percentage):
        """Handle progress updates"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(percentage)
    
    def _on_conversion_completed(self, input_file, output_file):
        """Handle successful conversion"""
        message = f"✓ Converted: {os.path.basename(input_file)} → {os.path.basename(output_file)}"
        self.log_text.append(message)
    
    def _on_conversion_failed(self, input_file, error):
        """Handle conversion failure"""
        message = f"✗ Failed: {os.path.basename(input_file)} - {error}"
        self.log_text.append(message)
    
    def _on_worker_finished(self):
        """Handle worker completion"""
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText("Conversion completed")
        self.worker = None

# For backward compatibility, keep the original ConverterDialog as BasicConverterDialog
ConverterDialog = BasicConverterDialog

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Test both dialogs
    basic_dialog = BasicConverterDialog()
    basic_dialog.show()
    
    advanced_dialog = AdvancedConverterDialog()
    advanced_dialog.show()
    
    sys.exit(app.exec_())
