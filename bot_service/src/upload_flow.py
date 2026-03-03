import json
import re
from dataclasses import dataclass
from pathlib import Path


SAFE_NAME_RE = re.compile(r'[^a-zA-Z0-9_.-]+')


def sanitize_filename(name: str) -> str:
    cleaned = SAFE_NAME_RE.sub('_', name).strip('._')
    if not cleaned:
        raise ValueError('Invalid filename')
    return cleaned


def load_metadata_json(path: Path) -> dict:
    raw = path.read_text(encoding='utf-8')
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('Metadata JSON must be an object')
    return data


@dataclass
class UploadState:
    session_path: Path | None = None
    metadata_path: Path | None = None

    def ready(self) -> bool:
        return self.session_path is not None and self.metadata_path is not None
