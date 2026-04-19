# Panopto Video Downloader & Audio Extractor (CLI & GUI)

## What it does
- Downloads a Panopto-protected video given:
  1. The Panopto Viewer URL (from the address bar)
  2. A cookies.txt file (Netscape format, exported from browser while streaming)
- Extracts audio from downloaded MP4 files or any other video files

## Usage

### GUI Mode (Recommended)
Simply run the application without arguments:
```
python app.py
```
This opens a modern graphical interface where you can:
- **Download Videos**: Enter Panopto URL, select cookies file, and download videos
- **Extract Audio**: Select any video file and extract audio to MP3 format
- Monitor download and extraction progress in real-time
- View detailed status messages

### CLI Mode
For automated/scripted usage:

**Video Download:**
```
python app.py --url "<YOUR_PANOPTO_URL>" --cookies /path/to/cookies.txt
```

**Audio Extraction:**
```
python app.py --extract-audio /path/to/video.mp4
```

Optional CLI arguments:
- **Video Download**:
  - Specify output file: `--output myvideo.mp4`
  - On Windows, if yt-dlp.exe is not in PATH: `--yt-dlp-path C:\path\to\yt-dlp.exe`
- **Audio Extraction**:
  - Specify audio output file: `--audio-output myaudio.mp3`

## How to get cookies.txt
- Use extensions like "Get cookies.txt" for Chrome/Edge/Firefox
- Export from Panopto domain while the video is playing

## Installation & Setup
```
pip install -r requirements.txt
```

This installs:
- `yt-dlp`: The video downloader engine
- `PyQt6`: Modern GUI framework (optional, only needed for GUI mode)
- `moviepy`: Python library for video processing and audio extraction

## Features
- **Modern GUI**: Clean, intuitive interface with real-time progress
- **CLI Support**: Full command-line interface for automation
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Auto-detection**: Automatically finds yt-dlp installation
- **Progress Monitoring**: Live download and extraction progress with status updates
- **Error Handling**: Clear error messages and validation
- **Threading**: Non-blocking UI during downloads and audio extraction
- **Audio Extraction**: Extract MP3 audio from any video file (MP4, AVI, MKV, MOV, etc.) using pure Python
- **Download Location Selection**: Choose custom download directory for videos (audio files saved in same directory)
