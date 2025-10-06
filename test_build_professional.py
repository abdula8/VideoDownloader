#!/usr/bin/env python3
"""
Test script for Video Downloader Professional build
Verifies that all components are properly built and configured
"""

import os
import sys
import subprocess
from pathlib import Path

def test_file_exists(file_path, description):
    """Test if a file exists and report status"""
    if Path(file_path).exists():
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description}: {file_path} (NOT FOUND)")
        return False

def test_python_imports():
    """Test if required Python packages can be imported"""
    print("\nTesting Python imports...")
    
    required_packages = [
        "PyQt5",
        "yt_dlp",
        "selenium",
        "browser_cookie3",
        "requests"
    ]
    
    all_imports_ok = True
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (NOT INSTALLED)")
            all_imports_ok = False
    
    return all_imports_ok

def test_nsis_available():
    """Test if NSIS is available"""
    print("\nTesting NSIS availability...")
    
    try:
        result = subprocess.run(["makensis", "/VERSION"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ NSIS is available")
            return True
        else:
            print("✗ NSIS not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ NSIS not found in PATH")
        return False

def test_build_files():
    """Test if all required build files exist"""
    print("\nTesting build files...")
    
    required_files = [
        ("main_V3.py", "Main application file"),
        ("VideoDownloader.spec", "PyInstaller spec file"),
        ("installer.nsi", "NSIS installer script"),
        ("build_installer_professional.py", "Build script"),
        ("LICENSE_AGREEMENT.txt", "License agreement"),
        ("RELEASE_NOTES.md", "Release notes"),
        ("requirements.txt", "Python requirements"),
        ("icon.ico", "Application icon")
    ]
    
    all_files_ok = True
    for file_path, description in required_files:
        if not test_file_exists(file_path, description):
            all_files_ok = False
    
    return all_files_ok

def test_pyinstaller_spec():
    """Test if PyInstaller spec file is valid"""
    print("\nTesting PyInstaller spec file...")
    
    try:
        with open("VideoDownloader.spec", "r") as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "Analysis(",
            "EXE(",
            "COLLECT(",
            "hiddenimports",
            "datas"
        ]
        
        for section in required_sections:
            if section in content:
                print(f"✓ Found {section}")
            else:
                print(f"✗ Missing {section}")
                return False
        
        print("✓ PyInstaller spec file appears valid")
        return True
        
    except FileNotFoundError:
        print("✗ PyInstaller spec file not found")
        return False
    except Exception as e:
        print(f"✗ Error reading spec file: {e}")
        return False

def test_nsis_script():
    """Test if NSIS script is valid"""
    print("\nTesting NSIS script...")
    
    try:
        with open("installer.nsi", "r") as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "!define APPNAME",
            "Section",
            "WriteUninstaller",
            "CreateShortCut",
            "WriteRegStr"
        ]
        
        for section in required_sections:
            if section in content:
                print(f"✓ Found {section}")
            else:
                print(f"✗ Missing {section}")
                return False
        
        print("✓ NSIS script appears valid")
        return True
        
    except FileNotFoundError:
        print("✗ NSIS script not found")
        return False
    except Exception as e:
        print(f"✗ Error reading NSIS script: {e}")
        return False

def main():
    """Main test function"""
    print("Video Downloader Professional - Build Test")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Python Imports", test_python_imports),
        ("NSIS Availability", test_nsis_available),
        ("Build Files", test_build_files),
        ("PyInstaller Spec", test_pyinstaller_spec),
        ("NSIS Script", test_nsis_script)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Ready to build.")
        print("\nTo build the application, run:")
        print("  build_all_professional.bat")
        print("  or")
        print("  python build_installer_professional.py")
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please fix the issues before building.")
        print("\nCommon solutions:")
        print("- Install missing Python packages: pip install -r requirements.txt")
        print("- Install NSIS and add it to PATH")
        print("- Ensure all required files are present")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
