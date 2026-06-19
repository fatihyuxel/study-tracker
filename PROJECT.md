# 📚 Çocuk Çalışma Takip Uygulaması — Proje Dokümantasyonu

> Bu doküman projenin tüm detaylarını, tasarım kararlarını ve teknik yapısını içerir.
> Gelecekteki geliştirmeler için referans olarak kullanılır.

---

## 📋 Proje Özeti

Aile içi kullanım için tasarlanmış, Streamlit tabanlı çocuk çalışma takip sistemi.
İki çocuk (Ayşe Bade ve Elmas) soru girişlerini kaydeder, ebevyn performans analizi yapar ve haftalık plan yönetir.

- **Teknoloji:** Python + Streamlit + Google Sheets + Plotly
- **Hosting:** Streamlit Cloud (ücretsiz)
- **Veritabanı:** Google Sheets (gspread kütüphanesi)
- **URL:** https://study-tracker1.streamlit.app/
- **GitHub:** https://github.com/fatihyuxel/study-tracker

---

## 🏗️ Dosya Yapısı

```
study_tracker/
├── .streamlit/
│   ├── config.toml           ← Dark tema ayarları
│   └── secrets.toml          ← Google Sheets credentials (gitignore'da)
├── app.py                    ← Ana uygulama (çocuk workspace + ebevyn paneli)
├── charts.py                 ← Plotly grafik fonksiyonları (4 grafik türü)
├── config.py                 ← Sabitler (isimler, günler, renkler, emoji'ler)
├── data.py                   ← Google Sheets CRUD fonksiyonları + cache yönetimi
├── requirements.txt          ← Python bağımlılıkları
├── .gitignore                ← secrets.toml hariç tutulur
└── README.md                 ← Kurulum rehberi
```

---

## 🗄️ Google Sheets Veri Yapısı

Uygulama ilk açıldığında 4 sayfa otomatik oluşturulur:

### 1. `logs` — Veri Girişleri
| Sütun | Tip | Açıklama |
|-------|-----|----------|
| Date | str | YYYY-MM-DD formatında tarih |
| ChildName | str | "Ayşe Bade" veya "Elmas" |
| Subject | str | Ders adı (Matematik, Türkçe, vb.) |
| Solved | int | Çözülen soru sayısı |
| Incorrect | int | Yanlış sayısı |
| Blank | int | Boş sayısı |

### 2. `targets` — Haftalık Plan
| Sütun | Tip | Açıklama |
|-------|-----|----------|
| ChildName | str | Çocuk adı |
| Subject | str | Ders adı |
| DayOfWeek | int | 0=Pazartesi ... 6=Pazar |
| TargetCount | int | O günkü hedef soru sayısı |

### 3. `subjects` — Ders Listesi
| Sütun | Tip | Açıklama |
|-------|-----|----------|
| ChildName | str | Çocuk adı |
| Subject | str | Ders adı |

### 4. `holidays` — Tatil Günleri
| Sütun | Tip | Açıklama |
|-------|-----|----------|
| Date | str | YYYY-MM-DD formatında tarih |
| Reason | str | Tatil sebebi (opsiyonel) |

---

## 👥 Kullanıcı Rolleri ve Akış

### Çocuk Workspace (Ayşe Bade / Elmas)

1. **Bugün bilgisi:** Türkiye saati (UTC+3) ile tarih ve gün adı
2. **Tatil kontrolü:** Bugün tatil mi? → Evetse "Bugün tatil! 🏖️" banner'ı
3. **Plan kontrolü:** Ebevyn plan ayarlamamışsa → "Henüz plan oluşturulmamış 📋"
4. **Bugünkü hedefler:** Bugün gününün planlı dersleri gösterilir
5. **Progress kartları:** Her ders için ilerleme çubuğu (%, renk kodlu)
6. **Metrikler:** Streak, Haftalık %, Bu Hafta toplam soru
7. **Haftalık grafik:** Hedef vs Gerçekleşen (Plotly bar chart)
8. **Soru girişi formu:** Tarih, ders, soru sayısı, yanlış, boş
9. **Geçmiş kayıtlar:** Tarih seçici ile geçmiş düzenleme

### Ebevyn Paneli

4 sekme:

