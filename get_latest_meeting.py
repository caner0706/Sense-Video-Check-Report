#!/usr/bin/env python3
"""
Hugging Face (Caner7/Sense-AI) üzerindeki 'Toplantı Kayıtları' altında
en son eklenen toplantı klasörünün verilerini listeler ve bilgi döner.

Token: Ortam değişkeni SENSEAI veya HF_TOKEN (GitHub secret adı SENSEAI).
"""

import os
import re
from datetime import datetime
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


def _folder_last_modified(hffs: HfFileSystem, folder_path: str) -> float | None:
    """Klasör içindeki dosyaların en son değişim zamanını döner (epoch). Yoksa None."""
    try:
        entries = hffs.ls(folder_path, detail=True)
    except Exception:
        return None
    latest = None
    for e in entries:
        m = e.get("modified") or e.get("mtime")
        if m is not None:
            try:
                ts = float(m) if isinstance(m, (int, float)) else m
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                if latest is None or ts > latest:
                    latest = ts
            except (TypeError, ValueError):
                pass
    return latest


def get_latest_meeting_folder(hffs: HfFileSystem) -> str | None:
    """
    'Toplantı Kayıtları' altındaki alt klasörleri listeler,
    zaman damgası (modified) en son olanı döner; yoksa isimden (gtN/hfN_YYYY-MM-DD) sıralar.
    """
    try:
        entries = hffs.ls(BASE_PATH, detail=False)
    except Exception as e:
        print(f"Klasör listelenemedi: {e}")
        return None

    folders: list[tuple[str, float | None, tuple[str, int]]] = []  # (name, mtime, name_sort)
    for path in entries:
        parts = path.rstrip("/").split("/")
        if len(parts) < 2:
            continue
        folder_name = parts[-1]
        parsed = parse_folder_name(folder_name)
        if not parsed:
            continue
        folder_path = f"{BASE_PATH}/{folder_name}"
        mtime = _folder_last_modified(hffs, folder_path)
        folders.append((folder_name, mtime, parsed))

    if not folders:
        return None

    # Önce zaman damgası (en büyük = en son), yoksa isim (tarih, numara)
    def sort_key(item: tuple) -> tuple:
        name, mtime, name_sort = item
        return (mtime if mtime is not None else -1.0, name_sort[0], name_sort[1])
    folders.sort(key=sort_key, reverse=True)
    return folders[0][0]


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
    import json
    from dotenv import load_dotenv
    load_dotenv()

    data = get_latest_meeting_data()
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
