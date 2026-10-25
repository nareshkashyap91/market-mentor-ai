import os
import json

def atomic_write_json(file_path, data, indent=2, cls=None, encoding="utf-8"):
    """Atomically writes JSON payload using temporary file and atomic replace.
    Ensures readers never observe partial or corrupted JSON files.
    """
    dirname = os.path.dirname(file_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    tmp_path = f"{file_path}.tmp"
    with open(tmp_path, "w", encoding=encoding) as f:
        json.dump(data, f, indent=indent, cls=cls)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, file_path)
    return file_path

def safe_read_json(file_path, default=None):
    """Safely reads JSON file, returning default if missing or corrupted."""
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default
