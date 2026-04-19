# sharepoint/sharepoint_downloader.py
# Modulo per il download da SharePoint UniPR

import requests
import os
import re
import subprocess
import shutil
from urllib.parse import unquote, urlparse, parse_qs

SHAREPOINT_HEADERS = {
    "Referer": "https://univpr.sharepoint.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def is_stream_url(url: str) -> bool:
    """Verifica se l'URL è un stream.aspx (web player) e non un URL diretto."""
    return "stream.aspx" in url.lower()

def extract_server_relative_path_from_stream_url(url: str) -> str:
    """Estrae il server-relative path da un URL stream.aspx."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    if 'id' in query_params:
        server_relative = unquote(query_params['id'][0])
        return server_relative
    
    raise ValueError(f"Impossibile estrarre il path dall'URL stream: {url}")

def get_tempauth_from_stream_page(stream_url: str, cookies: dict) -> tuple:
    """
    Accede alla pagina stream.aspx e estrae il token tempauth e UniqueId dal form di download.
    """
    print(f"Accessing stream page to get tempauth token...")
    
    response = requests.get(stream_url, headers=SHAREPOINT_HEADERS, cookies=cookies)
    
    if response.status_code != 200:
        raise Exception(f"Impossibile accedere alla pagina stream: {response.status_code}")
    
    html_content = response.text
    
    # Cerca il tempauth nel form di download
    # Pattern: download.aspx?UniqueId=...&...tempauth=...
    download_pattern = r'download\.aspx\?UniqueId=([^&]+)[^>]*tempauth=([^&"\'<>\s]+)'
    match = re.search(download_pattern, html_content)
    
    if match:
        unique_id = match.group(1)
        tempauth = match.group(2)
        print(f"Got tempauth token! UniqueId: {unique_id[:20]}...")
        return tempauth, unique_id
    
    raise Exception("Impossibile trovare il token tempauth nella pagina stream")

def build_download_url_with_tempauth(site_url: str, unique_id: str, tempauth: str) -> str:
    """Costruisce l'URL di download con il token tempauth."""
    return f"{site_url}/_layouts/15/download.aspx?UniqueId={unique_id}&Translate=false&tempauth={tempauth}"

def download_sharepoint_video(url: str, cookies_path: str, output_path: str,
                               progress_callback=None) -> str:
    """
    Scarica un video da SharePoint usando i cookie Microsoft 365.
    Accetta URL stream.aspx o URL diretti.
    Per stream.aspx, estrae il tempauth token dalla pagina per autorizzare il download.
    Per URL diretti, usa yt-dlp.
    """
    cookies = load_cookies_netscape(cookies_path)
    
    # Determina se l'URL è stream.aspx
    if is_stream_url(url):
        print(f"Detected stream.aspx URL - using tempauth method")
        
        # Estrai il site URL base
        parsed = urlparse(url)
        site_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Ottieni il tempauth dalla pagina stream
        tempauth, unique_id = get_tempauth_from_stream_page(url, cookies)
        
        # Costruisci l'URL di download con tempauth
        download_url = build_download_url_with_tempauth(site_url, unique_id, tempauth)
        
        print(f"Download URL prepared")
        
        # Download con requests usando il tempauth
        with requests.get(download_url, headers=SHAREPOINT_HEADERS,
                          cookies=cookies, stream=True) as r:
            if r.status_code == 401:
                raise Exception("Accesso negato (401). Cookie scaduti o non validi.")
            if r.status_code == 403:
                raise Exception("Accesso negato (403). Verifica i permessi sul file.")
            if r.status_code == 404:
                raise Exception("File non trovato (404). L'URL potrebbe essere errato.")
            r.raise_for_status()
            
            total = int(r.headers.get("content-length", 0))
            print(f"File size: {total / (1024*1024):.2f} MB")
            
            with open(output_path, "wb") as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total:
                        progress_callback(int(downloaded / total * 100))
            
            # Verifica che il file non sia HTML
            if os.path.getsize(output_path) < 10000:
                with open(output_path, 'rb') as f:
                    start = f.read(500)
                if start.startswith(b'<!DOCTYPE') or start.startswith(b'<html'):
                    os.remove(output_path)
                    raise Exception("Il file scaricato è HTML. Il tempauth potrebbe essere scaduto.")
        
        return output_path
    
    else:
        # URL diretto - usa yt-dlp
        return download_with_ytdlp(url, cookies_path, output_path, progress_callback)

def download_with_ytdlp(url: str, cookies_path: str, output_path: str, 
                         progress_callback=None) -> str:
    """Download usando yt-dlp."""
    yt_dlp_cmd = shutil.which('yt-dlp')
    if not yt_dlp_cmd:
        raise Exception('yt-dlp not found. Install with: pip install yt-dlp')
    
    command = [
        yt_dlp_cmd,
        '--cookies', cookies_path,
        '--no-check-certificates',
        url,
        '-o', output_path
    ]
    
    print(f"Running yt-dlp: {' '.join(command[:4])}...")
    
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output)
            if progress_callback and '%' in output:
                try:
                    pct = int(output.split('%')[0].split()[-1])
                    progress_callback(pct)
                except:
                    pass
    
    rc = process.poll()
    if rc != 0:
        raise Exception(f"Download failed with exit code {rc}")
    
    return output_path

def load_cookies_netscape(path: str) -> dict:
    """Carica un file cookies.txt in formato Netscape → dict.
    
    Formato Netscape: domain | tailmatch | path | secure | expiration | name | value
    """
    cookies = {}
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 7:
                cookies[parts[5]] = parts[6]  # name = index 5, value = index 6
    return cookies