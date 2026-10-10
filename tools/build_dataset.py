"""Build one talent's dataset (goods / voice / updates / todo CSVs).

Sources:
  1. hololive production official shop: Shopify products.json dumps
     (<shop_raw>/<collection>_p<N>.json, see fetch_shop.py)
  2. hololive BOOTH: item JSON cache (<booth_raw>/ids.txt + items/<id>.json,
     see fetch_booth.py). BOOTH-only products are merged in; products that
     duplicate an official-shop project are skipped.
  3. Official fan-club store (only for profiles with fc_store, e.g. suisei):
     list JSON + public detail HTML cache (<fc_raw>/list/p<N>.json,
     detail/<code>.html, images.json, see fetch_fc.py). Items are grouped
     into one project per sales campaign and appended after shop + BOOTH;
     campaigns that duplicate an existing project are skipped.

Usage:
  python3 -I tools/build_dataset.py <profile> --shop-raw DIR --booth-raw DIR [--fc-raw DIR] --out DIR [--report]

<profile> is a key of tools/profiles.py (e.g. nene, suisei). --out is required
on purpose so a rebuild never overwrites committed data by accident.
"""
import argparse
import collections
import csv
import datetime
import email.utils
import glob
import html
import importlib.util
import json
import os
import re
import unicodedata

_spec = importlib.util.spec_from_file_location(
    'profiles', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profiles.py'))
_profiles = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_profiles)
PROFILES = _profiles.PROFILES

SHOP = 'https://shop.hololivepro.com'
BOOTH_ITEM = 'https://hololive.booth.pm/items/'

# ---------------------------------------------------------------- shared rules
OTHER_GROUP_RE = re.compile(r'期生|期\+|期＋|ゲーマーズ|holoX|ReGLOSS|FLOW GLOW|\bID\b|\bEN\b|DEV_IS|STAGE\d|stage\d|インドネシア|English')
SIZE_RE = re.compile(r'(\s*[/／]?\s*(XS|S|M|L|XL|XXL|2XL|3XL|4XL|F)(サイズ)?)(?=\)|）|$)')
SET_RE = re.compile(r'フルセット|セット[AＡBＢ]?$|セット$|^「.*」.*セット|BOX$')
EXCLUDE_PRODUCT_RE = re.compile(r'デジタルメッセージボード|【ホロプラス】|壁紙（PC用）')
VOICE_PRODUCT_RE = re.compile(r'ボイス|ASMR')
NOT_VOICE_RE = re.compile(r'カレンダーブロマイド')
MEDIA_RE = re.compile(r'^(Blu-ray|CD)\b|Blu-ray|アルバム|CALENDAR|カレンダー\d{4}')
SIZE_OPT_RE = re.compile(r'^(XS|S|M|L|XL|XXL|2XL|3XL)サイズ$|^サイズ$')
GENERIC_CAT_RE = re.compile(r'^(グッズ|セット|フルセット|ボイス|単品販売|NEW|ホロライブ)$|期生|ゲーマーズ|holoX|STAGE|stage|DAY\d|vol\.|サイズ')
# Talents that never sold on the official shop but may appear on old BOOTH items.
BOOTH_EXTRA_TALENTS = {'魔乃アロエ'}
# BOOTH variation labels that are only a colour.
COLOR_ONLY_RE = re.compile(r'^(ブラック|ホワイト|ネイビー|グレー|ピンク|レッド|ブルー|ベージュ|カーキ|グリーン|イエロー|'
                           r'パープル|オレンジ|black|white|navy|gray|grey|pink)$', re.IGNORECASE)
BOOTH_EXCLUDE_ITEM_RE = re.compile(r'デジタルメッセージボード|【ホロプラス】|壁紙')
# pixivFACTORY-style BOOTH variation labels: "パーカー - M - ブラック".
FACTORY_SIZE_RE = re.compile(r' - (?:XS|S|M|L|XL|XXL|2XL|3XL|4XL) - ')
# Fan-club store: leading labels such as 【FC会員限定】 / 【二次販売/在庫販売】 / (※完売次第販売終了).
FC_LABEL_RE = re.compile(r'^\s*(?:【[^】]*】|[(（]※[^)）]*[)）])')
FC_RESALE_RE = re.compile(r'^【(?:二次販売|2次販売|２次販売|再販)[^】]*】')
# "【受注期間】 一次受注：2026/6/25(木) 22:00 ～ ..." -> first date/time of the section.
FC_PERIOD_RE = re.compile(r'【(?:受注|販売)期間】(.*?)(?=【|$)', re.DOTALL)
FC_DT_RE = re.compile(r'(\d{4})/(\d{1,2})/(\d{1,2})\s*[(（][^)）]*[)）]\s*(\d{1,2}):(\d{2})')
JST = datetime.timezone(datetime.timedelta(hours=9))

