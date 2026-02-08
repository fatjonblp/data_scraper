import sqlite3
import pandas as pd
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import ssl
from datetime import datetime

def create_pdf():
    conn = sqlite3.connect('hypotheken.db')
    today_str = datetime.now().strftime('%Y-%m-%d')
    df = pd.read_sql_query(f"SELECT * FROM zinsen WHERE datum = '{today_str}' ORDER BY laufzeit", conn)
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Wöchentlicher Hypotheken-Report", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Erstellt am: {pd.to_datetime('today').strftime('%d.%m.%Y')}", ln=True)
    
    # Einfache Tabelle im PDF
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(40, 10, "Datum", 1, 0, 'C', True)
    pdf.cell(60, 10, "Modell", 1, 0, 'C', True)
    pdf.cell(40, 10, "Zinssatz", 1, 1, 'C', True)

    for i, row in df.iterrows():
        pdf.cell(40, 10, str(row['datum']), 1)
        pdf.cell(60, 10, str(row['laufzeit']), 1)
        pdf.cell(40, 10, f"{row['zinssatz']}%", 1, 1)
    
    pdf.output("report.pdf")

def send_email():
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
    msg['Subject'] = f"Zins-Report vom {datetime.now().strftime('%d.%m.%Y')}"

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
    create_pdf()
    send_email()