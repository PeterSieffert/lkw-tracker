import streamlit as st
import gpxpy
import folium
from streamlit_folium import st_folium
import base64
import os

# --- KONFIGURATION ---
# Falls der untere Teil (Statistik) die Karte verdeckt, erhöhe diesen Wert.
# Habe ihn von 400 auf 420 erhöht, da wir den Titel nach unten geschoben haben.
HEADER_HEIGHT_PIXELS = 420

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def process_gpx_data(file):
    gpx = gpxpy.parse(file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    
    moving_data = gpx.get_moving_data()
    dist_km = moving_data.moving_distance / 1000.0
    moving_time_seconds = moving_data.moving_time
    
    if moving_time_seconds > 0:
        avg_speed = dist_km / (moving_time_seconds / 3600.0)
    else:
        avg_speed = 0.0

    return points, dist_km, avg_speed

def main():
    st.set_page_config(page_title="LKW Touren Viewer", page_icon="🚚", layout="wide")
    
    # Logo laden
    logo_filename = "movisl.jpg"
    logo_base64 = ""
    if os.path.exists(logo_filename):
        logo_base64 = get_base64_of_bin_file(logo_filename)

    # --- CSS MAGIC ---
    st.markdown(f"""
        <style>
            /* Grundfarbe */
            .stApp {{ background-color: #2654aa; }}
            
            /* 1. DER WEISSE LOGO-BALKEN (Ganz oben, fixiert) */
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

            /* 2. DER BLAUE KONTROLL-BEREICH (Fixiert unter dem Logo) */
            div[data-testid="stVerticalBlock"] > div:has(div#fixed-controls-anchor) {{
                position: fixed;
                top: 80px; 
                left: 0;
                width: 100%;
                background-color: #2654aa;
                z-index: 9999;
                padding-left: 5rem;
                padding-right: 5rem;
                padding-bottom: 20px;
                /* --- ÄNDERUNG HIER: Schatten und Rahmen entfernt --- */
                /* border-bottom: 1px solid rgba(255,255,255,0.2); */
                /* box-shadow: 0 4px 6px rgba(0,0,0,0.3); */
                /* --------------------------------------------------- */
            }}

            /* 3. PLATZ FÜR DEN INHALT SCHAFFEN */
            .block-container {{
                padding-top: {HEADER_HEIGHT_PIXELS}px !important;
            }}
            
            h1, h2, h3, p, div, label, .stMarkdown, .stMetricValue, .stMetricLabel {{ color: white !important; }}
            .header * {{ color: #2654aa !important; }}
            .stWarning {{ color: black !important; }} .stWarning p {{ color: black !important; }}
            .stAppDeployButton, header, #MainMenu, footer {{ visibility: hidden; }}

            /* Upload Texte anpassen */
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
        </style>
    """, unsafe_allow_html=True)

    # --- 1. LOGO HEADER (HTML) ---
    if logo_base64:
        st.markdown(f'<div class="header"><img src="data:image/jpeg;base64,{logo_base64}"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="header"><h2 style="color:#2654aa!important">movis</h2></div>', unsafe_allow_html=True)

    # --- 2. FIXIERTER KONTROLL-BEREICH ---
    with st.container():
        st.markdown('<div id="fixed-controls-anchor"></div>', unsafe_allow_html=True)
        
        # --- ÄNDERUNG HIER: margin-top: 20px ---
        st.markdown("<h2 style='text-align: center; color: white; margin-top: 20px;'>🚚 LKW Touren Viewer</h2>", unsafe_allow_html=True)
        # ---------------------------------------
        
        uploaded_file = st.file_uploader("Wähle eine GPX Datei", type=['gpx'])

        points = []
        dist_km = 0
        avg_speed = 0
        
        if uploaded_file is not None:
            try:
                points, dist_km, avg_speed = process_gpx_data(uploaded_file)
            except Exception as e:
                st.error(f"Fehler: {e}")

        if points:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<h3 style='color: white; text-align: center; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px;'>📏 Distanz: {dist_km:.2f} km</h3>", unsafe_allow_html=True)
            with col2:
                speed_text = f"{avg_speed:.1f} km/h" if avg_speed > 0 else "-"
                st.markdown(f"<h3 style='color: white; text-align: center; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px;'>🚚 Ø Geschw.: {speed_text}</h3>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # --- 3. SCROLLBARER BEREICH (Karte) ---
    if uploaded_file is not None and points:
        mid_index = len(points) // 2
        center_coords = points[mid_index]
        
        m = folium.Map(location=center_coords, zoom_start=12)
        
        folium.PolyLine(points, color="red", weight=5, opacity=0.8).add_to(m)
        folium.Marker(points[0], popup="Start", icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker(points[-1], popup="Ziel", icon=folium.Icon(color="black", icon="flag")).add_to(m)

        st_folium(m, use_container_width=True, height=800)

if __name__ == "__main__":
    main()