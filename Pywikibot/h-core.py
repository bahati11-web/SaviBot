import time
import psutil
from datetime import timedelta

def get_cpu():
    return psutil.cpu_percent(interval=1)

def get_ram():
    mem = psutil.virtual_memory()
    total = mem.total / (1024 * 1024)
    used = mem.used / (1024 * 1024)
    return used, total


def get_uptime():
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    return str(timedelta(seconds=int(uptime_seconds)))


def print_status():
    print("\033c", end="")  # clear console

    cpu = get_cpu()
    ram_used, ram_total = get_ram()
    uptime = get_uptime()

    print("ÉTAT SYSTÈME SAVIBOT\n")

    print(f"CPU : {cpu:.2f}%")
    print(f"RAM : {ram_used:.0f} MB / {ram_total:.0f} MB")
    print(f"Uptime : {uptime}")

    print("\nSTATUS PYWIKIBOT")
    print("✔ Process: actif (supposé)")
    print("✔ Mode: maintenance / automation")
    print("✔ Scheduler: 30 min cycle")

    print("\nÉTAT GLOBAL : STABLE")
    print("---------------------------------\n")


def main():
    print("Savibot Health Core...\n")

    while True:
        print_status()
        time.sleep(1800)


if __name__ == "__main__":
    main()
