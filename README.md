# 🎓 Panopto Video Downloader & Subtitle Extractor

Strumento **GUI + CLI** per scaricare video da piattaforme Panopto (es. UniMI, UniPV) ed estrarre i sottotitoli in formato SRT, con supporto all'estrazione audio da video MP4.

---

## ✨ Funzionalità

| Funzione | GUI | CLI |
|---|---|---|
| Download video Panopto | ✅ | ✅ |
| Estrazione audio (MP3) da video | ✅ | ✅ |
| Estrazione sottotitoli (.srt) | ✅ | ✅ |
| Supporto cookie (video protetti) | ✅ | ✅ |
| Scelta cartella di destinazione | ✅ | ✅ |

---

## 📋 Prerequisiti

- **Python 3.10+**
- **Google Chrome** installato (necessario per l'estrazione sottotitoli)
- **ChromeDriver** compatibile con la versione di Chrome installata → [scarica qui](https://chromedriver.chromium.org/)

---

## 🚀 Installazione

### 1. Clona il repository

```bash
git clone https://github.com/CarlSamma/unipvrdl.git
cd unipvrdl
```

### 2. Crea e attiva l'ambiente virtuale

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> ⚠️ Se ricevi un errore di esecuzione degli script, esegui prima:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

**Windows (CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

**Dipendenze principali:**

| Pacchetto | Descrizione |
|---|---|
| `yt-dlp` | Download video da Panopto |
| `PyQt6` | Interfaccia grafica |
| `moviepy` | Estrazione audio da MP4 |
| `selenium>=4.0.0` | Estrazione sottotitoli via browser |

---

## 🖥️ Utilizzo — Modalità GUI

Avvia l'applicazione senza argomenti:

```bash
python app.py
```

L'interfaccia grafica permette di:

1. **Download Video**: incolla l'URL del viewer Panopto, seleziona il file `cookies.txt` e la cartella di destinazione.
2. **Estrazione Audio**: seleziona un file MP4 già scaricato → genera un `.mp3`.
3. **Estrazione Sottotitoli**: inserisci l'URL e premi *Extract Subtitles* → genera un file `.srt` nella cartella selezionata.

---

## ⌨️ Utilizzo — Modalità CLI

### Download video

```bash
python app.py --url "https://unimi.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=..." --cookies cookies.txt
```

```bash
# Con nome file personalizzato e cartella di destinazione
python app.py --url "URL_VIDEO" --cookies cookies.txt --output "lezione_01.mp4"
```

### Estrazione audio da video

```bash
python app.py --extract-audio "percorso/video.mp4"

# Con nome output personalizzato
python app.py --extract-audio "video.mp4" --audio-output "audio_lezione.mp3"
```

### Estrazione sottotitoli

```bash
python app.py --extract-subtitles --url "URL_VIDEO" --output-dir "./sottotitoli"

# Con cookie per video protetti
python app.py --extract-subtitles --url "URL_VIDEO" --cookies cookies.txt --output-dir "./output"
```

**Formati disponibili** (default: `srt`): `srt`, `json`, `csv`, `txt`

```bash
python app.py --extract-subtitles --url "URL_VIDEO" --subtitle-formats srt json txt
```

---

## 🍪 Come ottenere il file cookies.txt

I video Panopto sono spesso protetti da autenticazione. Per scaricarli è necessario esportare i cookie della sessione attiva:

1. Accedi al portale Panopto con le tue credenziali universitarie nel browser.
2. Installa l'estensione **"Get cookies.txt LOCALLY"** (Chrome/Firefox).
3. Vai sulla pagina del video e clicca sull'estensione → *Export cookies*.
4. Salva il file come `cookies.txt` in formato Netscape.
5. Usa questo file come parametro `--cookies` oppure selezionalo nella GUI.

---

## 📁 Struttura del progetto

```
Panoptoextractor_CC/
│
├── app.py                          # Applicazione principale (GUI + CLI)
├── requirements.txt                # Dipendenze Python
│
├── sottotitoliextractor/
│   ├── panopto_extractor.py        # Modulo estrazione sottotitoli (Selenium)
│   ├── JavaScriptBookmarklet.js    # Script JS iniettato nel browser per parsing SRT
│   └── SOTTOTITOLIISTRUZIONI.MD   # Documentazione tecnica del modulo
│
└── md files/
    ├── README_panopto_downloader.md
    ├── BUG_FIX.md
    ├── COOKIE_SUPPORT.md
    └── JS_FIX.md
```

---

## ⚙️ Argomenti CLI — Riferimento completo

```
python app.py [OPTIONS]

Opzioni video download:
  --url URL               URL del viewer Panopto
  --cookies FILE          Percorso al file cookies.txt (formato Netscape)
  --output NOME           Nome del file di output (opzionale)
  --yt-dlp-path PATH      Percorso a yt-dlp se non è nel PATH di sistema

Opzioni estrazione audio:
  --extract-audio FILE    Percorso al file video da cui estrarre l'audio
  --audio-output NOME     Nome del file audio di output (opzionale)

Opzioni estrazione sottotitoli:
  --extract-subtitles     Attiva la modalità estrazione sottotitoli
  --subtitle-formats ...  Formati: srt json csv txt (default: srt)
  --output-dir DIR        Cartella di output (default: ./output)
```

---

## 🐛 Problemi noti & Soluzioni

| Problema | Soluzione |
|---|---|
| `yt-dlp not found` | Esegui `pip install yt-dlp` oppure specifica `--yt-dlp-path` |
| `moviepy not installed` | Esegui `pip install moviepy` |
| `ChromeDriver` non trovato | Scarica la versione corretta da [chromedriver.chromium.org](https://chromedriver.chromium.org/) |
| Script PowerShell bloccato | Esegui `Set-ExecutionPolicy RemoteSigned -Scope Process` |
| Sottotitoli non estratti | Verifica che il video abbia sottotitoli abilitati e riprova con `headless=False` |
| Video protetto da login | Usa il file `cookies.txt` esportato dalla sessione attiva |

---

## 📄 Licenza

Progetto ad uso personale/didattico. Non distribuire i contenuti scaricati senza autorizzazione dell'ente titolare dei diritti.
