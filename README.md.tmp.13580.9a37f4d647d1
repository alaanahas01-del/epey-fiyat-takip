# epey fiyat takibi

12 telefon modelinin (iPhone + Samsung) epey.com en ucuz sifir teklifini guvenilir
satici beyaz listesinden ceker, degisenleri Telegram'a bildirir. State: `epey-state.json`.

**Asil motor: 7/24 fisteki Android telefon** (Termux + cron, kurulum: `setup-phone.sh`).
`pc_sweep.py` 5 dk'da bir calisir (duz HTTP - ev IP'sinde Cloudflare challenge yok),
her taramada `heartbeat.txt` guncellenip push'lanir; commit damgasi cihazi soyler
("phone ..."/"pc ..."). Ayni script Windows PC'de de calisir (Gorev Zamanlayici
gorevi "epey-fiyat-takip", su an DEVRE DISI - tek yazar telefonda; telefon
emekli olursa `Enable-ScheduledTask epey-fiyat-takip` ile PC devralir).
PC'deki canli klon: `C:\Users\Asus\epey-fiyat-takip` (elle duzenleme yapma).

**Bekci + yedek: GitHub Actions** (`check.yml`, ~30 dk'da bir). Kalp atisi 40 dk'dan
eskiyse Telegram'a "PC sustu" uyarisi atar ve Playwright ile yedek taramayi dener
(CF, Actions IP'lerini cogunlukla blokluyor - gecerse veri surer, gecmezse sadece uyari).
PC donunce "geri geldi" mesaji gelir.

Gecmis: bot once tamamen Actions'ta kendini zincirleyen dongu olarak kosuyordu;
CF 2026-07-06/07'de Actions IP'lerini ~24 saat kesintisiz bloklayinca motor PC'ye tasindi.
