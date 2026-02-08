import sqlite3
import pandas as pd
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import ssl
from email.mime.text import MIMEText
from datetime import datetime

def get_aktueller_saron():
    try:
        conn = sqlite3.connect('hypotheken.db')
        today_str = datetime.now().strftime('%Y-%m-%d')
        df = pd.read_sql_query(f"SELECT zinssatz FROM zinsen WHERE datum = '{today_str}' AND laufzeit = 'SARON' LIMIT 1", conn)
        conn.close()
        return df['zinssatz'].values[0] if not df.empty else "N/A"
    except:
        return "N/A"

def create_pdf():
    conn = sqlite3.connect('hypotheken.db')
    today_str = datetime.now().strftime('%Y-%m-%d')
    # Wir holen alle Daten von heute
    df = pd.read_sql_query(f"SELECT datum, laufzeit, zinssatz, typ FROM zinsen WHERE datum = '{today_str}'", conn)
    conn.close()

    if df.empty:
        print("Keine Daten für heute gefunden. PDF wird nicht erstellt.")
        return

    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(40, 70, 120) # Dunkelblau
    pdf.cell(0, 15, txt="Wöchentlicher Hypotheken-Report", ln=True, align='C')
    
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(100)
    pdf.cell(0, 10, txt=f"Berichtsdatum: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align='C')
    pdf.ln(10)

    # Tabellen-Einstellungen
    # Gesamtbreite ca. 190mm
    col_widths = [30, 70, 40, 50] 
    headers = ["Datum", "Modell", "Zinssatz", "Typ"]
    
    # Kopfzeile der Tabelle
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_fill_color(230, 230, 230) # Hellgrau
    pdf.set_text_color(0)
    
    for i in range(len(headers)):
        pdf.cell(col_widths[i], 10, headers[i], border=1, align='C', fill=True)
    pdf.ln() # Zeilenumbruch nach Kopfzeile

    # Datenzeilen
    pdf.set_font("Helvetica", size=10)
    for _, row in df.iterrows():
        # Falls es der SARON ist, machen wir die Zeile fett oder färben sie ein
        if "SARON" in str(row['laufzeit']).upper():
            pdf.set_font("Helvetica", 'B', 10)
            pdf.set_fill_color(240, 255, 240) # Ganz leichtes Grün
            fill = True
        else:
            pdf.set_font("Helvetica", size=10)
            fill = False

        pdf.cell(col_widths[0], 10, str(row['datum']), border=1, align='C', fill=fill)
        pdf.cell(col_widths[1], 10, str(row['laufzeit']), border=1, align='L', fill=fill)
        pdf.cell(col_widths[2], 10, f"{row['zinssatz']:.2f}%", border=1, align='C', fill=fill)
        pdf.cell(col_widths[3], 10, str(row['typ']), border=1, align='C', fill=fill)
        pdf.ln()

    pdf.output("report.pdf")

def send_email(aktueller_saron):
    # Diese Werte legst du in GitHub Secrets fest!
    from_email = os.environ.get("EMAIL_SENDER")
    to_email = os.environ.get("EMAIL_RECEIVER")
    api_key = str(os.environ.get("EMAIL_PASSWORD", "")).strip() 
    smtp_server = "smtp.sendgrid.net" # Beispiel mit SendGrid
    smtp_port = 465
    username = "apikey"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = f"📊 Zins-Report vom {datetime.now().strftime('%d.%m.%Y')}"
    # Der dynamische Textkörper
    body = f"""
Hallo!

Hier ist dein aktueller Zins-Report. 

📈 Aktueller SARON: {aktueller_saron}%
📅 Stand: {datetime.now().strftime('%d.%m.%Y')}

Im Anhang findest du die detaillierte PDF-Analyse mit dem Verlauf der Migros Bank Festhypotheken.
Für interaktive Charts und den vollständigen historischen Verlauf besuche die Web-App:
🔗 https://cxda4fakhsx24ptyrzcdcu.streamlit.app/

Beste Grüße,
Dein Python-Bot
    """
    msg.attach(MIMEText(body, 'plain'))
    with open("report.pdf", "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=zins_report.pdf")
        msg.attach(part)
    context = ssl.create_default_context()
    try:
        # Nutzung von SMTP_SSL für Port 465
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(username, api_key)
            server.send_message(msg)
            print("E-Mail erfolgreich versendet!")
    except Exception as e:
        print(f"Kritischer Fehler beim Versand: {e}")

if __name__ == "__main__":
    aktueller_saron = get_aktueller_saron()
    create_pdf()
    send_email(aktueller_saron)