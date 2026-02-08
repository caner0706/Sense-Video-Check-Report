#!/usr/bin/env python3
"""
HF'e veri yükledikten hemen sonra çağır: GitHub Actions workflow'unu tetikler.
Lokal uygulamanda 'upload to HF' bittikten sonra bu fonksiyonu çalıştır.
"""
import os
import urllib.request
import json


def trigger_fetch_workflow(github_token: str | None = None) -> bool:
    """
    GitHub'daki 'Fetch latest meeting data' workflow'unu tetikler.
    Token: parametre veya GITHUB_TOKEN ortam değişkeni.
    Returns: True başarılı, False başarısız (sessiz).
    """
    token = github_token or os.environ.get("GITHUB_TOKEN")
    if not token:
        return False
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/caner0706/Sense-Video-Check-Report/dispatches",
            data=json.dumps({"event_type": "hf_dataset_update"}).encode(),
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    # Komut satırından: python trigger_workflow.py
    # GITHUB_TOKEN env veya .env'de olmalı
    ok = trigger_fetch_workflow()
    exit(0 if ok else 1)
