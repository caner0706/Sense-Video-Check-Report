#!/usr/bin/env python3
"""
latest_meeting.json'daki dosyaları HF'den indirir.
Sadece .webm (ekran kayıtları) ve .txt dosyalarını indirir.
"""
import json
import os
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO_ID = "Caner7/Sense-AI"


def get_token():
    return os.environ.get("SENSEAI") or os.environ.get("HF_TOKEN")


def path_in_repo(base_path: str, file_name: str) -> str:
    """HF repo içindeki göreli path: base_path datasets/Caner7/Sense-AI/..."""
    # base_path = "datasets/Caner7/Sense-AI/Toplantı Kayıtları/FolderName"
    prefix = f"datasets/{REPO_ID}/"
    if base_path.startswith(prefix):
        rel = base_path[len(prefix) :]
        return f"{rel}/{file_name}"
    return f"{base_path}/{file_name}"


def main():
    meeting_json = Path("latest_meeting.json")
    if not meeting_json.exists():
        print("HATA: latest_meeting.json bulunamadı. Önce get_latest_meeting.py çalıştırın.")
        return 1
    data = json.loads(meeting_json.read_text(encoding="utf-8"))
    base_path = data.get("base_path") or ""
    files = data.get("files") or []
    out_dir = Path("meeting_data")
    out_dir.mkdir(exist_ok=True)
    token = get_token()
    for f in files:
        name = f.get("name") or ""
        if not (name.endswith(".webm") or name.endswith(".txt")):
            continue
        try:
            rel = path_in_repo(base_path, name)
            path = hf_hub_download(
                repo_id=REPO_ID,
                filename=rel,
                repo_type="dataset",
                local_dir=str(out_dir),
                local_dir_use_symlinks=False,
                token=token,
            )
            print("İndirildi:", name, "->", path)
        except Exception as e:
            print(f"İndirme hatası {name}: {e}")
    return 0


if __name__ == "__main__":
    exit(main())
