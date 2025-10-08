import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QLabel, QStackedWidget)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont
import subprocess

from converter_tool import BasicConverterDialog, AdvancedConverterDialog
from main_V3 import YouTubeDownloader

class ConverterWindow(QWidget):
    def __init__(self, parent, main_window):
        super().__init__()
        self.parent = parent  # Reference to parent (QStackedWidget)
        self.main_window = main_window  # Reference to MainWindow instance
        
        # Layout for converter window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Title
        title_label = QLabel("Converter Options")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Choose your conversion mode")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #bbbbbb; font-size: 14px;")
        layout.addWidget(subtitle_label)
        
        # Debug label to verify loading
        debug_label = QLabel("Window loaded successfully")
        debug_label.setAlignment(Qt.AlignCenter)
        debug_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(debug_label)
        
        # Spacer
        layout.addStretch()
        
        # Buttons container
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(20)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # Basic Converter button
        self.basic_button = QPushButton("🛠 Basic Converter")
        self.basic_button.setFixedSize(300, 60)
        self.main_window.style_button(self.basic_button, "#4CAF50", "#45a049")
        self.basic_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.basic_button.setFocusPolicy(Qt.StrongFocus)
        self.basic_button.clicked.connect(self.run_basic_converter)
        buttons_layout.addWidget(self.basic_button, alignment=Qt.AlignCenter)
        print("Basic button initialized")
        
        # Advanced Converter button
        self.advanced_button = QPushButton("🔧 Advanced Converter")
        self.advanced_button.setFixedSize(300, 60)
        self.main_window.style_button(self.advanced_button, "#2196F3", "#1976D2")
        self.advanced_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.advanced_button.setFocusPolicy(Qt.StrongFocus)
        self.advanced_button.clicked.connect(self.run_advanced_converter)
        buttons_layout.addWidget(self.advanced_button, alignment=Qt.AlignCenter)
        print("Advanced button initialized")
        
        # Back button
        self.back_button = QPushButton("⬅ Back")
        self.back_button.setFixedSize(100, 40)
        self.back_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #888888, stop:1 #666666);
                border: 2px solid #555555;
                border-radius: 8px;
                color: white;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #999999, stop:1 #777777);
                border: 2px solid #666666;
            }
            QPushButton:pressed {
                background-color: #777777;
                border: 2px solid #444444;
            }
        """)
        self.back_button.setFocusPolicy(Qt.StrongFocus)
        self.back_button.clicked.connect(self.go_back)
        buttons_layout.addWidget(self.back_button, alignment=Qt.AlignCenter)
        print("Back button initialized")
        
        # Center buttons
        layout.addWidget(buttons_container, alignment=Qt.AlignCenter)
        
        # Spacer
        layout.addStretch()
        
        # Status label
        status_label = QLabel("Select a conversion tool")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(status_label)

    def run_basic_converter(self):
        print("Basic Converter button clicked")
        try:
            dialog = BasicConverterDialog(self)
            dialog.show()
            print("Basic Converter Dialog shown")
        except Exception as e:
            print(f"Error running basic converter: {e}")

    def run_advanced_converter(self):
        print("Advanced Converter button clicked")
        try:
            dialog = AdvancedConverterDialog(self)
            dialog.show()
            print("Advanced Converter Dialog shown")
        except Exception as e:
            print(f"Error running advanced converter: {e}")

    def go_back(self):
        print("Back button clicked")
        # Immediate switch attempt
        print(f"Current widget before switch: {self.parent.currentWidget()}")
        self.parent.setCurrentWidget(self.main_window.main_widget)
        print(f"Current widget after switch: {self.parent.currentWidget()}")
        
        # Fade-out animation
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        def on_animation_finished():
            print("Animation finished, forcing widget switch")
            self.parent.setCurrentWidget(self.main_window.main_widget)
            self.main_window.main_widget.setFocus()
            self.main_window.repaint()
        anim.finished.connect(on_animation_finished)
        
        # Fallback timer if animation fails
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.parent.setCurrentWidget(self.main_window.main_widget))
        timer.start(350)  # Slightly longer than animation duration
        anim.start()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Tools Hub")
        self.setGeometry(200, 100, 600, 400)
        
        # Set Fusion style
        app.setStyle('Fusion')
        
        # Use QStackedWidget for window switching
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Main widget
        self.main_widget = QWidget()
        self.main_widget.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.stacked_widget.addWidget(self.main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # Title
        title_label = QLabel("Media Tools Hub")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Your one-stop for downloading and converting media")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #bbbbbb; font-size: 14px;")
        main_layout.addWidget(subtitle_label)
        
        # Spacer
        main_layout.addStretch()
        
        # Buttons container
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(20)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # Downloader button
        self.downloader_button = QPushButton("📥 Downloader")
        self.downloader_button.setFixedSize(300, 60)
        self.style_button(self.downloader_button, "#4CAF50", "#45a049")
        self.downloader_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.downloader_button.clicked.connect(self.run_downloader)
        buttons_layout.addWidget(self.downloader_button, alignment=Qt.AlignCenter)
        
        # Converter button
        self.converter_button = QPushButton("🔄 Converter")
        self.converter_button.setFixedSize(300, 60)
        self.style_button(self.converter_button, "#2196F3", "#1976D2")
        self.converter_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.converter_button.clicked.connect(self.show_converter_window)
        buttons_layout.addWidget(self.converter_button, alignment=Qt.AlignCenter)
        
        # Center buttons
        main_layout.addWidget(buttons_container, alignment=Qt.AlignCenter)
        
        # Spacer
        main_layout.addStretch()
        
        # Status label
        status_label = QLabel("Ready to enhance your media experience")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("color: #888888; font-size: 12px;")
        main_layout.addWidget(status_label)
        
        # Converter window
        self.converter_window = ConverterWindow(self.stacked_widget, self)
        self.stacked_widget.addWidget(self.converter_window)
    
    def style_button(self, button, base_color, hover_color):
        """Apply modern stylesheet"""
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 {base_color}, stop:1 {base_color}20);
                border: 2px solid {base_color}80;
                border-radius: 10px;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 {hover_color}, stop:1 {hover_color}20);
                border: 2px solid {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
                border: 2px solid {hover_color}80;
            }}
        """)

    def show_converter_window(self):
        print("Showing Converter Window")
        self.stacked_widget.setCurrentWidget(self.converter_window)
        self.converter_window.setWindowOpacity(0.0)  # Start with full transparency
        self.converter_window.setFocus()
        # Fade-in animation
        anim = QPropertyAnimation(self.converter_window, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()
        print("Animation started")

    def run_downloader(self):
        try:
            self.downloader_win = YouTubeDownloader()
            self.downloader_win.show()
        except Exception as e:
            print(f"Error running downloader: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())