"""Append new official-shop projects to a published dataset (append-only).

Usage:
  python3 -I tools/sync_shop.py <profile> --shop-raw DIR [--data DIR] [--date Y/M/D] [--summary FILE]
  python3 -I tools/sync_shop.py <profile> --shop-raw DIR --init-seen

A product is new when its handle is neither listed in tools/shop_seen/<profile>.txt
nor already a project code in <data>/goods.csv or voice.csv. New products go
through the same rules as build_dataset.py (Builder.build_shop) and only their
rows are inserted; existing rows are never touched, so saved records
("<code>#<index>") keep pointing at the same items. The shop never adds
variants to an existing product page, so existing projects are not revisited.

After a run every handle of the collection is added to the seen list, so
products that yield no rows (excluded / nothing of the talent) and todo rows a
maintainer already removed are not picked up again.

--init-seen   only write the seen list from the given dumps (use the dumps the
              published data was built from), leaving the data untouched
"""
import argparse
import csv
import datetime
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('build_dataset', os.path.join(HERE, 'build_dataset.py'))
bd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bd)

SEEN_DIR = os.path.join(HERE, 'shop_seen')


def read_csv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.reader(f))


def seen_path(profile):
    return os.path.join(SEEN_DIR, profile + '.txt')


def read_seen(profile):
    path = seen_path(profile)
    if not os.path.exists(path):
        sys.exit(f'{path} is missing: create it with --init-seen first')
    with open(path, encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip()}


def write_seen(profile, handles):
    os.makedirs(SEEN_DIR, exist_ok=True)
    with open(seen_path(profile), 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(h + '\n' for h in sorted(handles))


def merge_voice(v_old, new_rows):
    """Insert new voice rows (oldest first) after the existing rows of the same or an earlier date."""
    di = v_old[0].index('date')
    out, pending = [v_old[0]], list(new_rows)
    for r in v_old[1:]:
        while pending and bd.dkey(pending[0][di]) < bd.dkey(r[di]):
            out.append(pending.pop(0))
        out.append(r)
    return out + pending


def today_jst():
    d = datetime.datetime.now(bd.JST).date()
    return f'{d.year}/{d.month}/{d.day}'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('profile', choices=sorted(bd.PROFILES))
    ap.add_argument('--shop-raw', required=True, help='dir with <collection>_p<N>.json dumps (see fetch_shop.py)')
    ap.add_argument('--data', help="dataset dir to update (default: the profile's data_dir)")
    ap.add_argument('--date', help='updates.csv date (default: today in JST)')
    ap.add_argument('--summary', help='append a Markdown summary of the additions to this file')
    ap.add_argument('--init-seen', action='store_true', help='only write the seen list from the dumps')
    args = ap.parse_args()

    profile = bd.PROFILES[args.profile]
    b = bd.Builder(profile)
    handles = {p['handle'] for p in bd.load_collection(args.shop_raw, b.collection)}
    if not handles:
        # An empty dump means the download failed; never treat it as "nothing new".
        sys.exit(f'no products for collection {b.collection} in {args.shop_raw}')
    if args.init_seen:
        write_seen(args.profile, handles)
        print('seen', args.profile, len(handles))
        return

    data = args.data or profile['data_dir']
    paths = {k: os.path.join(data, k + '.csv') for k in ('goods', 'voice', 'todo', 'updates')}
    old = {k: read_csv(p) for k, p in paths.items()}
    seen = read_seen(args.profile)
    codes = {r[0] for r in old['goods'][1:]} | {r[0] for r in old['voice'][1:]}
    new = handles - seen - codes

    shop = b.build_shop(args.shop_raw)
    new_goods = [gp for gp in shop['projects'] if gp['code'] in new]  # newest first
    new_voice = [r for r in shop['voice_dicts'] if r['project code'] in new]  # oldest first
    new_todo = [r for r in shop['todo'][1:] if r[1].rsplit('/', 1)[1] in new]

    out = dict(old)
    out['goods'] = bd.merge_goods(old['goods'], new_goods)
    out['voice'] = merge_voice(old['voice'], [[r[k] for k in bd.VOICE_HEADER] for r in new_voice])
    out['todo'] = old['todo'][:1] + new_todo + old['todo'][1:]  # todo sheet is newest first
    names = [gp['name'] for gp in new_goods]
    names += [n for n in dict.fromkeys(r['project name'] for r in new_voice)]
    if names:
        out['updates'] = old['updates'] + [
            [args.date or today_jst(), f'官方商店新增 {len(names)} 個企劃：' + '、'.join(names)]]

    for k, rows in out.items():
        if rows != old[k]:
            bd.write_csv(paths[k], rows)
    if handles - seen:
        write_seen(args.profile, seen | handles)

    print('sync', args.profile, f'new_handles={len(new)}', f'goods_projects={len(new_goods)}',
          f'goods_items={sum(len(gp["items"]) for gp in new_goods)}',
          f'voice_rows={len(new_voice)}', f'todo={len(new_todo)}')
    if args.summary and (names or new_todo):
        lines = [f'### {profile["short_name"]}（`{data}`）', '']
        for gp in new_goods:
            lines.append(f'- 周邊 {gp["date"]} [{gp["name"]}]({gp["url"]})（{len(gp["items"])} 件）')
            lines += [f'  - {n}（{p}）' for n, p, _ in gp['items']]
        for r in new_voice:
            lines.append(f'- Voice {r["date"]} [{r["project name"]}]({r["project website link"]})：{r["voice name"]}')
        for t, url in new_todo:
            lines.append(f'- 待確認：[{t}]({url})')
        with open(args.summary, 'a', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n\n')


if __name__ == '__main__':
    main()
