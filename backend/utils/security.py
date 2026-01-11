import base64
import hashlib
import hmac
import os


def verify_line_signature(body: str | bytes, signature: str) -> bool:
    """
    Verify LINE Webhook signature using HMAC-SHA256.

    Args:
        body: The raw request body (string or bytes)
        signature: The X-Line-Signature header value

    Returns:
        True if signature is valid, False otherwise
    """
    channel_secret = os.getenv("LINE_CHANNEL_SECRET", "")
    if not channel_secret:
        raise ValueError("LINE_CHANNEL_SECRET environment variable not set")
    
    # Handle None signature
    if signature is None:
        print("[Security] Signature is None")
        return False

    # Ensure body is bytes
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        body_bytes = body

    # Create HMAC-SHA256 signature
    channel_secret_bytes = channel_secret.encode("utf-8")
    calculated_hash = hmac.new(channel_secret_bytes, body_bytes, hashlib.sha256).digest()
    calculated_signature = base64.b64encode(calculated_hash).decode("utf-8")

    # Debug logging
    print(f"[Security] Channel secret (first 10 chars): {channel_secret[:10]}...")
    print(f"[Security] Calculated signature: {calculated_signature}")
    print(f"[Security] Received signature: {signature}")
    print(f"[Security] Match: {calculated_signature == signature}")

    # Compare signatures using constant-time comparison
    return hmac.compare_digest(calculated_signature, signature)
