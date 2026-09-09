import os
import sys
import threading

try:
    import yt_dlp
except ImportError:
    sys.exit("Error: yt-dlp package is missing. Run ./run_music.sh to auto-setup.")

# Shared global states accessed by layout managers
DOWNLOAD_URL = ""
DOWNLOAD_STATUS = "Idle"
DOWNLOAD_THREAD = None

def run_native_yt_downloader(url, output_dir):
    """Background thread worker to execute yt-dlp using its native Python API."""
    global DOWNLOAD_STATUS
    DOWNLOAD_STATUS = "Downloading..."
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '0',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        DOWNLOAD_STATUS = "Finished! Reloading..."
    except Exception as e:
        err_msg = str(e).strip()
        DOWNLOAD_STATUS = f"Error: {err_msg[:18]}..."

def trigger_download(url, output_dir):
    """Spawns an isolated thread sequence safely."""
    global DOWNLOAD_THREAD, DOWNLOAD_STATUS
    if DOWNLOAD_THREAD is None or not DOWNLOAD_THREAD.is_alive():
        DOWNLOAD_THREAD = threading.Thread(
            target=run_native_yt_downloader,
            args=(url, output_dir),
            daemon=True
        )
        DOWNLOAD_THREAD.start()
        return True, "Download thread deployed successfully."
    return False, "Wait, an active download stream is currently running!"
