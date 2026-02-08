import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

# 1. Datenbank-Setup
def init_db():
    conn = sqlite3.connect('hypotheken.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS zinsen 
                 (datum TEXT, laufzeit TEXT, zinssatz REAL)''')
    conn.commit()
    conn.close()

# 2. Daten von Migros Bank scrapen
def scrape_migros_bank():
    url = "https://www.migrosbank.ch/de/privatpersonen/hypotheken/hypothekarmodelle/festhypothek.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    # Hinweis: Die Selektoren müssen ggf. angepasst werden, wenn die Bank das Design ändert.
    # Wir suchen hier nach den typischen Tabellenzellen für Laufzeit und Zins.
    rows = soup.find_all('tr') 
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 2:
            laufzeit = cols[0].text.strip()
            zins_text = cols[1].text.strip().replace('%', '')
            try:
                zins = float(zins_text)
                results.append((datetime.now().strftime('%Y-%m-%d'), laufzeit, zins))
            except ValueError:
                continue
    return results

# 3. In Datenbank speichern
def save_to_db(data):
    conn = sqlite3.connect('hypotheken.db')
    c = conn.cursor()
    c.executemany('INSERT INTO zinsen VALUES (?,?,?)', data)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    daten = scrape_migros_bank()
    if daten:
        save_to_db(daten)
        print(f"{len(daten)} Einträge gespeichert.")
    else:
        print("Keine Daten gefunden. Evtl. Selektoren prüfen.")