from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import json

app = FastAPI(title="Secure OTA (basic)")
BASE_DIR = Path(__file__).resolve().parent 

# Basically gives the the paths to firmaware and metadata for each version
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

def return_number(vstr: str) -> int:
    if vstr.startswith("v") and vstr[1:].isdigit():
        return int(vstr[1:])
    return 0

@app.get("/check")
def check_version(current: str = Query(..., description="Your current version, e.g. v12 or 12")):
    current_n = return_number(current)
    if current_n < 0:
        return {
            "update_available": False,
            "reason": "invalid_current",
            "message": "Provide current like 'v12' or '12'.",
            "current": current,
        }

    versions = [(name, meta) for name, meta, _fw in iter_versions()]
    if not versions:
        return {"update_available": False, "reason": "no_versions", "current": current}

    latest_name, latest_meta = max(versions, key=lambda x: return_number(x[0]))
    latest_n = return_number(latest_name)

    if current_n >= latest_n:
        return {"update_available": False, "current": current, "latest": latest_name}

    try:
        metadata = json.loads(latest_meta.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid metadata.json for {latest_name}: {e}")

    return {
        "update_available": True,
        "from": current,
        "to": latest_name,
        "metadata": metadata,
        "download": f"/versions/{latest_name}/download",
    }
    
