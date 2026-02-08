import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('hypotheken.db')
    c = conn.cursor()
    # Wir fügen eine Spalte 'typ' hinzu, um zwischen Online-Zins und Standard-Zins zu unterscheiden
    c.execute('''CREATE TABLE IF NOT EXISTS zinsen 
                 (datum TEXT, laufzeit TEXT, zinssatz REAL, typ TEXT)''')
    conn.commit()
    conn.close()

def scrape_migros_bank():
    url = "https://www.migrosbank.ch/de/privatpersonen/hypotheken/hypothekarmodelle/festhypothek.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        heute = datetime.now().strftime('%Y-%m-%d')

        # Die Migros Bank nutzt Tabellen für die Darstellung
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    text_laufzeit = cols[0].get_text(strip=True)
                    # Wir suchen Zeilen, die "Jahr" oder "Jahre" enthalten
                    if "Jahr" in text_laufzeit:
                        # Wir extrahieren alle Zinssätze in dieser Zeile
                        for i, col in enumerate(cols[1:], 1):
                            zins_raw = col.get_text(strip=True).replace('%', '')
                            try:
                                zins_val = float(zins_raw)
                                # Typ-Zuweisung: Oft ist die erste Spalte Online, die zweite Standard
                                typ = "Vorzugszinssatz" if i == 1 else "Standard"
                                results.append((heute, text_laufzeit, zins_val, typ))
                            except ValueError:
                                continue
        return results
    except Exception as e:
        print(f"Fehler beim Scraping: {e}")
        return []

def save_to_db(data):
    conn = sqlite3.connect('hypotheken.db')
    c = conn.cursor()
    # Wir speichern nun 4 Werte (datum, laufzeit, zinssatz, typ)
    c.executemany('INSERT INTO zinsen VALUES (?,?,?,?)', data)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    daten = scrape_migros_bank()
    if daten:
        save_to_db(daten)
        print(f"Erfolgreich {len(daten)} Zinssätze gespeichert.")
    else:
        print("Keine Daten extrahiert.")