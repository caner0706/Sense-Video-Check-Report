# Yeni veri gelince workflow çalışsın

Lokal uygulaman HF'e yükleme bittikten hemen sonra workflow'u tetiklesin; sadece yeni veri geldiği anda çalışır.

## Pratik yol

### 1. Token oluştur (bir kez)

GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**  
- Note: `Sense workflow tetikleyici`  
- Scopes: **repo**  
- Token'ı kopyala (`ghp_...`)

### 2. Token'ı sakla (repoya koyma)

- **Ortam değişkeni:** `~/.zshrc` içine `export GITHUB_TOKEN="ghp_xxx"` → `source ~/.zshrc`
- Veya uygulama config / `.env` (dosyayı .gitignore'a ekle)

### 3. HF yüklemesi bittikten sonra tetikle

**Python:**
```python
from trigger_workflow import trigger_fetch_workflow
trigger_fetch_workflow()  # GITHUB_TOKEN env'den okur
```

**curl:**
```bash
curl -X POST -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/caner0706/Sense-Video-Check-Report/dispatches \
  -d '{"event_type":"hf_dataset_update"}'
```
