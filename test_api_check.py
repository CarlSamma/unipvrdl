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
    'Accept': 'application/json; odata=verbose',
    'Content-Type': 'application/json; odata=verbose',
}

site_url = 'https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb'
server_relative_path = '/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/Documenti condivisi/General/REGISTRAZIONI/MODULO 01/IRE - M01 - SALERI ROBERTA.mp4'

# Get file info via SharePoint API
api_url = f"{site_url}/_api/web/GetFileByServerRelativePath(decodedurl='{server_relative_path}')/ListItemAllFields"

print('Fetching file info via SharePoint REST API...')
print(f'URL: {api_url[:100]}...')

resp = requests.get(api_url, headers=headers, cookies=cookies)
print(f'Status: {resp.status_code}')

if resp.status_code == 200:
    data = resp.json()
    item = data.get('d', {})
    print(f'\nFile info:')
    print(f'  Name: {item.get("FileRef", "").split("/")[-1]}')
    print(f'  ID: {item.get("ID")}')
    print(f'  UniqueId: {item.get("FileRef", "")}')
    print(f'  FileSize: {item.get("FileLength", "N/A")}')
    
    # Check if we can get a download URL
    file_url = f"{site_url}/_api/web/GetFileByServerRelativePath(decodedurl='{server_relative_path}')/$value"
    print(f'\nDirect file API URL: {file_url}')
    
    # Try downloading via API
    print('\nTrying direct API download...')
    api_resp = requests.get(file_url, headers=headers, cookies=cookies, stream=True)
    print(f'Status: {api_resp.status_code}')
    print(f'Content-Type: {api_resp.headers.get("content-type")}')
    print(f'Content-Length: {api_resp.headers.get("content-length")}')
    
    if api_resp.status_code == 200:
        ct = api_resp.headers.get('content-type', '')
        if 'html' not in ct.lower():
            size = 0
            with open('test_api_download.mp4', 'wb') as f:
                for chunk in api_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    size += len(chunk)
            print(f'SUCCESS! Downloaded {size/(1024*1024):.2f} MB to test_api_download.mp4')
        else:
            print('Got HTML instead of video')
else:
    print(f'Error: {resp.text[:500]}')