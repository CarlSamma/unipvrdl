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

# Print what cookies we have
print('Cookies loaded:')
for name, value in cookies.items():
    print(f'  {name}: {value[:30]}...')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://univpr.sharepoint.com/',
}

# Stream URL
stream_url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_layouts/15/stream.aspx?id=%2Fsites%2FMasterdiIlivelloinIstruzioneeriabilitazionenegliequid%5Fhxwrvb%2FDocumenti%20condivisi%2FGeneral%2FREGISTRAZIONI%2FMODULO%2001%2FIRE%20%2D%20M01%20%2D%20SALERI%20ROBERTA%2Emp4'

print('\nStep 1: Fetching stream page...')
resp = requests.get(stream_url, headers=headers, cookies=cookies)
print(f'Status: {resp.status_code}')

# Get the actual download URL from the form
# Look for the form action in the stream page
form_match = re.search(r'action="([^"]*download\.aspx[^"]*)"', resp.text)
if form_match:
    action_url = form_match.group(1)
    print(f'Found form action: {action_url[:200]}...')
    
    # Decode the URL
    from urllib.parse import unquote
    decoded_url = unquote(action_url)
    print(f'Decoded URL: {decoded_url[:200]}...')
    
    # Now try to use this exact URL
    print('\nStep 2: Using exact download URL from form...')
    
    # We need to follow the form submission pattern
    # The form might need specific cookies or headers
    
    # Try directly with the extracted URL
    download_url = decoded_url.replace(' ', '%20')
    
    print(f'Fetching: {download_url[:150]}...')
    
    resp2 = requests.get(download_url, headers=headers, cookies=cookies)
    print(f'Status: {resp2.status_code}')
    print(f'Content-Type: {resp2.headers.get("content-type")}')
    
    if resp2.status_code == 200:
        ct = resp2.headers.get("content-type", "")
        if "html" in ct.lower():
            print('Got HTML error page')
            # Save to file to inspect
            with open('error_response.html', 'wb') as f:
                for chunk in resp2.iter_content(chunk_size=8192):
                    f.write(chunk)
            print('Saved to error_response.html')
            
            # Check for error message
            error_match = re.search(r'<title>(.*?)</title>', resp2.text)
            if error_match:
                print(f'Page title: {error_match.group(1)}')
        else:
            # It's video!
            total = int(resp2.headers.get('content-length', 0))
            print(f'SUCCESS! File size: {total / (1024*1024):.2f} MB')
            
            with open('test_download.mp4', 'wb') as f:
                for chunk in resp2.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f'Saved to test_download.mp4 ({os.path.getsize("test_download.mp4")/(1024*1024):.2f} MB)')
else:
    print('No form action found')