"""EDID hashing.

Monitors are matched by a truncated hash of their full EDID, not the raw
bytes. The serial-number bytes stay inside the hash input (some identical
models differ only by serial), but the hash itself never reveals them.
"""

import hashlib

HASH_LENGTH = 16


def hash_edid(raw_hex: str) -> str:
    """Reduce a raw EDID hex string to its truncated match key."""
    digest = hashlib.sha256(raw_hex.lower().encode("ascii")).hexdigest()
    return digest[:HASH_LENGTH]
