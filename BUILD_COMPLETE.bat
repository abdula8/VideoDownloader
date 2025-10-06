@echo off
title Video Downloader Professional - Complete Build System
color 0A

echo.
echo ================================================================
echo    Video Downloader Professional - Complete Build System
echo ================================================================
echo.
echo This script will build the complete Video Downloader Professional
echo application including:
echo.
echo - Windows Executable (EXE)
echo - Professional Installer with NSIS
echo - Portable Version (ZIP)
echo - User Documentation
echo - Release Notes
echo.
echo ================================================================
echo.

REM Check if Python is available
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo and add it to your system PATH
    echo.
    pause
    exit /b 1
)
echo ✓ Python is available

REM Check if NSIS is available
echo.
echo [2/6] Checking NSIS installation...
makensis /VERSION >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ERROR: NSIS is not installed or not in PATH
    echo Please install NSIS from https://nsis.sourceforge.io/Download
    echo and add it to your system PATH
    echo.
    pause
    exit /b 1
)
echo ✓ NSIS is available

REM Check if we're running as administrator
echo.
echo [3/6] Checking administrator privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo WARNING: Not running as Administrator
    echo Some features may not work properly
    echo Consider running as Administrator for best results
    echo.
    pause
)

REM Run the test script first
echo.
echo [4/6] Running pre-build tests...
python test_build_professional.py
if %errorLevel% neq 0 (
    echo.
    echo ERROR: Pre-build tests failed
    echo Please fix the issues and try again
    echo.
    pause
    exit /b 1
)
echo ✓ Pre-build tests passed

REM Run the complete build
echo.
echo [5/6] Starting complete build process...
echo This may take several minutes...
echo.
python build_complete_solution.py
if %errorLevel% neq 0 (
    echo.
    echo ERROR: Build process failed
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)

REM Show completion message
echo.
echo [6/6] Build completed successfully!
echo.
echo ================================================================
echo                    BUILD COMPLETED SUCCESSFULLY!
echo ================================================================
echo.
echo Files created:
echo ✓ VideoDownloader_Professional_Setup.exe (Installer)
echo ✓ VideoDownloader_Portable_v1.0.0.zip (Portable version)
echo ✓ README_USER.md (User manual)
echo ✓ RELEASE_NOTES.md (Release notes)
echo.
echo To install:
echo 1. Run 'VideoDownloader_Professional_Setup.exe' as Administrator
echo 2. Follow the installation wizard
echo 3. Choose your preferred options
echo 4. Complete the installation
echo.
echo For portable use:
echo 1. Extract 'VideoDownloader_Portable_v1.0.0.zip'
echo 2. Run 'Start.bat'
echo.
echo Documentation:
echo - README_USER.md (User manual)
echo - RELEASE_NOTES.md (Release notes)
echo - README_BUILD.md (Build instructions)
echo.
echo ================================================================
echo.

REM Ask if user wants to run the installer
set /p choice="Would you like to run the installer now? (y/n): "
if /i "%choice%"=="y" (
    echo.
    echo Starting installer...
    start "" "VideoDownloader_Professional_Setup.exe"
)

echo.
echo Build process completed!
echo Thank you for using Video Downloader Professional Build System.
echo.
pause
