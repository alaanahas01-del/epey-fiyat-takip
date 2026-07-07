# epey.com'daki 12 telefon modelinin (iPhone + Samsung) en ucuz SIFIR teklifini
# SADECE guvenilir satici beyaz listesinden (SELLERS + DIRECT; Outlet/2.el ve
# PTT AVM / Ciceksepeti / Idefix her durumda haric) ceker, epey-state.json ile
# karsilastirip degisenleri Telegram'a bildirir, state'i yazar.
# Once duz HTTP (ev IP'sinde CF challenge yok, 12 sayfa ~15 sn); hepsi bos gelirse
# ve PLAIN=1 degilse Playwright'a duser (Actions yedegi icin). PC'de PLAIN=1:
# playwright kurulu degil, kurulmasi da gerekmiyor (import lazy).
# DUMP=1 ise tek seferlik tam listeyi gonderir (test/ilk calisma icin).
import json, os, re, sys, time, urllib.request, urllib.parse
from urllib.parse import unquote

MODELS = [
    ("iPhone 17 Pro Max 256", "apple-iphone-17-pro-max"),
    ("iPhone 17 Pro 256", "apple-iphone-17-pro"),
    ("iPhone 17 256", "apple-iphone-17"),
    ("iPhone 16 128", "apple-iphone-16"),
    ("iPhone 15 128", "apple-iphone-15"),
    ("Galaxy S26 Ultra 256", "samsung-galaxy-s26-ultra"),
    ("Galaxy S26 256", "samsung-galaxy-s26"),
    ("Galaxy S25 FE 256", "samsung-galaxy-s25-fe"),
    ("Galaxy A57 256", "samsung-galaxy-a57-5g-256gb"),
    ("Galaxy A57 128", "samsung-galaxy-a57"),
    ("Galaxy A37 256", "samsung-galaxy-a37"),
    ("Galaxy A37 128", "samsung-galaxy-a37-5g-128gb"),
]
EXCLUDE = {"pttavm-com", "ciceksepeti-com", "idefix-com"}

# Guvenilir satici beyaz listesi: pazaryeri tekliflerinde satici adi bunlardan
# biri olmali (norm() ile karsilastirilir; epey'de gorulen gercek yazimlar).
SELLERS = {
    "MediaMarkt",                          # Trendyol/HB; n11 "mediamarkt", Pazarama "MEDIAMARKT" norm ile ayni
    "VATAN BİLGİSAYAR",
    "Teknosa",
    "Gürgençler Apple Yetkili Satıcı", "Gürgençler Apple", "Gürgençler Apple Premium Partner",
    "Troy Apple Yetkili Satıcı", "Troy Apple", "TroyApple",  # TroyApple = n11 yazimi
    "BittiBitiyor",
    "Trendyol", "Hepsiburada", "n11", "Pazarama", "Amazon.com.tr",
    "Turkcell Satış A.Ş.",                 # dikkat: "Turkcell Emre İletişim" gibi bayiler ESLESMEZ
    "Xiaomi Resmi Mağazası", "Xiaomi Türkiye",
}
# Saticisiz (dogrudan) satis yapan magazalarin epey slug'lari.
DIRECT = {"mediamarkt-com-tr", "vatanbilgisayar-com", "teknosa-com",
          "a101-com-tr", "troyestore-com"}


def norm(s):
    """Turkce buyuk/kucuk harf guvenli karsilastirma: I/İ/ı/i hepsi 'i' olur."""
    combining_dot = chr(0x0307)  # I-with-dot lower() kalintisi
    return " ".join(s.split()).lower().replace(combining_dot, "").replace("ı", "i")


ALLOWED = {norm(s) for s in SELLERS}
STATE = "epey-state.json"
BLOCKFLAG = "cf-blocked.flag"  # varligi = onceki calisma CF'ye takildi (tg mesaji tekrarlanmaz)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

OFFER = re.compile(r'<a[^>]+class="git[^"]*".*?</a>', re.S)
SLUG = re.compile(r'resim\.epey\.com/site/([a-z0-9-]+)\.')
NAME = re.compile(r'title="(.+?) (?:Apple iPhone|Samsung Galaxy)')
PRICE = re.compile(r'urun_fiyat_sort[^>]*>(\d+)<')
LINK = re.compile(r'data-link="([^"]+)"')
SATICI = re.compile(r'Satıcı:</strong>\s*([^|<]+)')  # pazaryeri alt saticisi, her satirda olmayabilir


