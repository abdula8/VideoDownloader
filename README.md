# Video Downloader Professional - User Manual

Last updated: October 2025

This README documents the features, recent updates and user-facing behavior of Video Downloader Professional. It is meant for end users and system administrators.

## Quick Start

1. Install the application using the provided installer (run as Administrator on Windows).
2. Launch the program from the Start Menu or Desktop.
3. Paste a video/playlist URL into the URL box or use the automatic clipboard URL detection.
4. Choose the download type (Video / Audio / Captions), quality and folder.
5. Click Start Download or use Batch Download to process a list.

## New and Notable Features (since last release)

- Tools menu reorganized: Tools now contains exactly three items — Convert, Download History, and Preferences. Preferences was moved from Edit->Settings to Tools.
- Preferences dialog: unified dialog exposing Theme (Light/Dark) and Language selection (English / Arabic / Japanese), and quick access hints. Settings persist to `settings.json`.
- Dark / Light theme support: toggle in Preferences or Edit -> Settings (theme saved across sessions).
- Multi-language UI: English, Arabic and Japanese translations for main UI strings; language choice is persisted and applied at runtime.
- Download History: full local history stored in `download_history.db` (SQLite). The Tools -> Download History dialog shows detailed records, search/filter, export, and basic actions (re-download, open file location, delete).
- Automatic logging: downloads (including batch downloads) are automatically logged to the history DB with best-effort file detection. Failures are also recorded.
- Convert dialogs integration: Convert (Tools) opens Basic / Advanced converter dialogs (see `converter_tool.py`) for remuxing and encoding tasks.
- Robustness improvements: additional error handling, thread-safe DB writes (per-call SQLite connections), and background heartbeat timer to maintain UI responsiveness.

## Features Overview

### Supported Platforms & Media
- YouTube (public and private with cookies)
- Facebook, Twitter/X, Instagram, TikTok, LinkedIn and other sites supported via yt-dlp extractor list

### Download Types
- Video downloads (multiple qualities) — can select formats discovered via the Load Formats button
- Audio extraction (MP3 and other audio codecs via FFmpeg)
- Captions download (VTT/SRT)
- Batch downloads (load a text file with URLs)

### Tools
- Convert (Tools -> Convert): Basic and Advanced converter dialogs powered by `converter_tool.py` (FFmpeg-backed).
- Download History: detailed history with filters, CSV export and actions.
- Preferences: theme, language, and quick access information.

### User Interface & UX
- Dark/Light themes with persistent preference.
- Multi-language UI (English / Arabic / Japanese). Arabic strings are provided; RTL layout may require additional tuning.
- Menu-driven layout: File, Edit (theme & language), Tools (Convert / Download History / Preferences), Help.

### Settings & Persistence
- Settings are stored in `settings.json` beside the application script.
- Download history is stored in `download_history.db` (SQLite).

## Troubleshooting

- If downloads fail, check the application log `youtube_downloader.log` in the application folder.
- Ensure FFmpeg is installed and on PATH for conversions and format remuxing.
- If a download does not appear in history immediately, wait until the download/worker finishes — history entries are created on completion (or marked failed on repeated errors).

## Keyboard Shortcuts
- Ctrl+V: Paste URL from clipboard
- Ctrl+F: Fetch video information
- Ctrl+D: Start download
- Ctrl+E: Toggle URL detection

## System Requirements

- Windows 10/11 (64-bit)
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space (more for temporary downloads)

## Privacy & Security

- All processing occurs locally; cookies and credentials are stored locally according to user preferences.
- The app does not transmit personal data to remote servers by default.

---
© 2024-2025 VTools. All rights reserved.
