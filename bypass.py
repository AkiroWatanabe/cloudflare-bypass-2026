# ============================================================
# Cloudflare Turnstile Atlatma Aracı - Tek Tarayıcı Sürümü (Önerilen)
# SeleniumBase UC Mode tabanlı
# Mac / Windows / Linux destekler
# ============================================================

import os
import sys
import time
import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from seleniumbase import SB


def linux_mi() -> bool:
    """Linux sistemi olup olmadığını kontrol eder"""
    return platform.system().lower() == "linux"


def ekran_ayarla():
    """Linux sanal ekranını ayarlar"""
    if linux_mi() and not os.environ.get("DISPLAY"):
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=False, size=(1920, 1080))
            display.start()
            os.environ["DISPLAY"] = display.new_display_var
            print("[*] Linux: Sanal ekran başlatıldı (Xvfb)")
            return display
        except ImportError:
            print("[!] Lütfen kurun: pip install pyvirtualdisplay")
            print("[!] Ve: apt-get install -y xvfb")
            sys.exit(1)
        except Exception as e:
            print(f"[!] Sanal ekran başlatılamadı: {e}")
            sys.exit(1)
    return None


def cloudflare_atlat(
    url: str,
    proxy: Optional[str] = None,
    zaman_asimi: float = 60.0,
    cookie_kaydet: bool = True
) -> Dict[str, Any]:
    """
    Cloudflare doğrulamasını atlatır ve Cookie alır (tek tarayıcı modu)
    
    Parametreler:
        url: Hedef web sitesi URL'si
        proxy: Proxy adresi (isteğe bağlı, format: http://host:port)
        zaman_asimi: Zaman aşımı süresi (saniye)
        cookie_kaydet: Cookie'leri dosyaya kaydet
    
    Döndürür:
        {
            "basarili": bool,
            "cookieler": dict,
            "cf_clearance": str,
            "user_agent": str,
            "hata": str
        }
    """
    sonuc = {
        "basarili": False,
        "cookieler": {},
        "cf_clearance": None,
        "user_agent": None,
        "hata": None
    }
    
    try:
        print(f"[*] Hedef: {url}")
        if proxy:
            print(f"[*] Proxy: {proxy}")
        
        # Tarayıcıyı başlat
        with SB(uc=True, test=True, locale="en", proxy=proxy) as sb:
            print("[*] Tarayıcı başlatıldı, sayfa yükleniyor...")
            
            # Sayfayı aç
            sb.uc_open_with_reconnect(url, reconnect_time=5.0)
            time.sleep(2)
            
            # Cloudflare doğrulamasını tespit et
            sayfa_kaynak = sb.get_page_source().lower()
            cf_belirtecleri = ["turnstile", "challenges.cloudflare", "just a moment", "verify you are human"]
            
            if any(x in sayfa_kaynak for x in cf_belirtecleri):
                print("[*] Cloudflare doğrulaması tespit edildi, işleniyor...")
                try:
                    sb.uc_gui_click_captcha()
                    time.sleep(3)
                except Exception as e:
                    print(f"[!] Captcha tıklama hatası: {e}")
            
            # Cookie'leri al
            cookie_listesi = sb.get_cookies()
            sonuc["cookieler"] = {c["name"]: c["value"] for c in cookie_listesi}
            sonuc["cf_clearance"] = sonuc["cookieler"].get("cf_clearance")
            sonuc["user_agent"] = sb.execute_script("return navigator.userAgent")
            
            if sonuc["cf_clearance"]:
                sonuc["basarili"] = True
                print(f"[+] cf_clearance başarıyla alındı!")
                
                # Cookie'leri kaydet
                if cookie_kaydet:
                    kayit_dizini = Path("output/cookies")
                    kayit_dizini.mkdir(parents=True, exist_ok=True)
                    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # JSON formatı
                    with open(kayit_dizini / f"cookies_{zaman_damgasi}.json", "w", encoding="utf-8") as f:
                        json.dump({
                            "url": url,
                            "cookieler": sonuc["cookieler"],
                            "user_agent": sonuc["user_agent"],
                            "zaman_damgasi": zaman_damgasi
                        }, f, indent=2, ensure_ascii=False)
                    
                    # Netscape formatı
                    with open(kayit_dizini / f"cookies_{zaman_damgasi}.txt", "w") as f:
                        f.write("# Netscape HTTP Cookie File\n")
                        for c in cookie_listesi:
                            domain = c.get("domain", "")
                            secure = "TRUE" if c.get("secure") else "FALSE"
                            expiry = int(c.get("expiry", 0))
                            f.write(f"{domain}\tTRUE\t{c.get('path', '/')}\t{secure}\t{expiry}\t{c['name']}\t{c['value']}\n")
                    
                    print(f"[+] Cookie kaydedildi: {kayit_dizini}")
            else:
                sonuc["hata"] = "cf_clearance alınamadı"
                print(f"[-] {sonuc['hata']}")
                
    except Exception as e:
        sonuc["hata"] = str(e)
        print(f"[-] Hata: {e}")
    
    return sonuc


# ============================================================
# Komut Satırı Girişi
# ============================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Cloudflare Turnstile Atlatma Aracı (Tek Tarayıcı Modu)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python bypass.py https://ornek.com
  python bypass.py https://ornek.com -p http://127.0.0.1:7890
        """
    )
    parser.add_argument("url", help="Hedef URL")
    parser.add_argument("-p", "--proxy", help="Proxy adresi")
    parser.add_argument("-t", "--timeout", type=float, default=60.0, help="Zaman aşımı (varsayılan: 60 saniye)")
    parser.add_argument("--no-save", action="store_true", help="Cookie kaydetme")
    args = parser.parse_args()
    
    # Linux sanal ekranı
    display = ekran_ayarla()
    
    print("\n" + "="*50)
    print("Cloudflare Turnstile Atlatma Aracı")
    print(f"Sistem: {platform.system()} {platform.release()}")
    print("="*50 + "\n")
    
    # Atlatmayı gerçekleştir
    sonuc = cloudflare_atlat(
        url=args.url,
        proxy=args.proxy,
        zaman_asimi=args.timeout,
        cookie_kaydet=not args.no_save
    )
    
    # Sonucu yazdır
    print("\n" + "-"*50)
    if sonuc["basarili"]:
        print(f"[OK] Başarılı | Cookie sayısı: {len(sonuc['cookieler'])}")
        print(f"[OK] cf_clearance: {sonuc['cf_clearance'][:50]}...")
    else:
        print(f"[BAŞARISIZ] Hata: {sonuc['hata']}")
    print("-"*50 + "\n")
    
    # Temizlik
    if display:
        display.stop()
