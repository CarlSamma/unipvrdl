# 🍪 Supporto Cookie - Video Protetti

## Risposta alla Domanda

**Q: PER FAR ANDARE L'ESTRATTORE DEVO ANCHE CARICARE I COOKIE?**

**A: SÌ, se il video Panopto è protetto da autenticazione** (tipico per video universitari). 

Il supporto cookie è stato ora **implementato** in tutte le interfacce (GUI e CLI).

---

## Implementazione

### 1. Backend - `panopto_extractor.py`

#### Nuovo parametro `cookies_path`

```python
def __init__(self, url: str, output_dir: str = "./output", headless: bool = False, 
             cookies_path: Optional[str] = None, progress_callback=None):
```

#### Nuovo metodo `_load_cookies()`

Carica cookie da file Netscape format nel browser Selenium:

```python
def _load_cookies(self):
    """Carica i cookie da file in formato Netscape nel browser"""
    import http.cookiejar
    
    cookie_jar = http.cookiejar.MozillaCookieJar()
    cookie_jar.load(self.cookies_path, ignore_discard=True, ignore_expires=True)
    
    for cookie in cookie_jar:
        cookie_dict = {
            'name': cookie.name,
            'value': cookie.value,
            'domain': cookie.domain,
            'path': cookie.path,
            'secure': cookie.secure
        }
        if cookie.expires:
            cookie_dict['expiry'] = cookie.expires
        
        self.driver.add_cookie(cookie_dict)
```

#### Caricamento cookie in `extract()`

```python
self.driver.get(self.url)

# Carica i cookie se forniti (per video protetti)
if self.cookies_path:
    self.progress_callback(f"[*] Caricamento cookie da: {self.cookies_path}")
    self._load_cookies()
    # Ricarica la pagina con i cookie
    self.driver.get(self.url)
```

---

### 2. GUI - `app.py`

#### `SubtitleExtractionWorker`

Aggiunto parametro `cookies_path`:

```python
def __init__(self, url, output_dir, formats, cookies_path=None, headless=True):
    self.cookies_path = cookies_path
    # ...
```

#### `start_subtitle_extraction()`

Usa lo stesso campo cookie del download video:

```python
def start_subtitle_extraction(self):
    url = self.url_input.text().strip()
    cookies_path = self.cookies_input.text().strip()  # 🍪 Campo esistente!
    
    self.subtitle_worker = SubtitleExtractionWorker(
        url, 
        download_location, 
        selected_formats,
        cookies_path if cookies_path else None  # Passa i cookie
    )
```

---

### 3. CLI

Il CLI usa automaticamente il parametro `--cookies` esistente:

```python
# Supporto cookie per video protetti
cookies_path = args.cookies if args.cookies and os.path.exists(args.cookies) else None

extractor = PanoptoSubtitleExtractor(
    url=args.url,
    output_dir=args.output_dir,
    cookies_path=cookies_path,  # 🍪 Cookie automatically supported
    headless=True
)
```

---

## Come Usarlo

### GUI

1. **Inserire URL Panopto** nel campo "Panopto Viewer URL"
2. **Selezionare file cookie** con il bottone "Browse..." accanto a "Cookies File"
3. (Opzionale) Selezionare directory output
4. **Cliccare "Extract Subtitles"**

> **Nota:** Lo stesso campo cookie vale sia per il download video che per l'estrazione sottotitoli!

### CLI

```bash
# Con cookie (video protetto)
python app.py --url "https://unimi.cloud.panopto.eu/..." \
              --cookies cookies.txt \
              --extract-subtitles

# Con cookie + formati multipli
python app.py --url "URL" \
              --cookies cookies.txt \
              --extract-subtitles \
              --subtitle-formats srt json csv
```

---

## Come Ottenere i Cookie

### Metodo 1: Estensione Browser "Get cookies.txt"

1. Installa estensione **"Get cookies.txt"** su Chrome/Firefox
2. Vai su Panopto e fai login
3. Clicca estensione e salva `cookies.txt`
4. Usa quel file nell'app

### Metodo 2: Manuale (DevTools)

1. Apri Panopto in Chrome
2. Fai login
3. Premi F12 → Application tab → Cookies
4. Copia cookie manualmente (complesso, sconsigliato)

---

## Verifica

✅ Sintassi verificata con `py_compile`
✅ Cookie supportati in GUI
✅ Cookie supportati in CLI
✅ Backward compatible (cookie opzionali)

---

## Cosa Succede Senza Cookie?

**Video pubblico:** ✅ Funziona normalmente
**Video protetto:** ❌ Fallisce con errore

Messaggio tipico senza cookie su video protetto:
```
[!] Errore nel trovare la lista sottotitoli: ...
[!] Nessun sottotitolo trovato
```

**Soluzione:** Fornire file cookie valido!

---

**Stato:** ✅ Implementato e testato (sintassi)
**Data:** 7 Dicembre 2025
