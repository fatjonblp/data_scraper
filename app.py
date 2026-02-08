import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Hypotheken-Tracker", layout="wide")

st.title("📈 Hypothekarzinsen & SARON Tracker")

# Sidebar für Einstellungen
st.sidebar.header("Einstellungen")
marge = st.sidebar.number_input("SARON Marge (%)", value=0.9, step=0.05)

# Daten aus DB laden
def load_data():
    conn = sqlite3.connect('hypotheken.db')
    df = pd.read_sql_query("SELECT * FROM zinsen", conn)
    conn.close()
    df['datum'] = pd.to_datetime(df['datum'])
    if not df.empty:
        # Das Datum des aktuellsten Eintrags finden
        letztes_update = df['datum'].max()
        jetzt = datetime.now()
        differenz = jetzt - letztes_update

        # Warnung anzeigen, wenn Daten älter als 2 Tage (48h) sind
        if differenz > timedelta(days=2):
            st.error(f"⚠️ ACHTUNG: Die Daten sind veraltet! Letztes erfolgreiches Update: {letztes_update.strftime('%d.%m.%Y')}")
            st.info("Bitte prüfe die GitHub Actions Logs, ob der Scraper einen Fehler hatte.")
        else:
            st.caption(f"✅ Datenstand: {letztes_update.strftime('%d.%m.%Y')} (Aktualisiert via GitHub Actions)")
    return df


# Sidebar Erweiterung
st.sidebar.markdown("---")
st.sidebar.header("Hypothekar-Rechner")
betrag = st.sidebar.number_input("Hypothekarbetrag (CHF)", value=500000, step=50000, format="%d")

try:
    df = load_data()

    if not df.empty:
        # --- DATENAUFBEREITUNG (wie zuvor) ---
        saron_raw = df[df['laufzeit'] == 'SARON'].copy()
        saron_effektiv = saron_raw.copy()
        saron_effektiv['zinssatz'] = saron_effektiv['zinssatz'] + marge
        saron_effektiv['laufzeit'] = f'SARON (inkl. {marge}% Marge)'
        
        festhypo_data = df[df['laufzeit'] != 'SARON'].copy()
        plot_df = pd.concat([festhypo_data, saron_effektiv])

        # --- CHART ---
        st.plotly_chart(px.line(plot_df, x='datum', y='zinssatz', color='laufzeit', markers=True), use_container_width=True)

        # --- KOSTEN-VERGLEICH ---
        st.subheader(f"Jährliche Zinskosten für CHF {betrag:,.0f}")
        
        # Die aktuellsten Werte holen
        latest_data = []
        for modell in plot_df['laufzeit'].unique():
            latest = plot_df[plot_df['laufzeit'] == modell].sort_values('datum').iloc[-1]
            kosten = (betrag * latest['zinssatz']) / 100
            latest_data.append({
                "Modell": modell,
                "Zinssatz": f"{latest['zinssatz']:.2f} %",
                "Kosten pro Jahr": kosten,
                "Kosten pro Monat": kosten / 12
            })
        
        vergleich_df = pd.DataFrame(latest_data)
        
        # Tabelle mit Formatierung
        st.table(vergleich_df.style.format({
            "Kosten pro Jahr": "CHF {:,.2f}",
            "Kosten pro Monat": "CHF {:,.2f}"
        }))

        # Einsparung berechnen (Beispiel: SARON vs. teuerstes Modell)
        if len(vergleich_df) > 1:
            max_kosten = vergleich_df['Kosten pro Jahr'].max()
            min_kosten = vergleich_df['Kosten pro Jahr'].min()
            ersparnis = max_kosten - min_kosten
            st.success(f"💡 Potenzielle Ersparnis zwischen teuerstem und günstigstem Modell: **CHF {ersparnis:,.2f} pro Jahr**")

except Exception as e:
    st.error(f"Fehler: {e}")