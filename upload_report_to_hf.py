#!/usr/bin/env python3
"""
Üretilen toplantı raporlarını (meeting_report.md, meeting_report.html) HF'deki
analiz edilen toplantı klasörüne yükler: toplanti_raporu.md, toplanti_raporu.html
"""
import json
import os
from pathlib import Path

from huggingface_hub import HfApi

REPO_ID = "Caner7/Sense-AI"
MEETINGS_FOLDER = "Toplantı Kayıtları"
LATEST_MEETING_JSON = Path("latest_meeting.json")
UPLOADS = [
    (Path("meeting_report.md"), "toplanti_raporu.md"),
    (Path("meeting_report.html"), "toplanti_raporu.html"),
    (Path("meeting_transcript.json"), "toplanti_transkripti.json"),
    (Path("meeting_transcript.txt"), "toplanti_transkripti.txt"),
]


def get_token():
    return os.environ.get("SENSEAI") or os.environ.get("HF_TOKEN")


def main():
    if not LATEST_MEETING_JSON.exists():
        print("HATA: latest_meeting.json bulunamadı.")
        return 1
    data = json.loads(LATEST_MEETING_JSON.read_text(encoding="utf-8"))
    latest_folder = (data.get("latest_folder") or "").strip()
    if not latest_folder:
        print("HATA: latest_folder bilgisi yok.")
        return 1

    token = get_token()
    if not token:
        print("HATA: SENSEAI veya HF_TOKEN ortam değişkeni gerekli.")
        return 1

    api = HfApi(token=token)
    for local_path, filename in UPLOADS:
        if not local_path.exists():
            continue
        path_in_repo = f"{MEETINGS_FOLDER}/{latest_folder}/{filename}"
        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo=path_in_repo,
            repo_id=REPO_ID,
            repo_type="dataset",
        )
        print("Yüklendi:", path_in_repo)
    return 0


if __name__ == "__main__":
    exit(main())
