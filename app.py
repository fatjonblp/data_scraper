import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Hypotheken-Tracker", layout="wide")

st.title("📈 Hypothekarzinsen & SARON Tracker")

# Sidebar für Einstellungen
st.sidebar.header("Einstellungen")
marge = st.sidebar.number_input("SARON Marge (%)", value=0.9, step=0.05)

def load_data():
    conn = sqlite3.connect('hypotheken.db')
    df = pd.read_sql_query("SELECT * FROM zinsen", conn)
    conn.close()
    df['datum'] = pd.to_datetime(df['datum'])
    if not df.empty:
        letztes_update = df['datum'].max()
        jetzt = datetime.now()
        differenz = jetzt - letztes_update

        if differenz > timedelta(days=2):
            st.error(f"⚠️ ACHTUNG: Die Daten sind veraltet! Letztes erfolgreiches Update: {letztes_update.strftime('%d.%m.%Y')}")
        else:
            st.caption(f"✅ Datenstand: {letztes_update.strftime('%d.%m.%Y')} (Aktualisiert via GitHub Actions)")
    return df

st.sidebar.markdown("---")
st.sidebar.header("Hypothekar-Rechner")
betrag = st.sidebar.number_input("Hypothekarbetrag (CHF)", value=500000, step=50000, format="%d")

try:
    df = load_data()

    if not df.empty:
        # --- NEU: TYP-FILTER IN DER SIDEBAR ---
        verfuegbare_typen = df['typ'].unique().tolist()
        auswahl_typ = st.sidebar.multiselect(
            "Zinstyp (Migros Bank):", 
            options=verfuegbare_typen, 
            default=["Vorzugszinssatz"] if "Vorzugszinssatz" in verfuegbare_typen else verfuegbare_typen
        )

        # Daten nach Typ filtern
        df = df[df['typ'].isin(auswahl_typ)].copy()

        # --- DATENAUFBEREITUNG ---
        # Wir erstellen ein Label, das Laufzeit und Typ kombiniert für den Chart
        df['Label'] = df['laufzeit'].astype(str)
        
        # SARON Logik
        is_saron = df['laufzeit'] == 'SARON'
        df.loc[is_saron, 'zinssatz'] += marge
        df.loc[is_saron, 'Label'] = df.loc[is_saron, 'laufzeit'] + f" (inkl. {marge}% Marge)"
        
        # Für Festhypotheken fügen wir den Typ zum Label hinzu, falls mehrere gewählt sind
        if len(auswahl_typ) > 1:
            df.loc[~is_saron, 'Label'] = df.loc[~is_saron, 'laufzeit'] + " (" + df.loc[~is_saron, 'typ'] + ")"
        else:
            df.loc[~is_saron, 'Label'] = df.loc[~is_saron, 'laufzeit']

        # --- CHART ---
        fig = px.line(
            df, 
            x='datum', 
            y='zinssatz', 
            color='Label', 
            markers=True,
            title="Zinsverlauf Vergleich",
            labels={'zinssatz': 'Effektiver Zins (%)', 'datum': 'Datum'}
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # --- KOSTEN-VERGLEICH ---
        st.subheader(f"Jährliche Zinskosten für CHF {betrag:,.0f}")
        
        latest_data = []
        # Wir gruppieren nach Label, um Typ + Laufzeit zu erhalten
        for label in df['Label'].unique():
            latest = df[df['Label'] == label].sort_values('datum').iloc[-1]
            kosten = (betrag * latest['zinssatz']) / 100
            latest_data.append({
                "Modell": label,
                "Zinssatz": f"{latest['zinssatz']:.2f} %",
                "Kosten pro Jahr": kosten,
                "Kosten pro Monat": kosten / 12
            })
        
        vergleich_df = pd.DataFrame(latest_data)
        st.table(vergleich_df.style.format({
            "Kosten pro Jahr": "CHF {:,.2f}",
            "Kosten pro Monat": "CHF {:,.2f}"
        }))

        if len(vergleich_df) > 1:
            ersparnis = vergleich_df['Kosten pro Jahr'].max() - vergleich_df['Kosten pro Jahr'].min()
            st.success(f"💡 Potenzielle Ersparnis zwischen teuerstem und günstigstem Modell: **CHF {ersparnis:,.2f} pro Jahr**")

except Exception as e:
    st.error(f"Fehler bei der Darstellung: {e}")