import yt_dlp
import os
from pathlib import Path


def download_complete_playlist(url, output_folder="downloads"):
    """Download entire playlist"""
    print("Downloading complete playlist...")
    
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        'format': 'best[height<=1080]', 
        'outtmpl': os.path.join(output_folder, '%(playlist_index)s. %(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'ignoreerrors': True,  
        'no_warnings': False,
        'quiet': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\n✓ Download complete!")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def download_partial_playlist(url, start, end, output_folder="downloads"):
    """Download specific range of videos from playlist"""
    print(f"Downloading videos {start} to {end}...")
    
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        'format': 'best[height<=1080]',  
        'playlist_items': f'{start}-{end}',
        'outtmpl': os.path.join(output_folder, '%(playlist_index)s. %(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'ignoreerrors': True,
        'no_warnings': False,
        'quiet': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\n✓ Download complete!")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def resume_download(url, start_from, output_folder="downloads"):
    """Resume download from specific video number"""
    print(f"Resuming download from video {start_from}...")
    
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        'format': 'best[height<=1080]',
        'playlist_items': f'{start_from}-',  
        'outtmpl': os.path.join(output_folder, '%(playlist_index)s. %(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'ignoreerrors': True,
        'no_warnings': False,
        'quiet': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\n✓ Download complete!")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def get_playlist_info(url):
    """Get information about the playlist"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                print(f"\nPlaylist: {info.get('title', 'Unknown')}")
                print(f"Number of videos: {len(info['entries'])}")
                print(f"Channel: {info.get('uploader', 'Unknown')}\n")
                return len(info['entries'])
            else:
                print("This appears to be a single video, not a playlist.")
                return 1
    except Exception as e:
        print(f"Error getting playlist info: {e}")
        return 0


def progress_hook(d):
    """Display download progress"""
    if d['status'] == 'downloading':
        try:
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"\r  Progress: {percent} | Speed: {speed} | ETA: {eta}", end='')
        except:
            pass
    elif d['status'] == 'finished':
        print(f"\n  ✓ Downloaded: {d['filename']}")


def main():
    print("=" * 60)
    print("         YouTube Playlist Downloader (yt-dlp)         ")
    print("=" * 60)
    print("\nOptions:")
    print("  1 - Download complete playlist")
    print("  2 - Resume download from specific video")
    print("  3 - Download specific range (custom)")
    print("  4 - Get playlist information only")
    print("=" * 60)
    
    try:
        option = input("\nEnter your option (1-4): ").strip()
        
        if option == '1':
            url = input("Enter playlist URL: ").strip()
            output = input("Enter output folder (default: downloads): ").strip() or "downloads"
            get_playlist_info(url)
            download_complete_playlist(url, output)
            
        elif option == '2':
            url = input("Enter playlist URL: ").strip()
            start_from = int(input("Enter video number to resume from: "))
            output = input("Enter output folder (default: downloads): ").strip() or "downloads"
            get_playlist_info(url)
            resume_download(url, start_from, output)
            
        elif option == '3':
            url = input("Enter playlist URL: ").strip()
            start = int(input("Enter starting video number: "))
            end = int(input("Enter ending video number: "))
            output = input("Enter output folder (default: downloads): ").strip() or "downloads"
            get_playlist_info(url)
            download_partial_playlist(url, start, end, output)
            
        elif option == '4':
            url = input("Enter playlist URL: ").strip()
            count = get_playlist_info(url)
            if count > 0:
                print(f"Playlist contains {count} video(s)")
        
        else:
            print("Invalid option. Please run the script again and choose 1-4.")
            
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    main()