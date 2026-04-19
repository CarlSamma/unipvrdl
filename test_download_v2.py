import requests
import re
import os
from urllib.parse import unquote

# Load cookies
cookies = {}
with open('univpr.sharepoint.com_cookies.txt') as f:
    for line in f:
        if line.startswith('#') or not line.strip():
            continue
        parts = line.strip().split('\t')
        if len(parts) >= 7:
            cookies[parts[5]] = parts[6]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://univpr.sharepoint.com/',
}

# Stream URL
stream_url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_layouts/15/stream.aspx?id=%2Fsites%2FMasterdiIlivelloinIstruzioneeriabilitazionenegliequid%5Fhxwrvb%2FDocumenti%20condivisi%2FGeneral%2FREGISTRAZIONI%2FMODULO%2001%2FIRE%20%2D%20M01%20%2D%20SALERI%20ROBERTA%2Emp4'

print('Step 1: Fetching stream page to get tempauth...')
resp = requests.get(stream_url, headers=headers, cookies=cookies)
print(f'Status: {resp.status_code}')

# Better pattern - GUID format is 8-4-4-4-12 hex chars
# download.aspx?UniqueId=86d6ab21-9fa1-4aeb-9837-60e94033593d&...tempauth=...
guid_pattern = r'download\.aspx\?UniqueId=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
match = re.search(guid_pattern, resp.text)
if not match:
    print('ERROR: Could not find valid UniqueId GUID!')
    exit(1)

unique_id = match.group(1)
print(f'Got UniqueId: {unique_id}')

# Now find tempauth after this match
# Find the download URL starting from the match position
start_pos = match.start()
download_section = resp.text[start_pos:start_pos+2000]

# Find tempauth in this section
tempauth_match = re.search(r'tempauth=([^&\s]+)', download_section)
if tempauth_match:
    tempauth = tempauth_match.group(1)
    print(f'Got tempauth: {tempauth[:50]}...')
else:
    print('ERROR: Could not find tempauth!')
    exit(1)

# Build download URL - use site URL with the path
site_url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb'
download_url = f"{site_url}/_layouts/15/download.aspx?UniqueId={unique_id}&Translate=false&tempauth={tempauth}"

print(f'\nStep 2: Downloading video...')
print(f'Download URL: {download_url[:100]}...')

response = requests.get(download_url, headers=headers, cookies=cookies, stream=True)
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.headers.get("content-type")}')

if response.status_code == 200:
    content_type = response.headers.get("content-type", "")
    if "html" in content_type.lower():
        # Check what we got
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > 5000:
                break
        print(f'Got HTML instead of video (first 500 chars):')
        print(content[:500].decode('utf-8', errors='ignore'))
    else:
        total = int(response.headers.get('content-length', 0))
        print(f'File size: {total / (1024*1024):.2f} MB')
        
        with open('test_tempauth_download.mp4', 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
        
        print(f'\nDownload complete! File: test_tempauth_download.mp4')
        print(f'File size on disk: {os.path.getsize("test_tempauth_download.mp4") / (1024*1024):.2f} MB')
else:
    print(f'ERROR: Download failed with status {response.status_code}')