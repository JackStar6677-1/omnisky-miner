import streamlit as st
import sqlite3
import pandas as pd
import config
import os
import plotly.express as px
import numpy as np
import time

# --- CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(
    page_title="OmniSky Research Station",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BACKEND & CACHING ---
class DashboardBackend:
    @staticmethod
    @st.cache_resource
    def get_db_connection():
        """Retorna conexión persistente a SQLite (Singleton-ish)."""
        return sqlite3.connect(config.DB_PATH, check_same_thread=False)

    @staticmethod
    @st.cache_data(ttl=5) # Cache data for 5 seconds (Live Feed)
    def fetch_latest_events(limit=500):
        """
        Consulta Unificada: Events Radio + Events Image + Hallazgos Legacy
        Retorna DataFrame normalizado.
        """
        conn = DashboardBackend.get_db_connection()
        
        # Query Radio Events (New Schema)
        q_radio = """
            SELECT 
                r.id as event_id,
                r.timestamp, 
                a.filename as object_name, 
                r.label as classification, 
                r.snr, 
                r.fch1 as frequency,
                r.path_audio_raw as path_main, 
                r.path_audio_clean as path_aux,
                'RADIO' as type,
                a.source_url
            FROM events_radio r
            JOIN artifacts a ON r.artifact_id = a.id
            ORDER BY r.timestamp DESC LIMIT ?
        """
        
        # Query Image Events (New Schema)
        q_image = """
            SELECT 
                i.id as event_id,
                i.timestamp, 
                a.filename as object_name, 
                i.label as classification, 
                i.score as snr, 
                0 as frequency,
                i.path_annotated as path_main, 
                i.path_cutout as path_aux,
                'IMAGE' as type,
                a.source_url
            FROM events_image i
            JOIN artifacts a ON i.artifact_id = a.id
            ORDER BY i.timestamp DESC LIMIT ?
        """
        
        # Query Legacy (Fallback)
        # Check if table exists first? Assume exists from 001_init.sql
        q_legacy = """
            SELECT
                id as event_id,
                timestamp,
                nombre_objeto as object_name,
                clasificacion as classification,
                snr,
                frecuencia as frequency,
                ruta_audio as path_main,
                ruta_audio_clean as path_aux,
                'LEGACY' as type,
                'N/A' as source_url
            FROM hallazgos
            ORDER BY timestamp DESC LIMIT ?
        """
        
        try:
            df_rad = pd.read_sql_query(q_radio, conn, params=(limit,))
            df_img = pd.read_sql_query(q_image, conn, params=(limit,))
            df_leg = pd.read_sql_query(q_legacy, conn, params=(limit,))
            
            # Combine all
            df = pd.concat([df_rad, df_img, df_leg], ignore_index=True)
            
            if df.empty:
                return pd.DataFrame(columns=[
                    'event_id', 'timestamp', 'object_name', 
                    'classification', 'snr', 'frequency', 
                    'path_main', 'path_aux', 'type', 'source_url'
                ])
            
            # Post-processing normalization
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df['snr'] = pd.to_numeric(df['snr'], errors='coerce').fillna(0)
            df['classification'] = df['classification'].fillna('UNKNOWN')
            df.sort_values(by='timestamp', ascending=False, inplace=True)
            
            return df
        except Exception as e:
            st.error(f"Error fetching DB: {e}")
            return pd.DataFrame(columns=[
                    'event_id', 'timestamp', 'object_name', 
                    'classification', 'snr', 'frequency', 
                    'path_main', 'path_aux', 'type', 'source_url'
                ])

    @staticmethod
    def resolve_path(path_str):
        """Diagnostica y resuelve ruta absoluta. Retorna (path_abs, exists, details)"""
        if not path_str or str(path_str).lower() == 'none' or path_str == '':
            return None, False, "Path is None/Empty in DB"
            
        # 1. Check absolute
        if os.path.exists(path_str):
            return os.path.abspath(path_str), True, "OK (Absolute)"
            
        # 2. Check relative to Project Root (CWD)
        abs_path = os.path.abspath(path_str)
        if os.path.exists(abs_path):
            return abs_path, True, "OK (Relative resolved)"
            
        # 3. Check relative to OMNISKY_ROOT (Data Dir)
        data_path = os.path.join(config.OMNISKY_ROOT, path_str)
        if os.path.exists(data_path):
            return os.path.abspath(data_path), True, "OK (In Data Artifacts)"
            
        return abs_path, False, "File Not Found on Disk"

# --- UI COMPONENTS ---

