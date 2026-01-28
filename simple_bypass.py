# ============================================================
# Cloudflare Turnstile Atlatma Aracı - Gelişmiş Sürüm (Önerilen)
# SeleniumBase UC Mode tabanlı, tek dosyada tüm özellikler
# Mac / Windows / Linux destekler
# ============================================================

import os
import sys
import time
import json
import random
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from seleniumbase import SB


def dosyadan_proxy_yukle(dosya_yolu: str = "proxy.txt") -> List[str]:
    """
    Dosyadan proxy listesi yükler
    
    Parametreler:
        dosya_yolu: Proxy dosya yolu
    
    Döndürür:
        Proxy listesi (format: http://IP:PORT)
    """
    proxyler = []
    yol = Path(dosya_yolu)
    
    if not yol.exists():
        return proxyler
    
    with open(yol, "r", encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            # Boş satırları ve yorumları atla
            if satir and not satir.startswith("#"):
                # Proxy'nin protokol öneki olduğundan emin ol
                if not satir.startswith(("http://", "https://", "socks5://", "socks4://")):
                    satir = f"http://{satir}"
                proxyler.append(satir)
    
    return proxyler


def rastgele_proxy_al(dosya_yolu: str = "proxy.txt") -> Optional[str]:
    """
    Dosyadan rastgele bir proxy alır
    
    Parametreler:
        dosya_yolu: Proxy dosya yolu
    
    Döndürür:
        Rastgele proxy veya None
    """
    proxyler = dosyadan_proxy_yukle(dosya_yolu)
    if proxyler:
        return random.choice(proxyler)
    return None


def linux_mi() -> bool:
    """Linux sistemi olup olmadığını kontrol eder"""
    return platform.system().lower() == "linux"


def proxy_canli_mi(proxy: str, zaman_asimi: float = 8.0) -> bool:
    """
    Proxy'nin HTTPS tünelini destekleyip desteklemediğini kontrol eder
    
    Parametreler:
        proxy: Proxy adresi
        zaman_asimi: Zaman aşımı süresi (saniye)
    
    Döndürür:
        Proxy kullanılabilir mi
    """
    import urllib.request
    import ssl
    
    try:
        # Proxy formatının doğru olduğundan emin ol
        if "://" not in proxy:
            proxy = f"http://{proxy}"
        
        # Proxy işleyicisi oluştur
        proxy_handler = urllib.request.ProxyHandler({
            'http': proxy,
            'https': proxy
        })
        opener = urllib.request.build_opener(proxy_handler)
        
        # HTTPS web sitesiyle test et, proxy'nin HTTPS tünelini (CONNECT) desteklediğinden emin ol
        request = urllib.request.Request(
            "https://httpbin.org/ip",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'
            }
        )
        
        # SSL sertifika doğrulamasını atla
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        response = opener.open(request, timeout=zaman_asimi)
        
        if response.status == 200:
            return True
        return False
        
    except Exception:
        return False


def calisan_proxy_al(dosya_yolu: str = "proxy.txt", max_kontrol: int = 10, zaman_asimi: float = 3.0) -> Optional[str]:
    """
    Dosyadan çalışan bir proxy alır
    
    Parametreler:
        dosya_yolu: Proxy dosya yolu
        max_kontrol: Maksimum kontrol edilecek proxy sayısı
        zaman_asimi: Her proxy için kontrol zaman aşımı
    
    Döndürür:
        Çalışan proxy veya None
    """
    proxyler = dosyadan_proxy_yukle(dosya_yolu)
    if not proxyler:
        return None
    
    # Sırayı karıştır
    random.shuffle(proxyler)
    
    kontrol_edildi = 0
    for proxy in proxyler:
        if kontrol_edildi >= max_kontrol:
            break
        
        print(f"[*] Proxy kontrol ediliyor: {proxy}...", end=" ")
        if proxy_canli_mi(proxy, zaman_asimi):
            print("✓ Kullanılabilir")
            return proxy
        else:
            print("✗ Kullanılamaz")
        kontrol_edildi += 1
    
    return None