def cheapest(html):
    best = None
    for m in OFFER.finditer(html):
        b = m.group(0)
        if 'class="outlet"' in b:
            continue
        slug, price = SLUG.search(b), PRICE.search(b)
        if not slug or not price or slug.group(1) in EXCLUDE:
            continue
        st = SATICI.search(b)
        if st:  # pazaryeri teklifi: satici beyaz listede olmali
            if norm(st.group(1)) not in ALLOWED:
                continue
        elif slug.group(1) not in DIRECT:  # saticisiz teklif: dogrudan satan magaza olmali
            continue
        p = int(price.group(1)) / 100  # urun_fiyat_sort kurus cinsinden
        if best is None or p < best[0]:
            nm, lk = NAME.search(b), LINK.search(b)
            who = nm.group(1) if nm else slug.group(1)
            if st and st.group(1).strip().lower() != who.lower():
                who += " (satıcı: %s)" % st.group(1).strip()
            best = (p, who, unquote(lk.group(1)) if lk else "")
    return best


def tl(p):
    s = f"{float(p):,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return s[:-3] if s.endswith(",00") else s


def tg(text):
    tok = os.environ["TELEGRAM_BOT_TOKEN"]
    chat = os.environ["TELEGRAM_CHAT_ID"]
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % tok,
                           data, timeout=30).read()


def blocked(pages):
    return all("urun_fiyat_sort" not in h for h in pages.values())


def fetch_plain():
    """Duz HTTP: CF challenge gormeyen IP'lerde (ev) yeterli, tarayici gerekmez."""
    out = {}
    for name, slug in MODELS:
        url = "https://www.epey.com/akilli-telefonlar/%s.html" % slug
        html = ""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except Exception as e:
            print("%s: fetch hata %s" % (name, e))
        out[name] = html
        time.sleep(1)  # ponytail: ev IP'sini CF'ye sevdirmeye devam; kaldirma
    return out


def fetch_all():
    """Tek tarayici baglami: ilk sayfada CF cozulur, cf_clearance cookie'si
    kalan sayfalarda tekrar kullanilir."""
    from playwright.sync_api import sync_playwright  # lazy: PC'de kurulu degil
    out = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
        ctx = browser.new_context(user_agent=UA, locale="tr-TR",
                                  timezone_id="Europe/Istanbul",
                                  viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        for name, slug in MODELS:
            url = "https://www.epey.com/akilli-telefonlar/%s.html" % slug
            html = ""
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:  # CF challenge cozulunce gercek icerik (fiyat span'i) gelir
                    page.wait_for_selector("span.urun_fiyat_sort", timeout=25000)
                except Exception:
                    pass
                html = page.content()
            except Exception as e:
                print("%s: goto hata %s" % (name, e))
            out[name] = html
        browser.close()
    return out


def main():
    dump = os.environ.get("DUMP") == "1"
    try:
        old = json.load(open(STATE, encoding="utf-8"))
    except Exception:
        old = {}
    pages = fetch_plain()
    if blocked(pages) and os.environ.get("PLAIN") != "1":
        pages = fetch_all()  # datacenter IP: duz HTTP CF'ye takildi, tarayici dene

    if blocked(pages):
        if not os.path.exists(BLOCKFLAG):  # sadece ilk blokta mesaj at, retry'larda sus
            open(BLOCKFLAG, "w").write("1")
            kim = "ev IP" if os.environ.get("PLAIN") == "1" else "GitHub Actions IP"
            tg("Cloudflare epey.com'u engelledi (%s) - duzelene kadar denemeye devam" % kim)
        print("BLOCKED by Cloudflare")
        sys.exit(1)
    if os.path.exists(BLOCKFLAG):
        os.remove(BLOCKFLAG)
        tg("epey erisimi geri geldi - takip devam ediyor")

    new = dict(old)
    lines = []
    for name, _ in MODELS:
        h = pages.get(name, "")
        off = cheapest(h) if h else None
        if not off:
            lines.append("%s: %s" % (name, "uygun teklif yok" if "urun_fiyat_sort" in h else "cekilemedi"))
            continue  # basarisiz cekimde eski kayit korunur
        p, seller, link = off
        prev = (old.get(name) or {}).get("fiyat")
        new[name] = {"fiyat": p, "satici": seller, "link": link}
        lines.append("%s: %s TL - %s - %s" % (name, tl(p), seller, link))
        if dump:
            continue
        if prev is None:
            tg("%s: %s TL - %s - %s (yeni takip)" % (name, tl(p), seller, link))
        elif abs(float(prev) - p) >= 0.005:
            tg("%s: %s TL (önceki %s TL) - %s - %s" % (name, tl(p), tl(prev), seller, link))

    if dump:
        tg("epey en ucuz (sıfır):\n" + "\n".join(lines))
    json.dump(new, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("OK\n" + "\n".join(lines))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
