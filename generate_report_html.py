#!/usr/bin/env python3
"""
evaluation.json'daki frame bazlı veriyi kullanarak grafikli, görsel zengin
tek sayfa HTML raporu üretir: kim ne kadar aktif, kim ne zaman etkisiz, zaman serisi grafikleri.
"""
import json
from pathlib import Path

MEETING_DATA = Path("meeting_data")
EVALUATION_JSON = Path("evaluation.json")
LATEST_MEETING_JSON = Path("latest_meeting.json")
REPORT_HTML_PATH = Path("meeting_report.html")

# DAiSEE: scores dizisi [boredom, confusion, engagement, frustration]
LABELS_EN = ["boredom", "confusion", "engagement", "frustration"]
LABELS_TR = {
    "boredom": "Düşük ilgi",
    "confusion": "Kafa karışıklığı",
    "engagement": "İlgili / odaklı",
    "frustration": "Hayal kırıklığı",
}
ENGAGEMENT_IDX = 2
FRAME_INTERVAL_SEC = 0.5
# Etkisiz say: engagement skoru bu eşiğin altında veya dominant değilse, 4+ ardışık frame
LOW_ENGAGEMENT_THRESHOLD = 0.3
MIN_INEFFECTIVE_FRAMES = 4


def load_txt_content() -> str:
    parts = []
    for p in sorted(MEETING_DATA.rglob("*.txt")):
        parts.append(p.read_text(encoding="utf-8", errors="replace").strip())
    return "\n\n".join(parts) if parts else ""


def load_evaluation() -> dict:
    if not EVALUATION_JSON.exists():
        return {}
    return json.loads(EVALUATION_JSON.read_text(encoding="utf-8"))


def load_meeting_meta() -> dict:
    if not LATEST_MEETING_JSON.exists():
        return {}
    return json.loads(LATEST_MEETING_JSON.read_text(encoding="utf-8"))


def engagement_series(frames: list) -> list:
    """Her frame için engagement skoru (0-1 benzeri)."""
    out = []
    for f in frames:
        scores = f.get("scores") or [0, 0, 0, 0]
        if len(scores) > ENGAGEMENT_IDX:
            # Softmax benzeri normalize edebiliriz; basitçe değeri kullan
            v = float(scores[ENGAGEMENT_IDX])
            out.append(round(v, 3))
        else:
            out.append(0.0)
    return out


def ineffective_segments(frames: list) -> list:
    """Etkisiz dönemler: başlangıç (sn), bitiş (sn), süre (sn)."""
    segments = []
    engagement = engagement_series(frames)
    i = 0
    while i < len(engagement):
        if engagement[i] >= LOW_ENGAGEMENT_THRESHOLD:
            i += 1
            continue
        start_i = i
        while i < len(engagement) and engagement[i] < LOW_ENGAGEMENT_THRESHOLD:
            i += 1
        count = i - start_i
        if count >= MIN_INEFFECTIVE_FRAMES:
            start_sec = start_i * FRAME_INTERVAL_SEC
            end_sec = i * FRAME_INTERVAL_SEC
            segments.append({"start_sec": start_sec, "end_sec": end_sec, "duration_sec": round((i - start_i) * FRAME_INTERVAL_SEC, 1)})
        i += 1
    return segments


