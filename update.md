# Technical Explanation: Why yt-dlp Works with SharePoint URLs

## Overview

This document explains why the following command works correctly for downloading videos from SharePoint:

```bash
python app.py --sharepoint-url "https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_layouts/15/stream.aspx?id=%2Fsites%2FMasterdiIlivelloinIstruzioneeriabilitazionenegliequid%5Fhxwrvb%2FDocumenti%20condivisi%2FGeneral%2FREGISTRAZIONI%2FMODULO%2002%2FIRE%20%2D%20M01%20%2D%20VENTURA%20ANNARITA%2002%2Emp4&referrer=StreamWebApp%2EWeb&referrerScenario=AddressBarCopied%2Eview%2E0dbafb36%2D4a89%2D4478%2Da712%2D2be01b4621b2" --cookies cookies6.txt --output "videffffffo.mp4" --yt-dlp-path "d:\PROGETTI\Panoptoextractor_CC.venv\Scripts\yt-dlp.exe"
```

## Why This Works

### 1. SharePoint Stream.aspx Authentication

The `stream.aspx` page is Microsoft's internal video streaming endpoint for SharePoint/OneDrive. Unlike public video URLs, it requires:

- **Valid Microsoft 365 session cookies** - The cookies contain authentication tokens that prove you have access to the video
- **Proper cookie format** - SharePoint requires cookies in Netscape format (not JSON)

The `--cookies` parameter passes these authentication credentials to yt-dlp, allowing it to "impersonate" your browser session.

### 2. How yt-dlp Handles SharePoint

yt-dlp has built-in extractors for Microsoft services that:

1. Parse the SharePoint URL to extract the file identifier
2. Use the provided cookies to authenticate
3. Locate the actual video manifest (DASH/HLS stream)
4. Download the video segments and reassemble them

### 3. Format Selection: `dash-v720p/dash-v480p`

SharePoint typically stores videos in multiple quality levels using DASH (Dynamic Adaptive Streaming over HTTP):

| Format | Description |
|--------|-------------|
| `dash-v720p` | 720p HD quality (preferred) |
| `dash-v480p` | 480p SD quality (fallback) |
| `dash-v240p` | 240p low quality (if nothing else available) |
| `best` | Best available quality |

The `/` separator tells yt-dlp to try `v720p` first, and if unavailable, fall back to `v480p`.

### 4. The `--yt-dlp-path` Parameter

On Windows, Python's `shutil.which()` may not reliably locate `yt-dlp.exe` in virtual environments. The `--yt-dlp-path` parameter explicitly tells the application where to find yt-dlp:

```
d:\PROGETTI\Panoptoextractor_CC.venv\Scripts\yt-dlp.exe
```

This is especially important when:
- Using a virtual environment (`.venv`)
- yt-dlp is not in system PATH
- Running from an IDE or shortcut

### 5. URL Structure Breakdown

```
https://univpr.sharepoint.com/sites/[SITE_NAME]/_layouts/15/stream.aspx
?id=%2Fsites%2F[SITE_NAME]%2F[PATH]%2F[FILENAME].mp4
&referrer=StreamWebApp%2EWeb
&referrerScenario=AddressBarCopied%2Eview%2E[GUID]
```

- `stream.aspx` - SharePoint's internal video player endpoint
- `id` parameter - URL-encoded path to the file in SharePoint
- `referrer` - Indicates the request came from the Stream web app
- `referrerScenario` - Additional context for access control

### 6. Cookie Requirements

The cookies file must contain at minimum:

| Cookie Name | Purpose |
|-------------|---------|
| `rtFa` | Real-Time Federated Authentication token |
| `FedAuth` | Federated Authentication cookie |
| `ESRAuth` | Exchange Server authentication (sometimes needed) |
| `UserId` | User identifier |

**How to export cookies:**
1. Install "Get cookies.txt LOCALLY" Chrome/Firefox extension
2. Navigate to any SharePoint page while logged in
3. Export cookies in Netscape format
4. Save as `.txt` file

## Troubleshooting

### "This video is not available"
- Cookies expired - re-export cookies from browser
- User lacks permission to view the video
- Video was moved/deleted from SharePoint

### "yt-dlp not found"
- Specify `--yt-dlp-path` explicitly
- Or ensure yt-dlp is in system PATH
- Or install globally: `pip install yt-dlp`

### Slow downloads
- Check internet connection
- Try a different format (lower quality)
- Download during off-peak hours

## Alternative: Using GUI

The GUI application provides the same functionality with a visual interface:

```bash
python app.py
```

Navigate to the "SharePoint UniPR" tab, enter your URL, select your cookies file, choose download location, and click download.
