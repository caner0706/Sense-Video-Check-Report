# Sense-Video-Check-Report

Toplantı kayıtlarını HF'den alır, ekran kayıtlarından frame çıkarır, DAiSEE modeli ile değerlendirir ve toplantı metni ile birleştirerek rapor üretir.

## Akış

1. **Lokal uygulama** toplantı kaydını Hugging Face’e (Caner7/Sense-AI) yükler.
2. Yükleme bitince uygulama bu repodaki workflow’u tetikler (`repository_dispatch`).
3. **Workflow:**  
   - En son toplantı klasörünü listeler → dosyaları indirir (.webm, .txt).  
   - **Ses transkripti:** Toplantı ses kaydı (.webm) WhisperX + pyannote ile “kim ne dedi” formatında metne dönüştürülür (`meeting_transcript.json`, `meeting_transcript.txt`). (Pyannote için HF token ve [model lisansı](https://huggingface.co/pyannote/speaker-diarization-3.1) kabulü gerekir.)  
   - .webm’lerden **0.5 saniye** aralıklarla frame çıkarır (224×224).  
   - **DAiSEE** modeli ile her frame’i değerlendirir (engagement / boredom / confusion / frustration).  
   - **Birden fazla katılımcı** (her ekran kaydı = bir katılımcı) için ayrı ayrı analiz + **toplu özet** ile tek rapor üretir.  
   - **Görsel rapor:** Grafikli HTML (`toplanti_raporu.html`) — ilgi zaman serisi, etkisiz dönemler, dağılım ve toplantı metni.
   - **Ses transkripti** raporun dışında ayrı verilir: `toplanti_transkripti.json`, `toplanti_transkripti.txt` (kim ne dedi).
   - Raporlar ve transkript HF'deki ilgili toplantı klasörüne yüklenir (`toplanti_raporu.md`, `toplanti_raporu.html`, `toplanti_transkripti.json`, `toplanti_transkripti.txt`); artifact olarak da saklanır.
