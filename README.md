# OmniSky Miner 🛰️

> Autonomous cosmic data mining station. Hunts for technosignatures and astronomical anomalies 24/7.

## Quick Start

```powershell
# Start everything (API + Daemon + UI)
cd scripts
.\run_all.ps1
```

Then open: http://127.0.0.1:8000

## Features

### 🔬 Research Station
- **Multi-Source Discovery**: Pluggable data sources (VLASS, Breakthrough Listen)
- **ML Triage**: Local RandomForest classifier for event scoring
- **Semantic Search**: SQLite FTS5 full-text search
- **Clustering**: DBSCAN hotspot detection
- **Gamification**: Research missions with XP rewards

### 👻 Daemon Mode
Runs silently in background, auto-pauses when you game.

```powershell
# Install auto-start
.\scripts\install_service_windows.ps1
```

Detects: GTA5, Cyberpunk, Blender, Premiere, etc.

### 🎛️ Command Center
Modern web UI with:
- Real-time status HUD
- Event Explorer
- Audio Lab (spectrogram)
- Live operations feed

### 📄 Evidence Contract
Every REAL event MUST have:
- `annotated.png` (visual evidence)
- `evidence.json` (metadata)
- `report.md` (analysis)

Missing evidence? Run backfill:
```bash
python scripts/backfill_evidence.py --all-missing
```

## Architecture

```
omnisky-miner/
├── api/              # FastAPI backend
├── ui/               # HTML/CSS/JS frontend
├── agent-win/        # C# Windows tray agent
├── modules/          # Python core
├── services/         # Daemon scripts
├── scripts/          # Utilities
└── OMNISKY_DATA/     # Data storage
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Daemon state |
| `/pause` | POST | Pause processing |
| `/resume` | POST | Resume |
| `/events` | GET | Query events |
| `/logs/tail` | GET | Recent logs |

## Configuration

Edit `config.py`:
- `ENABLED_SOURCES`: Active data sources
- `HEAVY_PROCESS_NAMES`: Games/apps that trigger pause
- `PAUSE_CPU_PCT`: CPU threshold (default 70%)

## Verification

```bash
python verify_pro_features.py      # Core systems
python verify_features2.py         # Research station
python verify_evidence_contract.py # Evidence system
```

## Requirements

- Python 3.9+
- .NET 8 SDK (optional, for C# agent)
- Node.js (optional, for UI build)

## License

MIT
