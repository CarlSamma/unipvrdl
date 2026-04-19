<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# proponi modifiche per adattare il git a unipvr.md system

Ora ho un quadro chiaro. Il file `unipvr.md` descrive un sistema completamente diverso da Panopto: si tratta di **SharePoint/Microsoft 365 di UniPR** (Università di Parma), dove i video sono serviti come blob MP4 diretti tramite API REST di SharePoint, non tramite Panopto. Di seguito le modifiche proposte al repository.

***

## Contesto della differenza

Il repo attuale (`unipvrdl`) gestisce download da **Panopto** (UniPV/UniMI) usando `yt-dlp` con URL del viewer e cookie . Il sistema UniPR descritto in `unipvr.md` usa invece **SharePoint Online** con API REST (`_api/web/GetFileByServerRelativePath`), URL MP4 diretti e cookie Microsoft 365 (`FedAuth`, `rtFa`, `ESTSAUTH`). Sono architetture radicalmente diverse.[^1]

***

## Modifiche proposte al codice

### 1. Nuovo modulo `sharepoint_downloader.py`

Creare `sharepoint/sharepoint_downloader.py` — un modulo dedicato al download da SharePoint UniPR, separato dal flusso Panopto:

```python
# sharepoint/sharepoint_downloader.py
# Modulo per il download da SharePoint UniPR

import requests
import os
from urllib.parse import unquote, urlparse, parse_qs

SHAREPOINT_HEADERS = {
    "Referer": "https://univpr.sharepoint.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def is_stream_url(url: str) -> bool:
    """Verifica se l'URL è un stream.aspx (web player) e non un URL diretto."""
    return "stream.aspx" in url.lower()

def extract_server_relative_path_from_stream_url(url: str) -> str:
    """
    Estrae il server-relative path da un URL stream.aspx.
    Esempio: https://univpr.sharepoint.com/sites/.../_layouts/15/stream.aspx?id=%2Fsites%2F...%2Ffile.mp4
    → /sites/.../file.mp4
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    if 'id' in query_params:
        server_relative = unquote(query_params['id'][0])
        return server_relative
    
    raise ValueError(f"Impossibile estrarre il path dall'URL stream: {url}")

def build_direct_file_url(site_url: str, server_relative_path: str) -> str:
    """Costruisce l'URL diretto al file MP4 da SharePoint."""
    encoded_path = server_relative_path.replace(" ", "%20")
    return f"{site_url.rstrip('/')}{encoded_path}"

def get_direct_url(url: str, cookies_path: str) -> tuple[str, str]:
    """
    Converte un URL qualsiasi (stream.aspx o diretto) in un URL diretto MP4.
    Restituisce: (direct_url, site_url)
    """
    if is_stream_url(url):
        server_relative = extract_server_relative_path_from_stream_url(url)
        parsed = urlparse(url)
        site_url = f"{parsed.scheme}://{parsed.netloc}"
        direct_url = build_direct_file_url(site_url, server_relative)
        return direct_url, site_url
    else:
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        try:
            sites_index = path_parts.index('sites')
            site_path = '/'.join(path_parts[:sites_index + 2])
            site_url = f"{parsed.scheme}://{parsed.netloc}{site_path}"
        except ValueError:
            site_url = f"{parsed.scheme}://{parsed.netloc}"
        return url, site_url

def download_sharepoint_video(encoded_abs_url: str, cookies_path: str, output_path: str,
                               progress_callback=None) -> str:
    """
    Scarica un MP4 diretto da SharePoint usando i cookie Microsoft 365.
    Accetta anche URL stream.aspx (web player) e li converte automaticamente.
    """
    cookies = load_cookies_netscape(cookies_path)
    
    direct_url, site_url = get_direct_url(encoded_abs_url, cookies_path)
    
    with requests.get(direct_url, headers=SHAREPOINT_HEADERS,
                      cookies=cookies, stream=True) as r:
        if r.status_code == 401:
            raise Exception("Accesso negato (401). Cookie scaduti o non validi.")
        if r.status_code == 403:
            raise Exception("Accesso negato (403). Verifica i permessi sul file.")
        if r.status_code == 404:
            raise Exception("File non trovato (404). L'URL potrebbe essere errato.")
        r.raise_for_status()
        
        total = int(r.headers.get("content-length", 0))
        
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
                raise Exception("Il file scaricato è HTML. Verifica i cookie e l'accessibilità del video.")
    
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
```


***

### 2. Nuova tab GUI in `app.py`

Aggiungere una quarta tab **"SharePoint UniPR"** all'interfaccia PyQt6 esistente:

