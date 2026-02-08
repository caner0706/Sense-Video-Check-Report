#!/usr/bin/env python3
"""
meeting_data/ içindeki toplantı ses kaydını bulur, WhisperX + pyannote ile
konuşmacı diarizasyonu yapıp "kim ne dedi" formatında transkript üretir.
Çıktı: meeting_transcript.json, meeting_transcript.txt

Gereksinimler: whisperx, torch, ffmpeg, Hugging Face token (pyannote modelleri için).
Token: SENSEAI veya HF_TOKEN. Pyannote kullanımı için HF'de pyannote/speaker-diarization-3.1
ve ilgili modellerin lisansını kabul etmeniz gerekir.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

MEETING_DATA = Path("meeting_data")
TRANSCRIPT_JSON = Path("meeting_transcript.json")
TRANSCRIPT_TXT = Path("meeting_transcript.txt")
TRANSCRIPT_HTML = Path("meeting_transcript.html")
AUDIO_WAV = Path("meeting_audio.wav")  # geçici 16kHz mono

# Ses dosyası adında aranacak anahtar kelimeler (öncelik)
AUDIO_NAME_HINTS = ("ses", "audio", "sound", "toplanti_sesi", "meeting_audio")


def get_token() -> str | None:
    return os.environ.get("SENSEAI") or os.environ.get("HF_TOKEN")


def find_audio_webm() -> Path | None:
    """Önce 'ses' içeren .webm, yoksa ilk .webm dosyasını döndürür. Alt klasörler dahil (rglob)."""
    if not MEETING_DATA.exists():
        return None
    webms = sorted(MEETING_DATA.rglob("*.webm"))  # alt klasörler dahil (download altına indiriyor)
    if not webms:
        return None
    for w in webms:
        name_lower = w.name.lower()
        if any(hint in name_lower for hint in AUDIO_NAME_HINTS):
            return w
    return webms[0]


def webm_to_wav_16k(webm_path: Path, wav_path: Path) -> bool:
    """WebM'den 16kHz mono WAV çıkarır (ffmpeg)."""
    cmd = [
        "ffmpeg", "-y", "-i", str(webm_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(wav_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or not wav_path.exists():
        if r.stderr:
            print(r.stderr[-800:], file=sys.stderr)
        return False
    return True


def run_transcription(wav_path: Path, hf_token: str) -> dict | None:
    """WhisperX: transcribe -> align -> diarize -> assign_word_speakers. Dönen sonuç segments içerir."""
    try:
        import torch
        # PyTorch 2.6+ weights_only=True: pyannote VAD checkpoint (omegaconf) yüklenebilsin
        if hasattr(torch.serialization, "add_safe_globals"):
            try:
                from omegaconf.listconfig import ListConfig
                from omegaconf.dictconfig import DictConfig
                torch.serialization.add_safe_globals([ListConfig, DictConfig])
            except Exception:
                pass
        import whisperx
        from whisperx.diarize import DiarizationPipeline, assign_word_speakers
    except ImportError as e:
        print("HATA: whisperx veya bağımlılıkları yüklü değil:", e, file=sys.stderr)
        print("Kurulum: pip install whisperx torch", file=sys.stderr)
        return None

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    model_size = "base"  # CPU için hızlı; daha iyi kalite için "small" veya "medium"

    print("Ses yükleniyor...")
    audio = whisperx.load_audio(str(wav_path))

    print("Whisper modeli yükleniyor ve transkripsiyon yapılıyor...")
    model = whisperx.load_model(model_size, device, compute_type=compute_type)
    result = model.transcribe(audio, batch_size=16)
    del model
    if getattr(torch, "cuda", None) and torch.cuda.is_available():
        torch.cuda.empty_cache()

    language = result.get("language", "tr")
    print("Dil:", language, "- Hizalama yapılıyor...")

    model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
    result = whisperx.align(
        result["segments"], model_a, metadata, audio, device, return_char_alignments=False
    )
    del model_a
    if getattr(torch, "cuda", None) and torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("Konuşmacı diarizasyonu yapılıyor (pyannote)...")
    diarize_model = DiarizationPipeline(use_auth_token=hf_token, device=device)
    diarize_df = diarize_model(str(wav_path))
    result = assign_word_speakers(diarize_df, result)

    return result


def segments_to_export(result: dict) -> list[dict]:
    """Her segment için {start, end, speaker, text} listesi."""
    out = []
    for seg in result.get("segments") or []:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        out.append({
            "start": round(seg.get("start", 0), 2),
            "end": round(seg.get("end", 0), 2),
            "speaker": seg.get("speaker", "SPEAKER_00"),
            "text": text,
        })
    return out


def format_time(sec: float) -> str:
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"


def speaker_label(speaker: str) -> str:
    """SPEAKER_00 -> Konuşmacı 1, SPEAKER_01 -> Konuşmacı 2."""
    if not speaker:
        return "Bilinmeyen"
    try:
        num = int(speaker.replace("SPEAKER_", "")) + 1
        return f"Konuşmacı {num}"
    except Exception:
        return speaker


def escape_html(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;") if s else "")


def write_outputs(segments: list[dict]) -> None:
    """meeting_transcript.json, meeting_transcript.txt ve meeting_transcript.html yazar."""
    data = {"segments": segments, "format": "kim ne dedi"}
    TRANSCRIPT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Yazıldı:", TRANSCRIPT_JSON)

    lines = []
    for s in segments:
        t = format_time(s["start"])
        label = speaker_label(s["speaker"])
        lines.append(f"[{t}] {label}: {s['text']}")
    TRANSCRIPT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print("Yazıldı:", TRANSCRIPT_TXT)

    html_lines = []
    for s in segments:
        t = format_time(s["start"])
        label = speaker_label(s["speaker"])
        text = escape_html((s.get("text") or "").strip())
        html_lines.append(f'<div class="line"><span class="time">[{t}]</span> <span class="speaker">{label}:</span> {text}</div>')
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>Toplantı transkripti — kim ne dedi</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f1419; color: #e6edf3; margin: 0; padding: 1.5rem; line-height: 1.6; max-width: 720px; margin-left: auto; margin-right: auto; }}
    h1 {{ font-size: 1.25rem; color: #58a6ff; }}
    .line {{ margin-bottom: 0.5rem; }}
    .time {{ color: #8b949e; font-size: 0.85rem; margin-right: 0.5rem; }}
    .speaker {{ font-weight: 600; color: #58a6ff; }}
  </style>
</head>
<body>
  <h1>Toplantı transkripti (kim ne dedi)</h1>
  <div class="content">
{chr(10).join(html_lines)}
  </div>
</body>
</html>
"""
    TRANSCRIPT_HTML.write_text(html, encoding="utf-8")
    print("Yazıldı:", TRANSCRIPT_HTML)


def main() -> int:
    webm = find_audio_webm()
    if not webm:
        print("meeting_data/ içinde .webm dosyası bulunamadı. Transkripsiyon atlanıyor.")
        return 0

    token = get_token()
    if not token:
        print("HATA: SENSEAI veya HF_TOKEN ortam değişkeni gerekli (pyannote için).", file=sys.stderr)
        return 1

    print("Ses kaynağı:", webm.name)
    if not webm_to_wav_16k(webm, AUDIO_WAV):
        print("HATA: WebM -> WAV dönüşümü başarısız.", file=sys.stderr)
        return 1

    try:
        result = run_transcription(AUDIO_WAV, token)
    finally:
        if AUDIO_WAV.exists():
            AUDIO_WAV.unlink()

    if not result:
        return 1

    segments = segments_to_export(result)
    if not segments:
        print("Transkript boş (segment yok).")
        return 0

    write_outputs(segments)
    return 0


if __name__ == "__main__":
    exit(main())
