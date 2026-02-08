import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hypotheken-Tracker", layout="wide")

st.title("📈 Hypothekarzinsen")
st.info("Diese Daten werden täglich automatisch via GitHub Actions aktualisiert.")

# Daten aus DB laden
def load_data():
    conn = sqlite3.connect('hypotheken.db')
    df = pd.read_sql_query("SELECT * FROM zinsen", conn)
    conn.close()
    # Datum konvertieren für bessere Sortierung
    df['datum'] = pd.to_datetime(df['datum'])
    return df

try:
    df = load_data()

    if not df.empty:
        # Filter für Laufzeit
        laufzeiten = df['laufzeit'].unique()
        auswahl = st.multiselect("Laufzeiten auswählen", laufzeiten, default=laufzeiten)
        typen = df['typ'].unique()
        typ_auswahl = st.radio("Zinstyp wählen", typen)

        filtered_df = df[(df['laufzeit'].isin(auswahl)) & (df['typ'] == typ_auswahl)]

        # Chart erstellen
        fig = px.line(filtered_df, x='datum', y='zinssatz', color='laufzeit',
                     title="Zinsverlauf über Zeit",
                     labels={'zinssatz': 'Zinssatz (%)', 'datum': 'Datum'},
                     markers=True)
        
        st.plotly_chart(fig, use_container_width=True)

        # Tabelle anzeigen
        st.subheader("Rohdaten")
        st.dataframe(df.sort_values(by='datum', ascending=False), use_container_width=True)
    else:
        st.warning("Noch keine Daten in der Datenbank vorhanden.")
except Exception as e:
    st.error(f"Fehler beim Laden der Daten: {e}")