#!/usr/bin/env python3
"""
evaluation.json (DAiSEE) ile meeting_data/.txt dosyasını birleştirir.
Katılımcı sayısı sabit değildir: toplantıdaki ekran kaydı ve txt dosyasına göre
kaç kişi varsa o kadar katılımcı bölümü + toplu özet ile tek rapor üretilir.
"""
import json
from pathlib import Path

MEETING_DATA = Path("meeting_data")
EVALUATION_JSON = Path("evaluation.json")
LATEST_MEETING_JSON = Path("latest_meeting.json")
REPORT_PATH = Path("meeting_report.md")

# DAiSEE etiketleri (Türkçe)
LABELS_TR = {
    "boredom": "Düşük ilgi",
    "confusion": "Kafa karışıklığı",
    "engagement": "İlgili / odaklı",
    "frustration": "Hayal kırıklığı",
}


def load_txt_content() -> str:
    """Toplantıya ait .txt dosya(lar)ının içeriğini birleştirir."""
    parts = []
    for p in sorted(MEETING_DATA.rglob("*.txt")):
        parts.append(p.read_text(encoding="utf-8", errors="replace").strip())
    return "\n\n".join(parts) if parts else ""


def load_evaluation() -> dict:
    if not EVALUATION_JSON.exists():
        return {}
    return json.loads(EVALUATION_JSON.read_text(encoding="utf-8"))


def load_meeting_meta() -> dict:
    """latest_meeting.json'dan toplantı klasör adı vb."""
    if not LATEST_MEETING_JSON.exists():
        return {}
    return json.loads(LATEST_MEETING_JSON.read_text(encoding="utf-8"))


def participant_section(video_name: str, data: dict, index: int) -> str:
    """Tek katılımcı için Markdown bölümü."""
    summary = data.get("summary") or {}
    total = data.get("frameCount") or 0
    if total == 0:
        return f"### Katılımcı {index + 1}: {video_name}\n\n*Veri yok.*\n"
    rows = []
    for label_en, label_tr in LABELS_TR.items():
        pct = 100 * (summary.get(label_en) or 0) / total
        rows.append(f"| {label_tr} | %{pct:.0f} |")
    table = "\n".join(rows)
    return f"""### Katılımcı {index + 1}: `{video_name}`
- **Toplam frame:** {total} (0.5 s aralıklarla)
- **DAiSEE dağılımı:**

| Durum | Oran |
|-------|------|
{table}

"""


def combined_summary(eval_data: dict) -> str:
    """Tüm katılımcıların toplu özeti (ortalama/agrega)."""
    videos = eval_data.get("videos") or {}
    if not videos:
        return "Toplu özet üretilemedi (ekran kaydı analizi yok)."
    all_sum = {k: 0 for k in LABELS_TR}
    total_frames = 0
    for data in videos.values():
        summary = data.get("summary") or {}
        fc = data.get("frameCount") or 0
        total_frames += fc
        for k in all_sum:
            all_sum[k] += summary.get(k) or 0
    if total_frames == 0:
        return "Toplam frame yok."
    rows = []
    for label_en, label_tr in LABELS_TR.items():
        pct = 100 * all_sum[label_en] / total_frames
        rows.append(f"| {label_tr} | %{pct:.0f} |")
    table = "\n".join(rows)
    return f"""**Tüm katılımcılar (toplam {len(videos)} kişi, {total_frames} frame):**

| Durum | Ortalama oran |
|-------|----------------|
{table}
"""


def main():
    meta = load_meeting_meta()
    latest_folder = meta.get("latest_folder") or "—"
    txt_content = load_txt_content()
    eval_data = load_evaluation()
    videos = eval_data.get("videos") or {}

    # Katılımcı sayısı = analiz edilen ekran kaydı sayısı (dinamik)
    num_participants = len(videos)
    if num_participants == 0:
        participant_label = "Analiz edilen ekran kaydı yok."
    elif num_participants == 1:
        participant_label = "1 katılımcı"
    else:
        participant_label = f"{num_participants} katılımcı"

    # Katılımcı bazlı bölümler (toplantıda kaç kişi varsa o kadar bölüm)
    participant_sections = []
    for i, (video_name, data) in enumerate(sorted(videos.items())):
        participant_sections.append(participant_section(video_name, data, i))
    participants_md = "\n".join(participant_sections) if participant_sections else "*Bu toplantıda analiz edilen ekran kaydı bulunmuyor.*"
    combined_md = combined_summary(eval_data)

    report = f"""# Toplantı analiz raporu

**Toplantı klasörü:** `{latest_folder}`  
**Katılımcı sayısı:** {participant_label} (ekran kaydı sayısına göre dinamik)  
**Analiz:** Her katılımcının ekran kaydı 0.5 s aralıklarla frame'lere bölündü; DAiSEE modeli ile değerlendirildi.

---

## Katılımcı bazlı analiz

{participants_md}

---

## Toplu özet

{combined_md}

---

## Toplantı metni / özet

{txt_content or '(Metin dosyası bulunamadı veya boş.)'}
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print("Rapor yazıldı:", REPORT_PATH)
    return 0


if __name__ == "__main__":
    exit(main())
