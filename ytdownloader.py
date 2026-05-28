import yt_dlp
import os
from pathlib import Path


def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')

        print(
            f"\rProgress: {percent} | Speed: {speed} | ETA: {eta}",
            end=''
        )

    elif d['status'] == 'finished':
        print(f"\n✓ Downloaded: {d['filename']}")


def get_ydl_opts(output_folder, playlist_items=None):
    opts = {
        'format': 'bestvideo+bestaudio/best',

        'merge_output_format': 'mp4',

        'outtmpl': os.path.join(
            output_folder,
            '%(playlist_index)s. %(title)s.%(ext)s'
        ),

        'progress_hooks': [progress_hook],

        'ignoreerrors': True,
        'quiet': False,
        'noplaylist': False,

        'concurrent_fragment_downloads': 1,

        'retries': 10,
        'fragment_retries': 10,

        'extractor_args': {
            'youtube': {
                'player_client': ['android']
            }
        },

    }

    if playlist_items:
        opts['playlist_items'] = playlist_items

    return opts


def get_playlist_info(url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                print("\n" + "=" * 60)
                print(f"Playlist : {info.get('title', 'Unknown')}")
                print(f"Channel  : {info.get('uploader', 'Unknown')}")
                print(f"Videos   : {len(info['entries'])}")
                print("=" * 60 + "\n")

                return len(info['entries'])

            else:
                print("Single video detected.")
                return 1

    except Exception as e:
        print(f"Error getting playlist info: {e}")
        return 0


def download_complete_playlist(url, output_folder="downloads"):
    print("\nDownloading complete playlist...\n")

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    ydl_opts = get_ydl_opts(output_folder)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("\n✓ Playlist download complete!")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def resume_download(url, start_from, output_folder="downloads"):
    print(f"\nResuming from video {start_from}...\n")

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    ydl_opts = get_ydl_opts(
        output_folder,
        playlist_items=f"{start_from}-"
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("\n✓ Resume complete!")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def download_partial_playlist(
    url,
    start,
    end,
    output_folder="downloads"
):
    print(f"\nDownloading videos {start} to {end}...\n")

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    ydl_opts = get_ydl_opts(
        output_folder,
        playlist_items=f"{start}-{end}"
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("\n✓ Selected videos downloaded!")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def main():
    print("=" * 60)
    print("        ADVANCED YOUTUBE PLAYLIST DOWNLOADER")
    print("=" * 60)

    print("\nOptions:")
    print("1 - Download complete playlist")
    print("2 - Resume from specific video")
    print("3 - Download custom range")
    print("4 - Playlist info only")

    print("=" * 60)

    try:
        option = input("\nEnter option (1-4): ").strip()

        if option == '1':
            url = input("\nEnter playlist URL: ").strip()

            output = (
                input(
                    "Enter output folder (default: downloads): "
                ).strip()
                or "downloads"
            )

            get_playlist_info(url)

            download_complete_playlist(url, output)

        elif option == '2':
            url = input("\nEnter playlist URL: ").strip()

            start_from = int(
                input("Enter video number to resume from: ")
            )

            output = (
                input(
                    "Enter output folder (default: downloads): "
                ).strip()
                or "downloads"
            )

            get_playlist_info(url)

            resume_download(
                url,
                start_from,
                output
            )

        elif option == '3':
            url = input("\nEnter playlist URL: ").strip()

            start = int(
                input("Enter starting video number: ")
            )

            end = int(
                input("Enter ending video number: ")
            )

            output = (
                input(
                    "Enter output folder (default: downloads): "
                ).strip()
                or "downloads"
            )

            get_playlist_info(url)

            download_partial_playlist(
                url,
                start,
                end,
                output
            )

        elif option == '4':
            url = input("\nEnter playlist URL: ").strip()

            count = get_playlist_info(url)

            print(f"\nTotal videos: {count}")

        else:
            print("\nInvalid option.")

    except KeyboardInterrupt:
        print("\n\nDownload cancelled.")

    except Exception as e:
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    main()
