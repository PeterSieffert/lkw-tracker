import streamlit as st
import gpxpy
import folium
from streamlit_folium import st_folium
import base64
import os
from datetime import timedelta

# --- KONFIGURATION ---
HEADER_HEIGHT_PIXELS = 480 

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def process_gpx_data(file):
    """Liest GPX Daten sicher aus (inklusive Datum)."""
    gpx = gpxpy.parse(file)
    points = []
    
    # 1. Punkte sammeln
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    
    if not points:
        for route in gpx.routes:
            for point in route.points:
                points.append((point.latitude, point.longitude))

    # 2. Bewegungsdaten
    moving_data = gpx.get_moving_data()
    dist_km = moving_data.moving_distance / 1000.0
    moving_time_seconds = moving_data.moving_time
    
    if moving_time_seconds > 0:
        avg_speed = dist_km / (moving_time_seconds / 3600.0)
    else:
        avg_speed = 0.0

    # 3. Zeit & Datum sicher ermitteln
    start_time_str = "-"
    end_time_str = "-"
    date_str = "" # Leeres Datum als Standard
    
    try:
        bounds = gpx.get_time_bounds()
        if bounds.start_time and bounds.end_time:
            # +2 Stunden Korrektur (Sommerzeit / UTC Offset)
            t_start = bounds.start_time + timedelta(hours=2)
            t_end = bounds.end_time + timedelta(hours=2)
            
            # Zeit formatieren (HH:MM Uhr)
            start_time_str = t_start.strftime("%H:%M Uhr")
            end_time_str = t_end.strftime("%H:%M Uhr")
            
            # Datum formatieren (TT.MM.JJJJ)
            date_str = t_start.strftime("%d.%m.%Y")
    except Exception:
        pass

    # Wir geben jetzt 6 Werte zurück (Datum ist neu)
    return points, dist_km, avg_speed, start_time_str, end_time_str, date_str

