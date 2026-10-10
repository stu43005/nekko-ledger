"""Validate a dataset dir (goods / voice / updates / todo CSVs).

Usage:
  python3 -I tools/validate.py <data_dir> [--before DIR] [--site-parsers]

Checks: headers, column counts, unique (code, index), cover row (index 0)
first with empty name/price, contiguous indexes, consistent project columns,
numeric prices, Y/M/D dates, goods newest-first / voice oldest-first,
project URL and image URL formats (same conventions as data/).
--before DIR      every line of DIR/*.csv must survive byte-identical and in order
--site-parsers    also parse goods/voice with js/app.js and js/voice.js via node
                  (run from the repo root; needs node on PATH)
"""
import argparse
import collections
import csv
import datetime
import json
import os
import re
import subprocess
import sys

GOODS_HEADER = ['goods project code', 'goods project name', 'project type', 'date',
                'goods official website', 'x link', 'goods index', 'goods name', 'goods type',
                'price', 'goods picture', 'note', 'project note', 'oversea']
VOICE_HEADER = ['project code', 'project name', 'date', 'voice name', 'price',
                'project website link', 'picture link']
PROJECT_URL_RE = re.compile(r'^https://(shop\.hololivepro\.com/products/[^/?#\s]+|hololive\.booth\.pm/items/\d+'
                            r'|[a-z0-9-]+-fc\.jp/s/[a-z]+/item/detail/[A-Za-z0-9-]+)$')
SHOP_IMG_RE = re.compile(r'^https://shop\.hololivepro\.com/cdn/shop/(files|products)/[^?#\s]+$')
BOOTH_IMG_RE = re.compile(r'^https://booth\.pximg\.net/[0-9a-f-]+/i/(\d+)/[^?#\s/]+$')
# Fan-club store (fc_* projects): item detail pages and /images/... on the same host.
FC_URL_RE = re.compile(r'^(https://[a-z0-9-]+-fc\.jp)/s/[a-z]+/item/detail/[A-Za-z0-9-]+$')
FC_IMG_RE = re.compile(r'^(https://[a-z0-9-]+-fc\.jp)/images/\d+/[0-9a-f]+/[0-9a-f]+(-\d+)?\.(jpg|jpeg|png|gif|webp)$')
GOODS_TYPES = ('', 'acrylic stand', 'badge', 'plushie', 'keychain')
PROJECT_TYPES = ('', 'anniversary', 'birthday')

NODE_SNIPPET = r"""
const fs = require('fs');
const out = {};
for (const [mod, file] of [['./js/app.js', 'goods.csv'], ['./js/voice.js', 'voice.csv']]) {
  try {
    global.window = { SITE: {} };
    const a = require(mod);
    const rows = a.parseCSV(fs.readFileSync(process.argv[1] + '/' + file, 'utf8'));
    const projects = a.buildProjects(rows);
    const list = Array.isArray(projects) ? projects : Object.values(projects || {});
    out[file] = { ok: true, rows: rows.length, projects: list.length };
  } catch (e) {
    out[file] = { ok: false, error: String(e && e.stack || e).split('\n').slice(0, 3).join(' | ') };
  }
}
console.log(JSON.stringify(out));
"""


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.reader(f))


def raw_lines(path):
    with open(path, 'rb') as f:
        return f.read().split(b'\r\n')


