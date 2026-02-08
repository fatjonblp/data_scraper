import sqlite3
import pandas as pd
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

def create_pdf():
    conn = sqlite3.connect('hypotheken.db')
    df = pd.read_sql_query("SELECT * FROM zinsen ORDER BY datum DESC LIMIT 20", conn)
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

    for i, row in df.head(15).iterrows():
        pdf.cell(40, 10, str(row['datum']), 1)
        pdf.cell(60, 10, str(row['laufzeit']), 1)
        pdf.cell(40, 10, f"{row['zinssatz']}%", 1, 1)
    
    pdf.output("report.pdf")

def send_email():
    # Diese Werte legst du in GitHub Secrets fest!
    from_email = os.environ.get("EMAIL_SENDER")
    to_email = os.environ.get("EMAIL_RECEIVER")
    password = os.environ.get("EMAIL_PASSWORD") 
    smtp_server = "smtp.sendgrid.net" # Beispiel mit SendGrid

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Dein wöchentlicher Zins-Report"

    with open("report.pdf", "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=zins_report.pdf")
        msg.attach(part)

    server = smtplib.SMTP(smtp_server, 587)
    server.starttls()
    server.login(from_email, password)
    server.send_message(msg)
    server.quit()

if __name__ == "__main__":
    create_pdf()
    send_email()