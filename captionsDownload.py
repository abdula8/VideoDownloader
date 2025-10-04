import os
import yt_dlp

def create_captions_directory():
    """Create a captions directory if it doesn't exist."""
    if not os.path.exists("captions"):
        os.makedirs("captions")

def download_captions(url, lang):
    """Download captions from a YouTube video or playlist."""
    ydl_opts = {
        'skip_download': True,  # Skip downloading the video
        'writeautomaticsub': True,  # Download automatic captions
        'writesubtitles': True,  # Download manual captions
        'subtitleslangs': [lang],  # Specify language (English)
        'outtmpl': 'captions/%(title)s.%(ext)s',  # Output template for captions
        'subtitle_format': 'vtt',  # Caption format
        'quiet': False,  # Set to True to suppress output
        'ignoreerrors': True,  # Continue on errors for playlists
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            create_captions_directory()
            print(f"Processing URL: {url}")
            ydl.download([url])
            print("Captions downloaded successfully to 'captions' directory.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def main():
    """Main function to get URL input and start downloading captions."""
    url = input("Enter YouTube video or playlist URL: ")
    lang = input("Enter CC Language Arabic[ar] - English[en]: ")
    download_captions(url, lang=lang)

if __name__ == "__main__":
    main()