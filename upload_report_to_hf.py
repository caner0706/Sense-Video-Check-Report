#!/usr/bin/env python3
"""
Üretilen toplantı raporlarını (meeting_report.md, meeting_report.html) HF'deki
analiz edilen toplantı klasörüne yükler: toplanti_raporu.md, toplanti_raporu.html
"""
import json
import os
import sys
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
    (Path("meeting_transcript.html"), "toplanti_transkripti.html"),
]


def get_token():
    return os.environ.get("SENSEAI") or os.environ.get("HF_TOKEN")


def main():
    if not LATEST_MEETING_JSON.exists():
        print("HATA: latest_meeting.json bulunamadı.", file=sys.stderr)
        return 1
    data = json.loads(LATEST_MEETING_JSON.read_text(encoding="utf-8"))
    latest_folder = (data.get("latest_folder") or "").strip()
    if not latest_folder:
        print("HATA: latest_folder bilgisi yok.", file=sys.stderr)
        return 1

    token = get_token()
    if not token:
        print("HATA: SENSEAI veya HF_TOKEN ortam değişkeni gerekli.", file=sys.stderr)
        return 1

    print(f"Hedef: {REPO_ID} (dataset) -> {MEETINGS_FOLDER}/{latest_folder}/")
    api = HfApi(token=token)
    uploaded = 0
    failed = 0
    for local_path, filename in UPLOADS:
        path_in_repo = f"{MEETINGS_FOLDER}/{latest_folder}/{filename}"
        if not local_path.exists():
            print(f"Atlandı (dosya yok): {local_path.name}")
            continue
        try:
            api.upload_file(
                path_or_fileobj=str(local_path),
                path_in_repo=path_in_repo,
                repo_id=REPO_ID,
                repo_type="dataset",
            )
            print("Yüklendi:", path_in_repo)
            uploaded += 1
        except Exception as e:
            print(f"HATA yükleme {path_in_repo}: {e}", file=sys.stderr)
            failed += 1
    print(f"Özet: {uploaded} yüklendi, {failed} hata.")
    return 1 if failed else 0


if __name__ == "__main__":
    exit(main())
