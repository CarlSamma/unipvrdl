"""
PANOPTO SUBTITLES EXTRACTOR
Estrae sottotitoli da video Panopto
Autore: Comet
Data: 30 Nov 2025
"""

import json
import csv
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class PanoptoSubtitleExtractor:
    """
    Estrattore di sottotitoli da Panopto
    Supporta multiple formati di output: JSON, CSV, TXT, SRT
    """

    def __init__(self, url: str, output_dir: str = "./output", headless: bool = False, 
                 cookies_path: Optional[str] = None, progress_callback=None):
        """
        Inizializza l'estrattore
        
        Args:
            url: URL del video Panopto
            output_dir: Directory di output
            headless: Eseguire browser in modalità headless
            cookies_path: Percorso al file cookies.txt (Netscape format) per video protetti
            progress_callback: Funzione per riportare il progresso
        """
        self.url = url
        self.output_dir = Path(output_dir)
        self.cookies_path = cookies_path
        self.progress_callback = progress_callback or (lambda msg: print(msg))
        self.output_dir.mkdir(exist_ok=True)
        
        # Configura Chrome
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions") # Disabilita le estensioni che possono interferire
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        self.subtitles: str = ""  # SRT grezzo
        self.subtitles_data: List[Dict] = []  # Dati strutturati per export multipli formati

    def extract(self) -> bool:
        """
        Estrae i sottotitoli dalla pagina
        
        Returns:
            True se l'estrazione è riuscita, False altrimenti
        """
        try:
            self.progress_callback(f"[*] Accesso a: {self.url}")
            self.driver.get(self.url)
            
            # Carica i cookie se forniti (per video protetti)
            if self.cookies_path:
                self.progress_callback(f"[*] Caricamento cookie da: {self.cookies_path}")
                self._load_cookies()
                # Ricarica la pagina con i cookie
                self.driver.get(self.url)
            
            # Aggiungiamo una pausa fissa per dare tempo alla pagina (costruita con JS) di stabilizzarsi
            # prima di iniziare a cercare elementi.
            self.progress_callback("[*] Attesa che la pagina si stabilizzi...")
            time.sleep(5)
            self.progress_callback("[*] Pagina caricata. Si procede senza cercare iframe.")
            
            # Clicca sul tab Sottotitoli se non è già selezionato
            try:
                # Troviamo il tab in modo più robusto, cercando un elemento con ruolo 'tab' che contenga il testo 'Sottotitoli'.
                # Questo è più affidabile che usare un ID che potrebbe cambiare.
                self.progress_callback("[*] Ricerca del tab 'Sottotitoli'...")
                subtitle_tab = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[@role='tab' and contains(., 'Sottotitoli')]"))
                )
                # Usa JavaScript per il click, che è più robusto e bypassa problemi di visibilità
                self.driver.execute_script("arguments[0].click();", subtitle_tab)
                self.progress_callback("[*] Tab 'Sottotitoli' attivato")
                time.sleep(2)
            except Exception as e:
                self.progress_callback(f"[!] Errore nell'attivazione del tab: {e}")
                return False
            
            # Attende il caricamento della lista dei sottotitoli
            try:
                transcript_pane = self.wait.until(
                    EC.presence_of_element_located((By.ID, "transcriptTabPane"))
                )
                self.progress_callback("[+] Pane sottotitoli trovato")
            except Exception as e:
                self.progress_callback(f"[!] Errore nel trovare la lista sottotitoli: {e}")
                return False
            
            # Estrae i dati tramite JavaScript
            self.progress_callback("[*] Estrazione dati in corso...")
            self._parse_subtitles()
            
            if not self.subtitles_data:
                self.progress_callback("[!] Nessun sottotitolo trovato")
                return False
            
            self.progress_callback(f"[+] {len(self.subtitles_data)} sottotitoli estratti")
            return True
            
        except Exception as e:
            self.progress_callback(f"[!] Errore durante l'estrazione: {e}")
            return False
        finally:
            self.driver.quit()

    def _parse_subtitles(self):
        """Esegue lo script JS per estrarre i sottotitoli e li memorizza."""
        try:
            # Carica lo script JS dal file
            js_script_path = Path(__file__).parent / "JavaScriptBookmarklet.js"
            with open(js_script_path, 'r', encoding='utf-8') as f:
                js_script = f.read()
            
            self.progress_callback("[*] Esecuzione dello script di estrazione nel browser...")
            
            # Attendi che gli elementi <li> siano caricati
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support import expected_conditions as EC
                
                self.progress_callback("[*] Attesa caricamento elementi sottotitoli...")
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#transcriptTabPane li"))
                )
                import time
                time.sleep(2)  # Pausa aggiuntiva per renderizzazione completa
                self.progress_callback("[+] Elementi sottotitoli caricati")
            except Exception as e:
                self.progress_callback(f"[!] Timeout caricamento elementi: {e}")
            
            # Esegui lo script e ottieni il risultato
            # Avvolgiamo lo script in un return esplicito
            wrapped_script = f"return {js_script}"
            result = self.driver.execute_script(wrapped_script)
            
            # DEBUG: Stampa il tipo e contenuto del risultato
            self.progress_callback(f"[DEBUG] Tipo risultato: {type(result)}")
            self.progress_callback(f"[DEBUG] Risultato: {result}")
            
            if result and 'error' in result:
                self.progress_callback(f"[!] Errore dallo script JS: {result['error']}")
                return
            
            if result and 'srt' in result and result['srt']:
                # Memorizza il contenuto SRT grezzo
                self.subtitles = result['srt']
                # Converte SRT in dati strutturati per formati multipli
                self.subtitles_data = self._parse_srt_to_dict(result['srt'])
                self.progress_callback("[+] Script eseguito, contenuto SRT ricevuto e convertito.")
            else:
                self.progress_callback("[!] Lo script non ha restituito contenuto SRT.")

        except Exception as e:
            self.progress_callback(f"[!] Errore nel parsing: {e}")

    def _load_cookies(self):
        """Carica i cookie da file in formato Netscape nel browser"""
        try:
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
            
            self.progress_callback(f"[+] {len(cookie_jar)} cookie caricati")
        except Exception as e:
            self.progress_callback(f"[!] Errore nel caricamento cookie: {e}")

    def _parse_srt_to_dict(self, srt_content: str) -> List[Dict]:
        """
        Converte contenuto SRT in lista di dizionari
        
        Args:
            srt_content: Stringa in formato SRT
        
        Returns:
            Lista di dict con chiavi 'timestamp' e 'text'
        """
        entries = []
        blocks = srt_content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                # Estrae solo il timestamp iniziale (prima del ' --> ')
                timestamp_line = lines[1]
                if ' --> ' in timestamp_line:
                    timestamp = timestamp_line.split(' --> ')[0].strip()
                    # Unisce tutte le righe di testo (può essere multilinea)
                    text = '\n'.join(lines[2:]).strip()
                    entries.append({
                        'timestamp': timestamp,
                        'text': text
                    })
        
        return entries


    def save_json(self, filename: Optional[str] = None) -> Path:
        """Salva i sottotitoli in JSON"""
        filename = filename or "subtitles.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.subtitles_data, f, ensure_ascii=False, indent=2)
        
        self.progress_callback(f"[+] Salvato: {filepath}")
        return filepath

    def save_csv(self, filename: Optional[str] = None) -> Path:
        """Salva i sottotitoli in CSV"""
        filename = filename or "subtitles.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'text'])
            writer.writeheader()
            writer.writerows(self.subtitles_data)
        
        self.progress_callback(f"[+] Salvato: {filepath}")
        return filepath

    def save_txt(self, filename: Optional[str] = None) -> Path:
        """Salva i sottotitoli in TXT"""
        filename = filename or "subtitles.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for sub in self.subtitles_data:
                f.write(f"[{sub['timestamp']}]\n")
                f.write(f"{sub['text']}\n\n")
        
        self.progress_callback(f"[+] Salvato: {filepath}")
        return filepath

    def save_srt(self, filename: Optional[str] = None) -> Path:
        """Salva i sottotitoli in formato SRT"""
        filename = filename or "subtitles.srt"
        filepath = self.output_dir / filename
        
        # self.subtitles ora contiene direttamente il testo SRT
        if isinstance(self.subtitles, str):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.subtitles)

        self.progress_callback(f"[+] Salvato: {filepath}")
        return filepath


def main():
    """Funzione principale"""
    print("=" * 60)
    print("  PANOPTO SUBTITLES EXTRACTOR")
    print("=" * 60)
    
    # Configurazione
    url = input("\n[?] Inserisci URL Panopto: ").strip()
    
    if not url:
        print("[!] URL non fornito")
        return
    
    # Crea estrattore
    extractor = PanoptoSubtitleExtractor(url, headless=False)
    
    # Estrae
    if extractor.extract():
        # Salva in tutti i formati
        extractor.save_json()
        extractor.save_csv()
        extractor.save_txt()
        extractor.save_srt()
        
        print("\n[+] Estrazione completata!")
        print(f"[+] File salvati in: {extractor.output_dir}")
    else:
        print("\n[!] Estrazione fallita")


if __name__ == "__main__":
    main()
