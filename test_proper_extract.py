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

stream_url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_layouts/15/stream.aspx?id=%2Fsites%2FMasterdiIlivelloinIstruzioneeriabilitazionenegliequid%5Fhxwrvb%2FDocumenti%20condivisi%2FGeneral%2FREGISTRAZIONI%2FMODULO%2001%2FIRE%20%2D%20M01%20%2D%20SALERI%20ROBERTA%2Emp4'

print('Step 1: Fetching stream page...')
resp = requests.get(stream_url, headers=headers, cookies=cookies)
print(f'Status: {resp.status_code}')

# Find the download URL with Unicode escapes
download_match = re.search(r'download\.aspx[^"\'<>\s]+', resp.text)
if not download_match:
    print('ERROR: No download URL found!')
    exit(1)

raw_url = download_match.group(0)
print(f'Raw URL (first 100 chars): {raw_url[:100]}...')

# Decode Unicode escapes like \u0026
decoded_url = raw_url.replace('\\u0026', '&')
print(f'Decoded URL (first 150 chars): {decoded_url[:150]}...')

# Now parse the parameters
from urllib.parse import urlparse, parse_qs
parsed = urlparse('?' + decoded_url.split('?')[1])
params = parse_qs(parsed.query)

print(f'\nParsed parameters:')
print(f'  UniqueId: {params.get("UniqueId", [""])[0]}')
tempauth = params.get('tempauth', [''])[0]
print(f'  tempauth: {tempauth[:60]}...' if tempauth else '  tempauth: NOT FOUND')

# Build the complete download URL
site_url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb'
download_url = f"{site_url}/_layouts/15/download.aspx?UniqueId={params['UniqueId'][0]}&Translate=false&tempauth={tempauth}"

print(f'\nStep 2: Downloading video...')
print(f'Download URL: {download_url[:150]}...')

response = requests.get(download_url, headers=headers, cookies=cookies, stream=True)
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.headers.get("content-type")}')

if response.status_code == 200:
    ct = response.headers.get("content-type", "")
    if "html" in ct.lower():
        print('Got HTML - checking error...')
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > 2000:
                break
        # Check title
        title_match = re.search(r'<title>(.*?)</title>', content.decode('utf-8', errors='ignore'))
        if title_match:
            print(f'Error title: {title_match.group(1).strip()}')
    else:
        total = int(response.headers.get('content-length', 0))
        print(f'SUCCESS! File size: {total / (1024*1024):.2f} MB')
        
        with open('test_proper_download.mp4', 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        size = os.path.getsize('test_proper_download.mp4')
        print(f'Saved to test_proper_download.mp4 ({size/(1024*1024):.2f} MB)')
else:
    print(f'ERROR: Status {response.status_code}')