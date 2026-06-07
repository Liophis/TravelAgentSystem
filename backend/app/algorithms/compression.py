import base64
import zlib


def compress_text(text: str) -> tuple[str, int, int]:
    raw = text.encode("utf-8")
    compressed = zlib.compress(raw)
    return base64.b64encode(compressed).decode("ascii"), len(raw), len(compressed)


def decompress_text(payload: str) -> str:
    compressed = base64.b64decode(payload.encode("ascii"))
    return zlib.decompress(compressed).decode("utf-8")


def compression_ratio(original_size: int, compressed_size: int) -> float:
    if original_size <= 0:
        return 1
    return round(compressed_size / original_size, 4)