#### 📊 Analiz
- Tarih aralığı ve çocuk filtresi
- 4 metric card: Toplam, Net Doğru, Yanlış, Hata Oranı
- Çizgi grafik: Günlük soru trendi
- Bar grafik: Ders bazlı hata oranı
- Pasta grafik: Ders dağılımı
- Ham veri tablosu (isteğe bağlı)

#### 📋 Haftalık Plan
- Her çocuk için ayrı section
- Her ders bir expander içinde
- 7 gün × input (Pzt-Paz)
- 0 = o gün çalışılmayacak
- Plan bir kez ayarlanır, iptal/revize edene kadar her hafta tekrar eder
- Mevcut plan özeti (ders bazlı toplam)

#### 📚 Dersler
- Her çocuk için ders listesi
- Ders ekleme formu
- Ders silme butonu (🗑️)

#### 🏖️ Tatiller
- Tatil günü listesi (tarih + sebep)
- Tatil ekleme formu
- Tatil silme butonu
- Tatil günlerinde hedef sıfırlanır

---

## 🔧 Teknik Detaylar

### Bağlantı Mekanizması
- `gspread` kütüphanesi ile Google Sheets API bağlantısı
- Service account authentication (JSON key)
- `st.cache_resource` ile bağlantı caching (bir kez oluşturulur)
- `st.cache_data(ttl=60)` ile veri caching (60 saniye)

### Cache Yönetimi
- Veri yazma sonrası `clear_all_caches()` çağrılır
- 4 cache fonksiyonu: `get_logs()`, `get_targets()`, `get_subjects()`, `get_holidays()`
- TTL: 60 saniye (otomatik yenileme)

### Doğrulama Kuralları
- Yanlış + Boş > Soru Sayısı → engelle
- Negatif değer → engelle
- 0 soru girişi → serbest (hasta günleri için)
- Aynı tarih+çocuk+ders → upsert (uyarı + güncelleme)

### Zaman Dilimi
- Türkiye saati (Europe/Istanbul, UTC+3)
- `zoneinfo.ZoneInfo` kullanılır
- "Bugün" Türkiye saatine göre hesaplanır

### Streak Hesaplama
- Son 365 güne kadar geriye bakar
- Bir gün "tamamlanmış" sayılır: o günün tüm planlı derslerinde kayıt varsa
- Tatil günleri streak'i devam ettirir
- Plansız günler (o gün programda yok) atlanır

---

## 📱 Mobil Uyumlu Tasarım

### CSS Düzenlemeleri
- Font boyutu: 16px (okunabilirlik)
- Metric kartları: gradient arka plan, border radius
- Butonlar: border radius, hover efekti
- Form alanları: border radius
- Success/Warning/Danger kutuları: renkli arka plan
- Tatil banner: gradient arka plan

### Düzen İlkeleri
- Tek sütun düzen (mobil uyumlu)
- Metric kartları: max 2 sütun
- Grafikler: tam genişlik, responsive
- Expanders: dar ekranda iyi çalışır
- Plotly: responsive=True, displayModeBar=False

---

## 🎨 Tema ve Renkler

### Streamlit Config (.streamlit/config.toml)
- Base: dark
- Primary Color: #3b82f6 (mavi)
- Background: #0e1117
- Secondary Background: #1a1a2e
- Text: #e2e8f0

### Renk Paleti (config.py)
- Success: #22c55e (yeşil)
- Warning: #f59e0b (sarı)
- Danger: #ef4444 (kırmızı)
- Info: #3b82f6 (mavi)

### Grafik Renkleri (charts.py)
8 renk paleti: mavi, kırmızı, yeşil, sarı, mor, pembe, teal, turuncu

---

## 📊 Grafik Türleri

### 1. Çizgi Grafik — Günlük Trend
- X ekseni: tarih
- Y ekseni: toplam soru sayısı
- Her çocuk ayrı çizgi
- Fonksiyon: `chart_daily_trend(logs, children)`

### 2. Bar Grafik — Hata Oranı
- X ekseni: hata oranı (%)
- Y ekseni: dersler
- Renk kodlu: <20% yeşil, 20-40% sarı, >40% kırmızı
- Fonksiyon: `chart_error_analysis(logs, child_name)`

### 3. Pasta Grafik — Ders Dağılımı
- Dilimler: ders bazlı toplam soru yüzdesi
- Hole: 0.4 (donut chart)
- Fonksiyon: `chart_subject_distribution(logs, child_name)`

