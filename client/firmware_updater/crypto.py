import base64, json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from .paths import PUBK


def canonical_payload(md: dict) -> bytes:
    md2 = dict(md)
    md2.pop("signature", None)
    return json.dumps(md2, sort_keys=True, separators=(',', ':')).encode("utf-8")

def verify_metadata_signature(md: dict, public_key) -> None:
    sig_b64 = md.get("signature")
    if not sig_b64:
        raise ValueError("metadata missing 'signature'")
    signature = base64.b64decode(sig_b64)
    public_key.verify(
        signature,
        canonical_payload(md),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )

def load_public_key():
    data = PUBK.read_bytes()
    return serialization.load_pem_public_key(data)