# Birdsong Visualizer

**A 3D spatial audio score for birdsong.**

A proof-of-concept tool that transforms birdsong into a 3D mapped visualization.

Much like musical visualizers, but for birdsongs!

---

## What it does

Given a birdsong recording, the system:

1. Splits the audio into short overlapping analysis windows (~46 ms @ 22.05 kHz).
2. Extracts a rich per-frame feature vector (log-mel, MFCCs, spectral centroid / rolloff / bandwidth, RMS, spectral novelty).
3. Projects the high-dimensional feature trajectory into **3D via UMAP**.
4. Smooths the trajectory with an EMA filter. Uses a Noise Gate.
5. Streams the audio to the browser and animates a Three.js scene. Position, color, and accumulation are influenced by `audio.currentTime`.

The backend computes a per-recording embedding on demand and caches it keyed by a content hash plus pipeline version. The frontend fetches the JSON, binds it to an `HTMLAudioElement`, and uses `currentTime` to drive every visualization on each animation frame.

---

## The trail!

A spectral centroid drives hue from warm amber (low) to cool cyan (high); RMS drives size and brightness.

---

## Tech stack

| Layer | Tools |
|---|---|
| Audio analysis | Python, librosa, NumPy, scikit-learn, UMAP |
| API | FastAPI, Uvicorn |
| Frontend | TypeScript, Three.js, Vite |
| Packaging | Docker, docker compose, nginx (static + reverse proxy) |

---

## Repository layout

```
backend/
  app/
    main.py          FastAPI entrypoint + routes
    pipeline.py      end-to-end audio → embedding payload, caching
    features.py      librosa per-frame feature extraction
    embedding.py     StandardScaler + UMAP(3D) + EMA smoothing
    schemas.py       pydantic response models
  scripts/
    precompute.py    CLI for batch precomputing embeddings
  requirements.txt
  Dockerfile
frontend/
  src/
    main.ts          bootstrap, UI wiring, RAF loop
    scene.ts         renderer, camera, OrbitControls, fog, grid
    api.ts           typed fetch clients
    trail.ts         persistent line with age-based fade
  index.html
  vite.config.ts
  Dockerfile         multi-stage: node build → nginx
  nginx.conf
data/                audio dataset (gitignored)
  songs/*.flac
  birdsong_metadata.csv
cache/               precomputed embedding JSON (gitignored)
docker-compose.yml
```

---

## Quick start

### With Docker (recommended)

```bash
docker compose up --build
```

Open **http://localhost:8080**. The backend mounts `./data` read-only and `./cache` read-write.

### Local development

**Backend** (Python 3.11+):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux / WSL
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The server picks up `data/` and `cache/` at the repo root automatically. Override with `DATA_DIR` / `CACHE_DIR` env vars if needed.

**Frontend** (Node 20+):

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to the backend on port 8000.

---

## Dataset

This project was built against the [British Birdsong Dataset](https://www.kaggle.com/datasets/rtatman/british-birdsong-dataset) (264 FLAC recordings, CC-licensed, sourced from xeno-canto). 
Any corpus of short mono recordings will work. 
Drop audio files (`.flac`, `.wav`, `.mp3`, `.ogg`) into `data/songs/` and optionally provide a `data/birdsong_metadata.csv` with `file_id`, `genus`, `species`, `english_cname` columns to populate labels.

---

## Precomputing embeddings

For if you want to precompute your embeddings beforehand.

```bash
cd backend
python -m scripts.precompute --all # process every audio file in data/songs/
python -m scripts.precompute ../data/songs/xc101371.flac # single file
```

Cache files are keyed by `{stem}_{sha256[:16]}_v{pipeline_version}.json`, so re-running is a no-op until the audio or pipeline changes.

---

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | liveness + data-dir sanity check |
| `GET` | `/api/recordings` | list recordings with metadata joined from CSV |
| `GET` | `/api/embedding/{id}` | return cached JSON (computes on miss) |
| `GET` | `/api/audio/{id}` | stream the raw audio file for `<audio>` playback |

---

## Configuration

Pipeline constants live in `backend/app/features.py`:

| Constant | Default | Notes |
|---|---|---|
| `SAMPLE_RATE` | 22050 | Sufficient for bird frequencies (Nyquist ≈ 11 kHz) |
| `N_FFT` | 1024 | ~46 ms window |
| `HOP_LENGTH` | 512 | ~23 ms hop |
| `N_MELS` | 40 | log-mel bins |
| `N_MFCC` | 13 | mel-frequency cepstral coefficients |

UMAP parameters are in `backend/app/embedding.py`

---

## TODOs

- Add an architecture diagram (currently only sketched out on paper...)
- Fix some minor bugs (visual artifacts)
- Experiment with new features (fancier shaders!)
- Adjust filters to avoid non-bird noise (e.g. background noise)

---

## License

Code: see `LICENSE`. 
<br>The British Birdsong Dataset is CC-licensed per xeno-canto (see individual recording metadata.)