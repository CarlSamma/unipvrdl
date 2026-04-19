import requests
import re
import os

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

# Extract tempauth
pattern = r'download\.aspx\?UniqueId=([^&]+)[^>]*tempauth=([^&"\'<>\s]+)'
match = re.search(pattern, resp.text)
if not match:
    print('ERROR: Could not find tempauth!')
    exit(1)

unique_id = match.group(1)
tempauth = match.group(2)
print(f'Got UniqueId: {unique_id}')
print(f'Got tempauth: {tempauth[:50]}...')

# Build download URL
site_url = 'https://univpr.sharepoint.com'
download_url = f"{site_url}/_layouts/15/download.aspx?UniqueId={unique_id}&Translate=false&tempauth={tempauth}"

print(f'\nStep 2: Downloading video...')
print(f'Download URL: {download_url[:100]}...')

response = requests.get(download_url, headers=headers, cookies=cookies, stream=True)
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.headers.get("content-type")}')
print(f'Content-Length: {response.headers.get("content-length")}')

if response.status_code == 200:
    total = int(response.headers.get('content-length', 0))
    print(f'File size: {total / (1024*1024):.2f} MB')
    
    with open('test_tempauth_download.mp4', 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = int(downloaded / total * 100)
                if downloaded % (1024*1024) < 8192:  # Print every ~1MB
                    print(f'Downloaded: {pct}% ({downloaded/(1024*1024):.1f} MB)')
    
    print(f'\nDownload complete! File: test_tempauth_download.mp4')
    print(f'File size on disk: {os.path.getsize("test_tempauth_download.mp4") / (1024*1024):.2f} MB')
else:
    print(f'ERROR: Download failed with status {response.status_code}')