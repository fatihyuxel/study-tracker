# 📚 Çocuk Çalışma Takip Uygulaması

Aile içi kullanım için tasarlanmış, Streamlit tabanlı çocuk çalışma takip sistesi.

## Özellikler

- 👧 Her çocuk için ayrı çalışma alanı
- 📊 Ebevyn paneli: analiz grafikleri, plan yönetimi
- 📅 Haftalık ders programı (Pazartesi-Pazar)
- 🏖️ Tatil günü desteği
- 📱 Mobil uyumlu tasarım
- ☁️ Google Sheets veritabanı (ücretsiz hosting)

## Kurulum

### 1. Google Cloud Ayarları

1. [Google Cloud Console](https://console.cloud.google.com/) gidin
2. Yeni proje oluşturun (veya mevcut projeyi seçin)
3. **APIs & Services → Library** kısmından **Google Sheets API**'yi etkinleştirin
4. **IAM & Admin → Service Accounts** kısmında yeni service account oluşturun
5. Oluşturulan service account'a tıklayın → **Keys → Add Key → Create New Key → JSON**
6. İndirilen JSON dosyasındaki bilgileri `.streamlit/secrets.toml` dosyasına girin

### 2. Google Sheet Oluşturma

1. [Google Sheets](https://sheets.google.com)'te yeni bir boş sheet oluşturun
2. Sheet'in URL'sini kopyalayın (veya key'ini)
3. **Share** butonuna tıklayın
4. Service account email adresini ekleyin (JSON'daki `client_email`)
5. **Editor** yetkisi verin

### 3. secrets.toml Dosyası

`.streamlit/secrets.toml` dosyasını oluşturun:

```toml
# Google Sheet URL'si veya Key'i
spreadsheet_key = "SHEET_KEY_BURAYA"

[gspread]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "[REDACTED PRIVATE KEY]\n"
client_email = "...@...iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

Örnek için `.streamlit/secrets.toml.example` dosyasına bakın.

### 4. Yerel Çalıştırma

```bash
pip install -r requirements.txt
streamlit run app.py
```

### 5. Streamlit Cloud'a Deploy

1. Bu repoyu GitHub'a yükleyin
2. [Streamlit Cloud](https://share.streamlit.io/) gidin
3. GitHub ile giriş yapın
4. **New app** → repoyu seçin → **Deploy**
5. **Settings → Secrets** kısmından `secrets.toml` içeriğini yapıştırın

## Veri Yapısı (Google Sheets)

Uygulama ilk açıldığında 4 sayfa otomatik oluşturulur:

| Sayfa | Açıklama |
|-------|----------|
| `logs` | Çocukların günlük soru kayıtları |
| `targets` | Haftalık ders planı (hangi gün, kaç soru) |
| `subjects` | Her çocuğun ders listesi |
| `holidays` | Tatil günleri |

## Kullanım

### Çocuk Girişi
- Sol menüden isim seçin
- Bugünkü hedeflerinizi görün
- Soru girin, geçmiş kayıtları düzenleyin

### Ebevyn Paneli
- **Analiz**: Grafikler ve istatistikler
- **Haftalık Plan**: Ders programını ayarlayın
- **Dersler**: Ders listesini yönetin
- **Tatiller**: Tatil günleri ekleyin
