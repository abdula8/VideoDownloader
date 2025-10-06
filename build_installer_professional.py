#!/usr/bin/env python3
"""
Professional Video Downloader Build System
Creates a complete Windows installer with all features
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
import requests

class VideoDownloaderBuilder:
    def __init__(self):
        self.project_root = Path.cwd()
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.installer_dir = self.project_root / "installer"
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
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        self.log("Checking dependencies...")
        
        required_packages = [
            "pyinstaller",
            "PyQt5",
            "yt-dlp",
            "selenium",
            "browser-cookie3",
            "requests"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.log(f"Missing packages: {missing_packages}", "ERROR")
            self.log("Installing missing packages...")
            for package in missing_packages:
                if not self.run_command(f"pip install {package}"):
                    self.log(f"Failed to install {package}", "ERROR")
                    return False
        
        # Check NSIS
        if not shutil.which("makensis"):
            self.log("NSIS not found in PATH. Please install NSIS and add it to PATH.", "ERROR")
            return False
        
        self.log("All dependencies satisfied")
        return True
    
    def clean_build(self):
        """Clean previous build artifacts"""
        self.log("Cleaning previous builds...")
        # Ensure any running app instances are stopped to avoid locked files
        try:
            self._kill_running_app()
        except Exception:
            pass
        
        def safe_rmtree(path):
            """Attempt to remove a directory tree with retries and fallback for locked files."""
            try:
                shutil.rmtree(path)
                self.log(f"Removed {path.name}")
                return True
            except Exception as e:
                self.log(f"Could not remove {path}: {e}", "WARNING")
                # Try to remove read-only flags and retry
                for root, dirs, files in os.walk(path, topdown=False):
                    for name in files:
                        fp = os.path.join(root, name)
                        try:
                            os.chmod(fp, 0o666)
                        except Exception:
                            pass
                    for name in dirs:
                        dp = os.path.join(root, name)
                        try:
                            os.chmod(dp, 0o777)
                        except Exception:
                            pass
                try:
                    shutil.rmtree(path)
                    self.log(f"Removed {path.name} on retry")
                    return True
                except Exception as e2:
                    self.log(f"Final attempt failed to remove {path}: {e2}", "WARNING")
                    return False

        dirs_to_clean = ['build', 'dist', '__pycache__', 'installer']
        for dir_name in dirs_to_clean:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                if not safe_rmtree(dir_path):
                    self.log(f"Skipping removal of {dir_name} (in use). Continue build.", "WARNING")
        
        # Clean .pyc files
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.pyc'):
                    os.remove(os.path.join(root, file))
        
        self.log("Build cleanup completed")
    
    def create_installer_assets(self):
        """Create installer assets like bitmaps and icons"""
        self.log("Creating installer assets...")
        
        # Create installer directory
        self.installer_dir.mkdir(exist_ok=True)
        
        # Create simple bitmap files for installer
        self.create_bitmap("welcome.bmp", 164, 314, "Welcome to Video Downloader Professional!")
        self.create_bitmap("header.bmp", 150, 57, "Professional Video Downloader")
        
        self.log("Installer assets created")
    
    def create_bitmap(self, filename, width, height, text):
        """Create a simple bitmap file for the installer"""
        # This is a placeholder - in a real implementation, you'd create actual bitmap files
        # For now, we'll create empty files
        bitmap_path = self.installer_dir / filename
        with open(bitmap_path, 'wb') as f:
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

        def _kill_running_app(self):
            """Kill any running instances of VideoDownloader to avoid locked files on Windows."""
            try:
                if sys.platform == 'win32':
                    # Use tasklist/taskkill to find and kill the process
                    proc_name = 'VideoDownloader.exe'
                    # Get list of processes
                    result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {proc_name}'], capture_output=True, text=True)
                    if proc_name in result.stdout:
                        self.log(f"Found running {proc_name}, attempting to terminate")
                        subprocess.run(['taskkill', '/F', '/IM', proc_name], capture_output=True)
                        time.sleep(1)
                    # Also attempt to kill common related processes (bootloader/runw.exe, python)
                    for name in ('runw.exe', 'VideoDownloader.exe', 'VideoDownloader_Professional_Setup.exe'):
                        try:
                            subprocess.run(['taskkill', '/F', '/IM', name], capture_output=True)
                        except Exception:
                            pass

                    # Try to kill processes whose command line mentions this project folder or VideoDownloader
                    try:
                        proj = str(self.project_root).replace('\\', '\\')
                        # Use PowerShell to find processes with matching command line and terminate them
                        ps_cmd = (
                            "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and (\"VideoDownloader\" -in $_.CommandLine -or \"%s\" -in $_.CommandLine) } | ForEach-Object { $_.Terminate() }"
                            % proj
                        )
                        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
                    except Exception:
                        pass
                else:
                    # On non-windows, attempt to kill by name (best-effort)
                    subprocess.run(['pkill', '-f', 'VideoDownloader'], capture_output=True)
                    time.sleep(1)
            except Exception as e:
                self.log(f"Could not kill running app processes: {e}", "WARNING")
    
    def build_exe(self):
        """Build the EXE using PyInstaller"""
        self.log("Building EXE with PyInstaller...")
        # Ensure no leftover running app and try to remove existing final dist folder
        try:
            self._kill_running_app()
        except Exception:
            pass

        final_app_dir = self.dist_dir / "VideoDownloader"
        if final_app_dir.exists():
            try:
                shutil.rmtree(final_app_dir)
                self.log(f"Removed existing final dist folder: {final_app_dir}")
            except Exception as e:
                self.log(f"Could not remove existing final dist folder before build: {e}", "WARNING")
        
        # Use the enhanced spec file and auto-confirm removal of existing dist (-y / --noconfirm)
        # Build into a temporary dist directory to avoid issues with locked existing dist/
        tmp_dist = self.project_root / f"dist_tmp_{int(time.time())}"
        if tmp_dist.exists():
            try:
                shutil.rmtree(tmp_dist)
            except Exception:
                pass

        pyinstaller_cmd = f"pyinstaller -y --distpath \"{tmp_dist}\" VideoDownloader.spec"
        if not self.run_command(pyinstaller_cmd):
            self.log("Failed to build EXE with PyInstaller", "ERROR")
            # Cleanup tmp_dist if present
            try:
                if tmp_dist.exists():
                    shutil.rmtree(tmp_dist)
            except Exception:
                pass
            return False

        # Verify the build in tmp_dist
        exe_path = tmp_dist / "VideoDownloader" / "VideoDownloader.exe"
        if not exe_path.exists():
            self.log(f"EXE file not found after build in {tmp_dist}", "ERROR")
            return False

        # Use the freshly built app directly from tmp_dist; avoid moving locked final dist
        self.built_dist = tmp_dist / "VideoDownloader"

        # Do not remove tmp_dist here; other steps will copy from self.built_dist
        self.log(f"EXE built successfully (in temp dist): {self.built_dist / 'VideoDownloader.exe'}")
        return True
    
    def create_installer(self):
        """Create the NSIS installer"""
        self.log("Creating NSIS installer...")
        
        # Copy installer script to installer directory
        installer_script = self.project_root / "installer.nsi"
        installer_dest = self.installer_dir / "installer.nsi"
        shutil.copy2(installer_script, installer_dest)
        
        # Copy required files to installer directory
        files_to_copy = [
            "LICENSE_AGREEMENT.txt",
            "RELEASE_NOTES.md",
            "icon.ico"
        ]
        
        for file_name in files_to_copy:
            src = self.project_root / file_name
            if src.exists():
                shutil.copy2(src, self.installer_dir / file_name)
        
        # Copy the built application (use temporary build output if present)
        app_source = getattr(self, 'built_dist', None) or (self.dist_dir / "VideoDownloader")
        app_dest = self.installer_dir / "dist" / "VideoDownloader"
        if app_source and app_source.exists():
            shutil.copytree(app_source, app_dest, dirs_exist_ok=True)
        
        # Build the installer
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.installer_dir)
            if not self.run_command("makensis installer.nsi"):
                self.log("Failed to create NSIS installer", "ERROR")
                return False
            # Try expected installer filename first
            installer_exe = self.installer_dir / "VideoDownloader_Professional_Setup.exe"
            if installer_exe.exists():
                dest = self.project_root / installer_exe.name
                shutil.move(installer_exe, dest)
                self.log(f"Installer created: {dest}")
                return True
            # Fallback: find any .exe produced in installer dir (newer NSIS may name differently)
            exes = list(self.installer_dir.glob('*.exe'))
            if exes:
                # choose the largest exe (likely the installer)
                exes_sorted = sorted(exes, key=lambda p: p.stat().st_size, reverse=True)
                chosen = exes_sorted[0]
                dest = self.project_root / chosen.name
                shutil.move(chosen, dest)
                self.log(f"Installer created (fallback): {dest}")
                return True
            self.log("Installer executable not found after makensis", "ERROR")
            return False
        finally:
            try:
                os.chdir(prev_cwd)
            except Exception:
                pass
    
    def create_portable_version(self):
        """Create a portable version"""
        self.log("Creating portable version...")
        
        portable_dir = self.project_root / "VideoDownloader_Portable"
        if portable_dir.exists():
            shutil.rmtree(portable_dir)
        
        # Copy the built application (use temporary build output if present)
        app_source = getattr(self, 'built_dist', None) or (self.dist_dir / "VideoDownloader")
        if not app_source.exists():
            self.log(f"Built application not found at {app_source}", "ERROR")
            return False
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
- Video (public and private videos)
- Facebook (videos and posts)
- Twitter/X (tweets and threads)
- Instagram (posts and stories)
- TikTok (videos and content)
- LinkedIn (professional content)

#### Authentication Methods
- **Smart Cookie Collection**: Automatically gathers cookies from all browsers
- **OAuth Integration**: Secure login through Google/Microsoft accounts
- **Manual Authentication**: Username/password login support
- **Selenium Automation**: Automated browser-based authentication

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
- Cookies are encrypted and auto-expire after 1 hour
- Full user control over data storage and processing

---
© 2025 VTools. All rights reserved.
"""
        
        with open(self.project_root / "README_USER.md", 'w', encoding='utf-8') as f:
            f.write(user_manual)
        
        self.log("Documentation created")
        return True
    
    def build_all(self):
        """Build everything"""
        self.log(f"Starting build process for {self.app_name} v{self.version}")
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Clean previous builds
        self.clean_build()
        
        # Create installer assets
        self.create_installer_assets()
        
        # Build EXE
        if not self.build_exe():
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
        
        self.log("Build completed successfully!")
        self.log("Files created:")
        self.log("- VideoDownloader_Professional_Setup.exe (Installer)")
        self.log("- VideoDownloader_Portable_v1.0.0.zip (Portable version)")
        self.log("- README_USER.md (User manual)")
        self.log("- RELEASE_NOTES.md (Release notes)")
        
        return True

def main():
    """Main function"""
    builder = VideoDownloaderBuilder()
    success = builder.build_all()
    
    if success:
        print("\n" + "="*60)
        print("BUILD COMPLETED SUCCESSFULLY!")
        print("="*60)
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
        print("="*60)
    else:
        print("\n" + "="*60)
        print("BUILD FAILED!")
        print("="*60)
        print("Please check the error messages above and try again.")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()
