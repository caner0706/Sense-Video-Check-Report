#!/usr/bin/env python3
"""
meeting_data/ içindeki .webm dosyalarından 0.5 saniye aralıklarla frame çıkarır.
Her frame 224x224 (DAiSEE model girişi) olarak kaydedilir.
Çıktı: frames/<video_adı>/frame_0000.png, frame_0001.png, ...
"""
import subprocess
import sys
from pathlib import Path

FRAME_INTERVAL = 0.5  # saniye
WIDTH, HEIGHT = 224, 224
INPUT_DIR = Path("meeting_data")
OUTPUT_DIR = Path("frames")
# Sadece ses içeren .webm'leri atla (video track yok, frame çıkarılamaz)
AUDIO_ONLY_NAME_HINTS = ("ses", "audio", "sound", "toplanti_sesi", "meeting_audio")


def extract_from_video(video_path: Path) -> Path | None:
    """Bir .webm'den frame çıkar. Dönen path frame klasörü."""
    out_sub = OUTPUT_DIR / video_path.stem
    out_sub.mkdir(parents=True, exist_ok=True)
    # ffmpeg: -i input -vf fps=2,scale=224:224 -q:v 1 frame_%04d.png
    # fps=2 => 2 frame/saniye = 0.5s aralık
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"fps=2,scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2",
        "-q:v", "1",
        str(out_sub / "frame_%04d.png"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 and "Output file is empty" not in r.stderr:
        print("ffmpeg uyarı/hata:", r.stderr[-500:] if r.stderr else r.stdout, file=sys.stderr)
    if not list(out_sub.glob("frame_*.png")):
        return None
    return out_sub


def main():
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    webms = list(INPUT_DIR.rglob("*.webm"))
    # Sadece video içerenleri al (ses .webm atlansın)
    video_webms = [v for v in webms if not any(h in v.name.lower() for h in AUDIO_ONLY_NAME_HINTS)]
    if not video_webms:
        print("meeting_data altında (ses dışı) .webm bulunamadı.")
        return 0
    for v in video_webms:
        print("Frame çıkarılıyor:", v.name)
        extract_from_video(v)
    print("Frame çıkarma tamamlandı:", OUTPUT_DIR)
    return 0


if __name__ == "__main__":
    exit(main())
