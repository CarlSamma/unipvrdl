import requests
import re

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
    'Referer': 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_layouts/15/stream.aspx',
}

stream_url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_layouts/15/stream.aspx?id=%2Fsites%2FMasterdiIlivelloinIstruzioneeriabilitazionenegliequid%5Fhxwrvb%2FDocumenti%20condivisi%2FGeneral%2FREGISTRAZIONI%2FMODULO%2001%2FIRE%20%2D%20M01%20%2D%20SALERI%20ROBERTA%2Emp4'

print('Step 1: Fetching stream page to get proper download URL...')
resp = requests.get(stream_url, headers=headers, cookies=cookies)
print(f'Status: {resp.status_code}')

# Get the raw download URL with Unicode escapes
download_match = re.search(r'download\.aspx[^"\'<>\s]+', resp.text)
if not download_match:
    print('ERROR: No download URL found!')
    exit(1)

raw_url = download_match.group(0)
decoded_url = raw_url.replace('\\u0026', '&')

# Parse the URL properly
from urllib.parse import urlparse, parse_qs, urlencode
parsed = urlparse('?' + decoded_url.split('?')[1])
params = parse_qs(parsed.query)

# Build download URL
site_url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb'
download_url = f"{site_url}/_layouts/15/download.aspx?UniqueId={params['UniqueId'][0]}&Translate=false&tempauth={params['tempauth'][0]}"

print(f'\nStep 2: Downloading video...')

# Use follow_redirects and check all headers
response = requests.get(download_url, headers=headers, cookies=cookies, allow_redirects=True)
print(f'Status: {response.status_code}')
print(f'Final URL: {response.url[:150]}...')
print(f'Content-Type: {response.headers.get("content-type")}')
print(f'Content-Length: {response.headers.get("content-length")}')
print(f'All headers:')
for k, v in response.headers.items():
    print(f'  {k}: {v[:80]}')

# Save the response to a file
with open('download_response.html', 'w') as f:
    f.write(response.text)

print(f'\nSaved response to download_response.html')
print(f'Response length: {len(response.text)} chars')

# Check if it's HTML
if '<html' in response.text.lower() or '<!doctype' in response.text.lower():
    print('\nIt is HTML - extracting error info:')
    title_match = re.search(r'<title>(.*?)</title>', response.text, re.DOTALL)
    if title_match:
        print(f'Title: {title_match.group(1).strip()}')
    
    # Check for error messages
    error_match = re.search(r'Error|error|Exception|exception|denied|Denied', response.text)
    if error_match:
        print('Found error keyword in response')
else:
    # It's video data
    print(f'\nFile size: {len(response.content) / (1024*1024):.2f} MB')
    with open('test_video.mp4', 'wb') as f:
        f.write(response.content)
    print('Saved to test_video.mp4')