def escape_html(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;") if s else "")


def build_report_data(eval_data: dict, meta: dict, txt_content: str) -> dict:
    videos = eval_data.get("videos") or {}
    latest_folder = meta.get("latest_folder") or "—"
    participants = []
    time_labels = []
    max_frames = 0
    for video_name, data in sorted(videos.items()):
        frames = data.get("frames") or []
        eng = engagement_series(frames)
        max_frames = max(max_frames, len(frames))
        participants.append({
            "name": video_name,
            "engagement_series": eng,
            "ineffective": ineffective_segments(frames),
            "summary": data.get("summary") or {},
            "frameCount": len(frames),
        })
    if max_frames:
        time_labels = [f"{i * FRAME_INTERVAL_SEC:.0f}s" for i in range(max_frames)]
        # Serileri aynı uzunluğa getir (kısa olanları null ile doldur)
        for p in participants:
            n = len(p["engagement_series"])
            if n < max_frames:
                p["engagement_series"] = p["engagement_series"] + [None] * (max_frames - n)
    return {
        "latest_folder": latest_folder,
        "num_participants": len(participants),
        "participants": participants,
        "time_labels": time_labels,
        "max_frames": max_frames,
        "total_duration_sec": round(max_frames * FRAME_INTERVAL_SEC, 1),
        "txt_content": escape_html(txt_content or "(Metin yok.)"),
        "labels_tr": LABELS_TR,
    }


def render_html(data: dict) -> str:
    r = data
    participants_json = json.dumps(r["participants"], ensure_ascii=False)
    time_labels_json = json.dumps(r["time_labels"], ensure_ascii=False)
    num = r["num_participants"]
    part_label = "Analiz edilen ekran kaydı yok." if num == 0 else f"{num} katılımcı" if num > 1 else "1 katılımcı"

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>Toplantı analiz raporu — {r['latest_folder']}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    :root {{ --bg: #0f1419; --card: #1a2332; --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff; --success: #3fb950; --warning: #d29922; --danger: #f85149; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 1.5rem; line-height: 1.6; }}
    .container {{ max-width: 960px; margin: 0 auto; }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
    .meta {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 2rem; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .card {{ background: var(--card); border-radius: 8px; padding: 1rem; text-align: center; }}
    .card .value {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); }}
    .card .label {{ font-size: 0.8rem; color: var(--muted); }}
    section {{ margin-bottom: 2.5rem; }}
    section h2 {{ font-size: 1.25rem; margin-bottom: 1rem; color: var(--accent); border-bottom: 1px solid var(--card); padding-bottom: 0.5rem; }}
    .chart-wrap {{ background: var(--card); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; height: 280px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid var(--card); }}
    th {{ color: var(--muted); font-weight: 600; }}
    .badge {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; }}
    .badge-ok {{ background: var(--success); color: #000; }}
    .badge-warn {{ background: var(--warning); color: #000; }}
    .txt-block {{ background: var(--card); border-radius: 8px; padding: 1rem; white-space: pre-wrap; font-size: 0.9rem; color: var(--muted); }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Toplantı analiz raporu</h1>
    <p class="meta">Klasör: <code>{r['latest_folder']}</code> · Katılımcı sayısı: {part_label} · Süre: {r['total_duration_sec']} sn</p>

    <div class="cards">
      <div class="card"><span class="value">{r['num_participants']}</span><div class="label">Katılımcı</div></div>
      <div class="card"><span class="value">{r['total_duration_sec']}</span><div class="label">Süre (sn)</div></div>
      <div class="card"><span class="value">{r['max_frames']}</span><div class="label">Frame</div></div>
    </div>

    <section>
      <h2>İlgi / odak seviyesi — zaman içinde (tüm katılımcılar)</h2>
      <div class="chart-wrap"><canvas id="chartCombined"></canvas></div>
    </section>

    <section>
      <h2>Katılımcı bazlı: kim ne kadar aktif, kim ne zaman etkisiz</h2>
      <div id="participantSections"></div>
    </section>

    <section>
      <h2>Ortalama dağılım (tüm katılımcılar)</h2>
      <div class="chart-wrap"><canvas id="chartDistribution"></canvas></div>
    </section>

    <section>
      <h2>Etkisiz dönemler özeti (düşük ilgi/odak)</h2>
      <table>
        <thead><tr><th>Katılımcı</th><th>Başlangıç</th><th>Bitiş</th><th>Süre</th></tr></thead>
        <tbody id="ineffectiveTable"></tbody>
      </table>
    </section>

    <section>
      <h2>Toplantı metni / özet</h2>
      <div class="txt-block">{r['txt_content']}</div>
    </section>
  </div>

  <script>
    const DATA = {participants_json};
    const TIME_LABELS = {time_labels_json};
    const LABELS_TR = {json.dumps(LABELS_TR, ensure_ascii=False)};

    const colors = ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#a371f7'];
    function getColor(i) {{ return colors[i % colors.length]; }}

    // Combined engagement over time
    const combinedCtx = document.getElementById('chartCombined').getContext('2d');
    const combinedDatasets = DATA.map((p, i) => ({{
      label: p.name,
      data: p.engagement_series,
      borderColor: getColor(i),
      backgroundColor: getColor(i) + '20',
      fill: false,
      tension: 0.2,
    }}));
    new Chart(combinedCtx, {{
      type: 'line',
      data: {{ labels: TIME_LABELS, datasets: combinedDatasets }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{ y: {{ min: 0, max: 1, title: {{ display: true, text: 'İlgi skoru' }} }} }},
        plugins: {{ legend: {{ position: 'top' }} }},
      }},
    }});

    // Per-participant sections (chart + ineffective table rows)
    const partContainer = document.getElementById('participantSections');
    let allIneffectiveRows = '';
    DATA.forEach((p, idx) => {{
      const sec = document.createElement('section');
      sec.innerHTML = `<h3 style="font-size:1.1rem;margin-bottom:0.5rem">${{p.name}}</h3><div class="chart-wrap" style="height:220px"><canvas id="chartP${{idx}}"></canvas></div>`;
      partContainer.appendChild(sec);
      new Chart(document.getElementById(`chartP${{idx}}`).getContext('2d'), {{
        type: 'line',
        data: {{ labels: TIME_LABELS, datasets: [{{ label: 'İlgi skoru', data: p.engagement_series, borderColor: getColor(idx), fill: true, backgroundColor: getColor(idx)+'30', tension: 0.2 }}] }},
        options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ min: 0, max: 1 }} }} }},
      }});
      p.ineffective.forEach(seg => {{
        allIneffectiveRows += `<tr><td>${{p.name}}</td><td>${{seg.start_sec}} sn</td><td>${{seg.end_sec}} sn</td><td>${{seg.duration_sec}} sn</td></tr>`;
      }});
    }});

    document.getElementById('ineffectiveTable').innerHTML = allIneffectiveRows || '<tr><td colspan="4">Etkisiz dönem tespit edilmedi.</td></tr>';

    // Distribution bar chart (aggregate)
    const agg = {{ boredom: 0, confusion: 0, engagement: 0, frustration: 0 }};
    let totalF = 0;
    DATA.forEach(p => {{
      Object.keys(agg).forEach(k => {{ agg[k] += p.summary[k] || 0; }});
      totalF += p.frameCount;
    }});
    const distLabels = Object.keys(LABELS_TR).map(k => LABELS_TR[k]);
    const distData = Object.keys(agg).map(k => totalF ? (100 * agg[k] / totalF).toFixed(1) : 0);
    new Chart(document.getElementById('chartDistribution').getContext('2d'), {{
      type: 'bar',
      data: {{ labels: distLabels, datasets: [{{ label: 'Oran (%)', data: distData, backgroundColor: [colors[3], colors[2], colors[1], colors[4]] }}] }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true, max: 100 }} }} }},
    }});
  </script>
</body>
</html>
"""


def main():
    meta = load_meeting_meta()
    txt = load_txt_content()
    eval_data = load_evaluation()
    data = build_report_data(eval_data, meta, txt)
    html = render_html(data)
    REPORT_HTML_PATH.write_text(html, encoding="utf-8")
    print("HTML rapor yazıldı:", REPORT_HTML_PATH)
    return 0


if __name__ == "__main__":
    exit(main())
