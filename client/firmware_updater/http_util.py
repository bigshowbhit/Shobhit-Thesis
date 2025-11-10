import requests

def get_json(url, *, verify=True, **kw):
    """Fetch JSON with configurable TLS verification"""
    r = requests.get(url, timeout=30, verify=verify, **kw)
    r.raise_for_status()
    return r.json()

def download(url: str, dst, *, verify=True):
    """Download binary file with TLS verification"""
    with requests.get(url, stream=True, timeout=60, verify=verify) as r:
        r.raise_for_status()
        with open(dst, "wb") as f:
            for chunk in r.iter_content(64 * 1024):
                if chunk:
                    f.write(chunk)