def parse_date(s):
    m = re.fullmatch(r'(\d{4})/(\d{1,2})/(\d{1,2})', s)
    if not m:
        raise ValueError(f'bad date {s!r}')
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def img_ok(url, project_url):
    if project_url.startswith('https://hololive.booth.pm/items/'):
        m = BOOTH_IMG_RE.match(url)
        return bool(m) and project_url.endswith('/' + m.group(1))
    fc = FC_URL_RE.match(project_url)
    if fc:
        m = FC_IMG_RE.match(url)
        return bool(m) and m.group(1) == fc.group(1)
    return bool(SHOP_IMG_RE.match(url))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data_dir')
    ap.add_argument('--before')
    ap.add_argument('--site-parsers', action='store_true')
    args = ap.parse_args()
    data = args.data_dir
    errors = []

    def check(cond, msg):
        if not cond:
            errors.append(msg)

    def safe_date(s, where):
        try:
            return parse_date(s)
        except ValueError as e:
            errors.append(f'{where}: {e}')
            return None

    if args.before:
        for name in ('goods.csv', 'voice.csv', 'updates.csv', 'todo.csv'):
            old, new = raw_lines(os.path.join(args.before, name)), raw_lines(os.path.join(data, name))
            it = iter(new)
            missing = [ln for ln in old if not any(ln == x for x in it)]
            check(not missing, f'{name}: {len(missing)} original lines missing/reordered')

    # ---- goods ----
    g = read(os.path.join(data, 'goods.csv'))
    check(g[0] == GOODS_HEADER, f'goods header mismatch {g[0]}')
    H = {h: i for i, h in enumerate(GOODS_HEADER)}
    seen, projects, order = set(), collections.defaultdict(list), []
    for n, r in enumerate(g[1:], 2):
        if len(r) != len(GOODS_HEADER):
            errors.append(f'goods line {n}: {len(r)} cols')
            continue
        code, idx = r[H['goods project code']], r[H['goods index']]
        check((code, idx) not in seen, f'goods dup key {code}#{idx}')
        seen.add((code, idx))
        if code not in projects:
            order.append(code)
        projects[code].append(r)
        safe_date(r[H['date']], f'goods line {n}')
        check(r[H['project type']] in PROJECT_TYPES, f'goods line {n} project type')
        check(r[H['goods type']] in GOODS_TYPES, f'goods line {n} goods type')
        url = r[H['goods official website']]
        check(PROJECT_URL_RE.match(url) is not None, f'goods line {n} url {url!r}')
        check(img_ok(r[H['goods picture']], url), f'goods line {n} picture {r[H["goods picture"]]!r}')
        if url.startswith('https://shop.hololivepro.com/'):
            check(url.endswith('/' + code), f'goods line {n} code/url mismatch')
        elif FC_URL_RE.match(url):
            check(code.startswith('fc_'), f'goods line {n} fan-club code {code!r} without fc_ prefix')
        else:
            check(code == 'booth_' + url.rsplit('/', 1)[1], f'goods line {n} booth code/url mismatch')
        if idx == '0':
            check(r[H['goods name']] == '' and r[H['price']] == '', f'goods line {n} cover row has name/price')
        else:
            check(re.fullmatch(r'[1-9]\d*', r[H['price']]) is not None, f'goods line {n} price {r[H["price"]]!r}')
            check(r[H['goods name']].strip() != '', f'goods line {n} empty goods name')
    check(len(order) == len(set(order)), 'goods project codes not contiguous')
    prev = None
    for code in order:
        rows = projects[code]
        idxs = [r[H['goods index']] for r in rows]
        check(idxs == [str(i) for i in range(len(rows))], f'{code}: indexes {idxs}')
        check(len(rows) >= 2, f'{code}: project without items')
        for col in ('goods project name', 'project type', 'date', 'goods official website'):
            if col == 'goods official website' and code.startswith('fc_'):
                # Fan-club items keep their own detail page; the cover row
                # (project link) is the first item's page.
                urls = [r[H[col]] for r in rows]
                check(len(urls) < 2 or urls[0] == urls[1], f'{code}: cover URL is not the first item URL')
                check(len({FC_URL_RE.match(u).group(1) for u in urls if FC_URL_RE.match(u)}) == 1,
                      f'{code}: mixed fan-club hosts')
                continue
            check(len({r[H[col]] for r in rows}) == 1, f'{code}: inconsistent {col}')
        d = safe_date(rows[0][H['date']], code)
        if d:
            check(prev is None or d <= prev, f'{code}: not sorted newest first')
            prev = d
    n_items = sum(len(v) - 1 for v in projects.values())
    n_booth = sum(1 for c in order if c.startswith('booth_'))
    n_fc = sum(1 for c in order if c.startswith('fc_'))
    print(f'goods: {len(projects)} projects ({n_booth} BOOTH, {n_fc} fan-club), {n_items} items, {len(g) - 1} rows')

    # ---- voice ----
    v = read(os.path.join(data, 'voice.csv'))
    check(v[0] == VOICE_HEADER, f'voice header mismatch {v[0]}')
    V = {h: i for i, h in enumerate(VOICE_HEADER)}
    keys, prev = set(), None
    for n, r in enumerate(v[1:], 2):
        if len(r) != len(VOICE_HEADER):
            errors.append(f'voice line {n}: cols')
            continue
        key = r[V['project code']] + '#' + re.sub(r'\s+', '', r[V['voice name']]).replace('（', '(').replace('）', ')')
        check(key not in keys, f'voice dup key {key}')
        keys.add(key)
        d = safe_date(r[V['date']], f'voice line {n}')
        if d:
            check(prev is None or d >= prev, f'voice line {n}: not oldest first')
            prev = d
        check(re.fullmatch(r'[1-9]\d*', r[V['price']]) is not None, f'voice line {n} price')
        url = r[V['project website link']]
        check(PROJECT_URL_RE.match(url) is not None, f'voice line {n} url')
        check(img_ok(r[V['picture link']], url), f'voice line {n} picture {r[V["picture link"]]!r}')
    print(f'voice: {len({r[0] for r in v[1:]})} projects, {len(v) - 1} rows')

    # ---- updates / todo ----
    u = read(os.path.join(data, 'updates.csv'))
    check(u[0] == ['date', 'note'], 'updates header')
    for n, r in enumerate(u[1:], 2):
        check(len(r) == 2 and r[1] != '', f'updates line {n}')
        safe_date(r[0], f'updates line {n}')
    t = read(os.path.join(data, 'todo.csv'))
    check(t[0] == ['TODO', 'Website'], 'todo header')
    for n, r in enumerate(t[1:], 2):
        check(len(r) == 2 and r[0] != '', f'todo line {n}')
        check(len(r) == 2 and PROJECT_URL_RE.match(r[1]) is not None, f'todo line {n} url')
    print(f'updates: {len(u) - 1} rows, todo: {len(t) - 1} rows')

    if args.site_parsers:
        res = subprocess.run(['node', '-e', NODE_SNIPPET, os.path.abspath(data)],
                             capture_output=True, text=True, check=False)
        if res.returncode != 0:
            errors.append(f'node failed: {res.stderr.strip()[:500]}')
        else:
            out = json.loads(res.stdout.strip().splitlines()[-1])
            for f, info in out.items():
                print(f'site parser {f}: {info}')
                check(info.get('ok'), f'site parser failed for {f}: {info.get("error")}')

    if errors:
        print('ERRORS:')
        for e in errors[:100]:
            print('  ', e)
        sys.exit(1)
    print('OK')


if __name__ == '__main__':
    main()
