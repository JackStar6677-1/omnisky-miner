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
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Type", row['type'])
    c2.metric("Origin", "✅ REAL DATA" if row['data_origin'] == "REAL" else "🛠️ TEST/LEGACY")
    
    c3.metric("Classification", row['classification'])
    c4.metric(row.get('value_unit', 'Value'), f"{row['data_value']:.2f}")
    c5.metric("Frequency/Band", f"{row.get('frequency', 0):.2f} MHz" if row['type'] == 'RADIO' else "N/A")
    
    # PRO: ML Metrics
    ml_score = row.get('ml_score', None)
    ml_label = row.get('ml_label', 'N/A')
    if ml_score is not None:
        c6.metric("ML Triage Score", f"{ml_score:.1f}%", delta=ml_label)
    else:
        c6.metric("ML Triage", "Pending/N/A")

    st.caption(f"Timestamp: {row['timestamp']}")
    
    st.markdown("---")
    
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
            
            # BACKFILL BUTTON
            import time
            unique_key = f"backfill_{row.get('event_id')}_{int(time.time())}"
            if st.button(f"🛠️ Backfill Evidence for Event {row.get('event_id', 'N/A')}", key=unique_key):
                import subprocess
                result = subprocess.run(
                    ["python", "scripts/backfill_evidence.py", "--event-id", str(row.get('event_id'))],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    st.success("✅ Backfill complete! Refresh page.")
                    st.code(result.stdout)
                else:
                    st.error("Backfill failed:")
                    st.code(result.stderr)
        
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

# --- PRO TABS ---

def tab_intelligence(df):
    st.header("🧠 Artificial Intelligence Core")
    
    # 1. Triage Model Status
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🤖 Triage Engine")
        from modules.triage import TriageEngine
        engine = TriageEngine()
        st.metric("Model Status", "Active" if engine.is_ready else "Heuristic Fallback")
        if st.button("Re-Train Model (Dummy)"):
            try:
                msg = engine.train_dummy()
                st.success(msg)
            except Exception as e:
                st.error(str(e))
                
    with c2:
        st.subheader("🛑 RFI Intelligence")
        from modules.rfi_intel import RFIIntelligence
        heatmap = RFIIntelligence.get_frequency_heatmap()
        if heatmap is not None and not heatmap.empty:
            fig = px.bar(heatmap, x='freq_bin', y='count', title="RFI Density by Frequency (MHz)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient RFI data for Heatmap.")

def tab_search(df):
    st.header("🔎 Deep Semantic Search")
    q = st.text_input("Query Database (Reports, Title, Tags):")
    if q:
        from modules.search import SearchEngine
        se = SearchEngine()
        results = se.search(q)
        if results:
            for r in results:
                st.markdown(f"**Event {r['event_id']}**: {r['title']}")
                st.caption(f"...{r['snippet']}...", unsafe_allow_html=True)
                st.divider()
        else:
            st.info("No results found.")

def tab_missions(df):
    st.header("🎯 Research Missions")
    st.info("Complete objectives to earn XP and Badges (Gamification Engine Active)")
    # Stub visualization of 'missions' table
    # In real impl, fetch from DB
    c1, c2, c3 = st.columns(3)
    c1.metric("Mission: Radio Novice", "3/10", "In Progress")
    c2.metric("Mission: Deep Field", "0/1", "Pending")
    c3.metric("XP Level", "5 (Novice)")

def tab_quality(df):
    st.header("⚠️ Data Quality & Flags")
    # Stub
    st.metric("Corrupt Files", "0")
    st.metric("Missing Metadata", "2")

def tab_clusters(df):
    st.header("🧩 Spatial Clustering")
    from modules.clustering import ClusteringEngine
    if st.button("Re-Run DBSCAN"):
        ce = ClusteringEngine()
        res = ce.compute_clusters()
        st.json(res)

def tab_collections(df):
    st.header("📚 Collections")
    st.caption("Manage Playlists and Gallagheries")
    st.text_input("New Collection Name")
    st.button("Create")

def tab_ops(df):
    # Expanded Ops
    st.header("💼 Operations & Exports")
    
    st.subheader("📄 Paper Generation")
    if st.button("Generate PDF Report (Active Session)"):
        from scripts.export_paper import generate_paper
        path = generate_paper(session_id="CURRENT")
        if path: st.success(f"PDF created: {path}")

    st.subheader("📁 Data Export")
    if st.button("Export All (CSV)"):
        pass

# ... (Main update is needed to include these new functions)

# ... (Main Update) ...
# t_intel, t_ops = st.tabs(["🧠 Intelligence", "💼 Ops"])


def main():
    try:
        raw_df = load_data()
        df = render_sidebar(raw_df)
        
        t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13 = st.tabs([
            "📊 Overview", "🛰️ Images", "🎧 Audio", "🌌 Map", "📡 Network", "🖥️ Live", "🧠 Intel", 
            "🔎 Search", "🎯 Missions", "⚠️ Quality", "🧩 Clusters", "📚 Coll.", "💼 Ops"
        ])
        
        with t1: tab_overview(df)
        with t2: tab_images(df)
        with t3: tab_audio(df)
        with t4: 
             st.header("🌌 Galactic Viz")
             st.plotly_chart(px.scatter_3d(df.head(50), x='data_value', y='data_value', z='data_value'), use_container_width=True)
        with t5: tab_network(df)
        with t6: tab_live_ops()
        with t7: tab_intelligence(df)
        with t8: tab_search(df)
        with t9: tab_missions(df)
        with t10: tab_quality(df)
        with t11: tab_clusters(df)
        with t12: tab_collections(df)
        with t13: tab_ops(df) # Updated ops

                
    except Exception as e:
        st.error(f"Dashboard Crash: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
