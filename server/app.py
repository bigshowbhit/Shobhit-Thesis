from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import json

app = FastAPI(title="Secure OTA (basic)")
BASE_DIR = Path(__file__).resolve().parent 

def iter_versions():
    for p in BASE_DIR.iterdir():
        if p.is_dir():
            meta = p / "metadata.json"
            fw = p / "firmware.txt"
            if meta.exists() and fw.exists():
                yield p.name, meta, fw

def get_version_paths(version: str):
    vdir = BASE_DIR / version
    meta = vdir / "metadata.json"
    fw = vdir / "firmware.txt"
    return meta, fw

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/versions")
def list_versions():
    out = []
    for name, meta, _ in iter_versions():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        out.append({"version": name})
    return {"versions": sorted(out, key=lambda x: x["version"])}

@app.get("/versions/{version}/metadata")
def get_metadata(version: str):
    meta, _ = get_version_paths(version)
    if not meta.exists():
        raise HTTPException(404, "metadata.json not found")
    try:
        return JSONResponse(json.loads(meta.read_text(encoding="utf-8")))
    except Exception as e:
        raise HTTPException(500, f"Invalid metadata.json: {e}")

@app.get("/versions/{version}/download")
def download_firmware(version: str):
    _, fw = get_version_paths(version)
    if not fw.exists():
        raise HTTPException(404, "firmware.txt not found")
    return FileResponse(
        path=fw,
        media_type="text/plain",
        filename=f"firmware_{version}.txt"
    )

@app.get("/versions/{version}/view")
def view_firmware(version: str):
    _, fw = get_version_paths(version)
    if not fw.exists():
        raise HTTPException(404, "firmware.txt not found")
    return {"version": version, "content": fw.read_text(encoding="utf-8")}

