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

## Utilizzo GUI
1. Seleziona la tab "SharePoint UniPR"
2. Inserisci l'URL diretto del video MP4
3. Seleziona il file cookies.txt con i token Microsoft 365
4. Scegli la cartella di destinazione
5. Clicca su "Scarica da SharePoint"

## Utilizzo CLI
```bash
python app.py --sharepoint-url "https://univpr.sharepoint.com/.../video.mp4" \
              --cookies cookies.txt --output lezione.mp4
```

## Utilizzo API (avanzato)
```python
from sharepoint.sharepoint_downloader import resolve_sharepoint_url, download_sharepoint_video

# Risolvi URL da server relative path
metadata = resolve_sharepoint_url(
    site_url="https://univpr.sharepoint.com/sites/NomeSito",
    server_relative_path="/sites/NomeSito/Video/lezione.mp4",
    cookies_path="cookies.txt"
)
print(metadata["EncodedAbsUrl"])

# Download diretto
download_sharepoint_video(
    encoded_abs_url="https://univpr.sharepoint.com/.../video.mp4",
    cookies_path="cookies.txt",
    output_path="lezione.mp4"
)
```
