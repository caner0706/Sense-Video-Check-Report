# Sense-Video-Check-Report

Toplantı kayıtlarını HF'den alır, ekran kayıtlarından frame çıkarır, DAiSEE modeli ile değerlendirir ve toplantı metni ile birleştirerek rapor üretir.

## Akış

1. **Lokal uygulama** toplantı kaydını Hugging Face’e (Caner7/Sense-AI) yükler.
2. Yükleme bitince uygulama bu repodaki workflow’u tetikler (`repository_dispatch`).
3. **Workflow:**  
   - En son toplantı klasörünü listeler → dosyaları indirir (.webm, .txt).  
   - .webm’lerden **0.5 saniye** aralıklarla frame çıkarır (224×224).  
   - **DAiSEE** modeli ile her frame’i değerlendirir (engagement / boredom / confusion / frustration).  
   - **Birden fazla katılımcı** (her ekran kaydı = bir katılımcı) için ayrı ayrı analiz + **toplu özet** ile tek rapor üretir.  
   - Rapor **HF’deki ilgili toplantı klasörüne** `toplanti_raporu.md` olarak yüklenir; ayrıca artifact olarak da saklanır.
