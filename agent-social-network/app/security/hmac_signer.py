import hmac
import hashlib
from typing import Union
from app.config import settings

def generate_hmac_signature(payload: Union[str, bytes], secret: str = settings.HMAC_SECRET_KEY) -> str:
    """
    Signs outgoing webhook payload using HMAC-SHA256.
    Ensures recipient agents can cryptographically verify origin authenticity.
    """
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    secret_bytes = secret.encode("utf-8")
    return hmac.new(secret_bytes, payload, hashlib.sha256).hexdigest()

def verify_hmac_signature(payload: Union[str, bytes], signature: str, secret: str = settings.HMAC_SECRET_KEY) -> bool:
    """
    Verifies HMAC-SHA256 signature using timing-safe comparison.
    """
    expected = generate_hmac_signature(payload, secret)
    return hmac.compare_digest(expected, signature)
