import requests
import re

# Test fetching the stream page
url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_layouts/15/stream.aspx?id=%2Fsites%2FMasterdiIlivelloinIstruzioneeriabilitazionenegliequid%5Fhxwrvb%2FDocumenti%20condivisi%2FGeneral%2FREGISTRAZIONI%2FMODULO%2001%2FIRE%20%2D%20M01%20%2D%20SALERI%20ROBERTA%2Emp4'

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

print('Fetching stream page...')
resp = requests.get(url, headers=headers, cookies=cookies)
print(f'Status: {resp.status_code}')
print(f'Content length: {len(resp.text)}')

# Search for tempauth pattern
pattern = r'download\.aspx\?UniqueId=([^&]+)[^>]*tempauth=([^&"\'<>\s]+)'
match = re.search(pattern, resp.text)
if match:
    print(f'Found! UniqueId: {match.group(1)[:30]}...')
    print(f'tempauth: {match.group(2)[:50]}...')
else:
    print('No tempauth pattern found')
    # Let's look for any download links
    dl_matches = re.findall(r'download\.aspx[^"]+', resp.text)
    print(f'Found {len(dl_matches)} download.aspx links')
    if dl_matches:
        print(f'First link: {dl_matches[0][:200]}')