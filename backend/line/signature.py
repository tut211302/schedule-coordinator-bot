import base64
import hashlib
import hmac


def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    """
    Verify LINE signature using channel secret.
    Docs: https://developers.line.biz/en/reference/messaging-api/#signature-validation
    """
    mac = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature)

