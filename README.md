# Cloudflare Bypass Aracı 2026

SeleniumBase UC Mode tabanlı Cloudflare Turnstile doğrulama atlatma aracı.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Mac%20%7C%20Windows%20%7C%20Linux-green.svg)
![Lisans](https://img.shields.io/badge/Lisans-MIT-yellow.svg)

---

## ⚠️ Sorumluluk Reddi

Bu araç yalnızca eğitim ve araştırma amaçlıdır. Lütfen ilgili yasalara ve hedef web sitelerinin kullanım koşullarına uyun.

---

## 🚀 Özellikler

| Özellik | Açıklama |
|:---|:---|
| SeleniumBase UC Mode | İşletim sistemi seviyesinde fare simülasyonu, en yüksek başarı oranı |
| Tek Tarayıcı Modu | Basit ve güvenilir, düşük kaynak kullanımı |
| Paralel Mod | Birden fazla tarayıcı aynı anda çalışır, verimliliği artırır |
| Proxy Rotasyonu | Dosyadan toplu proxy yükleme desteği |
| HTTPS Tünel Kontrolü | Proxy'nin HTTPS'i destekleyip desteklemediğini otomatik doğrular |
| Çoklu Platform | Mac / Windows / Linux |
| Cookie Kaydetme | JSON + Netscape çift format |

---

## ⚡ Hızlı Başlangıç

```bash
# Kurulum
pip install seleniumbase

# Temel kullanım (önerilen)
python bypass.py https://ornek.com

# Proxy ile kullanım
python bypass.py https://ornek.com -p http://127.0.0.1:7890
```

---

## 📦 Kurulum

### Mac / Windows

```bash
git clone https://github.com/zencefilefendi/cloudflare-bypass-2026.git
cd cloudflare-bypass-2026
pip install -r requirements.txt
```

### Linux (Ubuntu/Debian)

```bash
# Yöntem 1: Tek komutla kurulum
git clone https://github.com/zencefilefendi/cloudflare-bypass-2026.git
cd cloudflare-bypass-2026
sudo bash install_linux.sh

# Yöntem 2: Manuel kurulum
sudo apt-get update
sudo apt-get install -y xvfb libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libgbm1 libasound2

# Chrome kurulumu
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y

# Python bağımlılıkları
pip install seleniumbase pyvirtualdisplay
```

---

## 📖 Kullanım

### 1. Basit Mod (bypass.py) - Önerilen

Tek tarayıcı, basit ve güvenilir:

```bash
# Doğrudan bağlantı
python bypass.py https://ornek.com

# Proxy ile
python bypass.py https://ornek.com -p http://127.0.0.1:7890

# Zaman aşımı ayarı
python bypass.py https://ornek.com -t 60
```

**Parametreler:**

| Parametre | Açıklama | Varsayılan |
|:---|:---|:---:|
| `url` | Hedef URL | Zorunlu |
| `-p, --proxy` | Proxy adresi | - |
| `-t, --timeout` | Zaman aşımı (saniye) | 60 |
| `--no-save` | Cookie kaydetme | Hayır |

---

### 2. Gelişmiş Mod (simple_bypass.py)

Paralel çalışma ve proxy rotasyonu desteği:

```bash
# Doğrudan bağlantı modu
python simple_bypass.py https://ornek.com

# Belirtilen proxy ile
python simple_bypass.py https://ornek.com -p http://127.0.0.1:7890

# Proxy rotasyonu modu (proxy.txt dosyasındaki proxy'leri sırayla dener)
python simple_bypass.py https://ornek.com -r -f proxy.txt

# Paralel mod (3 tarayıcı aynı anda çalışır)
python simple_bypass.py https://ornek.com -P -b 3 -t 60

# Paralel + Proxy kontrolü + 30 tur
python simple_bypass.py https://ornek.com -P -c -b 3 -t 15 -n 30 -f proxy.txt
```

**Parametreler:**

| Parametre | Açıklama | Varsayılan |
|:---|:---|:---:|
| `url` | Hedef URL | Zorunlu |
| `-p, --proxy` | Belirtilen proxy adresi | - |
| `-f, --proxy-file` | Proxy dosyası yolu | proxy.txt |
| `-r, --rotate` | Sıralı proxy rotasyonu modu | Hayır |
| `-P, --parallel` | Paralel mod | Hayır |
| `-b, --batch` | Paralel tarayıcı sayısı | 3 |
| `-t, --timeout` | Zaman aşımı (saniye) | 60 |
| `-n, --retries` | Maksimum tur/deneme sayısı | 3 |
| `-c, --check-proxy` | Proxy canlılık kontrolü | Hayır |
| `--no-save` | Cookie kaydetme | Hayır |

---

### 3. Python API

```python
# Basit mod
from bypass import bypass_cloudflare

result = bypass_cloudflare("https://ornek.com")
if result["success"]:
    print(f"cf_clearance: {result['cf_clearance']}")
    print(f"User-Agent: {result['user_agent']}")

# Gelişmiş mod
from simple_bypass import bypass_cloudflare, bypass_parallel

# Tekli atlatma
result = bypass_cloudflare("https://ornek.com", proxy="http://127.0.0.1:7890")

# Paralel atlatma
result = bypass_parallel(
    url="https://ornek.com",
    proxy_file="proxy.txt",
    batch_size=3,
    timeout=15.0,
    max_batches=30
)
```

---

## 📝 Proxy Dosya Formatı

`proxy.txt` dosyasında her satıra bir proxy yazın:

```
# Desteklenen formatlar
127.0.0.1:7890
http://127.0.0.1:7890
socks5://127.0.0.1:1080
http://kullanici:sifre@sunucu:port
```

---

## 📂 Çıktı Dosyaları

Cookie'ler `output/cookies/` dizinine kaydedilir:

| Dosya | Format | Kullanım |
|:---|:---|:---|
| `cookies_*.json` | JSON | Programatik kullanım |
| `cookies_*.txt` | Netscape | curl -b ile kullanım |

**JSON Örneği:**
```json
{
  "url": "https://ornek.com",
  "cookies": {
    "cf_clearance": "xxx..."
  },
  "user_agent": "Mozilla/5.0...",
  "timestamp": "20260122_103000"
}
```

---

## 📁 Proje Yapısı

```
cloudflare-bypass-2026/
├── bypass.py              # Basit sürüm (önerilen)
├── simple_bypass.py       # Gelişmiş sürüm (paralel+proxy rotasyonu)
├── install_linux.sh       # Linux kurulum scripti
├── requirements.txt       # Python bağımlılıkları
├── proxy.txt              # Proxy listesi
├── output/                # Cookie çıktı dizini
└── README.md
```

---

## ❓ Sık Sorulan Sorular

**S: Neden başsız (headless) mod kullanılmıyor?**
> Cloudflare başsız tarayıcıları tespit edebilir. En yüksek başarı oranı için görsel modu kullanmanız önerilir.

**S: cf_clearance geçerlilik süresi nedir?**
> Genellikle 30 dakika ile birkaç saat arasında. Süresi dolmadan yeniden almanız önerilir.

**S: Linux'ta "X11 display failed" hatası alıyorum?**
> `sudo bash install_linux.sh` komutunu çalıştırarak Xvfb ve diğer bağımlılıkları kurun.

**S: Proxy çalışmıyor?**
> Çoğu ücretsiz proxy HTTPS tünelini desteklemez. Doğrudan bağlantı modunu kullanın veya kaliteli konut proxy'leri satın alın.

**S: Chrome birden fazla işlem başlatıyor?**
> Bu Chrome'un normal mimarisidir (ana işlem + render işlemi + GPU işlemi), kod sorunu değil.

---

## 🔗 Teknik Referanslar

- [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/)
- [SeleniumBase UC Mode](https://seleniumbase.com/)

---

## 📄 Lisans

MIT Lisansı - 2026

---


