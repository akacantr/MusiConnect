# 🎵 MusiConnect

Spotify çalma listelerinizi (**şarkı sayısı sınırı olmaksızın**) en doğru eşleşmelerle YouTube Music'e aktaran, modern web arayüzüne sahip kişisel müzik transfer uygulaması.

---

## ✨ Özellikler

- **Limitsiz Aktarım (Kota Dostu):** Resmi YouTube Data API'nin günlük 66 şarkı sınırlamasına takılmaz. `ytmusicapi` altyapısı sayesinde 100, 500 veya 1.000+ şarkılık listeleri tek seferde aktarır.
- **Akıllı Şarkı Eşleştirme (Smart Matcher):**
  - Gereksiz başlık eklerini (örn. `Official Video`, `Remastered`, `Lyrics`) otomatik temizler.
  - Şarkının orijinal süresi ile YouTube'daki videonun süresini karşılaştırır (varsayılan: ±7 sn tolerans). Böylece 1 saatlik loop'lar, röportajlar veya uzatılmış canlı kayıtlar elenir.
  - YouTube Music'in "Şarkılar" (Songs) kategorisindeki resmi plak şirketi yüklemelerine öncelik verir.
- **Toplu İşlem & Hız Koruma (Batching & Anti-RateLimit):** Şarkıları YouTube Music'e 25'erli paketler halinde ekler ve sunucu engeline takılmamak için istekler arasına güvenli bekleme süreleri koyar.
- **Canlı İlerleme Çubuğu:** Web arayüzünde anlık olarak hangi şarkının işlendiğini, eşleşme skorunu ve aktarım durumunu canlı izleyebilirsiniz.
- **Modüler & Genişletilebilir Mimari:** `BaseMusicProvider` arayüzü sayesinde ileride Apple Music, Deezer vb. platformlar kolayca eklenebilir.

---

## 🚀 Hızlı Başlangıç

### 1. Çalıştırma
Uygulamayı başlatmak için proje klasöründeki **`start.bat`** dosyasına çift tıklayın veya terminalden çalıştırın:

```powershell
py run.py
```

Tarayıcınız otomatik olarak `http://127.0.0.1:8000` adresinde açılacaktır.

---

## 🔑 Bağlantı Kurulumu

### 1. Spotify Bağlantısı
1. [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) adresine gidin ve Spotify hesabınızla giriş yapın.
2. **Create app** butonuna basarak bir uygulama oluşturun (İsim olarak `MusiConnect` yazabilirsiniz).
3. Uygulamanızın **Settings** bölümünden **Client ID** ve **Client Secret** değerlerini kopyalayın.
4. MusiConnect web arayüzündeki **Bağlantılar & Ayarlar** sekmesine yapıştırıp **Kaydet** butonuna basın.

### 2. YouTube Music Bağlantısı (Kota Sınırsız)
1. Tarayıcınızda [music.youtube.com](https://music.youtube.com) adresini açıp Google hesabınızla oturum açın.
2. Klavyeden **F12** tuşuna basarak Geliştirici Araçlarını açın ve **Network (Ağ)** sekmesine gelin.
3. Sayfayı yenileyin veya arama yapın. Network listesinde görünen **browse** (veya herhangi bir) isteğe sağ tıklayın.
4. **Copy ➔ Copy request headers** (İstek başlıklarını kopyala) seçeneğine tıklayın.
5. MusiConnect web arayüzündeki **YouTube Music** kutusuna yapıştırıp **Bağlan ve Doğrula** butonuna basın.

---

## 📁 Proje Mimarisi

```text
MusiConnect/
├── app/
│   ├── config.py             # Ayarlar ve dosya yönetimi
│   ├── main.py               # FastAPI uygulaması ve CORS
│   ├── api/
│   │   └── routes.py         # REST & Server-Sent Events (SSE) uç noktaları
│   ├── core/
│   │   ├── base_provider.py  # Genişletilebilir platform arayüzü (BaseMusicProvider)
│   │   ├── matcher.py        # Süre ve metin benzerliği hesaplayan akıllı algoritma
│   │   └── transfer.py       # Arka plan aktarım yöneticisi ve kuyruk sistemi
│   ├── providers/
│   │   ├── spotify_provider.py # Spotify API entegrasyonu ve sayfalama
│   │   └── youtube_provider.py # YouTube Music arama ve liste oluşturma
│   └── static/               # Modern Glassmorphic Dark UI (HTML, CSS, JS)
├── data/                     # Yerel ayarlar ve geçmiş (gitignored)
├── requirements.txt
├── run.py                    # Başlatıcı script
└── start.bat                 # Windows tek tıkla başlatıcı
```
