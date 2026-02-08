#!/usr/bin/env python3
"""
Üretilen toplantı raporunu (meeting_report.md) HF'deki analiz edilen toplantı klasörüne yükler.
Dosya adı: toplanti_raporu.md
"""
import json
import os
from pathlib import Path

from huggingface_hub import HfApi

REPO_ID = "Caner7/Sense-AI"
MEETINGS_FOLDER = "Toplantı Kayıtları"
LATEST_MEETING_JSON = Path("latest_meeting.json")
REPORT_PATH = Path("meeting_report.md")
REPORT_FILENAME = "toplanti_raporu.md"


def get_token():
    return os.environ.get("SENSEAI") or os.environ.get("HF_TOKEN")


def main():
    if not REPORT_PATH.exists():
        print("HATA: meeting_report.md bulunamadı.")
        return 1
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

    path_in_repo = f"{MEETINGS_FOLDER}/{latest_folder}/{REPORT_FILENAME}"
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(REPORT_PATH),
        path_in_repo=path_in_repo,
        repo_id=REPO_ID,
        repo_type="dataset",
    )
    print("Rapor HF'e yüklendi:", path_in_repo)
    return 0


if __name__ == "__main__":
    exit(main())
