"""Per-talent profiles for tools/build_dataset.py.

Every rule that is specific to one talent lives here; build_dataset.py only
holds the shared rules (media detection, set detection, goods types, naming).
Regexes are matched against Shopify variant titles ("<option1> / <option2>")
and BOOTH variation names, so only add markers that were seen in that data.
"""
import re

PROFILES = {
    'nene': {
        # Display / identity
        'full_name': '桃鈴ねね',
        'short_name': 'ねね',  # used in todo / updates wording
        # Variant titles that refer to the talent herself.
        'name_re': re.compile(r'桃鈴ねね|ねね|NENE|\bNene\b'),
        # BOOTH tag that marks an item as hers.
        'booth_tag_re': re.compile(r'^(桃鈴ねね|Momosuzu ?Nene)$', re.IGNORECASE),
        # Short names of unit mates that may appear without surname
        # (full names come from the Talent_* tags automatically).
        'extra_other_names': ['ラミィ', 'ぼたん', 'ポルカ', 'Lamy', 'Botan', 'Polka', 'Sora', 'Miko', 'Hajime',
                              'まつり', 'ルーナ', 'FUWAMOCO', 'ホロスターズ', 'HOLOSTARS', '大道シノヴ'],
        # Generation / unit markers that include the talent.
        'own_group_re': re.compile(r'5期|５期|ねぽらぼ|NePoLaBo|nepolabo', re.IGNORECASE),
        # Official shop collection handle (https://shop.hololivepro.com/collections/<handle>).
        'collection': 'momosuzunene',
        # Collections whose Talent_* tags form the list of "other talent" names.
        'name_collections': ['momosuzunene', 'azki'],
        # Handle fragments that mark a product as solo when it has no Talent_* tag.
        'solo_handle_hints': ['momosuzunene'],
        # Suggested output dir (relative to the repo root). build_dataset.py
        # never writes here unless it is passed explicitly with --out.
        'data_dir': 'data',
        # updates.csv rows; {booth_added} = number of BOOTH projects added.
        'updates': [
            ('2026/10/10', '初版：ねね版資料集建立（資料來源 hololive production official shop）'),
            ('2026/10/10', '補上 hololive BOOTH 商品（ねね相關 {booth_added} 件）'),
        ],
    },
    'suisei': {
        'full_name': '星街すいせい',
        'short_name': 'すいせい',
        # Seen in shop variants: 星街すいせい (172), Hoshimachi Suisei (5),
        # すいちゃん (5, e.g. "おでかけすいちゃんぬいぐるみ"), （すいせい） (miComet),
        # スイちゃん (1, "「スイちゃんのメンテナンスソング」").
        # 古河七星 is her hololive ERROR role: hololiveerror_merch2022 has
        # "アクリルスタンド 古河七星 ver.（星街すいせい）", while the 2021
        # hololiveerror_aogamihs variant is only "アクリルスタンド 古河七星 ver.".
        # Bare すい / スイ are NOT used: "スイ" also matches "ボイスインドネシア語".
        'name_re': re.compile(r'星街すいせい|すいせい|すいちゃん|スイちゃん|Hoshimachi Suisei|\bSuisei\b|SUISEI|古河七星'),
        'booth_tag_re': re.compile(r'^(星街すいせい|Hoshimachi ?Suisei)$', re.IGNORECASE),
        # "（みこ）" is used for Sakura Miko in miComet variants
        # ("ぬいぐるみキーホルダー miCometベアブランド衣装（みこ）ver.");
        # "まつり＆ルーナ" appears in hololive-summerfes-tapestry.
        'extra_other_names': ['みこ', 'Miko', 'まつり', 'ルーナ', 'FUWAMOCO', 'ホロスターズ', 'HOLOSTARS'],
        # Verified in shop variant titles: 0期生 (308) / 0期 (6, "0期+1期+2期+ゲーマーズ"),
        # miComet (4), 不知火建設 (1, "不知火建設 1st EP『scrap ＆ build !』").
        # The lookbehind keeps "10期" etc. from matching.
        # (Other-name matching runs first, so "みこめっと" would be caught by
        # "みこ" anyway; it does not occur in the data and is left out.)
        'own_group_re': re.compile(r'(?<![0-9０-９])[0０]期|miComet|不知火建設', re.IGNORECASE),
        'collection': 'hoshimachisuisei',
        'name_collections': ['hoshimachisuisei', 'azki', 'momosuzunene'],
        'solo_handle_hints': ['hoshimachisuisei'],
        'data_dir': 'suisei/data',
        # Official fan-club store (HOSHIMACHI SUISEI ONLINE STORE), see fetch_fc.py.
        # Each item is assigned to a sales campaign (= one project) by the first
        # campaign whose regex matches the item name with its leading 【...】 /
        # (※...) labels removed. Items whose raw name starts with a re-sale label
        # (【二次販売...】 / 【再販...】) go to "<code>_2nd", named
        # "<that label><name>". Names come from the store / FC news posts:
        #   - 8周年: FC news 10006 "星街すいせい8周年生誕祭記念グッズ＆FC限定Tシャツ販売スタート！"
        #   - tour:  FC news 10045 "HOSHIMACHI SUISEI ARENA TOUR 2026 Once Upon a Stellar"
        #            ("ツアーグッズの事前通販がスタート！")
        #   - Echoes Baa / PAJAMA PARTY: no news post; names follow the item
        #     names ("ロゴ…(Echoes Baa ver.)") and descriptions ("PAJAMA PARTYのロゴ").
        'fc_store': {
            'base': 'https://hoshimachi-suisei-fc.jp/s/hs',
            'campaigns': [
                # (item name regex, project code, project name, project type)
                (re.compile(r'^(PAJAMA SET|EYE MASK|SLIPPERS|CUSHION)$'),
                 'fc_pajamaparty', '【FC会員限定】PAJAMA PARTY グッズ', ''),
                (re.compile(r'^『Once Upon a Stellar』'),
                 'fc_onceuponastellar', 'HOSHIMACHI SUISEI ARENA TOUR 2026 Once Upon a Stellar ツアーグッズ', ''),
                (re.compile(r'^星街すいせい ロゴ.*\(Echoes Baa ver\.\)$'),
                 'fc_echoesbaa_logo', '星街すいせい ロゴグッズ(Echoes Baa ver.)', ''),
                (re.compile(r'^星街すいせい (Tシャツ|ステッカーセット|アクリルパネルスタンド|フルセットBOX|FC限定Tシャツ)$'),
                 'fc_bd2026_an8th', '星街すいせい8周年生誕祭記念グッズ＆FC限定Tシャツ', 'birthday'),
            ],
        },
        'updates': [
            ('2026/10/10', ('初版：すいせい版資料集建立（資料來源 hololive production official shop、'
                            'hololive BOOTH 與 HOSHIMACHI SUISEI ONLINE STORE）')),
        ],
    },
}