def main():
    st.set_page_config(page_title="LKW Touren Viewer", page_icon="🚚", layout="wide")
    
    logo_filename = "movisl.jpg"
    logo_base64 = ""
    if os.path.exists(logo_filename):
        logo_base64 = get_base64_of_bin_file(logo_filename)

    # --- CSS MAGIC ---
    st.markdown(f"""
        <style>
            /* Grundfarbe */
            .stApp {{ background-color: #2654aa; }}
            
            /* Hide Anchor Links */
            h1 > a, h2 > a, h3 > a, h4 > a, h5 > a, h6 > a {{ display: none !important; }}
            .anchor-link, [data-testid="stMarkdownContainer"] a {{ text-decoration: none !important; display: none !important; }}

            /* Header */
            .header {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                background-color: white;
                padding: 10px 30px;
                z-index: 10000;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                display: flex;
                align-items: center;
                height: 80px;
            }}
            .header img {{ height: 60px; width: auto; }}

            /* Fixierter blauer Bereich */
            div[data-testid="stVerticalBlock"] > div:has(div#fixed-controls-anchor) {{
                position: fixed;
                top: 80px; 
                left: 0;
                width: 100%;
                background-color: #2654aa;
                z-index: 9999;
                padding-left: 2rem;
                padding-right: 2rem;
                padding-bottom: 20px;
            }}

            /* Platzhalter oben */
            .block-container {{
                padding-top: {HEADER_HEIGHT_PIXELS}px !important;
            }}
            
            /* Textfarben */
            h1, h2, h3, h4, p, div, label, .stMarkdown, .stMetricValue, .stMetricLabel {{ color: white !important; }}
            .header * {{ color: #2654aa !important; }}
            .stException, .stException div, .stError, .stError div {{ color: black !important; }}
            .stAppDeployButton, header, #MainMenu, footer {{ visibility: hidden; }}

            /* Upload Texte */
            [data-testid='stFileUploader'] section > div > div > span,
            [data-testid='stFileUploader'] section > div > div > small {{ display: none; }}
            [data-testid='stFileUploader'] section > div > div::after {{
                content: "Drag and drop GPX Datei hier \\A Maximale Dateigröße 200 MB";
                white-space: pre;
                color: white;
                text-align: center;
                display: block;
                font-weight: bold;
                margin-top: 10px;
            }}
            
            /* Button Style */
            div[data-testid="stDownloadButton"] {{
                text-align: left;
                margin-top: 10px;
                margin-bottom: 0px;
            }}
            div[data-testid="stDownloadButton"] > button {{
                background-color: white !important;
                color: #2654aa !important;
                border: 2px solid white !important;
                font-weight: bold !important;
                padding: 10px 20px !important;
                border-radius: 8px !important;
                transition: all 0.3s;
                width: auto !important;
                min-width: 300px;
            }}
            div[data-testid="stDownloadButton"] > button:hover {{
                background-color: #f0f0f0 !important;
                transform: translateY(-2px);
                color: #2654aa !important;
            }}
            div[data-testid="stDownloadButton"] > button p {{
                color: #2654aa !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    # --- HEADER ---
    if logo_base64:
        st.markdown(f'<div class="header"><img src="data:image/jpeg;base64,{logo_base64}"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="header"><h2 style="color:#2654aa!important">movis</h2></div>', unsafe_allow_html=True)

    # --- FIXIERTER BEREICH ---
    with st.container():
        st.markdown('<div id="fixed-controls-anchor"></div>', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: white; margin-top: 20px;'>🚚 LKW Touren Viewer</h2>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Wähle eine GPX Datei", type=['gpx'])

        points = []
        dist_km = 0
        avg_speed = 0
        start_time = "-"
        end_time = "-"
        date_str = ""
        m = None 
        tour_info_line = "" # Variable für den kombinierten Text (Nummer + Datum)
        
        if uploaded_file is not None:
            # 1. GPX Daten verarbeiten
            try:
                # Jetzt mit date_str Rückgabewert
                points, dist_km, avg_speed, start_time, end_time, date_str = process_gpx_data(uploaded_file)
                if not points:
                    st.error("Keine Wegpunkte in dieser Datei gefunden.")
            except Exception as e:
                st.error(f"Fehler beim Lesen der Datei: {e}")

            # 2. Text für Tournummer und Datum bauen
            filename = uploaded_file.name
            parts = []
            
            # Prüfen ob DL-Nummer
            if filename.startswith("DL") and filename.lower().endswith(".gpx"):
                nummer = filename[2:-4]
                parts.append(f"Tournummer: {nummer}")
            
            # Prüfen ob Datum vorhanden
            if date_str:
                parts.append(f"Datum: {date_str}")
            
            # Zusammenfügen mit Trennzeichen (Punkt oder Strich)
            if parts:
                tour_info_line = " &nbsp;•&nbsp; ".join(parts)


        # Anzeige der Info-Zeile (Nummer & Datum)
        if tour_info_line:
            st.markdown(f"<h3 style='text-align: center; color: white; margin-bottom: 15px;'>{tour_info_line}</h3>", unsafe_allow_html=True)
        elif uploaded_file is not None and not tour_info_line:
            st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)


        if points:
            # --- LAYOUT: START | ENDE | DISTANZ | GESCHWINDIGKEIT ---
            col1, col2, col3, col4 = st.columns(4)
            
            box_style = "color: white; text-align: center; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px;"
            
            with col1:
                st.markdown(f"<div style='{box_style}'><h3>⏱️ Start</h3><h3>{start_time}</h3></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='{box_style}'><h3>🏁 Ende</h3><h3>{end_time}</h3></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div style='{box_style}'><h3>📏 Distanz</h3><h3>{dist_km:.2f} km</h3></div>", unsafe_allow_html=True)
            with col4:
                speed_text = f"{avg_speed:.1f} km/h" if avg_speed > 0 else "-"
                st.markdown(f"<div style='{box_style}'><h3>🚚 Ø Geschw.</h3><h3>{speed_text}</h3></div>", unsafe_allow_html=True)

            # Karte vorbereiten
            mid_index = len(points) // 2
            center_coords = points[mid_index]
            m = folium.Map(location=center_coords, zoom_start=12)
            folium.PolyLine(points, color="red", weight=5, opacity=0.8).add_to(m)
            folium.Marker(points[0], popup="Start", icon=folium.Icon(color="green", icon="play")).add_to(m)
            folium.Marker(points[-1], popup="Ziel", icon=folium.Icon(color="black", icon="flag")).add_to(m)

            # Button + Erklärungstext
            st.markdown("<br>", unsafe_allow_html=True) 
            map_html = m.get_root().render()
            
            st.download_button(
                label="🌍 Karte für 2. Monitor speichern (Vollbild)",
                data=map_html,
                file_name="LKW_Tour_Karte.html",
                mime="text/html"
            )
            st.markdown("""
                <p style='color: #ddd; font-size: 0.9em; margin-top: 5px;'>
                ℹ️ <b>Hinweis:</b> Die Karte wird im Download-Ordner gespeichert. Bitte öffne die Datei von dort manuell (kein automatischer Start).
                </p>
            """, unsafe_allow_html=True)
        
        else:
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # --- SCROLLBARER BEREICH ---
    if m is not None:
        st_folium(m, use_container_width=True, height=800)

if __name__ == "__main__":
    main()