### 4. Grouped Bar — Hedef vs Gerçekleşen
- X ekseni: dersler
- 2 bar: Hedef (mavi), Gerçekleşen (yeşil)
- Fonksiyon: `chart_weekly_target_comparison(progress, child_name)`

---

## 🚀 Deployment

### Streamlit Cloud
1. GitHub repo: fatihyuxel/study-tracker
2. Streamlit Cloud: https://share.streamlit.io
3. Secrets: Settings → Secrets → secrets.toml içeriği yapıştır
4. URL: https://study-tracker1.streamlit.app/

### Secrets Yapısı (Streamlit Cloud)
```toml
spreadsheet_key = "SHEET_KEY"

[gspread]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = """-----BEGIN PRIVATE KEY-----
...key content...
-----END PRIVATE KEY-----"""
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

### Google Cloud Ayarları
1. Google Cloud Console'da proje oluştur
2. Google Sheets API etkinleştir
3. Service Account oluştur
4. JSON key indir
5. Google Sheet'i service account email ile paylaş (Editor yetkisi)

---

## 🐛 Bilinen Sorunlar ve Çözümleri

### 1. `AttributeError: 'list' object has no attribute 'empty'`
- **Neden:** `today_targets` boş liste `[]` olarak geliyor
- **Çözüm:** `hasattr(today_targets, 'empty')` kontrolü eklendi

### 2. Tarih İngilizce Görünüyor
- **Neden:** `strftime("%d %B %Y")` İngilizce ay adı döndürüyor
- **Çözüm:** Türkçe ay isimleri sözlüğü eklendi

### 3. TOML Format Hatası (Streamlit Cloud)
- **Neden:** Private key special karakterler içeriyor
- **Çözüm:** Triple quotes (`"""..."""`) kullanıldı

---

## 🔮 Gelecek Geliştirmeler

### Öncelikli
- [ ] Bildirim sistemi (hedef tamamlandığında ebevyn bilgilendirme)
- [ ] Export fonksiyonu (CSV/PDF)
- [ ] Karşılaştırma görünümü (Ayşe Bade vs Elmas)

### Orta Öncelikli
- [ ] Haftalık/aylık özet raporlar
- [ ] Ders bazlı trend analizi
- [ ] Motivasyon mesajları (AI destekli)

### Düşük Öncelikli
- [ ] Çoklu dil desteği
- [ ] Tema seçici (light/dark)
- [ ] Veri yedekleme/geri yükleme

---

## 📝 Geliştirme Notları

### Yerel Çalıştırma
```bash
cd study_tracker
pip install -r requirements.txt
streamlit run app.py
```

### Test Prosedürü
1. Ebevyn panelinden ders ekle
2. Haftalık plan ayarla
3. Çocuk tarafından veri gir
4. Progress bar ve metriklerin güncellendiğini kontrol et
5. Geçmiş kayıtları düzenle
6. Tatil günü ekle, hedef sıfırlandığını kontrol et

### Git Workflow
```bash
git add -A
git commit -m "descriptive message"
git push origin main
# Streamlit Cloud otomatik deploy eder
```

---

## 📊 Veri Akışı Diyagramı

```
[Çocuk] → [Soru Girişi Formu] → [Doğrulama] → [Google Sheets: logs]
                                                      ↓
[Ebevyn] → [Plan Yönetimi] → [Google Sheets: targets]
                                                      ↓
[Ebevyn] → [Ders Yönetimi] → [Google Sheets: subjects]
                                                      ↓
[Ebevyn] → [Tatil Yönetimi] → [Google Sheets: holidays]
                                                      ↓
[Çocuk Workspace] ← [Okuma: targets + logs + holidays] → [Grafikler + Metrikler]
[Ebevyn Paneli] ← [Okuma: logs + targets + subjects] → [Analiz Grafikleri]
```

---

## 🔐 Güvenlik

- URL bilen herkes erişebilir (aile içi kullanım)
- Google Sheets API erişimi service account ile sınırlı
- secrets.toml gitignore'da (GitHub'da yayınlanmaz)
- Streamlit Cloud secrets encrypted storage

---

*Son güncelleme: 19 Haziran 2026*
