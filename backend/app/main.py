"""FastAPI backend."""
from __future__ import annotations

import csv
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .pipeline import load_or_compute
from .schemas import Recording, RecordingList

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DATA_DIR") or (REPO_ROOT / "data"))
SONGS_DIR = DATA_DIR / "songs"
METADATA_CSV = DATA_DIR / "birdsong_metadata.csv"
CACHE_DIR = Path(os.environ.get("CACHE_DIR") or (REPO_ROOT / "cache"))
AUDIO_EXTS = {".flac", ".wav", ".mp3", ".ogg"}

app = FastAPI(title="Birdsong Visualizer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_metadata() -> dict[str, dict]:
    """Map file_id (e.g. '101371') to metadata row (filenames look like xc101371.flac)."""
    if not METADATA_CSV.exists():
        return {}
    out: dict[str, dict] = {}
    with METADATA_CSV.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            fid = row.get("file_id", "").strip()
            if fid:
                out[fid] = row
    return out


def _find_audio(recording_id: str) -> Path | None:
    """Find audio file by stem (e.g. 'xc101371')."""
    for ext in AUDIO_EXTS:
        candidate = (SONGS_DIR / f"{recording_id}{ext}").resolve()
        if candidate.parent != SONGS_DIR.resolve():
            return None  # path traversal attempt
        if candidate.exists():
            return candidate
    return None


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "songs_exist": SONGS_DIR.exists()}


@app.get("/api/recordings", response_model=RecordingList)
def list_recordings() -> RecordingList:
    if not SONGS_DIR.exists():
        raise HTTPException(404, f"songs directory not found: {SONGS_DIR}")

    # fetch metadata
    meta = _load_metadata()
    items: list[Recording] = []

    # iterate through song list
    for p in sorted(SONGS_DIR.iterdir()):
        if p.suffix.lower() not in AUDIO_EXTS:
            continue
        stem = p.stem # e.g. xc101371
        # strip leading non-digits to match csv file_id
        fid = "".join(ch for ch in stem if ch.isdigit())
        row = meta.get(fid, {})
        items.append(
            Recording(
                id=stem,
                filename=p.name,
                genus=row.get("genus") or None,
                species=row.get("species") or None,
                english_name=row.get("english_cname") or None,
            )
        )
    return RecordingList(recordings=items)


@app.get("/api/embedding/{recording_id}")
def get_embedding(recording_id: str) -> JSONResponse:
    audio = _find_audio(recording_id)
    if audio is None:
        raise HTTPException(404, f"recording not found: {recording_id}")
    payload = load_or_compute(audio, CACHE_DIR)
    return JSONResponse(payload)


@app.get("/api/audio/{recording_id}")
def get_audio(recording_id: str) -> FileResponse:
    audio = _find_audio(recording_id)
    if audio is None:
        raise HTTPException(404, f"recording not found: {recording_id}")
    media_type = {
        ".flac": "audio/flac",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
    }.get(audio.suffix.lower(), "application/octet-stream")
    return FileResponse(audio, media_type=media_type, filename=audio.name)