GOODS_HEADER = ['goods project code', 'goods project name', 'project type', 'date',
                'goods official website', 'x link', 'goods index', 'goods name', 'goods type',
                'price', 'goods picture', 'note', 'project note', 'oversea']
VOICE_HEADER = ['project code', 'project name', 'date', 'voice name', 'price',
                'project website link', 'picture link']
UPDATES_HEADER = ['date', 'note']
TODO_HEADER = ['TODO', 'Website']


def load_collection(raw_dir, coll):
    out = []
    for f in sorted(glob.glob(os.path.join(raw_dir, coll + '_p*.json'))):
        with open(f, encoding='utf-8') as fh:
            out.extend(json.load(fh)['products'])
    return out


def shop_img(src):
    """cdn.shopify.com/s/files/1/0529/2641/5045/files/x.png?v=1 -> shop.hololivepro.com/cdn/shop/files/x.png"""
    if not src:
        return ''
    src = src.split('?', 1)[0]
    m = re.match(r'https?://cdn\.shopify\.com/s/files/1/0529/2641/5045/(files|products)/(.+)$', src)
    if m:
        return f'{SHOP}/cdn/shop/{m.group(1)}/{m.group(2)}'
    return src


def ymd(iso):
    """'2024-03-08T12:00:00+09:00' -> '2024/3/8' (the shop/BOOTH timestamps are JST)."""
    y, m, d = iso[:10].split('-')
    return f'{int(y)}/{int(m)}/{int(d)}'


def pub_date(p):
    return ymd(p.get('published_at') or p.get('created_at') or '')


def dkey(s):
    y, m, d = (int(x) for x in s.split('/'))
    return (y, m, d)


def clean_title(t):
    return re.sub(r'\s+', ' ', t.replace('\n', ' ')).strip()


def last_opt(v):
    parts = [x for x in (v.get('option1'), v.get('option2'), v.get('option3')) if x and x != 'Default Title']
    return parts[-1].strip() if parts else v['title'].strip()


def talents_of(p):
    return {t[7:].replace('【卒業生】', '') for t in p['tags'] if t.startswith('Talent_')}


def goods_type(name, title):
    s = name
    if (re.search(r'ぬいぐるみ|パペット|マスコット|hololive friends', s) or re.search(r'hololive friends', title)) \
            and not re.search(r'帽子|キャップ', s):
        return 'plushie'
    if re.search(r'キーホルダー|アクリルチャーム', s):
        return 'keychain'
    if re.search(r'缶バッジ|ネームバッジ', s):
        return 'badge'
    if re.search(r'アクリルスタンド|ゆらゆらアクリル', s) and not re.search(r'パネル|ペンライト|ジオラマ|スマホ|カード', s):
        return 'acrylic stand'
    if re.search(r'hololive closet', title):
        return 'acrylic stand'
    return ''


def strip_size(name):
    n = SIZE_RE.sub('', name)
    n = re.sub(r'\(\s*([^()/]+)\s*\)', r'(\1)', n)
    return n.strip()


def voice_name(n):
    n = n.replace('（', ' (').replace('）', ')')
    return re.sub(r'\s+', ' ', n).strip()


def base_title(title):
    t = clean_title(title)
    t = re.sub(r'^(【[^】]*】\s*)+', '', t)
    return re.sub(r'\s*先行通販$', '', t)


def norm(s):
    """Normalisation used for BOOTH duplicate detection only."""
    s = unicodedata.normalize('NFKC', s or '').lower()
    s = re.sub(r'【[^】]*】', '', s)
    s = re.sub(r'先行通販|受注販売|予約販売|\(\d次[^)]*\)', '', s)
    s = s.replace('一周年', '1周年').replace('二周年', '2周年').replace('三周年', '3周年')
    s = re.sub(r'[\s・「」『』"\'“”!！?？~～〜\-‐ー_/／()（）\[\]]', '', s)
    return s


def project_type(title, cls):
    if '誕生日' in title:
        return 'birthday'
    if re.search(r'周年|Anniversary', title, re.IGNORECASE) and cls in ('solo', 'unit'):
        return 'anniversary'
    return ''


def goods_rows(gp):
    """Items are (name, price, img) or (name, price, img, item_url, note); an
    item URL that differs from the project URL shows up as a per-item link."""
    base = [gp['code'], gp['name'], gp['type'], gp['date'], gp['url'], '']
    rows = [base + ['0', '', '', '', gp['cover'], '', '', '']]
    for i, it in enumerate(gp['items'], 1):
        n, price, img = it[:3]
        url, note = it[3:5] if len(it) > 3 else (gp['url'], '')
        rows.append(base[:4] + [url, ''] + [str(i), n, goods_type(n, gp['name']), str(price), img, note, '', ''])
    return rows


