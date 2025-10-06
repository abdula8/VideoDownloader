#!/usr/bin/env python3
"""
Complete Video Downloader Professional Build Solution
This script handles the entire build process from start to finish
"""

import os
import sys
import subprocess
import shutil
import tempfile
import time
from pathlib import Path
import json
import zipfile

class CompleteBuilder:
    def __init__(self):
        self.project_root = Path.cwd()
        self.version = "1.0.0"
        self.app_name = "Video Downloader Professional"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def run_command(self, cmd, cwd=None, check=True):
        """Run a command and return success status"""
        try:
            self.log(f"Running: {cmd}")
            result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
            if result.returncode != 0 and check:
                self.log(f"Command failed: {result.stderr}", "ERROR")
                return False
            return True
        except Exception as e:
            self.log(f"Exception running command {cmd}: {e}", "ERROR")
            return False
    
    def check_system_requirements(self):
        """Check if system meets requirements"""
        self.log("Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.log("Python 3.8+ required", "ERROR")
            return False
        
        # Check if we're on Windows
        if sys.platform != 'win32':
            self.log("This build script is designed for Windows only", "ERROR")
            return False
        
        # Check NSIS
        if not shutil.which("makensis"):
            self.log("NSIS not found in PATH. Please install NSIS and add it to PATH.", "ERROR")
            return False
        
        self.log("System requirements satisfied")
        return True
    
    def install_dependencies(self):
        """Install required Python dependencies"""
        self.log("Installing Python dependencies...")
        
        # Install PyInstaller if not present
        if not self.run_command("pip install pyinstaller"):
            self.log("Failed to install PyInstaller", "ERROR")
            return False
        
        # Install other dependencies
        if not self.run_command("pip install -r requirements.txt"):
            self.log("Failed to install requirements", "ERROR")
            return False
        
        # Install additional packages for better compatibility
        additional_packages = [
            "pywin32",
            "chromedriver-autoinstaller",
            "webdriver-manager"
        ]
        
        for package in additional_packages:
            self.run_command(f"pip install {package}")
        
        self.log("Dependencies installed successfully")
        return True
    
    def clean_build_environment(self):
        """Clean previous build artifacts"""
        self.log("Cleaning build environment...")
        
        dirs_to_clean = ['build', 'dist', '__pycache__', 'installer']
        for dir_name in dirs_to_clean:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                self.log(f"Removed {dir_name}")
        
        # Clean .pyc files
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.pyc'):
                    os.remove(os.path.join(root, file))
        
        self.log("Build environment cleaned")
    
    def create_installer_assets(self):
        """Create installer assets"""
        self.log("Creating installer assets...")
        
        # Create installer directory
        installer_dir = self.project_root / "installer"
        installer_dir.mkdir(exist_ok=True)
        
        # Create simple bitmap files for installer
        self.create_bitmap(installer_dir / "welcome.bmp", 164, 314)
        self.create_bitmap(installer_dir / "header.bmp", 150, 57)
        
        self.log("Installer assets created")
    
    def create_bitmap(self, filepath, width, height):
        """Create a simple bitmap file"""
        with open(filepath, 'wb') as f:
            # Write a minimal BMP header
            f.write(b'BM')  # BMP signature
            f.write((54).to_bytes(4, 'little'))  # File size
            f.write((0).to_bytes(4, 'little'))   # Reserved
            f.write((54).to_bytes(4, 'little'))  # Data offset
            f.write((40).to_bytes(4, 'little'))  # Header size
            f.write(width.to_bytes(4, 'little'))  # Width
            f.write(height.to_bytes(4, 'little')) # Height
            f.write((1).to_bytes(2, 'little'))   # Planes
            f.write((24).to_bytes(2, 'little'))  # Bits per pixel
            f.write((0).to_bytes(4, 'little'))   # Compression
            f.write((0).to_bytes(4, 'little'))   # Image size
            f.write((0).to_bytes(4, 'little'))   # X pixels per meter
            f.write((0).to_bytes(4, 'little'))   # Y pixels per meter
            f.write((0).to_bytes(4, 'little'))   # Colors in color table
            f.write((0).to_bytes(4, 'little'))   # Important color count
            
            # Write pixel data (all black for simplicity)
            for _ in range(width * height):
                f.write(b'\x00\x00\x00')  # RGB values
    
    def build_application(self):
        """Build the application using PyInstaller"""
        self.log("Building application with PyInstaller...")
        
        if not self.run_command("pyinstaller VideoDownloader.spec"):
            self.log("Failed to build application", "ERROR")
            return False
        
        # Verify the build
        exe_path = self.project_root / "dist" / "VideoDownloader" / "VideoDownloader.exe"
        if not exe_path.exists():
            self.log("Application executable not found after build", "ERROR")
            return False
        
        self.log(f"Application built successfully: {exe_path}")
        return True
    
    def create_installer(self):
        """Create the NSIS installer"""
        self.log("Creating NSIS installer...")
        
        installer_dir = self.project_root / "installer"
        
        # Copy installer script
        installer_script = self.project_root / "installer.nsi"
        installer_dest = installer_dir / "installer.nsi"
        shutil.copy2(installer_script, installer_dest)
        
        # Copy required files
        files_to_copy = [
            "LICENSE_AGREEMENT.txt",
            "RELEASE_NOTES.md",
            "icon.ico"
        ]
        
        for file_name in files_to_copy:
            src = self.project_root / file_name
            if src.exists():
                shutil.copy2(src, installer_dir / file_name)
        
        # Copy the built application
        app_source = self.project_root / "dist" / "VideoDownloader"
        app_dest = installer_dir / "dist" / "VideoDownloader"
        if app_source.exists():
            shutil.copytree(app_source, app_dest, dirs_exist_ok=True)
        
        # Build the installer
        os.chdir(installer_dir)
        if not self.run_command("makensis installer.nsi"):
            self.log("Failed to create NSIS installer", "ERROR")
            return False
        
        # Move installer to project root
        installer_exe = installer_dir / "VideoDownloader_Professional_Setup.exe"
        if installer_exe.exists():
            shutil.move(installer_exe, self.project_root / "VideoDownloader_Professional_Setup.exe")
            self.log(f"Installer created: {self.project_root / 'VideoDownloader_Professional_Setup.exe'}")
            return True
        else:
            self.log("Installer executable not found", "ERROR")
            return False
    
    def create_portable_version(self):
        """Create portable version"""
        self.log("Creating portable version...")
        
        portable_dir = self.project_root / "VideoDownloader_Portable"
        if portable_dir.exists():
            shutil.rmtree(portable_dir)
        
        # Copy the built application
        app_source = self.project_root / "dist" / "VideoDownloader"
        shutil.copytree(app_source, portable_dir)
        
        # Create portable launcher
        launcher_script = f'''@echo off
echo Starting {self.app_name} Portable...
cd /d "%~dp0"
VideoDownloader.exe
pause
'''
        with open(portable_dir / "Start.bat", 'w') as f:
            f.write(launcher_script)
        
        # Create portable info file
        portable_info = {
            "name": self.app_name,
            "version": self.version,
            "type": "portable",
            "description": "Portable version of Video Downloader Professional"
        }
        
        with open(portable_dir / "portable_info.json", 'w') as f:
            json.dump(portable_info, f, indent=2)
        
        # Create ZIP archive
        zip_path = self.project_root / f"VideoDownloader_Portable_v{self.version}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(portable_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(portable_dir)
                    zipf.write(file_path, arc_path)
        
        self.log(f"Portable version created: {zip_path}")
        return True
    
    def create_documentation(self):
        """Create comprehensive documentation"""
        self.log("Creating documentation...")
        
        # Create user manual
        user_manual = f"""# {self.app_name} - User Manual

## Quick Start Guide

### Installation
1. Run the installer as Administrator
2. Follow the installation wizard
3. Accept the license agreement
4. Choose your preferred options
5. Complete the installation

### First Use
1. Launch {self.app_name} from the Start Menu or Desktop
2. The application will automatically collect cookies from your browsers
3. Paste a video URL or enable automatic URL detection
4. Select your preferred download options
5. Click "Start Download"

### Features Overview

#### Multi-Platform Support
- Video (public and private videos (Using cookies file manually))
- Facebook (videos and posts)
- Twitter/X (tweets and threads)
- Instagram (posts and stories)
- TikTok (videos and content)
- LinkedIn (professional content)

#### Authentication Methods (Future)
- **Smart Cookie Collection**: Automatically gathers cookies from all browsers (Future)
- **OAuth Integration**: Secure login through Google/Microsoft accounts (Future)
- **Manual Authentication**: Username/password login support (Future)
- **Selenium Automation**: Automated browser-based authentication (Future)

#### Download Options
- **Video Downloads**: High-quality video downloads up to 4K
- **Audio Extraction**: Convert videos to MP3 audio files
- **Caption Downloads**: Download subtitles in multiple languages
- **Playlist Support**: Download entire playlists with one click
- **Batch Processing**: Download multiple videos simultaneously

### Keyboard Shortcuts
- **Ctrl+V**: Paste URL from clipboard
- **Ctrl+F**: Fetch video information
- **Ctrl+D**: Start download
- **Ctrl+E**: Toggle URL detection

### Troubleshooting

#### Common Issues
1. **Authentication Errors**: Try clearing cookies and re-authenticating
2. **Download Failures**: Check internet connection and URL validity
3. **Format Issues**: Ensure FFmpeg is properly installed
4. **Performance Issues**: Close other applications to free up resources

#### Getting Help
- Check the Release Notes for latest information
- Visit our support website: https://www.vtools.com/support
- Contact support: support@vtools.com

### System Requirements
- Windows 10/11 (64-bit)
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space
- Broadband internet connection

### Privacy and Security
- All data is processed locally on your device
- No personal data is sent to external servers
- Cookies are encrypted and auto-expire after 1 hour (Future)
- Full user control over data storage and processing

---
© 2024 VTools. All rights reserved.
"""
        
        with open(self.project_root / "README_USER.md", 'w', encoding='utf-8') as f:
            f.write(user_manual)
        
        self.log("Documentation created")
        return True
    
    def run_tests(self):
        """Run basic tests to verify the build"""
        self.log("Running build tests...")
        
        # Test if main executable exists
        exe_path = self.project_root / "dist" / "VideoDownloader" / "VideoDownloader.exe"
        if not exe_path.exists():
            self.log("Main executable not found", "ERROR")
            return False
        
        # Test if installer exists
        installer_path = self.project_root / "VideoDownloader_Professional_Setup.exe"
        if not installer_path.exists():
            self.log("Installer not found", "ERROR")
            return False
        
        # Test if portable version exists
        portable_path = self.project_root / f"VideoDownloader_Portable_v{self.version}.zip"
        if not portable_path.exists():
            self.log("Portable version not found", "ERROR")
            return False
        
        self.log("All tests passed")
        return True
    
    def build_all(self):
        """Build everything"""
        self.log(f"Starting complete build process for {self.app_name} v{self.version}")
        
        # Check system requirements
        if not self.check_system_requirements():
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            return False
        
        # Clean build environment
        self.clean_build_environment()
        
        # Create installer assets
        self.create_installer_assets()
        
        # Build application
        if not self.build_application():
            return False
        
        # Create installer
        if not self.create_installer():
            return False
        
        # Create portable version
        if not self.create_portable_version():
            return False
        
        # Create documentation
        if not self.create_documentation():
            return False
        
        # Run tests
        if not self.run_tests():
            return False
        
        self.log("Complete build process finished successfully!")
        return True

def main():
    """Main function"""
    print("=" * 60)
    print("Video Downloader Professional - Complete Build Solution")
    print("=" * 60)
    print()
    
    builder = CompleteBuilder()
    success = builder.build_all()
    
    if success:
        print("\n" + "=" * 60)
        print("BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nFiles created:")
        print("✓ VideoDownloader_Professional_Setup.exe (Installer)")
        print("✓ VideoDownloader_Portable_v1.0.0.zip (Portable version)")
        print("✓ README_USER.md (User manual)")
        print("✓ RELEASE_NOTES.md (Release notes)")
        print("\nTo install:")
        print("1. Run 'VideoDownloader_Professional_Setup.exe' as Administrator")
        print("2. Follow the installation wizard")
        print("3. Choose your preferred options")
        print("4. Complete the installation")
        print("\nFor portable use:")
        print("1. Extract 'VideoDownloader_Portable_v1.0.0.zip'")
        print("2. Run 'Start.bat'")
        print("\nDocumentation:")
        print("- README_USER.md (User manual)")
        print("- RELEASE_NOTES.md (Release notes)")
        print("- README_BUILD.md (Build instructions)")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("BUILD FAILED!")
        print("=" * 60)
        print("Please check the error messages above and try again.")
        print("Common solutions:")
        print("- Install Python 3.8+ and add to PATH")
        print("- Install NSIS and add to PATH")
        print("- Run as Administrator")
        print("- Check antivirus settings")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
