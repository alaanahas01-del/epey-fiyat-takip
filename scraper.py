# epey.com'daki 14 iPhone modelinin en ucuz SIFIR teklifini (Outlet/2.el ve
# PTT AVM / Cicieksepeti / Idefix haric) gercek tarayiciyla (Playwright) ceker,
# epey-state.json ile karsilastirip degisenleri Telegram'a bildirir, state'i yazar.
# DUMP=1 ise tek seferlik tam listeyi gonderir (test/ilk calisma icin).
import json, os, re, sys, urllib.request, urllib.parse
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

MODELS = [
    ("iPhone 15", "apple-iphone-15"),
    ("iPhone 15 Plus", "apple-iphone-15-plus"),
    ("iPhone 15 Pro", "apple-iphone-15-pro"),
    ("iPhone 15 Pro Max", "apple-iphone-15-pro-max"),
    ("iPhone 16", "apple-iphone-16"),
    ("iPhone 16 Plus", "apple-iphone-16-plus"),
    ("iPhone 16 Pro", "apple-iphone-16-pro"),
    ("iPhone 16 Pro Max", "apple-iphone-16-pro-max"),
    ("iPhone 16e", "apple-iphone-16e"),
    ("iPhone 17", "apple-iphone-17"),
    ("iPhone 17 Pro", "apple-iphone-17-pro"),
    ("iPhone 17 Pro Max", "apple-iphone-17-pro-max"),
    ("iPhone Air", "apple-iphone-air"),
    ("iPhone 17e", "apple-iphone-17e"),
]
EXCLUDE = {"pttavm-com", "ciceksepeti-com", "idefix-com"}
STATE = "epey-state.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

OFFER = re.compile(r'<a[^>]+class="git[^"]*".*?</a>', re.S)
SLUG = re.compile(r'resim\.epey\.com/site/([a-z0-9-]+)\.')
NAME = re.compile(r'title="(.+?) Apple iPhone')
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
        p = int(price.group(1)) / 100  # urun_fiyat_sort kurus cinsinden
        if best is None or p < best[0]:
            nm, lk, st = NAME.search(b), LINK.search(b), SATICI.search(b)
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


def fetch_all():
    """Tek tarayici baglami: ilk sayfada CF cozulur, cf_clearance cookie'si
    sonraki 13 sayfada tekrar kullanilir."""
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
    pages = fetch_all()

    if all("urun_fiyat_sort" not in h for h in pages.values()):
        tg("Cloudflare epey.com'u engelledi (GitHub Actions IP) - fiyat cekilemedi")
        print("BLOCKED by Cloudflare")
        sys.exit(1)

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
