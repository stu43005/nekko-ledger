"""Fetch hololive BOOTH listing pages and item JSONs into a cache dir.

Usage: python3 -I tools/fetch_booth.py <raw_dir>

Writes <raw_dir>/list/p<N>.html, <raw_dir>/ids.txt and
<raw_dir>/items/<id>.json (from https://booth.pm/ja/items/<id>.json).
Sequential requests with a small delay; cached responses are never refetched
(delete the cache dir, or list/ + ids.txt, to pick up new items).
"""
import os
import re
import sys
import time
import urllib.request

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
DELAY = 0.5


def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, encoding='utf-8') as f:
            return f.read()
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode('utf-8')
            break
        except Exception as e:  # noqa: BLE001 - retry transient errors
            print('retry', url, e, file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    else:
        raise RuntimeError(f'failed {url}')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(body)
    time.sleep(DELAY)
    return body


def main():
    raw = sys.argv[1]
    os.makedirs(os.path.join(raw, 'list'), exist_ok=True)
    os.makedirs(os.path.join(raw, 'items'), exist_ok=True)
    first = get('https://hololive.booth.pm/items?page=1', os.path.join(raw, 'list', 'p1.html'))
    last = max([int(x) for x in re.findall(r'/items\?page=(\d+)', first)] or [1])
    ids = []
    for n in range(1, last + 1):
        html = get(f'https://hololive.booth.pm/items?page={n}', os.path.join(raw, 'list', f'p{n}.html'))
        page_ids = re.findall(r'/items/(\d+)', html)
        ids.extend(page_ids)
        print('page', n, len(set(page_ids)))
    ids = list(dict.fromkeys(ids))
    print('unique items', len(ids))
    with open(os.path.join(raw, 'ids.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(ids) + '\n')
    for i, iid in enumerate(ids, 1):
        get(f'https://booth.pm/ja/items/{iid}.json', os.path.join(raw, 'items', f'{iid}.json'))
        if i % 50 == 0:
            print('items', i)
    print('done', len(ids))


if __name__ == '__main__':
    main()
