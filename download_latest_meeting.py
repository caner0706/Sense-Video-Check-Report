#!/usr/bin/env python3
"""
latest_meeting.json'daki en son toplantı dosyalarını HF'den indirir.
Workflow'da get_latest_meeting.py (OUTPUT_JSON=latest_meeting.json) sonrası çalıştırılır.
"""
import json
import os
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO_ID = "Caner7/Sense-AI"


def main():
    json_path = os.environ.get("LATEST_MEETING_JSON", "latest_meeting.json")
    out_dir = os.environ.get("DOWNLOAD_DIR", "latest_meeting")

    if not Path(json_path).exists():
        print(f"HATA: {json_path} bulunamadı.")
        return 1

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if not data.get("ok"):
        print("HATA:", data.get("error", "Bilinmeyen hata"))
        return 1

    token = os.environ.get("SENSEAI") or os.environ.get("HF_TOKEN")
    base_path = data["base_path"]
    # "datasets/Caner7/Sense-AI/Toplantı Kayıtları/gt1_2026-02-08" -> "Toplantı Kayıtları/gt1_2026-02-08"
    repo_prefix = f"datasets/{REPO_ID}/"
    if base_path.startswith(repo_prefix):
        repo_rel_base = base_path[len(repo_prefix) :]
    else:
        repo_rel_base = base_path

    Path(out_dir).mkdir(parents=True, exist_ok=True)

    for f in data["files"]:
        path_in_repo = f"{repo_rel_base}/{f['name']}"
        print(f"İndiriliyor: {f['name']}")
        try:
            fp = hf_hub_download(
                repo_id=REPO_ID,
                filename=path_in_repo,
                repo_type="dataset",
                token=token,
                local_dir=out_dir,
                local_dir_use_symlinks=False,
                force_download=True,
            )
            print(f"  -> {fp}")
        except Exception as e:
            print(f"  HATA: {e}")
            return 1

    print(f"\nTamamlandı. Dosyalar: {out_dir}/")
    return 0


if __name__ == "__main__":
    exit(main())
