import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
import os
import config

# Import Adapters
from modules.ui_data import UIDataLoader
from modules.gamification import GamificationManager

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="OmniSky Research Station",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CACHING & DATA ---
@st.cache_data(ttl=15) # Refresh every 15s automatically
def load_data(limit=1000):
    return UIDataLoader.fetch_all_events(limit)

def clear_cache():
    st.cache_data.clear()
    st.cache_resource.clear()

# --- SIDEBAR ---
def render_sidebar(df):
    st.sidebar.title("🛸 Station Controls")
    
    # Global Filters
    st.sidebar.subheader("🔎 Data Filters")
    show_test = st.sidebar.checkbox("Show TEST/LEGACY Data", value=False)
    
    # Filter Data
    if not show_test:
        filtered_df = df[df['data_origin'] == 'REAL'].copy()
    else:
        filtered_df = df.copy()
        
    # Stats
    total = len(filtered_df)
    real_count = len(filtered_df[filtered_df['data_origin'] == 'REAL'])
    anomalies = len(filtered_df[filtered_df['classification'].str.contains('CANDID', case=False, na=False)])
    
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Visible Events", total)
    col2.metric("Anomalies", anomalies)
    
    st.sidebar.markdown("---")
    
    # Gamification
    game = GamificationManager()
    stats = game.get_stats()
    if stats:
        st.sidebar.markdown(f"**Rank:** `{stats['rank']}`")
        st.sidebar.progress(stats['progress'] / 100)
        st.sidebar.caption(f"XP: {int(stats['xp'])} | GB: {stats['mb']/1024:.2f}")

    st.sidebar.markdown("---")
    
    # --- IMMERSION ENGINE ---
    st.sidebar.subheader("🎛️ Immersion Field")
    immersion_on = st.sidebar.toggle("Activate Ambience", value=True)
    
    if immersion_on:
        vol = st.sidebar.slider("Field Intensity", 0.0, 1.0, 0.3, step=0.1)
        
        # Determine Driver Event
        drive_event = None
        if not df.empty:
            # Simple strategy: Use Top Real Score or Latest Real
            candidates = df[df['data_origin'] == 'REAL']
            if not candidates.empty:
                drive_event = candidates.iloc[0].to_dict()
        
        # Generate Audio (Cached via Session State/Time to avoid re-gen every ms)
        # We regen if event ID changes OR every X minutes (simulated by key)
        from modules.immersive_radio import ImmersiveRadio
        import base64
        
        # Logic: If event changed, regen. Else keep.
        current_event_id = drive_event['event_id'] if drive_event else "TEST"
        
        if 'immersion_audio' not in st.session_state or st.session_state.get('imm_evt_id') != current_event_id:
            wav_bytes, meta = ImmersiveRadio.build_ambient_wav(drive_event, duration=12.0, volume=vol)
            b64 = base64.b64encode(wav_bytes).decode()
            st.session_state['immersion_audio'] = b64
            st.session_state['imm_evt_id'] = current_event_id
            st.session_state['imm_meta'] = meta
        
        # Embed Player (Hidden Loop)
        audio_src = f"data:audio/wav;base64,{st.session_state['immersion_audio']}"
        # Autoplay loop invisible
        audio_html = f"""
            <audio autoplay loop id="immersion_player">
                <source src="{audio_src}" type="audio/wav">
            </audio>
            <script>
                var audio = document.getElementById("immersion_player");
                audio.volume = {vol};
            </script>
            <div style="font-size:0.8em; color:#444; text-align:center; border:1px solid #333; padding:5px; border-radius:5px;">
                📡 <b>Radio Room Active</b><br>
                Mode: {st.session_state['imm_meta']['mode']}<br>
                {st.session_state['imm_meta']['params']}
            </div>
        """
        st.sidebar.markdown(audio_html, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh Data"):
        clear_cache()
        st.rerun()
        
    return filtered_df

# --- COMPONENTS ---

def render_detail_panel(row):
    """Universal Detail Panel for any event type"""
    st.markdown("### 🧾 Event Detail Analysis")
    
    # Header
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.markdown(f"**Object:** `{row['object_name']}`")
    c2.markdown(f"**Type:** `{row['type']}`")
    
    origin_badge = "✅ REAL DATA" if row['data_origin'] == 'REAL' else "🧪 TEST DATA"
    c3.markdown(f"**Origin:** `{origin_badge}`")
    
    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Classification", row['classification'])
    m2.metric(row.get('value_unit', 'Value'), f"{row['data_value']:.2f}")
    m3.metric("Frequency/Band", f"{row.get('frequency', 0):.2f} MHz" if row['type'] == 'RADIO' else "N/A")
    m4.metric("Timestamp", str(row['timestamp']).split('.')[0])
    
    st.divider()
    
    # Evidence Section
    c_media, c_meta = st.columns([2, 1])
    
    with c_media:
        st.subheader("📸 Visual / Audio Evidence")
        
        # 1. Visual (PNG)
        path_vis, exists_vis, _ = UIDataLoader.resolve_path(row.get('path_visual_main'))
        if exists_vis:
            st.image(path_vis, caption=f"Visual Evidence: {os.path.basename(path_vis)}", use_container_width=True)
        elif row['type'] == 'IMAGE':
            st.warning("⚠️ Annotated PNG missing.")
        
        # 2. Audio (WAV)
        path_aud, exists_aud, _ = UIDataLoader.resolve_path(row.get('path_audio_raw'))
        if exists_aud:
            st.markdown("🔊 **Raw Audio Sonification**")
            st.audio(path_aud)
        elif row['type'] == 'RADIO':
            st.info("No audio sonification available.")

    with c_meta:
        st.subheader("📂 Metadata & Path Diagnostics")
        
        meta = {
            "Event ID": row['event_id'],
            "Artifact ID": row.get('artifact_id', 'N/A'),
            "File Hash": row.get('file_hash', 'N/A')[:12] + "..." if row.get('file_hash') else "N/A",
            "Source URL": row['source_url']
        }
        st.json(meta)
        
        # Path Table
        st.markdown("**File System Checks:**")
        
        def check_p(label, p):
            _, exists, details = UIDataLoader.resolve_path(p)
            icon = "✅" if exists else "❌"
            return {"File": label, "Status": icon, "Details": details, "Path": str(p)[-30:]}

        checks = []
        if row.get('path_visual_main'): checks.append(check_p("Visual (PNG)", row['path_visual_main']))
        if row.get('path_data_aux'): checks.append(check_p("Data (NPZ)", row['path_data_aux']))
        if row.get('path_audio_raw'): checks.append(check_p("Audio (Raw)", row['path_audio_raw']))
        
        if checks:
            st.dataframe(pd.DataFrame(checks), hide_index=True)
        else:
            st.caption("No files associated with this event.")


def tab_overview(df):
    st.header("📊 Mission Status")
    
    # Live Feed
    st.subheader("� Live Signals Feed")
    
    # Filters
    c1, c2, c3 = st.columns(3)
    f_type = c1.multiselect("Type", df['type'].unique(), default=df['type'].unique())
    f_class = c2.multiselect("Classification", df['classification'].unique(), default=df['classification'].unique())
    
    feed = df[
        (df['type'].isin(f_type)) & 
        (df['classification'].isin(f_class))
    ]
    
    # Selection
    event_id = None
    
    # Grid Options
    st.dataframe(
        feed[['timestamp', 'data_origin', 'type', 'classification', 'data_value', 'object_name']],
        use_container_width=True,
        hide_index=True,
        height=300
    )
    
    # Selection Mechanism (Simple Selectbox for Detail)
    st.markdown("---")
    st.info("Select an event below to inspect full details.")
    selected_idx = st.selectbox(
        "Select Event ID:", 
        feed.index, 
        format_func=lambda i: f"[{feed.loc[i, 'timestamp']}] {feed.loc[i, 'object_name']} ({feed.loc[i, 'classification']})"
    )
    
    if selected_idx is not None:
        render_detail_panel(feed.loc[selected_idx])


def tab_images(df):
    st.header("🛰️ Visual Survey Gallery")
    
    img_df = df[df['type'] == 'IMAGE'].copy()
    
    if img_df.empty:
        st.warning("No visual survey data available.")
        return
        
    # Filters
    score_filter = st.slider("Min Sigma Score", 0.0, 100.0, 0.0)
    gallery = img_df[img_df['data_value'] >= score_filter]
    
    # Grid Layout
    cols = st.columns(4)
    for i, (idx, row) in enumerate(gallery.head(12).iterrows()):
        col = cols[i % 4]
        
        path, exists, _ = UIDataLoader.resolve_path(row['path_visual_main'])
        
        with col:
            with st.container(border=True):
                if exists:
                    st.image(path, use_container_width=True)
                else:
                    st.markdown("🖼️ *Image Missing*")
                    
                st.caption(f"**{row['object_name']}**")
                st.caption(f"Sigma: {row['data_value']:.1f} | {row['data_origin']}")
                if st.button("Inspect", key=f"btn_img_{idx}"):
                    st.session_state['selected_img_idx'] = idx

    # Detail View (if selected)
    if 'selected_img_idx' in st.session_state:
        st.markdown("---")
        render_detail_panel(df.loc[st.session_state['selected_img_idx']])


def tab_audio(df):
    st.header("� Radio Signal Lab")
    rad_df = df[df['type'].isin(['RADIO', 'LEGACY'])]
    
    if rad_df.empty:
        st.info("No radio data.")
        return
        
    col_list, col_play = st.columns([1, 2])
    
    with col_list:
        st.markdown("param: **Select Signal**")
        sel_idx = st.radio(
            "Signal List", 
            rad_df.index[:10],
            format_func=lambda i: f"{rad_df.loc[i, 'object_name']} (SNR {rad_df.loc[i, 'data_value']:.1f})"
        )
        
    with col_play:
        if sel_idx is not None:
            render_detail_panel(rad_df.loc[sel_idx])

@st.cache_data(ttl=2)
def load_telemetry(limit=60):
    conn = UIDataLoader.get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT ?", conn, params=(limit,))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        conn.close()
        return df
    except:
        conn.close()
        return pd.DataFrame()

def tab_network(df):
    st.header("📡 Network & Pipeline Live Telemetry")
    
    tel_df = load_telemetry(60) # Last 60s
    if tel_df.empty:
        st.warning("No telemetry data yet. Start the Orchestrator.")
        return
        
    latest = tel_df.iloc[0]
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Download Speed", f"{latest['mbps_down']:.2f} Mbps", delta=f"{latest['mbps_down'] - tel_df.iloc[-1]['mbps_down']:.2f}")
    c2.metric("Upload Speed", f"{latest['mbps_up']:.2f} Mbps")
    c3.metric("Peak Session", f"{latest['mbps_peak_session']:.2f} Mbps")
    c4.metric("Bandwidth Usage", f"{latest['plan_usage_pct']:.1f}%", help=f"Of {config.PLAN_MBPS} Mbps Plan")
    
    # Charts
    st.subheader("Traffic Analysis (Last 60s)")
    chart_data = tel_df.sort_values('timestamp')
    fig = px.line(chart_data, x='timestamp', y=['mbps_down', 'mbps_up'], 
                  labels={'value': 'Mbps', 'variable': 'Direction'}, 
                  title="Network Throughput")
    st.plotly_chart(fig, use_container_width=True)
    
# --- LIVE OPS ---
def tab_live_ops():
    st.header("🖥️ Pipeline Operations Center")
    
    # 1. Status Snapshot
    from modules.obs import Observability
    status = Observability.get_status()
    
    if not status:
        st.warning("No active operations detected. (OBS file missing)")
    else:
        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Stage", status.get('stage', 'IDLE'))
        c2.metric("Active TS", status.get('ts', 'N/A').split('T')[-1])
        curr = status.get('current', {})
        c3.metric("Processing Artifact", curr.get('artifact_id', 'None'))
        c4.metric("Last Action", curr.get('url', 'N/A')[-30:])

    st.markdown("---")
    
    # 2. Event Timeline
    st.subheader("📜 Event Log Stream")
    events = Observability.get_recent_events(20) # Last 20
    
    if not events:
        st.info("Log is empty.")
    else:
        # Display as a clean list/table
        # Custom formatting
        for e in events:
            evt_type = e.get('event', 'UNKNOWN')
            icon = "ℹ️"
            if "FAIL" in evt_type or "ERROR" in evt_type: icon = "❌"
            if "DONE" in evt_type: icon = "✅"
            if "START" in evt_type: icon = "🚀"
            
            with st.container(border=True):
                col_i, col_t, col_msg = st.columns([0.5, 2, 8])
                col_i.write(icon)
                col_t.caption(e.get('ts', '').split('T')[-1])
                
                # Construct message based on keys
                msg = f"**{evt_type}**"
                if 'artifact_id' in e: msg += f" | Art: `{e['artifact_id']}`"
                if 'url' in e: msg += f" | URL: `{e['url']}`"
                if 'size' in e: msg += f" | Size: {e['size']/1024:.0f} KB"
                if 'reason' in e: msg += f" | ⚠️ {e['reason']}"
                
                col_msg.markdown(msg)

# ... (Inside main) ...
# t1, t2, t3, t4, t5, t6 = st.tabs(["📊 Overview", "🛰️ Images", "🎧 Audio Lab", "🌌 3D Map", "📡 Network", "🖥️ Live Ops"])
# with t6: tab_live_ops()

def main():
    try:
        raw_df = load_data()
        df = render_sidebar(raw_df)
        
        t1, t2, t3, t4, t5, t6 = st.tabs(["📊 Overview", "🛰️ Images", "🎧 Audio Lab", "🌌 3D Map", "📡 Network", "🖥️ Live Ops"])
        
        with t1: tab_overview(df)
        with t2: tab_images(df)
        with t3: tab_audio(df)
        with t4: 
            st.header("🌌 Galactic Viz (Exploratory)")
            if not df.empty:
                fig = px.scatter_3d(
                    df.head(100), x='data_value', y='data_value', z='data_value', # Mock coords
                    color='classification', hover_name='object_name'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data.")
        with t5: tab_network(df)
        with t6: tab_live_ops()
                
    except Exception as e:
        st.error(f"Dashboard Crash: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
