# PC tarafi tek tarama: Gorev Zamanlayici bunu 5 dk'da bir pythonw ile calistirir.
# Akis: kilit al -> git pull (yerel state kazanir) -> scraper (PLAIN=1, duz HTTP)
# -> heartbeat.txt yaz -> commit+push (bekci workflow bu kalp atisini izler).
# Push basarisiz olsa da (internet yok vb.) yerel state dogru kalir, commit birikir,
# ilk firsatta topluca gider. Beklenmedik hatalar sweep.log'a yazilir; Telegram
# alarmi PC-genelinde bekcinin isi (kalp atisi kesilince), buradan spam atilmaz.
import os, socket, subprocess, sys, time

REPO = os.path.dirname(os.path.abspath(__file__))
# Ayni dosya telefonda da (Termux) calisir; creationflags Windows'a ozel.
NOWIN = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW: pythonw altinda git konsolu acilmasin
WHO = "pc" if os.name == "nt" else "phone"  # commit damgasi: hangi cihaz canli, gecmisten okunur


def g(*args):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                       text=True, creationflags=NOWIN)
    if r.returncode:
        print("git %s: %s" % (" ".join(args), (r.stderr or r.stdout).strip()))
    return r.returncode == 0


def main():
    # ayni anda ikinci tarama calismasin (soket kilidi: proses olunce kendiliginden birakilir)
    lock = socket.socket()
    try:
        lock.bind(("127.0.0.1", 47391))
    except OSError:
        print("zaten calisiyor, cikiliyor")
        return

    os.chdir(REPO)  # Zamanlayici System32'den baslatir; scraper goreli yol kullaniyor
    os.environ["PLAIN"] = "1"
    g("fetch", "origin")
    g("pull", "--rebase", "-X", "theirs", "origin", "master") or g("rebase", "--abort")

    import scraper
    try:
        scraper.main()
    except SystemExit:
        pass  # CF blogu: scraper mesajini atti, kalp atisi yine de yazilir
    except Exception as e:
        print("scraper hata: %r" % e)

    with open(os.path.join(REPO, "heartbeat.txt"), "w") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + "\n")
    g("add", "-A")
    g("commit", "-m", WHO + " " + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    g("push", "origin", "master")


if __name__ == "__main__":
    # pythonw'de stdout yok; tum ciktiyi loga akit (1 MB'i asinca sifirla)
    log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweep.log")
    mode = "w" if os.path.exists(log) and os.path.getsize(log) > 1_000_000 else "a"
    with open(log, mode, encoding="utf-8", errors="replace") as f:
        sys.stdout = sys.stderr = f
        print("--- sweep " + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        try:
            main()
        except Exception as e:
            print("olumcul: %r" % e)
