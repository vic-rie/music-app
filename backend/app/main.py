from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pathlib import Path
import json

app = FastAPI(title="Music App API")

# Autoriser le frontend à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod : mettre le domaine du frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chemins
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "music.json"
AUDIO_PATH = BASE_DIR / "data" / "audio"

# Stockage en mémoire
tracks_db = []


# Charger le JSON au démarrage
@app.on_event("startup")
def load_data():
    global tracks_db
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"music.json introuvable : {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        tracks_db = json.load(f)

    # Ajouter un ID si absent
    for i, track in enumerate(tracks_db):
        track["id"] = i


# Endpoint de recherche
@app.get("/search")
def search(q: str):
    q_lower = q.lower()

    results = [
        track for track in tracks_db
        if q_lower in track.get("title", "").lower()
        or q_lower in track.get("artist", "").lower()
        or q_lower in track.get("album", "").lower()
    ]

    return {"results": results}


# Récupérer un track par ID
@app.get("/tracks/{track_id}")
def get_track(track_id: int):
    if track_id < 0 or track_id >= len(tracks_db):
        raise HTTPException(status_code=404, detail="Track not found")

    return tracks_db[track_id]


# Streaming audio
@app.get("/stream/{track_id}")
def stream_track(track_id: int):
    if track_id < 0 or track_id >= len(tracks_db):
        raise HTTPException(status_code=404, detail="Track not found")

    track = tracks_db[track_id]
    audio_file = AUDIO_PATH / track["audio_path"]

    if not audio_file.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    def iterfile():
        with open(audio_file, "rb") as f:
            yield from f

    return StreamingResponse(iterfile(), media_type="audio/mpeg")