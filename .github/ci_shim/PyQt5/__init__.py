"""
Lightweight PyQt5 compatibility shim backed by PySide6.

This file is used only in CI via PYTHONPATH to satisfy imports like
`from PyQt5 import QtWidgets` when PyQt5 wheels are not available.
It re-exports commonly used submodules from PySide6.

Note: This shim is not added to sys.path by default; the CI workflow will
prepend the directory to PYTHONPATH before running tests.
"""
try:
    # Try to import PySide6 and re-export key modules
    import importlib
    _pside = importlib.import_module('PySide6')
    # Import most commonly used modules
    from PySide6 import QtWidgets as QtWidgets
    from PySide6 import QtCore as QtCore
    from PySide6 import QtGui as QtGui
    from PySide6 import QtTest as QtTest

    # Expose them at package level
    __all__ = ['QtWidgets', 'QtCore', 'QtGui', 'QtTest']
except Exception as e:
    # If PySide6 is not available, provide minimal dummy objects to avoid hard crashes.
    # Tests may fail with missing functionality, but import will succeed.
    class _Dummy:
        pass

    QtWidgets = _Dummy()
    QtCore = _Dummy()
    QtGui = _Dummy()
    QtTest = _Dummy()
    __all__ = ['QtWidgets', 'QtCore', 'QtGui', 'QtTest']