```python
# In app.py — aggiungere alla classe MainWindow

class SharepointTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Campo URL SharePoint (server relative path o encoded abs url)
        layout.addWidget(QLabel("URL SharePoint (EncodedAbsUrl o ServerRelativePath):"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://univpr.sharepoint.com/sites/.../video.mp4")
        layout.addWidget(self.url_input)

        # Campo Site URL (base del sito SharePoint)
        layout.addWidget(QLabel("Site URL (opzionale, per risoluzione API):"))
        self.site_url_input = QLineEdit()
        self.site_url_input.setPlaceholderText("https://univpr.sharepoint.com/sites/NomeSito")
        layout.addWidget(self.site_url_input)

        # Cookie file
        layout.addWidget(QLabel("File cookies.txt (con FedAuth, rtFa, ESTSAUTH):"))
        cookie_row = QHBoxLayout()
        self.cookie_path = QLineEdit()
        self.cookie_path.setPlaceholderText("Percorso al cookies.txt Microsoft 365")
        btn_cookie = QPushButton("Sfoglia...")
        btn_cookie.clicked.connect(self.browse_cookie)
        cookie_row.addWidget(self.cookie_path)
        cookie_row.addWidget(btn_cookie)
        layout.addLayout(cookie_row)

        # Output dir
        layout.addWidget(QLabel("Cartella di destinazione:"))
        out_row = QHBoxLayout()
        self.out_dir = QLineEdit()
        btn_out = QPushButton("Sfoglia...")
        btn_out.clicked.connect(self.browse_output)
        out_row.addWidget(self.out_dir)
        out_row.addWidget(btn_out)
        layout.addLayout(out_row)

        # Progress + pulsante
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        btn_dl = QPushButton("⬇ Scarica da SharePoint")
        btn_dl.clicked.connect(self.start_download)
        layout.addWidget(btn_dl)

    def browse_cookie(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona cookies.txt", "", "Text Files (*.txt)")
        if path:
            self.cookie_path.setText(path)

    def browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Seleziona cartella")
        if d:
            self.out_dir.setText(d)

    def start_download(self):
        from sharepoint.sharepoint_downloader import download_sharepoint_video
        url = self.url_input.text().strip()
        cookies = self.cookie_path.text().strip()
        out_dir = self.out_dir.text().strip() or "."
        filename = url.split("/")[-1].split("?")[^0]
        output_path = os.path.join(out_dir, filename)
        download_sharepoint_video(url, cookies, output_path,
                                  progress_callback=self.progress.setValue)
```


***

### 3. Estensione CLI in `app.py`

Aggiungere argomenti CLI per il flusso SharePoint:

```python
# Aggiungere al parser argparse esistente

sp_group = parser.add_argument_group("SharePoint UniPR")
sp_group.add_argument("--sharepoint-url", help="URL diretto MP4 da SharePoint")
sp_group.add_argument("--site-url", help="Base URL del sito SharePoint (per risoluzione API)")
sp_group.add_argument("--server-relative-path", help="ServerRelativePath del file su SharePoint")

# Logica di esecuzione CLI
if args.sharepoint_url:
    from sharepoint.sharepoint_downloader import download_sharepoint_video
    output = args.output or os.path.basename(args.sharepoint_url.split("?")[^0])
    download_sharepoint_video(args.sharepoint_url, args.cookies, output)
```


***

### 4. Aggiornamento `requirements.txt`

```
yt-dlp
PyQt6
moviepy
selenium>=4.0.0
requests          # ← NUOVO: per le API REST SharePoint
```


***

### 5. Nuova documentazione `md files/SHAREPOINT_SUPPORT.md`

```markdown
# Download da SharePoint UniPR

I video delle registrazioni su **univpr.sharepoint.com** sono serviti come
blob MP4 direttamente dalle API REST di SharePoint, senza Panopto.

## Cookie necessari (Microsoft 365)
- `FedAuth` — token federato SharePoint (obbligatorio)
- `rtFa` — refresh token
- `ESTSAUTH` / `ESTSAUTHPERSISTENT` — sessione Microsoft 365

## Come esportarli
1. Accedi a SharePoint con le credenziali UniPR
2. Apri la pagina del video e avvialo
3. Usa "Get cookies.txt LOCALLY" → Export (formato Netscape)

## Utilizzo CLI
```bash
python app.py --sharepoint-url "https://univpr.sharepoint.com/.../video.mp4" \
              --cookies cookies.txt --output lezione.mp4
```

```

***

## Riepilogo delle modifiche

| File | Tipo di modifica |
|---|---|
| `sharepoint/sharepoint_downloader.py` | **NUOVO** — modulo API REST SharePoint |
| `app.py` | **MODIFICA** — nuova tab GUI + argomenti CLI SharePoint |
| `requirements.txt` | **MODIFICA** — aggiunta `requests` |
| `md files/SHAREPOINT_SUPPORT.md` | **NUOVO** — documentazione |

<div align="center">⁂</div>

[^1]: unipvr.md```