def linux_ekran_ayarla():
    """
    Linux ekran ortamını ayarlar (masaüstü ortamı olmayan sunucular için)
    Gerekli: xvfb, pyvirtualdisplay
    """
    if linux_mi() and not os.environ.get("DISPLAY"):
        # Sanal ekran kullanmayı dene
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=False, size=(1920, 1080))
            display.start()
            os.environ["DISPLAY"] = display.new_display_var
            print("[*] Linux: Sanal ekran başlatıldı (Xvfb)")
            return display
        except ImportError:
            print("[!] Linux ekran ortamı yok, lütfen çalıştırın: bash install_linux.sh")
            print("[!] Veya manuel kurulum:")
            print("    apt-get install -y xvfb libglib2.0-0 libnss3 libatk1.0-0")
            print("    pip install pyvirtualdisplay")
            sys.exit(1)
        except Exception as e:
            print(f"[!] Sanal ekran başlatılamadı: {e}")
            print("[!] Lütfen Xvfb'nin kurulu olduğundan emin olun: apt-get install -y xvfb")
            sys.exit(1)
    return None


def chrome_kurulu_mu():
    """Chrome'un kurulu olup olmadığını kontrol eder"""
    import shutil
    
    chrome_yollari = [
        "google-chrome",
        "google-chrome-stable", 
        "chromium",
        "chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    ]
    
    for yol in chrome_yollari:
        if shutil.which(yol):
            return True
    
    return False


def proxy_rotasyonuyla_cloudflare_atlat(
    url: str,
    proxy_dosyasi: str = "proxy.txt",
    bekleme_suresi: float = 5.0,
    cookie_kaydet: bool = True,
    zaman_asimi: float = 60.0,
    max_deneme: int = 3,
    proxy_kontrol: bool = True
) -> Dict[str, Any]:
    """
    proxy.txt dosyasındaki proxy'leri sırayla deneyerek atlatır
    
    Parametreler:
        url: Hedef web sitesi URL'si
        proxy_dosyasi: Proxy dosya yolu
        bekleme_suresi: Sayfa yükleme bekleme süresi
        cookie_kaydet: Cookie kaydet
        zaman_asimi: Tekil zaman aşımı süresi
        max_deneme: Her proxy için maksimum deneme sayısı
        proxy_kontrol: Önceden proxy canlılık kontrolü yap
    """
    proxyler = dosyadan_proxy_yukle(proxy_dosyasi)
    
    if not proxyler:
        print("[!] Proxy dosyası boş, doğrudan bağlantı modu kullanılıyor")
        return cloudflare_atlat(url, None, bekleme_suresi, cookie_kaydet, zaman_asimi, 1)
    
    print(f"[*] {proxy_dosyasi} dosyasından {len(proxyler)} proxy yüklendi")
    
    # Proxy sırasını rastgele karıştır
    random.shuffle(proxyler)
    
    for i, proxy in enumerate(proxyler[:max_deneme], 1):
        print(f"\n{'='*50}")
        print(f"[*] Proxy deneniyor {i}/{min(len(proxyler), max_deneme)}: {proxy}")
        print(f"{'='*50}")
        
        # Proxy canlılık kontrolü
        if proxy_kontrol:
            print(f"[*] Proxy canlılık kontrolü...", end=" ")
            if not proxy_canli_mi(proxy, zaman_asimi=3.0):
                print("✗ Kullanılamaz, atlanıyor")
                continue
            print("✓ Kullanılabilir")
        
        # Atlatmayı dene
        sonuc = cloudflare_atlat(url, proxy, bekleme_suresi, cookie_kaydet, zaman_asimi, 1)
        
        if sonuc["basarili"]:
            sonuc["kullanilan_proxy"] = proxy
            return sonuc
        
        print(f"[-] Proxy {proxy} başarısız, sonraki deneniyor...")
    
    return {
        "basarili": False,
        "cookieler": {},
        "cf_clearance": None,
        "user_agent": None,
        "hata": f"Tüm proxy'ler başarısız ({min(len(proxyler), max_deneme)} denendi)",
        "deneme_sayisi": min(len(proxyler), max_deneme)
    }


def paralel_atlat(
    url: str,
    proxy_dosyasi: str = "proxy.txt",
    grup_boyutu: int = 3,
    zaman_asimi: float = 15.0,
    bekleme_suresi: float = 5.0,
    cookie_kaydet: bool = True,
    proxy_kontrol: bool = True,
    max_grup: int = 10
) -> Dict[str, Any]:
    """
    Birden fazla tarayıcıyı paralel olarak başlatır, farklı proxy'lerle aynı anda dener
    
    Parametreler:
        url: Hedef web sitesi URL'si
        proxy_dosyasi: Proxy dosya yolu
        grup_boyutu: Her grupta paralel tarayıcı sayısı (varsayılan 3)
        zaman_asimi: Her grup için zaman aşımı süresi (varsayılan 15 saniye)
        bekleme_suresi: Sayfa yükleme bekleme süresi
        cookie_kaydet: Cookie kaydet
        proxy_kontrol: Önceden proxy canlılık kontrolü yap
        max_grup: Maksimum grup sayısı
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    proxyler = dosyadan_proxy_yukle(proxy_dosyasi)
    
    if not proxyler:
        print("[!] Proxy dosyası boş")
        return {"basarili": False, "hata": "Kullanılabilir proxy yok"}
    
    print(f"[*] {proxy_dosyasi} dosyasından {len(proxyler)} proxy yüklendi")
    print(f"[*] Paralel mod: Her grupta {grup_boyutu} tarayıcı, zaman aşımı {zaman_asimi} saniye")
    
    # Proxy'leri rastgele karıştır
    random.shuffle(proxyler)
    
    # Önceden proxy canlılık kontrolü
    if proxy_kontrol:
        print("[*] Proxy canlılık kontrolü yapılıyor...")
        canli_proxyler = []
        for proxy in proxyler[:50]:  # Maksimum 50 kontrol
            if proxy_canli_mi(proxy, zaman_asimi=2.0):
                canli_proxyler.append(proxy)
                print(f"  ✓ {proxy}")
                if len(canli_proxyler) >= grup_boyutu * max_grup:
                    break
            else:
                print(f"  ✗ {proxy}")
        proxyler = canli_proxyler
        print(f"[*] {len(proxyler)} canlı proxy bulundu")
    
    if not proxyler:
        return {"basarili": False, "hata": "Canlı proxy bulunamadı"}
    
    # Başarılı sonucu saklamak için thread-safe değişken
    basari_sonucu = {"sonuc": None}
    sonuc_kilidi = threading.Lock()
    dur_olayi = threading.Event()
    
    def atlatma_dene(proxy: str, tarayici_id: int) -> Dict[str, Any]:
        """Tek tarayıcı denemesi"""
        if dur_olayi.is_set():
            return {"basarili": False, "hata": "İptal edildi"}
        
        try:
            print(f"[Tarayıcı{tarayici_id}] Başlatılıyor, proxy: {proxy}")
            
            with SB(uc=True, test=True, locale="en", proxy=proxy) as sb:
                if dur_olayi.is_set():
                    return {"basarili": False, "hata": "İptal edildi"}
                
                sb.uc_open_with_reconnect(url, reconnect_time=bekleme_suresi)
                time.sleep(2)
                
                if dur_olayi.is_set():
                    return {"basarili": False, "hata": "İptal edildi"}
                
                # Doğrulamayı tespit et ve işle
                sayfa_kaynak = sb.get_page_source().lower()
                if any(x in sayfa_kaynak for x in ["turnstile", "challenges.cloudflare", "just a moment"]):
                    print(f"[Tarayıcı{tarayici_id}] Doğrulama tespit edildi, tıklanıyor...")
                    try:
                        sb.uc_gui_click_captcha()
                        time.sleep(3)
                    except:
                        pass
                
                # Cookie'leri al
                cookie_listesi = sb.get_cookies()
                cookieler = {c["name"]: c["value"] for c in cookie_listesi}
                cf_clearance = cookieler.get("cf_clearance")
                
                if cf_clearance:
                    sonuc = {
                        "basarili": True,
                        "cookieler": cookieler,
                        "cf_clearance": cf_clearance,
                        "user_agent": sb.execute_script("return navigator.userAgent"),
                        "kullanilan_proxy": proxy,
                        "tarayici_id": tarayici_id
                    }
                    
                    # Başarılı sonucu ayarla ve diğer thread'lere dur sinyali gönder
                    with sonuc_kilidi:
                        if basari_sonucu["sonuc"] is None:
                            basari_sonucu["sonuc"] = sonuc
                            dur_olayi.set()
                            print(f"[Tarayıcı{tarayici_id}] ✅ Başarılı!")
                    
                    return sonuc
                else:
                    print(f"[Tarayıcı{tarayici_id}] cf_clearance alınamadı")
                    return {"basarili": False, "hata": "cf_clearance alınamadı", "proxy": proxy}
                    
        except Exception as e:
            print(f"[Tarayıcı{tarayici_id}] Hata: {str(e)[:50]}")
            return {"basarili": False, "hata": str(e), "proxy": proxy}
    
    # Gruplar halinde çalıştır
    grup_no = 0
    for i in range(0, len(proxyler), grup_boyutu):
        if grup_no >= max_grup:
            break
        
        grup_no += 1
        grup_proxyleri = proxyler[i:i+grup_boyutu]
        
        print(f"\n{'='*60}")
        print(f"[*] Grup {grup_no}: {len(grup_proxyleri)} tarayıcı başlatılıyor")
        print(f"{'='*60}")
        
        dur_olayi.clear()
        
        with ThreadPoolExecutor(max_workers=grup_boyutu) as executor:
            futures = {
                executor.submit(atlatma_dene, proxy, idx+1): proxy 
                for idx, proxy in enumerate(grup_proxyleri)
            }
            
            try:
                # Zaman aşımı veya başarı bekle
                for future in as_completed(futures, timeout=zaman_asimi):
                    sonuc = future.result()
                    if sonuc["basarili"]:
                        # Cookie kaydet
                        if cookie_kaydet:
                            kayit_dizini = Path("output/cookies")
                            kayit_dizini.mkdir(parents=True, exist_ok=True)
                            zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
                            with open(kayit_dizini / f"cookies_{zaman_damgasi}.json", "w", encoding="utf-8") as f:
                                json.dump(sonuc, f, indent=2)
                            print(f"[+] Cookie kaydedildi")
                        return sonuc
                        
            except Exception as e:
                print(f"[!] Grup zaman aşımı veya hata: {e}")
                dur_olayi.set()
        
        # Başarılı sonuç var mı kontrol et
        if basari_sonucu["sonuc"]:
            return basari_sonucu["sonuc"]
        
        print(f"[-] Grup {grup_no} başarısız, sonraki grup deneniyor...")
    
    return {
        "basarili": False,
        "cookieler": {},
        "cf_clearance": None,
        "hata": f"Tüm gruplar başarısız (toplam {grup_no} grup)",
        "deneme_sayisi": grup_no * grup_boyutu
    }


def cloudflare_atlat(
    url: str,
    proxy: Optional[str] = None,
    bekleme_suresi: float = 5.0,
    cookie_kaydet: bool = True,
    zaman_asimi: float = 60.0,
    max_deneme: int = 1
) -> Dict[str, Any]:
    """
    Cloudflare doğrulamasını atlatır ve Cookie alır
    
    Parametreler:
        url: Hedef web sitesi URL'si
        proxy: Proxy adresi (isteğe bağlı, format: http://host:port)
        bekleme_suresi: Sayfa yükleme bekleme süresi (saniye)
        cookie_kaydet: Cookie'leri dosyaya kaydet
        zaman_asimi: Erken durdurma zaman aşımı süresi (saniye), varsayılan 15 saniye
        max_deneme: Maksimum deneme sayısı, varsayılan 3
    
    Döndürür:
        {
            "basarili": bool,           # Başarılı mı
            "cookieler": dict,          # Cookie sözlüğü {ad: değer}
            "cf_clearance": str,        # cf_clearance değeri
            "user_agent": str,          # Kullanılan User-Agent
            "hata": str                 # Hata mesajı (başarısızsa)
        }
    
    Kullanım örneği:
        sonuc = cloudflare_atlat("https://ornek.com")
        if sonuc["basarili"]:
            print(f"cf_clearance: {sonuc['cf_clearance']}")
    """
    import signal
    
    sonuc = {
        "basarili": False,
        "cookieler": {},
        "cf_clearance": None,
        "user_agent": None,
        "hata": None,
        "deneme_sayisi": 0
    }
    
    # Zaman aşımı işleyicisi
    class ZamanAsimiHatasi(Exception):
        pass
    
    def zaman_asimi_isleyici(signum, frame):
        raise ZamanAsimiHatasi("İşlem zaman aşımına uğradı")
    
    # Tekil deneme
    def tekil_deneme(deneme_no: int) -> bool:
        nonlocal sonuc
        print(f"\n[*] Deneme {deneme_no}/{max_deneme}...")
        
        try:
            # Zaman aşımı ayarla (sadece Unix sistemlerinde sinyal desteklenir)
            if not linux_mi() or platform.system() == "Darwin":
                # Mac/Linux sinyal zaman aşımı kullan
                try:
                    signal.signal(signal.SIGALRM, zaman_asimi_isleyici)
                    signal.alarm(int(zaman_asimi))
                except (AttributeError, ValueError):
                    pass  # Windows desteklemez
            
            with SB(uc=True, test=True, locale="en", proxy=proxy) as sb:
                print(f"[*] Açılıyor: {url}")
                
                # UC modu ile sayfayı aç
                sb.uc_open_with_reconnect(url, reconnect_time=bekleme_suresi)
                time.sleep(2)
                
                # Doğrulamayı tespit et ve işle
                sayfa_kaynak = sb.get_page_source().lower()
                if any(x in sayfa_kaynak for x in ["turnstile", "challenges.cloudflare", "just a moment", "verify you are human"]):
                    print("[*] Cloudflare doğrulaması tespit edildi, tıklanmaya çalışılıyor...")
                    try:
                        sb.uc_gui_click_captcha()
                        time.sleep(3)
                    except Exception as e:
                        print(f"[!] Tıklama hatası: {e}")
                
                # Cookie'leri al
                cookie_listesi = sb.get_cookies()
                sonuc["cookieler"] = {c["name"]: c["value"] for c in cookie_listesi}
                sonuc["cf_clearance"] = sonuc["cookieler"].get("cf_clearance")
                sonuc["user_agent"] = sb.execute_script("return navigator.userAgent")
                
                # Zaman aşımını iptal et
                try:
                    signal.alarm(0)
                except (AttributeError, ValueError):
                    pass
                
                if sonuc["cf_clearance"]:
                    sonuc["basarili"] = True
                    print(f"[+] Atlatma başarılı! cf_clearance alındı")
                    
                    # Cookie kaydet
                    if cookie_kaydet:
                        kayit_dizini = Path("output/cookies")
                        kayit_dizini.mkdir(parents=True, exist_ok=True)
                        zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        with open(kayit_dizini / f"cookies_{zaman_damgasi}.json", "w", encoding="utf-8") as f:
                            json.dump({"url": url, "cookieler": sonuc["cookieler"], "user_agent": sonuc["user_agent"]}, f, indent=2)
                        
                        with open(kayit_dizini / f"cookies_{zaman_damgasi}.txt", "w") as f:
                            f.write("# Netscape HTTP Cookie File\n")
                            for c in cookie_listesi:
                                domain = c.get("domain", "")
                                f.write(f"{domain}\tTRUE\t{c.get('path', '/')}\t{'TRUE' if c.get('secure') else 'FALSE'}\t{int(c.get('expiry', 0))}\t{c['name']}\t{c['value']}\n")
                        
                        print(f"[+] Cookie kaydedildi: {kayit_dizini}")
                    
                    return True
                else:
                    print(f"[-] cf_clearance alınamadı, Cookie sayısı: {len(sonuc['cookieler'])}")
                    return False
                    
        except ZamanAsimiHatasi:
            print(f"[-] Zaman aşımı ({zaman_asimi} saniye)")
            try:
                signal.alarm(0)
            except:
                pass
            return False
        except Exception as e:
            sonuc["hata"] = str(e)
            print(f"[-] Hata: {e}")
            try:
                signal.alarm(0)
            except:
                pass
            return False
    
    # Yeniden deneme döngüsü
    for deneme in range(1, max_deneme + 1):
        sonuc["deneme_sayisi"] = deneme
        if tekil_deneme(deneme):
            return sonuc
        
        if deneme < max_deneme:
            print(f"[*] 2 saniye sonra yeniden deneniyor...")
            time.sleep(2)
    
    if not sonuc["hata"]:
        sonuc["hata"] = f"Maksimum deneme sayısına ulaşıldı ({max_deneme})"
    
    return sonuc


# ============================================================
# Komut Satırı Girişi
# ============================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Cloudflare Turnstile Atlatma Aracı (Mac/Windows/Linux destekler)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python simple_bypass.py https://ornek.com
  python simple_bypass.py https://ornek.com -p http://127.0.0.1:7890
  python simple_bypass.py https://ornek.com --proxy-file proxy.txt
  python simple_bypass.py https://ornek.com -f proxy.txt --random
        """
    )
    parser.add_argument("url", help="Hedef URL")
    parser.add_argument("-p", "--proxy", help="Proxy adresi (doğrudan belirt)")
    parser.add_argument("-f", "--proxy-file", default="proxy.txt", help="Proxy dosya yolu (varsayılan: proxy.txt)")
    parser.add_argument("-r", "--rotate", action="store_true", help="Sıralı proxy rotasyonu modu")
    parser.add_argument("-P", "--parallel", action="store_true", help="Paralel mod: Birden fazla tarayıcı aynı anda başlat")
    parser.add_argument("-b", "--batch", type=int, default=3, help="Paralel modda her gruptaki tarayıcı sayısı (varsayılan: 3)")
    parser.add_argument("-w", "--wait", type=float, default=5.0, help="Bekleme süresi (varsayılan: 5 saniye)")
    parser.add_argument("-t", "--timeout", type=float, default=60.0, help="Zaman aşımı (varsayılan: 60 saniye)")
    parser.add_argument("-n", "--retries", type=int, default=3, help="Maksimum deneme grubu/proxy sayısı (varsayılan: 3)")
    parser.add_argument("-c", "--check-proxy", action="store_true", help="Önceden proxy canlılık kontrolü yap")
    parser.add_argument("--no-save", action="store_true", help="Cookie'leri dosyaya kaydetme")
    args = parser.parse_args()
    
    # Chrome kurulu mu kontrol et
    if not chrome_kurulu_mu():
        print("\n[!] Hata: Chrome/Chromium kurulu değil!")
        if linux_mi():
            print("[!] Linux için çalıştırın: bash install_linux.sh")
            print("[!] Veya manuel kurun: wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && dpkg -i google-chrome-stable_current_amd64.deb")
        else:
            print("[!] Lütfen Google Chrome kurun: https://www.google.com/chrome/")
        sys.exit(1)
    
    # Linux sanal ekran ayarı
    display = linux_ekran_ayarla()
    
    print("\n" + "="*50)
    print("Cloudflare Turnstile Atlatma Aracı")
    print(f"Sistem: {platform.system()} {platform.release()}")
    print("="*50)
    
    # Paralel mod
    if args.parallel:
        print(f"[*] 🚀 Paralel mod: Her grupta {args.batch} tarayıcı")
        print(f"[*] Zaman aşımı: {args.timeout} saniye | Maksimum {args.retries} grup")
        print(f"[*] Canlılık kontrolü: {'Evet' if args.check_proxy else 'Hayır'}")
        
        sonuc = paralel_atlat(
            url=args.url,
            proxy_dosyasi=args.proxy_file,
            grup_boyutu=args.batch,
            zaman_asimi=args.timeout,
            bekleme_suresi=args.wait,
            cookie_kaydet=not args.no_save,
            proxy_kontrol=args.check_proxy,
            max_grup=args.retries
        )
    # Sıralı proxy rotasyonu modu
    elif args.rotate:
        print(f"[*] Sıralı rotasyon modu | Maksimum {args.retries} proxy deneme")
        print(f"[*] Zaman aşımı: {args.timeout} saniye | Canlılık kontrolü: {'Evet' if args.check_proxy else 'Hayır'}")
        
        sonuc = proxy_rotasyonuyla_cloudflare_atlat(
            url=args.url,
            proxy_dosyasi=args.proxy_file,
            bekleme_suresi=args.wait,
            cookie_kaydet=not args.no_save,
            zaman_asimi=args.timeout,
            max_deneme=args.retries,
            proxy_kontrol=args.check_proxy
        )
    else:
        # Tek proxy/doğrudan bağlantı modu
        proxy = args.proxy
        if proxy:
            print(f"[*] Belirtilen proxy kullanılıyor: {proxy}")
        else:
            print("[*] Doğrudan bağlantı modu (proxy yok)")
        
        print(f"[*] Zaman aşımı: {args.timeout} saniye")
        
        sonuc = cloudflare_atlat(
            url=args.url,
            proxy=proxy,
            bekleme_suresi=args.wait,
            cookie_kaydet=not args.no_save,
            zaman_asimi=args.timeout,
            max_deneme=1
        )
    
    print("\n" + "-"*50)
    if sonuc["basarili"]:
        print(f"✅ Başarılı | Cookie: {len(sonuc['cookieler'])} adet")
        if sonuc["cf_clearance"]:
            print(f"📍 cf_clearance: {sonuc['cf_clearance'][:50]}...")
    else:
        print(f"❌ Başarısız: {sonuc['hata']}")
    print("-"*50 + "\n")
    
    # Linux sanal ekranı temizle
    if display:
        display.stop()