def existing_index(g_old, v_old):
    """Existing goods / voice rows -> ({code: {'name', 'date', 'kind', 'items'}}, {norm name: [codes]})
    for duplicate detection of BOOTH / fan-club items."""
    GH = {h: i for i, h in enumerate(g_old[0])}
    VH = {h: i for i, h in enumerate(v_old[0])}
    existing = {}  # code -> {'name', 'date', 'items': set((norm name, price))}
    for r in g_old[1:]:
        e = existing.setdefault(r[GH['goods project code']], {
            'name': r[GH['goods project name']], 'date': r[GH['date']], 'kind': 'goods', 'items': set()})
        if r[GH['goods index']] != '0':
            e['items'].add((norm(r[GH['goods name']]), r[GH['price']]))
    for r in v_old[1:]:
        e = existing.setdefault(r[VH['project code']], {
            'name': r[VH['project name']], 'date': r[VH['date']], 'kind': 'voice', 'items': set()})
        e['items'].add((norm(r[VH['voice name']]), r[VH['price']]))
    by_norm_name = {}
    for code, e in existing.items():
        by_norm_name.setdefault(norm(e['name']), []).append(code)
    return existing, by_norm_name


def find_duplicate(existing, by_norm_name, title, date, cand_items):
    """(code, reason) of an existing project that the candidate duplicates, else None."""
    match = None
    for code in by_norm_name.get(norm(title), []):
        match = (code, 'same project name')
    if not match:
        for code, e in existing.items():
            common = cand_items & e['items']
            names_common = {a for a, _ in cand_items} & {a for a, _ in e['items']}
            if e['date'] == date and names_common:
                match = (code, f'same date + {len(names_common)} same item names')
                break
            if cand_items and len(common) >= max(2, (len(cand_items) + 1) // 2):
                match = (code, f'{len(common)}/{len(cand_items)} same (item, price)')
                break
    return match


def merge_goods(g_old, new_goods):
    """Insert new projects (already sorted newest first) into the goods rows;
    a new project goes after the existing projects of the same date."""
    GH = {h: i for i, h in enumerate(g_old[0])}
    blocks, cur = [], None
    for r in g_old[1:]:
        if cur is None or cur[0] != r[GH['goods project code']]:
            cur = (r[GH['goods project code']], dkey(r[GH['date']]), [])
            blocks.append(cur)
        cur[2].append(r)
    g_new = [g_old[0]]
    pending = list(new_goods)
    for code, d, rows in blocks:
        while pending and dkey(pending[0]['date']) > d:
            g_new.extend(goods_rows(pending.pop(0)))
        g_new.extend(rows)
    for gp in pending:
        g_new.extend(goods_rows(gp))
    return g_new


def fc_clean_name(name):
    """Drop leading campaign labels: 【二次販売/在庫販売】(※完売次第販売終了)X -> X."""
    prev = None
    while prev != name:
        prev, name = name, FC_LABEL_RE.sub('', name, count=1)
    return name.strip()


def fc_detail(page):
    """Public item detail HTML -> variations, members-only flag and sale start (ISO, JST) if stated."""
    variations = []
    for m in re.finditer(r'<component-item-detail-variation\b([^>]*)>', page):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        variations.append({'name': html.unescape(attrs.get('name', '')).strip(),
                           'price': int(attrs['price']), 'sale_label': attrs.get('sale-label', '')})
    text = html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<br\s*/?>', '\n', page)))
    start = None
    period = FC_PERIOD_RE.search(text)
    m = FC_DT_RE.search(period.group(1)) if period else None
    if m:
        y, mo, d, h, mi = (int(x) for x in m.groups())
        start = f'{y:04d}-{mo:02d}-{d:02d}T{h:02d}:{mi:02d}:00+09:00'
    # Members-only items replace the cart / variation block with a login form.
    return {'variations': variations, 'members_only': 'name="form_login1"' in page, 'start': start}


def http_date_jst(s):
    """'Sun, 30 Aug 2026 11:00:08 GMT' -> '2026-08-30T20:00:08+09:00'."""
    return email.utils.parsedate_to_datetime(s).astimezone(JST).isoformat()


def collapse_factory_sizes(picked):
    """Drop the size segment of "<kind> - <size> - <colour>" labels, but only
    when all sizes of that label share one price (else the size is kept so
    rows with different prices stay distinguishable)."""
    prices = {}
    for _, name, price, _ in picked:
        if FACTORY_SIZE_RE.search(name):
            prices.setdefault(FACTORY_SIZE_RE.sub(' - ', name), set()).add(price)
    out = []
    for v, name, price, kind in picked:
        short = FACTORY_SIZE_RE.sub(' - ', name)
        out.append((v, short if len(prices.get(short, ())) == 1 else name, price, kind))
    return out


def todo_text(title, picked, skipped, is_voice, short):
    ex = '、'.join(dict.fromkeys(skipped[:4]))
    more = f' 等 {len(skipped)} 項' if len(skipped) > 4 else ''
    what = '共通ボイス' if is_voice else '共通商品'
    state = f'已收錄{short}專屬項目，' if picked else ''
    return f'{title}：{state}{what}未收錄（{ex}{more}），是否含{short}需人工確認'


class Builder:
    def __init__(self, profile):
        self.full = profile['full_name']
        self.short = profile['short_name']
        self.name_re = profile['name_re']
        self.booth_tag_re = profile['booth_tag_re']
        self.own_group_re = profile['own_group_re']
        self.extra_other = profile['extra_other_names']
        self.solo_hints = profile['solo_handle_hints']
        self.collection = profile['collection']
        self.name_collections = profile['name_collections']
        self.updates = profile['updates']
        self.fc = profile.get('fc_store')
        self.talent_only_re = re.compile(re.escape(self.full) + r'|ホロライブ|\d期生|友人Ａ|秘密結社|holoX|[+＋&＆『』]|ver\.|\s')

    # ------------------------------------------------------------ shared logic
    def variant_kind(self, title, other_names):
        """self / other / own_group / other_group / generic"""
        if self.name_re.search(title):
            return 'self'
        if any(n and n in title for n in other_names):
            return 'other'
        if self.own_group_re.search(title):
            return 'own_group'
        if OTHER_GROUP_RE.search(title):
            return 'other_group'
        return 'generic'

    def full_prefixed(self, last, base, cls):
        """Variant label starting with the full name in a multi-talent product."""
        suffix = last[len(self.full):].strip()
        if suffix and suffix in base:
            return base if self.full in base else f'{base} {self.full}'
        return f'{base} {last}'

    # ---------------------------------------------------------- official shop
    def shop_classify(self, p):
        ts = talents_of(p)
        if ts == {self.full} or (not ts and any(h in p['handle'] for h in self.solo_hints)):
            return 'solo'
        if self.full in ts and len(ts) <= 5:
            return 'unit'
        return 'group'

    def shop_item_name(self, v, p, cls):
        parts = [x.strip() for x in (v.get('option1'), v.get('option2'), v.get('option3'))
                 if x and x != 'Default Title' and not SIZE_OPT_RE.match(x.strip())]
        parts = [re.sub(r'^(【[^】]*】\s*)+', '', strip_size(x)) for x in parts] or [v['title']]
        last = parts[-1]
        base = base_title(p['title'])
        if not self.talent_only_re.sub('', last):
            # Variant label is only the talent / generation name -> add product context.
            if len(parts) > 1 and not GENERIC_CAT_RE.search(parts[0]):
                return f'{parts[0]} / {last}'
            return base if last in base else f'{base} {last}'
        if cls != 'solo' and re.match(r'^Vol\.\d+ ', last):
            # Bushiroad collections: "Vol.29 hololive SUPER EXPO 2022『<name>』" lacks the item kind.
            return f'{base} {last}'
        if cls != 'solo' and last.startswith(self.full):
            return self.full_prefixed(last, base, cls)
        return last

    def build_shop(self, shop_raw):
        prods = load_collection(shop_raw, self.collection)
        all_talents = set()
        for coll in self.name_collections:
            for p in load_collection(shop_raw, coll):
                all_talents |= talents_of(p)
        other_names = sorted((all_talents - {self.full}) | set(self.extra_other))

        goods_projects, voice_rows, todo, log = [], [], [], []
        for p in prods:
            title = clean_title(p['title'])
            url = f"{SHOP}/products/{p['handle']}"
            cls = self.shop_classify(p)
            if EXCLUDE_PRODUCT_RE.search(title):
                log.append(('excluded-digital', p['handle'], title))
                if cls in ('solo', 'unit') and 'デジタルメッセージボード' in title:
                    todo.append([f'{title}（數位留言板，附特典ボイス；未收錄）', url])
                continue
            is_voice = bool(VOICE_PRODUCT_RE.search(title)) and not NOT_VOICE_RE.search(title)
            picked, skipped_generic = [], []
            for v in p['variants']:
                price = round(float(v['price']))
                vt = v['title']
                name = last_opt(v)
                if price <= 0 or '【旧価格】' in vt:
                    continue
                kind = self.variant_kind(vt, other_names)
                if kind in ('other', 'other_group'):
                    continue
                is_set = bool(SET_RE.search(name)) or (v.get('option1') or '').strip() in ('セット', 'フルセット')
                if is_voice and is_set:
                    continue
                if kind == 'generic' and cls == 'group':
                    skipped_generic.append(name)
                    continue
                picked.append((v, name, price, kind))

            if cls == 'group' and not picked and skipped_generic:
                # Multi-talent single media item (Blu-ray / CD) -> include it.
                media = [v for v in p['variants'] if float(v['price']) > 0 and MEDIA_RE.search(v['title'])]
                if media and len(skipped_generic) <= 2 and not is_voice:
                    picked = [(v, last_opt(v), round(float(v['price'])), 'generic') for v in media]
                    skipped_generic = []
            if skipped_generic:
                todo.append([todo_text(title, picked, skipped_generic, is_voice, self.short), url])
            if not picked:
                log.append(('no-own-items', p['handle'], title))
                continue

            cover = shop_img(p['images'][0]['src']) if p['images'] else ''
            date = pub_date(p)
            if is_voice:
                names = [voice_name(n) for _, n, _, _ in picked]
                for v, name, price, kind in picked:
                    vn = voice_name(name)
                    if len(picked) == 1 and cls == 'solo':
                        vn = voice_name(name) if self.full in name else title
                    if names.count(vn) > 1:
                        # Same label under different categories (e.g. 【ゆくホロ】/【くるホロ】).
                        cat = (v.get('option1') or '').strip()
                        m = re.match(r'^【[^】]*】', cat)
                        vn = (m.group(0) if m else cat + ' ') + vn
                    voice_rows.append({'project code': p['handle'], 'project name': title, 'date': date,
                                       'voice name': vn, 'price': str(price),
                                       'project website link': url, 'picture link': cover,
                                       '_pub': p['published_at']})
                continue

            items, seen = [], set()
            for v, name, price, kind in picked:
                n = strip_size(self.shop_item_name(v, p, cls))
                if (n, price) in seen:
                    continue
                seen.add((n, price))
                img = shop_img((v.get('featured_image') or {}).get('src')) or cover
                items.append((n, price, img))
            goods_projects.append({'code': p['handle'], 'name': title, 'type': project_type(title, cls),
                                   'date': date, 'url': url, 'cover': cover, 'items': items,
                                   'pub': p['published_at'], 'cls': cls})

        # Newest project first; stable tie-break by code.
        goods_projects.sort(key=lambda x: x['code'])
        goods_projects.sort(key=lambda x: x['pub'], reverse=True)
        g = [GOODS_HEADER]
        for gp in goods_projects:
            g.extend(goods_rows(gp))
        voice_rows.sort(key=lambda r: r['_pub'])  # voice sheet is oldest first
        v = [VOICE_HEADER] + [[r[k] for k in VOICE_HEADER] for r in voice_rows]
        t = [TODO_HEADER] + todo
        stats = {'goods_projects': len(goods_projects),
                 'goods_items': sum(len(x['items']) for x in goods_projects),
                 'voice_rows': len(voice_rows),
                 'voice_projects': len({r['project code'] for r in voice_rows}),
                 'todo': len(todo)}
        return {'goods': g, 'voice': v, 'todo': t, 'log': log, 'stats': stats,
                'projects': goods_projects, 'voice_dicts': voice_rows}

    # ----------------------------------------------------------------- BOOTH
    def booth_related(self, item):
        if any(self.booth_tag_re.match(t['name'].strip()) for t in item['tags']):
            return 'tag'
        if self.name_re.search(item['name']):
            return 'name'
        if any(self.name_re.search(v['name'] or '') for v in item['variations']):
            return 'variation'
        return ''

    def booth_classify(self, item, known):
        tags = {t['name'].strip() for t in item['tags']}
        ts = {t for t in tags if t in known}
        if any(self.booth_tag_re.match(t['name'].strip()) for t in item['tags']):
            ts.add(self.full)
        if ts == {self.full} or (not (ts - {self.full}) and self.name_re.search(item['name'])):
            return 'solo', ts
        if self.full in ts and len(ts) <= 5:
            return 'unit', ts
        return 'group', ts

    def booth_item_name(self, vname, title, cls):
        """BOOTH variation label -> goods name (mirrors shop_item_name for single-option variants)."""
        last = re.sub(r'^(【[^】]*】\s*)+', '', strip_size(vname.strip()))
        last = re.sub(r'^(XS|S|M|L|XL|XXL|2XL|3XL)サイズ\s*', '', last)  # leading size label
        last = re.sub(r'[\s・/／]+$', '', last).strip()
        base = base_title(title)
        if not last or COLOR_ONLY_RE.match(last):
            # Variation label is only a colour (sizes already stripped) -> keep product context.
            return f'{base} {last}'.strip()
        if not self.talent_only_re.sub('', last):
            return base if last in base else f'{base} {last}'
        if cls != 'solo' and last.startswith(self.full):
            return self.full_prefixed(last, base, cls)
        return last

    def merge_booth(self, booth_raw, shop_raw, shop):
        known = set(BOOTH_EXTRA_TALENTS)
        for coll in self.name_collections:
            for p in load_collection(shop_raw, coll):
                known |= talents_of(p)
        other_names = sorted((known - {self.full}) | set(self.extra_other))

        with open(os.path.join(booth_raw, 'ids.txt'), encoding='utf-8') as fh:
            ids = [x for x in fh.read().split() if x]
        items = []
        for i in ids:
            with open(os.path.join(booth_raw, 'items', f'{i}.json'), encoding='utf-8') as fh:
                items.append(json.load(fh))

        # ---- existing official-shop rows (for de-duplication) ----
        g_old, v_old = shop['goods'], shop['voice']
        VH = {h: i for i, h in enumerate(v_old[0])}
        existing, by_norm_name = existing_index(g_old, v_old)

        new_goods, new_voice, todo, dups, log = [], [], [], [], []
        related = 0
        for it in items:
            if not self.booth_related(it):
                continue
            related += 1
            title = clean_title(it['name'])
            url = BOOTH_ITEM + str(it['id'])
            cls, ts = self.booth_classify(it, known)
            if BOOTH_EXCLUDE_ITEM_RE.search(title):
                log.append(('excluded', it['id'], title))
                continue
            is_voice = bool(VOICE_PRODUCT_RE.search(title)) and not NOT_VOICE_RE.search(title)
            picked, skipped_generic = [], []
            for v in it['variations']:
                price = int(v['price'] or 0)
                name = (v['name'] or '').strip() or title
                if price <= 0:
                    continue
                kind = self.variant_kind(name, other_names)
                if kind in ('other', 'other_group'):
                    continue
                if is_voice and SET_RE.search(name):
                    continue
                if kind == 'generic' and cls == 'group':
                    skipped_generic.append(name)
                    continue
                picked.append((v, name, price, kind))
            picked = collapse_factory_sizes(picked)
            if skipped_generic:
                todo.append(['[BOOTH] ' + todo_text(title, picked, skipped_generic, is_voice, self.short), url])
            if not picked:
                log.append(('no-own-items', it['id'], title, cls, sorted(ts)))
                continue

            date = ymd(it['published_at'])
            cover = it['images'][0]['original'] if it['images'] else ''

            # ---- duplicate detection against the official-shop rows ----
            if is_voice:
                cand_items = {(norm(voice_name(n)), str(p)) for _, n, p, _ in picked}
            else:
                cand_items = {(norm(strip_size(self.booth_item_name(n, title, cls))), str(p)) for _, n, p, _ in picked}
            match = find_duplicate(existing, by_norm_name, title, date, cand_items)
            if match:
                dups.append((it['id'], date, title, match[0], existing[match[0]]['name'],
                             existing[match[0]]['date'], match[1]))
                continue

            code = f'booth_{it["id"]}'
            if is_voice:
                names = [voice_name(n) for _, n, _, _ in picked]
                for v, name, price, kind in picked:
                    vn = voice_name(name)
                    if len(picked) == 1 and cls == 'solo':
                        vn = vn if self.full in name else title
                    if names.count(vn) > 1:
                        vn = f'{vn} ({price})'
                    new_voice.append({'project code': code, 'project name': title, 'date': date,
                                      'voice name': vn, 'price': str(price),
                                      'project website link': url, 'picture link': cover,
                                      '_pub': it['published_at'], '_cls': cls})
                continue

            gitems, seen = [], set()
            for v, name, price, kind in picked:
                n = strip_size(self.booth_item_name(name, title, cls))
                if (n, price) in seen:
                    continue
                seen.add((n, price))
                gitems.append((n, price, cover))
            new_goods.append({'code': code, 'name': title, 'type': project_type(title, cls), 'date': date,
                              'url': url, 'cover': cover, 'items': gitems, 'pub': it['published_at'], 'cls': cls})

        # ---- merge goods: newest first; new projects go after existing ones of the same date ----
        new_goods.sort(key=lambda x: x['code'])
        new_goods.sort(key=lambda x: x['pub'], reverse=True)
        g_new = merge_goods(g_old, new_goods)

        # ---- merge voice: oldest first; new rows go after existing rows of the same date ----
        new_voice.sort(key=lambda r: (r['_pub'], r['project code']))
        v_new = [v_old[0]]
        pv = list(new_voice)
        for r in v_old[1:]:
            while pv and dkey(pv[0]['date']) < dkey(r[VH['date']]):
                v_new.append([pv.pop(0)[k] for k in VOICE_HEADER])
            v_new.append(r)
        for r in pv:
            v_new.append([r[k] for k in VOICE_HEADER])

        t = list(shop['todo'])
        old_todo = {tuple(r) for r in t}
        t.extend(r for r in todo if tuple(r) not in old_todo)

        n_added = len(new_goods) + len({r['project code'] for r in new_voice})
        stats = {'scanned': len(items), 'related': related, 'new_goods_projects': len(new_goods),
                 'new_goods_items': sum(len(g['items']) for g in new_goods),
                 'new_voice_rows': len(new_voice),
                 'new_voice_projects': len({r['project code'] for r in new_voice}),
                 'duplicates': len(dups), 'todo': len(todo), 'added': n_added}
        return {'goods': g_new, 'voice': v_new, 'todo': t, 'stats': stats, 'dups': dups, 'log': log,
                'new_goods': new_goods, 'new_voice': new_voice, 'todo_new': todo}

    # ------------------------------------------------------- fan-club store
    def fc_campaign(self, raw_name, item_code):
        """Item name -> (project code, project name, project type, mapped?)."""
        name = fc_clean_name(raw_name)
        camp = next((c for c in self.fc['campaigns'] if c[0].search(name)), None)
        if camp:
            code, pname, ptype, mapped = camp[1], camp[2], camp[3], True
        else:
            # Unknown series: one project per item until a campaign rule is added.
            stem = re.sub(r'-\d+$', '', item_code).lower()
            code, pname, ptype, mapped = 'fc_' + re.sub(r'[^0-9a-z]+', '_', stem).strip('_'), name, '', False
        resale = FC_RESALE_RE.match(raw_name)
        if resale:
            code, pname = code + '_2nd', resale.group(0) + pname
        return code, pname, ptype, mapped

    def merge_fc(self, fc_raw, prev):
        """Append fan-club store projects (one per sales campaign) to the shop + BOOTH rows."""
        base = self.fc['base'].rstrip('/')
        pages = sorted(glob.glob(os.path.join(fc_raw, 'list', 'p*.json')),
                       key=lambda p: int(re.search(r'p(\d+)\.json$', p).group(1)))
        items = []
        for p in pages:
            with open(p, encoding='utf-8') as fh:
                items.extend(json.load(fh)['list'])
        with open(os.path.join(fc_raw, 'images.json'), encoding='utf-8') as fh:
            heads = json.load(fh)

        projects, log = {}, []
        for it in items:
            icode = it['item_code']
            raw_name = clean_title(it['item_name'])
            name = fc_clean_name(raw_name)
            if EXCLUDE_PRODUCT_RE.search(raw_name):
                log.append(('excluded', icode, raw_name))
                continue
            with open(os.path.join(fc_raw, 'detail', f'{icode}.html'), encoding='utf-8') as fh:
                det = fc_detail(fh.read())
            img = it['item_img_url']
            head = heads.get(img) or {}
            img_start = http_date_jst(head['last_modified']) if head.get('last_modified') else None
            start, src = (det['start'], 'text') if det['start'] else (img_start, 'image Last-Modified')
            if not start:
                raise RuntimeError(f'{icode}: no sale period and no image Last-Modified')
            if det['start'] and img_start and det['start'][:10] != img_start[:10]:
                log.append(('start-differs', icode, det['start'], 'image', img_start))
            lo, hi = int(it['min_price']), int(it['max_price'])
            prices = sorted({v['price'] for v in det['variations']}) or sorted({lo, hi})
            if det['variations'] and (lo not in prices or hi not in prices):
                log.append(('price-differs', icode, 'list', lo, hi, 'detail', prices))
            code, pname, ptype, mapped = self.fc_campaign(raw_name, icode)
            if not mapped:
                log.append(('unmapped', icode, raw_name, code))
            url = f'{base}/item/detail/{icode}'
            note = 'FC会員限定' if det['members_only'] else ''
            rows = []
            if len(prices) == 1:
                rows.append((name, prices[0], img, url, note))
            else:
                # Variations with different prices stay apart (sizes of one price are merged).
                for pr in prices:
                    labels = dict.fromkeys(strip_size(v['name']) or v['name'] for v in det['variations']
                                           if v['price'] == pr)
                    rows.append((f"{name} ({'・'.join(labels)})", pr, img, url, note))
            gp = projects.setdefault(code, {'code': code, 'name': pname, 'type': ptype, 'url': url,
                                            'cover': img, 'items': [], 'starts': [], 'cls': 'solo'})
            gp['items'].extend(rows)
            gp['starts'].append((start, src, icode))

        existing, by_norm_name = existing_index(prev['goods'], prev['voice'])
        new_goods, dups = [], []
        for gp in projects.values():
            starts = sorted({s for s, _, _ in gp['starts']})
            if len(starts) > 1:
                log.append(('campaign-starts-differ', gp['code'], starts))
            text = sorted(s for s, src, _ in gp['starts'] if src == 'text')
            if text:
                gp['pub'], gp['date_src'] = text[0], 'text'
            else:
                # Image upload times: some images are uploaded days before the sale,
                # so take the most common upload date (ties -> later) and its
                # earliest time, instead of the overall earliest upload.
                days = collections.Counter(s[:10] for s in starts)
                day = max(days, key=lambda d: (days[d], d))
                gp['pub'], gp['date_src'] = min(s for s in starts if s[:10] == day), 'image Last-Modified'
            gp['date'] = ymd(gp['pub'])
            cand = {(norm(n), str(p)) for n, p, *_ in gp['items']}
            match = find_duplicate(existing, by_norm_name, gp['name'], gp['date'], cand)
            if match:
                dups.append((gp['code'], gp['date'], gp['name'], match[0], existing[match[0]]['name'],
                             existing[match[0]]['date'], match[1]))
                continue
            new_goods.append(gp)
        new_goods.sort(key=lambda x: x['code'])
        new_goods.sort(key=lambda x: x['pub'], reverse=True)
        g_new = merge_goods(prev['goods'], new_goods)
        stats = {'scanned': len(items), 'new_goods_projects': len(new_goods),
                 'new_goods_items': sum(len(g['items']) for g in new_goods), 'duplicates': len(dups)}
        return {'goods': g_new, 'voice': prev['voice'], 'todo': prev['todo'], 'stats': stats,
                'dups': dups, 'log': log, 'new_goods': new_goods}

    def updates_rows(self, booth_added):
        return [UPDATES_HEADER] + [[d, note.format(booth_added=booth_added)] for d, note in self.updates]


def write_csv(path, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('profile', choices=sorted(PROFILES))
    ap.add_argument('--shop-raw', required=True, help='dir with <collection>_p<N>.json dumps')
    ap.add_argument('--booth-raw', required=True, help='dir with ids.txt and items/<id>.json')
    ap.add_argument('--fc-raw', help='dir with list/p<N>.json, detail/<code>.html and images.json '
                                     '(required for profiles with fc_store)')
    ap.add_argument('--out', required=True, help='output dir for goods/voice/updates/todo.csv')
    ap.add_argument('--report', action='store_true', help='print per-item decisions')
    args = ap.parse_args()

    b = Builder(PROFILES[args.profile])
    if b.fc and not args.fc_raw:
        ap.error(f'profile {args.profile} has fc_store: --fc-raw is required')
    shop = b.build_shop(args.shop_raw)
    booth = b.merge_booth(args.booth_raw, args.shop_raw, shop)
    final = booth
    fc = None
    if b.fc:
        fc = b.merge_fc(args.fc_raw, booth)
        final = fc

    os.makedirs(args.out, exist_ok=True)
    write_csv(os.path.join(args.out, 'goods.csv'), final['goods'])
    write_csv(os.path.join(args.out, 'voice.csv'), final['voice'])
    write_csv(os.path.join(args.out, 'updates.csv'), b.updates_rows(booth['stats']['added']))
    write_csv(os.path.join(args.out, 'todo.csv'), final['todo'])

    print('profile', args.profile)
    print('shop', *(f'{k}={v}' for k, v in shop['stats'].items()))
    print('booth', *(f'{k}={v}' for k, v in booth['stats'].items()))
    if fc:
        print('fc', *(f'{k}={v}' for k, v in fc['stats'].items()))
    if args.report:
        for e in shop['log']:
            print('SHOPLOG', *e, sep='\t')
        for d in booth['dups']:
            print('BOOTHDUP', *d, sep='\t')
        for e in booth['log']:
            print('BOOTHLOG', *e, sep='\t')
        for g in booth['new_goods']:
            print('BOOTHGOODS', g['code'], g['date'], g['cls'], g['type'] or '-', g['name'], sep='\t')
            for n, p, _ in g['items']:
                print('   ', p, n, goods_type(n, g['name']) or '', sep='\t')
        for r in booth['new_voice']:
            print('BOOTHVOICE', r['project code'], r['date'], r['_cls'], r['project name'], r['voice name'],
                  r['price'], sep='\t')
        for r in booth['todo_new']:
            print('BOOTHTODO', *r, sep='\t')
        if fc:
            for d in fc['dups']:
                print('FCDUP', *d, sep='\t')
            for e in fc['log']:
                print('FCLOG', *e, sep='\t')
            for g in fc['new_goods']:
                print('FCGOODS', g['code'], g['date'], g['pub'], g['date_src'], g['type'] or '-',
                      g['name'], g['url'], sep='\t')
                for n, p, _, url, note in g['items']:
                    print('   ', p, n, goods_type(n, g['name']) or '', note, url.rsplit('/', 1)[1], sep='\t')


if __name__ == '__main__':
    main()
