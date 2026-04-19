## Informazioni estratte per il download del video

Tramite le **API REST di SharePoint** (senza bisogno di F12/DevTools), ho ottenuto tutti i metadati del file. [univpr.sharepoint](https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_api/web/GetFileByServerRelativePath(decodedurl='/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/Documenti%20condivisi/General/REGISTRAZIONI/MODULO%2001/IRE%20-%20M01%20-%20SALERI%20ROBERTA.mp4')?$select=Name,ServerRelativeUrl,UniqueId,LinkingUri,ListId)

***

### Dati identificativi del file

| Campo | Valore |
|---|---|
| **Nome file** | `IRE - M01 - SALERI ROBERTA.mp4` |
| **UniqueId (GUID file)** | `86d6ab21-9fa1-4aeb-9837-60e94033593d` |
| **ListId (GUID libreria)** | `f31807e5-2d6e-4c9d-9a73-442fff0a1658` |
| **Item ID** | `54` |
| **ServerRelativeUrl** | `/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/Documenti condivisi/General/REGISTRAZIONI/MODULO 01/IRE - M01 - SALERI ROBERTA.mp4` |

***

### URL di download diretto (EncodedAbsUrl)

```
https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/Documenti%20condivisi/General/REGISTRAZIONI/MODULO%2001/IRE%20-%20M01%20-%20SALERI%20ROBERTA.mp4
```

Questo è l'**URL diretto MP4** — non un manifest HLS né un flusso segmentato. Il file è servito direttamente da SharePoint come blob MP4. [univpr.sharepoint](https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/_api/web/GetFileByServerRelativePath(decodedurl='/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/Documenti%20condivisi/General/REGISTRAZIONI/MODULO%2001/IRE%20-%20M01%20-%20SALERI%20ROBERTA.mp4')/ListItemAllFields?$select=Id,FileRef,EncodedAbsUrl,FileDirRef)

***

### Comando di download con `curl` (usando il file cookie)

```bash
curl -L \
  -b cookies.txt \
  -H "Referer: https://univpr.sharepoint.com/" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36" \
  -o "IRE-M01-SALERI-ROBERTA.mp4" \
  "https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/Documenti%20condivisi/General/REGISTRAZIONI/MODULO%2001/IRE%20-%20M01%20-%20SALERI%20ROBERTA.mp4"
```

### Comando con `yt-dlp` (alternativa più robusta)

```bash
yt-dlp \
  --cookies cookies.txt \
  -o "IRE-M01-SALERI-ROBERTA.mp4" \
  "https://univpr.sharepoint.com/sites/MasterdiIlivelloinIstruzioneeriabilitazionenegliequid_hxwrvb/Documenti%20condivisi/General/REGISTRAZIONI/MODULO%2001/IRE%20-%20M01%20-%20SALERI%20ROBERTA.mp4"
```

***

### Nota sui cookie necessari

Il file cookie deve contenere almeno questi token (generati all'avvio del video sulla sessione autenticata):
- **`FedAuth`** — token federato SharePoint (più importante)
- **`rtFa`** — refresh token
- **`ESTSAUTH`** / **`ESTSAUTHPERSISTENT`** — sessione Microsoft 365

Esporta il file in formato **Netscape** con l'estensione "Get cookies.txt LOCALLY" mentre sei sulla pagina del video con il video **già avviato**.