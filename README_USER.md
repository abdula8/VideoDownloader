# Video Downloader Professional - User Manual

Last updated: October 2025

This user guide mirrors the README and includes step-by-step instructions and notes for end users.

## Quick Start

1. Install the application using the provided installer (run as Administrator on Windows).
2. Launch the program from the Start Menu or Desktop.
3. Paste a video/playlist URL into the URL box or use the automatic clipboard URL detection.
4. Choose the download type (Video / Audio / Captions), quality and folder.
5. Click Start Download or use Batch Download to process a list.

## Recent Updates (Oct 2025)

- Preferences moved to Tools and now exposes Theme and Language settings.
- Tools now contains only Convert, Download History and Preferences.
- Download History is implemented and stores records in `download_history.db`.
- Batch and normal downloads are automatically logged to history with best-effort file detection.
- Dark/Light theme and multi-language support were added.

## Common Usage Patterns

- Single URL: paste URL and click "Start Download".
- Batch: prepare a text file with one URL per line and use Batch Download from File.
- Convert: use Tools -> Convert -> Basic / Advanced to open converter dialogs.
- History: use Tools -> Download History to view/export/manage history.

## Troubleshooting & Support

- Check `youtube_downloader.log` for detailed errors.
- Confirm FFmpeg is installed for conversion tasks.
- If downloads don't appear in History, wait for the worker thread to finish — history is written on completion.

---
© 2024-2025 VTools. All rights reserved.
