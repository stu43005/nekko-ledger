/* Per-talent site config: 桃鈴ねね (site root).
 * Shared scripts (js/app.js, js/voice.js, js/log.js) read everything talent-specific from window.SITE.
 * i18n keys may be prefixed with the page id ('ledger.' / 'voice.' / 'log.'); a prefixed key wins over
 * an unprefixed one, and both win over the generic strings in each shared script's own I18N table.
 * Language / theme preference keys are not here: they are shared by all talents (see js/*.js).
 */
(function (root) {
  'use strict';

  const SITE = {
    id: 'nene',
    storage: { ledger: 'nene-ledger-v1', voice: 'nene-voice-v1' },
    // Relative to the page that loads this file.
    data: { goods: 'data/goods.csv', voice: 'data/voice.csv', updates: 'data/updates.csv', todo: 'data/todo.csv' },
    exportApp: { ledger: 'nene-ledger', voice: 'nene-voice' },
    exportFile: { ledger: 'ねっ子繳稅紀錄', voice: 'ねっ子Voice收集紀錄' },
    themeColor: '#e0661b',

    // Solo voice projects: name (after optional 【…】 prefixes such as 【再販】) starts with "桃鈴ねね" / "ねね" /
    // "Momosuzu Nene" / "Nene" (not as part of a longer latin word), or with "スターティングボイス" followed by
    // her name; or the title is quoted as 「ねねの…」 (e.g. ホロライブボイスドラマ「ねねのなつやすみ」).
    soloRe: /^(?:【[^】]*】\s*)*(?:桃鈴\s*ねね|ねね|Momosuzu\s*Nene(?![a-z])|Nene(?![a-z])|スターティングボイス\s*(?:桃鈴\s*)?ねね)|「ねねの/i,

    i18n: {
      'zh-Hant': {
        'ledger.doc.title': 'ねっ子繳稅紀錄簿｜桃鈴ねね 周邊收集清單',
        'ledger.doc.desc': '給ねっ子們的桃鈴ねね周邊收集清單。非官方粉絲製作。',
        'ledger.title': 'ねっ子繳稅紀錄簿',
        'ledger.lead': '把每一筆為ねね繳的稅記下來。點「繳稅」標記已入手的周邊，紀錄只存在你這台裝置的瀏覽器裡。',
        'voice.doc.title': 'ねね Voice 收集簿｜遜炮偶像株式會社',
        'voice.doc.desc': '整理桃鈴ねね參與的官方ボイス商品，記錄自己收集了哪些。非官方粉絲製作。',
        'voice.title': 'ねね Voice 收集簿',
        'voice.lead': '整理桃鈴ねね參與的官方ボイス商品。點「收集」標記已入手的 Voice，紀錄只存在你這台裝置的瀏覽器裡。',
        'kind.solo': 'ねね 個人',
        footer1: '本站為ねっ子自製的非官方粉絲網站，與 COVER 株式会社無關。',
      },
      ja: {
        'ledger.doc.title': 'ねっ子納税記録簿｜桃鈴ねね グッズコレクション',
        'ledger.doc.desc': 'ねっ子のための桃鈴ねねグッズ収集リスト。非公式ファンサイトです。',
        'ledger.title': 'ねっ子納税記録簿',
        'ledger.lead': 'ねねのために納めた税をひとつずつ記録しよう。「納税」を押して入手済みのグッズをチェック。記録はこの端末のブラウザ内にだけ保存されます。',
        'voice.doc.title': 'ねね ボイスコレクション｜遜炮偶像株式会社',
        'voice.doc.desc': '桃鈴ねねが参加した公式ボイス商品の一覧と、自分の収集記録。非公式ファンサイトです。',
        'voice.title': 'ねね ボイスコレクション',
        'voice.lead': '桃鈴ねねが参加した公式ボイス商品の一覧です。「収集」を押して入手済みのボイスをチェック。記録はこの端末のブラウザ内にだけ保存されます。',
        'kind.solo': 'ねね 単独',
        footer1: '本サイトはねっ子による非公式のファンサイトで、カバー株式会社とは一切関係ありません。',
      },
    },
  };

  root.SITE = SITE;
  if (typeof module !== 'undefined' && module.exports) module.exports = SITE;
})(typeof window !== 'undefined' ? window : globalThis);
