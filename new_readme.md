# Panoptoextractor_CC

A powerful tool for downloading videos from **Panopto** and **SharePoint** with support for audio extraction and subtitle download.

## Features

- 📥 Download videos from Panopto Cloud
- 📁 Download videos from SharePoint/OneDrive
- 🎵 Extract audio from downloaded videos
- 📝 Download subtitles from Panopto videos
- 🖥️ GUI and CLI interfaces

## Installation

### Prerequisites

- Python 3.8 or higher
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (installed automatically)
- [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/) browser extension (for cookie export)

### Setup

```bash
# Clone the repository
git clone https://github.com/CarlSamma/unipvrdl.git
cd unipvrdl

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### GUI Mode

```bash
python app.py
```

The GUI has two tabs:
1. **Panopto Download** - Download from Panopto Cloud
2. **SharePoint UniPR** - Download from SharePoint

### CLI Mode

#### Download from SharePoint

```bash
python app.py --sharepoint-url "https://univpr.sharepoint.com/sites/SITE/_layouts/15/stream.aspx?id=..." --cookies cookies.txt --output "video.mp4"
```

#### Download from SharePoint (with explicit yt-dlp path)

```bash
python app.py --sharepoint-url "YOUR_SHAREPOINT_URL" --cookies "cookies6.txt" --output "videffffffo.mp4" --yt-dlp-path "d:\PROGETTI\Panoptoextractor_CC.venv\Scripts\yt-dlp.exe"
```

#### Download from Panopto

```bash
python app.py --url "https://unimi.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=..." --cookies cookies.txt
```

#### Extract Audio

```bash
python app.py --extract-audio "video.mp4" --audio-output "audio.mp3"
```

#### Extract Subtitles

```bash
python app.py --extract-subtitles --url "PANOPTO_URL" --cookies cookies.txt --subtitle-formats srt
```

## Getting Cookies

### Chrome/Firefox

1. Install the ["Get cookies.txt LOCALLY"](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/) extension
2. Log into your SharePoint/Microsoft 365 account
3. Click the extension icon and export cookies
4. Save as `.txt` file

### Required Cookies

For SharePoint downloads, ensure your cookies include:
- `rtFa` - Authentication token
- `FedAuth` - Federated authentication cookie

## Usage Examples

### Complete SharePoint Download

```bash
# Full command with all parameters
python app.py \
    --sharepoint-url "https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_layouts/15/stream.aspx?id=%2Fsites%2FMasterdiIlivelloinIstruzioneeriabilitazionenegliequid%5Fhxwrvb%2FDocumenti%20condivisi%2FGeneral%2FREGISTRAZIONI%2FMODULO%2002%2FIRE%20%2D%20M01%20%2D%20VENTURA%20ANNARITA%2002%2Emp4&referrer=StreamWebApp%2EWeb&referrerScenario=AddressBarCopied%2Eview%2E0dbafb36%2D4a89%2D4478%2Da712%2D2be01b4621b2" \
    --cookies cookies6.txt \
    --output "videffffffo.mp4" \
    --yt-dlp-path "d:\PROGETTI\Panoptoextractor_CC.venv\Scripts\yt-dlp.exe"
```

### Batch Download with Different Output Paths

```bash
# Download to specific directory
python app.py --sharepoint-url "SHAREPOINT_URL" --cookies cookies.txt --output "Downloads/video.mp4"
```

## Command Line Arguments

### SharePoint Options

| Argument | Description | Required |
|----------|-------------|----------|
| `--sharepoint-url` | SharePoint video URL (stream.aspx) | Yes |
| `--cookies` | Path to cookies file (Netscape format) | Yes |
| `--output` | Output filename | No |
| `--yt-dlp-path` | Path to yt-dlp executable | No |

### Panopto Options

| Argument | Description | Required |
|----------|-------------|----------|
| `--url` | Panopto viewer URL | Yes |
| `--cookies` | Path to cookies file | Yes |
| `--output` | Output filename | No |

### Audio Extraction Options

| Argument | Description | Required |
|----------|-------------|----------|
| `--extract-audio` | Path to video file | Yes |
| `--audio-output` | Output audio filename | No |

### Subtitle Extraction Options

| Argument | Description | Default |
|----------|-------------|---------|
| `--extract-subtitles` | Enable subtitle extraction | - |
| `--url` | Panopto video URL | Yes |
| `--subtitle-formats` | Output formats | `srt` |
| `--output-dir` | Output directory | `./output` |

## Troubleshooting

### "yt-dlp not found"

**Solution:** Use `--yt-dlp-path` to specify the yt-dlp executable location:

```bash
python app.py --yt-dlp-path "C:\path\to\yt-dlp.exe" ...
```

### "Cookies file not found"

**Solution:** 
1. Verify the cookies file exists
2. Check the file path is correct
3. Ensure the file has `.txt` extension

### "Video not available" / "Access denied"

**Solutions:**
1. Re-export fresh cookies (they may have expired)
2. Verify you have access to the video in SharePoint
3. Check if the video was moved or deleted

### Slow Downloads

**Solutions:**
1. Check your internet connection
2. Try downloading during off-peak hours
3. Use a lower quality format if available

## Project Structure

```
Panoptoextractor_CC/
├── app.py                 # Main application (GUI + CLI)
├── requirements.txt       # Python dependencies
├── sharepoint/           # SharePoint utilities
├── panop/                # Panopto utilities
├── sottotitoliextractor/  # Subtitle extractor
└── md files/             # Documentation
```

## Dependencies

- **yt-dlp** - Video downloading engine
- **PyQt6** - GUI framework
- **moviepy** - Audio extraction
- **selenium** - Browser automation (for some features)
- **requests** - HTTP library

## License

This project is for educational purposes. Please respect copyright and only download content you have permission to access.

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The video downloader engine
- [Panopto](https://www.panopto.com/) - Video platform
- [SharePoint](https://sharepoint.com/) - Microsoft collaboration platform
