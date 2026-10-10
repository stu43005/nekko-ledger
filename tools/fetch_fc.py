"""Fetch an official fan-club online store (e.g. HOSHIMACHI SUISEI ONLINE STORE) into a cache dir.

Usage: python3 -I tools/fetch_fc.py <raw_dir> <store_base_url>
  e.g. python3 -I tools/fetch_fc.py "$RAW/fc" https://hoshimachi-suisei-fc.jp/s/hs

Writes <raw_dir>/list/p<N>.json (GET <base>/api/list/item_list?rw=48&page=N,
N = 0, 1, ... until pages.total; the store's own front-end sends the same
rw / page parameters) and <raw_dir>/detail/<item_code>.html (the public
HTML detail page <base>/item/detail/<item_code>, which carries the variation
names / prices, the image list and the description with the sale period).
The JSON details endpoint needs a member session, so it is not used.
Finally every list image is HEAD-checked (no Referer) and its status and
Last-Modified header are kept in <raw_dir>/images.json.
Sequential requests with a small delay; cached responses are never refetched
(delete list/ to pick up new items, or a detail file to refresh it).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
DELAY = 0.5
PER_PAGE = 48  # LIST.ITEMS_PER_PAGE in the store's app-config
MAX_PAGES = 50


def get(url, path, accept):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, encoding='utf-8') as f:
            return f.read()
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': accept, 'Accept-Language': 'ja'})
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
    raw, base = sys.argv[1], sys.argv[2].rstrip('/')
    os.makedirs(os.path.join(raw, 'list'), exist_ok=True)
    os.makedirs(os.path.join(raw, 'detail'), exist_ok=True)
    items = []
    for n in range(MAX_PAGES):
        body = get(f'{base}/api/list/item_list?rw={PER_PAGE}&page={n}',
                   os.path.join(raw, 'list', f'p{n}.json'), 'application/json')
        data = json.loads(body)
        items.extend(data['list'])
        total = int(data['pages']['total'])
        print('page', n, len(data['list']), 'of', total, 'count', data['count'])
        if n + 1 >= total:
            break
    codes = list(dict.fromkeys(x['item_code'] for x in items))
    print('unique items', len(codes))
    for code in codes:
        get(f'{base}/item/detail/{code}', os.path.join(raw, 'detail', f'{code}.html'), 'text/html')
    heads = head_images(raw, [x['item_img_url'] for x in items])
    bad = [u for u, h in heads.items() if h['status'] != 200]
    print('images', len(heads), 'not 200:', len(bad), *bad)
    print('done', len(codes))


def head_images(raw, urls):
    """HEAD every list image (no Referer) and cache status + Last-Modified in
    <raw_dir>/images.json. Last-Modified is the fallback sale-start date for
    items whose description has no sale period (images go live with the sale)."""
    path = os.path.join(raw, 'images.json')
    heads = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            heads = json.load(f)
    for url in dict.fromkeys(urls):
        if url in heads and heads[url]['status'] == 200:
            continue
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                heads[url] = {'status': r.status, 'last_modified': r.headers.get('Last-Modified', ''),
                              'content_type': r.headers.get('Content-Type', '')}
        except urllib.error.HTTPError as e:
            heads[url] = {'status': e.code, 'last_modified': '', 'content_type': ''}
        time.sleep(DELAY)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(heads, f, ensure_ascii=False, indent=1, sort_keys=True)
    return heads


if __name__ == '__main__':
    main()