def sidebar_controls():
    st.sidebar.title("🛸 Station Controls")
    
    # KPIs Rápidos
    df = DashboardBackend.fetch_latest_events(500)
    total = len(df)
    candidates = len(df[df['classification'].str.contains('CANDID', case=False, na=False)])
    
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Total Events", total)
    col2.metric("Anomalies", candidates, delta_color="inverse")
    
    st.sidebar.markdown("---")
    
    # Gamification Light
    xp = total * 15 + candidates * 500
    rank = "Observer"
    if xp > 1000: rank = "Signal Hunter"
    if xp > 5000: rank = "Cosmic Sentinel"
    
    st.sidebar.markdown(f"**Rank:** `{rank}`")
    st.sidebar.progress(min(1.0, xp/10000))
    st.sidebar.caption(f"XP: {xp} / 10000")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refrescar Datos"):
        st.cache_data.clear()
        st.rerun()
        
    if st.sidebar.button("🧹 Limpiar Caché Global"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.success("Caché purgada.")
        time.sleep(1)
        st.rerun()

def tab_overview(df):
    st.header("📊 Mission Overview")
    
    # Top Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Radio Events", len(df[df['type'] == 'RADIO']))
    c2.metric("Visual Captures", len(df[df['type'] == 'IMAGE']))
    c3.metric("RFI/Noise Rejected", len(df[df['classification'].isin(['NOISE', 'RFI', 'INTERFERENCIA TERRESTRE'])]))
    
    recent_ts = df['timestamp'].max() if not df.empty else "N/A"
    c4.metric("Last Contact", str(recent_ts).split('.')[0])

    # Recent Feed
    st.subheader("📡 Live Feed")
    st.dataframe(
        df[['timestamp', 'type', 'classification', 'snr', 'object_name', 'source_url']].head(50),
        use_container_width=True,
        hide_index=True
    )

def tab_audio_lab(df):
    st.header("🎧 Audio Analysis Lab")
    
    # Filter only Radio/Legacy
    radio_df = df[df['type'].isin(['RADIO', 'LEGACY'])].copy()
    
    if radio_df.empty:
        st.info("No radio signals detected yet.")
        return

    # Selector
    c1, c2 = st.columns([3, 1])
    with c1:
        selected_event_idx = st.selectbox(
            "Select Event to Analyze:", 
            radio_df.index,
            format_func=lambda x: f"[{radio_df.loc[x, 'timestamp']}] {radio_df.loc[x, 'object_name']} (SNR: {radio_df.loc[x, 'snr']:.1f})"
        )
    
    row = radio_df.loc[selected_event_idx]
    
    # Path Resolution Logic
    path_raw, exists_raw, diag_raw = DashboardBackend.resolve_path(row['path_main'])
    path_clean, exists_clean, diag_clean = DashboardBackend.resolve_path(row['path_aux'])
    
    col_player, col_details = st.columns([1, 1])
    
    with col_player:
        st.subheader("Signal Playback")
        # RAW PLAYER
        st.markdown("**🔊 RAW Signal**")
        if exists_raw:
            st.audio(path_raw, format='audio/wav')
            st.caption(f"📍 {os.path.basename(path_raw)}")
        else:
            st.error("RAW Audio Missing")
            with st.expander("Diagnostic Info"):
                st.code(f"DB Value: {row['path_main']}\nResolved: {path_raw}\nStatus: {diag_raw}")

        st.markdown("---")

        # CLEAN PLAYER
        st.markdown("**🔇 Denoised Signal (Clean)**")
        if exists_clean:
            st.audio(path_clean, format='audio/wav')
            st.caption(f"📍 {os.path.basename(path_clean)}")
        else:
            if exists_raw:
                st.warning("Clean version not available (Processing skipped?)")
            else:
                st.error("Clean Audio Missing")
            
    with col_details:
        st.subheader("Metadata")
        st.json({
            "Source": row['source_url'],
            "Frequency": row['frequency'],
            "SNR": row['snr'],
            "Class": row['classification'],
            "Timestamp": str(row['timestamp'])
        })

def tab_3d_map(df):
    st.header("🌌 Galactic Distribution")
    
    if df.empty:
        st.warning("No data to map.")
        return
        
    # Generate Synthetic Coords for rendering (Scientific accuracy TODO: RA/DEC parser)
    
    # We use hashing of object name to deterministically place 'unknown' objects, 
    # ensuring they don't jump around on refresh.
    def hash_coord(s, seed_offset):
        return (hash(s + str(seed_offset)) % 200) - 100

    df['x'] = df['object_name'].apply(lambda x: hash_coord(str(x), 1))
    df['y'] = df['object_name'].apply(lambda x: hash_coord(str(x), 2))
    df['z'] = df['object_name'].apply(lambda x: hash_coord(str(x), 3))
    
    # Size based on SNR (clamped)
    df['size_plot'] = df['snr'].apply(lambda x: max(1, min(x, 50)))
    
    fig = px.scatter_3d(
        df, x='x', y='y', z='z',
        color='classification',
        size='size_plot',
        hover_name='object_name',
        hover_data=['timestamp', 'type'],
        title="Artifact Cluster Viz (Synthetic Topology)",
        color_discrete_map={
            'CANDIDATE': 'red', 'RFI': 'orange', 'NOISE': 'gray', 
            'VISUAL_SOURCE': 'green', 'UNKNOWN': 'blue'
        }
    )
    st.plotly_chart(fig, use_container_width=True)

# --- MAIN APP ---
def main():
    sidebar_controls()
    
    df = DashboardBackend.fetch_latest_events()
    
    t1, t2, t3, t4 = st.tabs(["📊 Overview", "🎧 Audio Lab", "🌌 Star Map", "⚠️ Diagnostics"])
    
    with t1: tab_overview(df)
    with t2: tab_audio_lab(df)
    with t3: tab_3d_map(df)
    with t4: 
        st.header("System Health")
        st.write("Config Settings:", {k:v for k,v in config.__dict__.items() if not k.startswith("__")})
        st.write("Pending Migrations Checks...")
        # Add more diagnostic tools here

if __name__ == "__main__":
    main()
