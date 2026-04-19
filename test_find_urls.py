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
    'Referer': 'https://univpr.sharepoint.com/',
}

stream_url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_layouts/15/stream.aspx?id=%2Fsites%2FMasterdiIlivelloinIstruzioneeriabilitazionenegliequid%5Fhxwrvb%2FDocumenti%20condivisi%2FGeneral%2FREGISTRAZIONI%2FMODULO%2001%2FIRE%20%2D%20M01%20%2D%20SALERI%20ROBERTA%2Emp4'

print('Fetching stream page...')
resp = requests.get(stream_url, headers=headers, cookies=cookies)
print(f'Status: {resp.status_code}')

# Find ALL download URLs in the page
all_download_urls = re.findall(r'download\.aspx[^"\'<>\s]+', resp.text)
print(f'\nFound {len(all_download_urls)} download.aspx URLs:')
for i, url in enumerate(all_download_urls[:5]):  # Show first 5
    print(f'{i+1}. {url[:200]}...')

# Also look for any URLs containing the UniqueId
unique_ids = re.findall(r'86d6ab21-9fa1-4aeb-9837-60e94033593d', resp.text)
print(f'\nFound UniqueId mentions: {len(unique_ids)}')

# Look for patterns around the tempauth
# The HTML might have URL-encoded tempauth
tempauth_patterns = re.findall(r'tempauth=([A-Za-z0-9%_-]{50,})', resp.text)
print(f'\nFound tempauth patterns: {len(tempauth_patterns)}')
if tempauth_patterns:
    print(f'First: {tempauth_patterns[0][:80]}...')