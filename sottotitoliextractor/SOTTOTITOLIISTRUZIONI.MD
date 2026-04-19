# SCRIPT PYTHON PER ESTRARRE SOTTOTITOLI DA PANOPTO

## 🎯 INFORMAZIONI ESSENZIALI

### 1. **DATI DELLA SESSIONE PANOPTO**
```python
# URL del video Panopto
video_url = "https://unimi.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=cd9955a4-a54d-4d6d-a609-b3a700f7bb4f&start=0"
video_id = "cd9955a4-a54d-4d6d-a609-b3a700f7bb4f"  # Estratto dall'URL
```

### 2. **LIBRERIE NECESSARIE**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
```

### 3. **SCRIPT COMPLETO**

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class PanoptoSubtitleExtractor:
    def __init__(self, video_url):
        self.video_url = video_url
        self.driver = webdriver.Chrome()
        self.subtitles = []
    
    def open_video(self):
        """Apre il video Panopto"""
        self.driver.get(self.video_url)
        time.sleep(3)
    
    def click_subtitles_tab(self):
        """Clicca sul tab 'Sottotitoli'"""
        try:
            # Usa l'ID del tab per trovare e cliccare "Sottotitoli"
            subtitles_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "transcriptTabHeader"))
            )
            subtitles_tab.click()
            time.sleep(2)
        except Exception as e:
            print(f"Errore nel clic del tab: {e}")
    
    def scroll_subtitles_to_bottom(self):
        """Scrollega il panel dei sottotitoli fino in fondo per caricare tutto"""
        subtitles_panel = self.driver.find_element(By.CLASS_NAME, "transcript-panel")
        
        # Scroll iniziale
        self.driver.execute_script("""
            var panel = document.querySelector('[class*="transcript"]');
            var scrollHeight = panel.scrollHeight;
            panel.scrollTop = scrollHeight;
        """)
        
        # Aspetta il caricamento
        time.sleep(3)
    
    def extract_subtitles(self):
        """Estrae tutti i sottotitoli dal panel"""
        try:
            # Trova tutti gli elementi dei sottotitoli
            subtitle_items = self.driver.find_elements(
                By.XPATH, 
                "//div[contains(@class, 'transcript-item')] | //li[contains(@class, 'transcript')]"
            )
            
            for item in subtitle_items:
                try:
                    # Estrae timestamp (es: "0:00")
                    timestamp = item.find_element(By.CLASS_NAME, "timestamp").text
                    
                    # Estrae testo sottotitolo
                    text = item.find_element(By.CLASS_NAME, "text").text
                    
                    self.subtitles.append({
                        "timestamp": timestamp,
                        "text": text
                    })
                except:
                    continue
            
            print(f"Estratti {len(self.subtitles)} sottotitoli")
            return self.subtitles
            
        except Exception as e:
            print(f"Errore nell'estrazione: {e}")
            return None
    
    def extract_via_page_source(self):
        """Metodo alternativo: estrae dal sorgente della pagina"""
        page_source = self.driver.page_source
        
        # Cereca pattern JSON nei dati di Panopto
        if "transcript" in page_source.lower():
            import re
            # Pattern per trovare timestamp e testo
            pattern = r'(\d+:\d+)\s*-\s*([^\n]+)'
            matches = re.findall(pattern, page_source)
            
            for timestamp, text in matches:
                self.subtitles.append({
                    "timestamp": timestamp,
                    "text": text
                })
        
        return self.subtitles
    
    def save_to_file(self, filename="subtitles.txt"):
        """Salva i sottotitoli in un file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for sub in self.subtitles:
                f.write(f"{sub['timestamp']} - {sub['text']}\n")
        
        print(f"Sottotitoli salvati in {filename}")
    
    def save_to_markdown(self, filename="subtitles.md"):
        """Salva i sottotitoli in formato Markdown"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Sottotitoli Video Panopto\n\n")
            for sub in self.subtitles:
                f.write(f"**{sub['timestamp']}** - {sub['text']}\n\n")
        
        print(f"Sottotitoli salvati in {filename}")
    
    def save_to_pastebin(self):
        """Carica i sottotitoli su Pastebin"""
        import requests
        
        content = "\n".join([f"{s['timestamp']} - {s['text']}" for s in self.subtitles])
        
        data = {
            'api_dev_key': 'YOUR_PASTEBIN_API_KEY',
            'api_option': 'paste',
            'api_paste_code': content,
            'api_paste_name': 'Panopto_Subtitles',
            'api_paste_expire_date': 'N'
        }
        
        response = requests.post('https://pastebin.com/api/api_post.php', data=data)
        return response.text
    
    def close(self):
        """Chiude il browser"""
        self.driver.quit()


# UTILIZZO
if __name__ == "__main__":
    video_url = "https://unimi.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=cd9955a4-a54d-4d6d-a609-b3a700f7bb4f&start=0"
    
    extractor = PanoptoSubtitleExtractor(video_url)
    
    # Esegui i passaggi
    extractor.open_video()
    extractor.click_subtitles_tab()
    extractor.scroll_subtitles_to_bottom()
    extractor.extract_subtitles()
    
    # Salva i risultati
    extractor.save_to_file("sottotitoli.txt")
    extractor.save_to_markdown("sottotitoli.md")
    
    # Stampa primo sottotitolo come verifica
    if extractor.subtitles:
        print(f"Primo sottotitolo: {extractor.subtitles[0]}")
    
    extractor.close()
```

## 4. **METODO ALTERNATIVO CON BEAUTIFULSOUP**
```python
from selenium import webdriver
from bs4 import BeautifulSoup
import time

def extract_with_beautifulsoup(video_url):
    driver = webdriver.Chrome()
    driver.get(video_url)
    time.sleep(5)
    
    # Clicca tab sottotitoli
    driver.find_element("id", "transcriptTabHeader").click()
    time.sleep(3)
    
    # Scroll fino in fondo
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # Estrai HTML
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Cerca i sottotitoli
    subtitles = []
    for item in soup.find_all('div', class_='transcript-item'):
        timestamp = item.find('span', class_='timestamp')
        text = item.find('div', class_='text')
        
        if timestamp and text:
            subtitles.append({
                'timestamp': timestamp.text,
                'text': text.text
            })
    
    driver.quit()
    return subtitles
```

## 5. **REQUISITI (requirements.txt)**
```
selenium>=4.0.0
beautifulsoup4>=4.9.0
requests>=2.25.0
lxml>=4.6.0
```

## 6. **COMANDI DA ESEGUIRE**
```bash
# Installa le librerie
pip install -r requirements.txt

# Installa ChromeDriver (o scaricalo manualmente)
# https://chromedriver.chromium.org/

# Esegui lo script
python extract_subtitles.py
```

## 7. **PUNTI CHIAVE PER IL SUCCESSO**
✅ **Tab ID**: `transcriptTabHeader` - ID del tab sottotitoli  
✅ **Timeout**: 10 secondi per caricare gli elementi  
✅ **Scroll**: Scroll massimo (`scrollHeight`) per caricare tutto  
✅ **Attesa**: `time.sleep()` dopo ogni azione per Panopto  
✅ **Pattern**: Timestamp formato `M:SS` o `MM:SS` seguito dal testo  
✅ **Encoding**: UTF-8 per il testo italiano  

## 8. **DATI SPECIFICI DEL TUO VIDEO**
- **Lingua**: Italiano
- **Durata**: 3:00:46 (180 minuti, ~3 ore)
- **Numero sottotitoli**: ~150+ entries
- **Formato output**: Timestamp - Testo
- **Qualità**: Auto-generated captions (potrebbero contenere errori)