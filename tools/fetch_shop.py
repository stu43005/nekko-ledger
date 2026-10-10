"""Download Shopify collection dumps from the hololive production official shop.

Usage: python3 -I tools/fetch_shop.py <raw_dir> <collection_handle> [<collection_handle> ...]

Writes <raw_dir>/<handle>_p<N>.json for N = 1, 2, ... until an empty page
(the empty page is kept too, so a finished download is recognisable).
Existing non-empty files are reused; delete them to refetch.
"""
import json
import os
import sys
import time
import urllib.request

SHOP = 'https://shop.hololivepro.com'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
DELAY = 1.0
MAX_PAGES = 50


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode('utf-8')
        except Exception as e:  # noqa: BLE001 - retry transient errors
            print('retry', url, e, file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f'failed {url}')


def fetch_collection(raw_dir, handle):
    os.makedirs(raw_dir, exist_ok=True)
    total = 0
    for n in range(1, MAX_PAGES + 1):
        path = os.path.join(raw_dir, f'{handle}_p{n}.json')
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, encoding='utf-8') as f:
                body = f.read()
        else:
            body = get(f'{SHOP}/collections/{handle}/products.json?limit=250&page={n}')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(body)
            time.sleep(DELAY)
        count = len(json.loads(body)['products'])
        print(handle, 'page', n, count)
        total += count
        if count == 0:
            break
    print(handle, 'total', total)
    return total


def main():
    raw_dir = sys.argv[1]
    for handle in sys.argv[2:]:
        fetch_collection(raw_dir, handle)


if __name__ == '__main__':
    main()
