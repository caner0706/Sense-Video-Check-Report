# Sense-Video-Check-Report

Extract video frames, evaluate the model, run additional checks, prepare the report, and submit it to the data team.

## Akış

1. **Lokal uygulama** toplantı kaydını Hugging Face’e (Caner7/Sense-AI) yükler.
2. Yükleme bitince uygulama bu repodaki workflow’u tetikler (`repository_dispatch`).
3. **Workflow** HF’den en son toplantı klasörünü alır (`get_latest_meeting.py`), `latest_folder` çıktısı ve `latest-meeting` artifact’ı üretir; sonraki adımlar (video analiz, rapor) buna göre eklenebilir.
