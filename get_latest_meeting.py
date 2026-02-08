#!/usr/bin/env python3
"""
Hugging Face (Caner7/Sense-AI) üzerindeki 'Toplantı Kayıtları' altında
en son eklenen toplantı klasörünün verilerini listeler ve bilgi döner.

Token: Ortam değişkeni SENSEAI veya HF_TOKEN (GitHub secret adı SENSEAI).
"""

import os
import re
from pathlib import Path

from huggingface_hub import HfFileSystem


# Repo sabitleri
REPO_ID = "Caner7/Sense-AI"
REPO_TYPE = "dataset"
MEETINGS_FOLDER = "Toplantı Kayıtları"
BASE_PATH = f"datasets/{REPO_ID}/{MEETINGS_FOLDER}"


def get_token() -> str | None:
    """HF token'ı SENSEAI veya HF_TOKEN ile al."""
    return os.environ.get("SENSEAI") or os.environ.get("HF_TOKEN")


def parse_folder_name(name: str) -> tuple[str, int] | None:
    '''
    "hf3_2026-02-08" veya "gt1_2026-02-08" -> ("2026-02-08", num).
    Sıralama için (tarih, numara) döner. hf/gt vb. prefix desteklenir.
    '''
    m = re.match(r"^[a-zA-Z]+(\d+)_(\d{4}-\d{2}-\d{2})$", name.strip())
    if not m:
        return None
    num, date = int(m.group(1)), m.group(2)
    return (date, num)


def get_latest_meeting_folder(hffs: HfFileSystem) -> str | None:
    """
    'Toplantı Kayıtları' altındaki alt klasörleri listeler,
    isimden (hfN_YYYY-MM-DD) en son olanı döner.
    """
    try:
        entries = hffs.ls(BASE_PATH, detail=False)
    except Exception as e:
        print(f"Klasör listelenemedi: {e}")
        return None

    # Sadece alt klasör isimlerini al (path'in son parçası)
    folders: list[tuple[tuple[str, int], str]] = []
    for path in entries:
        parts = path.rstrip("/").split("/")
        if len(parts) < 2:
            continue
        folder_name = parts[-1]
        parsed = parse_folder_name(folder_name)
        if parsed:
            folders.append((parsed, folder_name))

    if not folders:
        return None

    # En son: önce tarih, sonra numara büyük olsun
    folders.sort(key=lambda x: (x[0][0], x[0][1]), reverse=True)
    return folders[0][1]


def get_latest_meeting_data(token: str | None = None, folder_name: str | None = None) -> dict:
    """
    HF'den toplantı klasörünün verilerini döner.
    folder_name verilirse onu kullanır (tetikleyici payload'dan); yoksa en son klasörü bulur.
    """
    t = token or get_token()
    if not t:
        return {
            "ok": False,
            "error": "Token bulunamadı. SENSEAI veya HF_TOKEN ortam değişkenini ayarlayın.",
            "latest_folder": None,
            "files": [],
            "base_path": None,
        }

    hffs = HfFileSystem(token=t)

    latest = (folder_name or os.environ.get("MEETING_FOLDER") or "").strip() or get_latest_meeting_folder(hffs)
    if not latest:
        return {
            "ok": False,
            "error": "Toplantı Kayıtları altında uygun klasör bulunamadı.",
            "latest_folder": None,
            "files": [],
            "base_path": None,
        }

    folder_path = f"{BASE_PATH}/{latest}"
    try:
        # detail=True ile boyut vb. bilgi al
        entries = hffs.ls(folder_path, detail=True)
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "latest_folder": latest,
            "files": [],
            "base_path": folder_path,
        }

    files = []
    for e in entries:
        full_path = e.get("name", "")
        name = Path(full_path).name
        size = e.get("size")
        files.append({
            "path": full_path,
            "name": name,
            "size": size,
        })

    return {
        "ok": True,
        "error": None,
        "latest_folder": latest,
        "base_path": folder_path,
        "files": files,
        "repo_id": REPO_ID,
    }


def main():
    import json
    from dotenv import load_dotenv
    load_dotenv()

    # Tetikleyici payload'dan veya MEETING_FOLDER env'den klasör adı (örn. gt3_2026-02-08)
    folder = os.environ.get("MEETING_FOLDER")
    data = get_latest_meeting_data(folder_name=folder)
    output_json = os.environ.get("OUTPUT_JSON")

    if not data["ok"]:
        print("HATA:", data["error"])
        if output_json:
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return 1

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Çıktı:", output_json)

    print("En son toplantı klasörü:", data["latest_folder"])
    print("Path:", data["base_path"])
    print("\nDosyalar:")
    for f in data["files"]:
        size = f.get("size")
        size_str = f" {size} bytes" if size is not None else ""
        print(f"  - {f['name']}{size_str}")
    return 0


if __name__ == "__main__":
    exit(main())
