# epey fiyat takibi

12 telefon modelinin (iPhone + Samsung) epey.com en ucuz sifir teklifini guvenilir
satici beyaz listesinden ceker, degisenleri Telegram'a bildirir. State: `epey-state.json`.

**Asil motor: ev PC'si.** `pc_sweep.py` Gorev Zamanlayici ile 5 dk'da bir calisir
(duz HTTP - ev IP'sinde Cloudflare challenge yok), her taramada `heartbeat.txt`
guncellenip push'lanir. Bu klasorun canli kopyasi PC'de: `C:\Users\Asus\epey-fiyat-takip`
(elle duzenleme yapma; degisiklikler bot commit'leriyle karisir).

**Bekci + yedek: GitHub Actions** (`check.yml`, ~30 dk'da bir). Kalp atisi 40 dk'dan
eskiyse Telegram'a "PC sustu" uyarisi atar ve Playwright ile yedek taramayi dener
(CF, Actions IP'lerini cogunlukla blokluyor - gecerse veri surer, gecmezse sadece uyari).
PC donunce "geri geldi" mesaji gelir.

Gecmis: bot once tamamen Actions'ta kendini zincirleyen dongu olarak kosuyordu;
CF 2026-07-06/07'de Actions IP'lerini ~24 saat kesintisiz bloklayinca motor PC'ye tasindi.
