#!/data/data/com.termux/files/usr/bin/sh
# epey bot - Termux telefon kurulumu (7/24 birincil motor).
# Kullanim (Termux icinde):
#   pkg install -y curl
#   curl -fLo setup-phone.sh https://raw.githubusercontent.com/alaanahas01-del/epey-fiyat-takip/master/setup-phone.sh
#   bash setup-phone.sh
# (curl | sh YAPMA: script soru soruyor, stdin'in klavye olmasi lazim.)
# On kosullar: Termux + Termux:Boot F-Droid'den kurulu, Termux:Boot bir kez acilmis,
# Android pil ayarinda Termux "kisitlamasiz". Telefon fiste ve Wi-Fi'da kalacak.
set -e

echo "== paketler =="
yes | pkg update || true
yes | pkg install python git gh cronie termux-api >/dev/null || pkg install -y python git gh cronie

echo "== github girisi =="
if ! gh auth status >/dev/null 2>&1; then
  echo "Tarayici acilacak / kod gosterilecek; GitHub hesabinla onayla."
  gh auth login -h github.com -p https -w
fi
gh auth setup-git

echo "== repo =="
cd ~
[ -d epey-fiyat-takip ] || gh repo clone alaanahas01-del/epey-fiyat-takip
cd epey-fiyat-takip
git pull --rebase origin master || true
git config user.name "epey-bot (phone)"
git config user.email "internetsatis23@gmail.com"

echo "== telegram =="
if [ ! -f ~/.epey_env ]; then
  printf "TELEGRAM_BOT_TOKEN degerini yapistir: "; read -r tok
  printf "TELEGRAM_CHAT_ID degerini yapistir: "; read -r chat
  cat > ~/.epey_env <<EOF
export PATH=/data/data/com.termux/files/usr/bin:\$PATH
export TELEGRAM_BOT_TOKEN=$tok
export TELEGRAM_CHAT_ID=$chat
EOF
  chmod 600 ~/.epey_env
fi

echo "== zamanlama (cron her 5 dk) =="
( crontab -l 2>/dev/null | grep -v pc_sweep.py; \
  echo "*/5 * * * * . ~/.epey_env && cd ~/epey-fiyat-takip && python pc_sweep.py" ) | crontab -

echo "== acilista otomatik baslama (Termux:Boot) =="
mkdir -p ~/.termux/boot
{
  echo '#!/data/data/com.termux/files/usr/bin/sh'
  echo 'termux-wake-lock'
  echo 'pgrep crond >/dev/null || crond'
} > ~/.termux/boot/epey
chmod +x ~/.termux/boot/epey
# Termux elle acilirsa da crond'u kaldir (kazara kapatilmisti senaryosu)
grep -q 'pgrep crond' ~/.bashrc 2>/dev/null || \
  echo 'pgrep crond >/dev/null || { termux-wake-lock; crond; }' >> ~/.bashrc

echo "== simdi baslat =="
termux-wake-lock
pgrep crond >/dev/null || crond
. ~/.epey_env && python pc_sweep.py   # ilk tarama hemen; sonrasi 5 dk'da bir cron
echo ""
echo "KURULUM TAMAM. Bot bu telefonda calisiyor; commit damgasi: 'phone ...'"
echo "Telefonu fiste ve Wi-Fi'da birak. Termux bildirimi kalsin, uygulamayi Exit'leme."
