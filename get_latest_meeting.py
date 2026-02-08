#!/usr/bin/env python3
"""
Hugging Face (Caner7/Sense-AI) üzerindeki 'Toplantı Kayıtları' altında
en son eklenen toplantı klasörünün verilerini listeler ve bilgi döner.

Token: Ortam değişkeni SENSEAI veya HF_TOKEN (GitHub secret adı SENSEAI).
"""

import argparse
import json
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
    Sıralama için (tarih, numara) döner.
    '''
    m = re.match(r"(?:hf|gt)(\d+)_(\d{4}-\d{2}-\d{2})$", name.strip(), re.IGNORECASE)
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
        if not (folder_name.lower().startswith("hf") or folder_name.lower().startswith("gt")):
            continue
        parsed = parse_folder_name(folder_name)
        if parsed:
            folders.append((parsed, folder_name))

    if not folders:
        return None

    # En son: önce tarih, sonra numara büyük olsun
    folders.sort(key=lambda x: (x[0][0], x[0][1]), reverse=True)
    return folders[0][1]


def get_latest_meeting_data(token: str | None = None) -> dict:
    """
    HF'den en son toplantı klasörünün verilerini döner.
    - latest_folder: en son klasör adı (örn. hf3_2026-02-08)
    - files: dosya listesi (path, size bilgisi)
    - base_path: bu klasörün HF path'i
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

    latest = get_latest_meeting_folder(hffs)
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
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="HF'den en son toplantı klasörünü listeler.")
    parser.add_argument("--output", "-o", metavar="FILE", help="Sonucu JSON dosyasına yazar (workflow için)")
    args = parser.parse_args()

    data = get_latest_meeting_data()
    if not data["ok"]:
        print("HATA:", data["error"])
        if args.output:
            out = {k: v for k, v in data.items() if k != "ok"}
            Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    if args.output:
        Path(args.output).write_text(
            json.dumps(
                {
                    "latest_folder": data["latest_folder"],
                    "base_path": data["base_path"],
                    "repo_id": data["repo_id"],
                    "files": data["files"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

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
