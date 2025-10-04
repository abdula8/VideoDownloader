import subprocess
import os
import re

def find_video_files(folder_path: str) -> list[str]:
    """
    Scans a folder and its subfolders to find all video files.
    
    Args:
        folder_path (str): The root directory to start the scan from.
        
    Returns:
        list[str]: A list of full paths to all found video files.
    """
    video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
    video_files = []
    
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(dirpath, filename))
                
    return video_files

def convert_to_mp4(input_file: str) -> None:
    """
    Converts a single video file to MP4 format using FFmpeg.
    
    The function creates an output filename with a '.mp4' extension
    and places it in the same directory as the input file. It copies
    the video and audio streams to preserve quality.
    
    Args:
        input_file (str): The full path to the video file to be converted.
    """
    # Create the output filename by replacing the extension with .mp4
    # and ensuring the original file isn't overwritten if it's already an MP4.
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}.mp4"
    
    if os.path.normpath(input_file).lower() == os.path.normpath(output_file).lower():
        print(f"Skipping '{input_file}' as it is already an MP4 file.")
        return
    
    # FFmpeg command to convert the video to MP4
    # -i: specifies the input file
    # -c:v copy: copies the video stream without re-encoding
    # -c:a copy: copies the audio stream without re-encoding
    # This is the fastest and best-quality method, as it only changes the container.
    command = [
        'ffmpeg',
        '-i', input_file,
        '-c:v', 'copy',
        '-c:a', 'copy',
        output_file
    ]

    print(f"\nStarting conversion of '{os.path.basename(input_file)}'...")
    
    try:
        # Use subprocess.run to execute the FFmpeg command
        process = subprocess.run(command, check=True, text=True, capture_output=True, encoding='utf-8')
        print(f"✔ Conversion successful! Output saved to '{output_file}'")
        
    except FileNotFoundError:
        print("Error: FFmpeg not found. Please ensure FFmpeg is installed and added to your system's PATH.")
        print("You can download it from https://ffmpeg.org/")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def parse_user_input(input_str: str, max_index: int) -> list[int]:
    """
    Parses a user input string of numbers and ranges (e.g., '1-5, 8, 10-12').
    
    Args:
        input_str (str): The user's raw input string.
        max_index (int): The maximum valid index number.
        
    Returns:
        list[int]: A sorted list of unique, valid indices to convert.
    """
    selected_indices = set()
    parts = re.split(r'[,;]\s*', input_str)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                # Ensure start is less than or equal to end
                if start > end:
                    start, end = end, start
                
                # Check for out-of-bounds numbers and add to set
                for i in range(start, end + 1):
                    if 1 <= i <= max_index:
                        selected_indices.add(i)
                    else:
                        print(f"Warning: Index {i} is out of the valid range (1-{max_index}). Skipping.")
            except ValueError:
                print(f"Warning: Invalid range format '{part}'. Skipping.")
        else:
            try:
                index = int(part)
                if 1 <= index <= max_index:
                    selected_indices.add(index)
                else:
                    print(f"Warning: Index {index} is out of the valid range (1-{max_index}). Skipping.")
            except ValueError:
                print(f"Warning: Invalid number format '{part}'. Skipping.")
                
    return sorted(list(selected_indices))

def main():
    """Main function to run the video conversion utility."""
    print("Welcome to the Video Converter!")
    print("This tool will find videos in a folder and convert them to MP4 format.")
    
    # 1. Get folder path from user
    folder_path = input("Please enter the folder path to scan: ").strip()
    
    if not os.path.isdir(folder_path):
        print(f"Error: The path '{folder_path}' is not a valid directory.")
        return

    # 2. Find all video files
    print("\nScanning for video files...")
    all_videos = find_video_files(folder_path)
    
    if not all_videos:
        print("No video files were found in the specified folder or its subfolders.")
        return

    # 3. Display the list of found videos
    print("\nFound the following video files:")
    for i, video in enumerate(all_videos, 1):
        print(f"  {i}. {os.path.basename(video)}")
    
    num_videos = len(all_videos)
    
    # 4. Prompt for user choice
    print(f"\nSelect videos to convert (enter 'all' or a list of numbers/ranges):")
    print("  e.g., 'all' to convert all files, or '1-5, 8, 10' to select specific ones.")
    user_choice = input("Your choice: ").strip().lower()

    if user_choice == 'all':
        videos_to_convert = all_videos
    else:
        selected_indices = parse_user_input(user_choice, num_videos)
        if not selected_indices:
            print("No valid videos selected. Exiting.")
            return
            
        videos_to_convert = [all_videos[i - 1] for i in selected_indices]
    
    # 5. Start the conversion process
    print(f"\n--- Starting conversion for {len(videos_to_convert)} videos ---")
    for video_file in videos_to_convert:
        convert_to_mp4(video_file)
    
    print("\n--- All selected conversions are complete! ---")

if __name__ == "__main__":
    main()
