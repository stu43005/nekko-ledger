/* Per-talent site config: 星街すいせい (/suisei/).
 * Same shape as the root site.js; see the comment there for how SITE.i18n is merged.
 */
(function (root) {
  'use strict';

  const SITE = {
    id: 'suisei',
    storage: { ledger: 'suisei-ledger-v1', voice: 'suisei-voice-v1' },
    // Relative to the page that loads this file, i.e. /suisei/data/*.csv.
    data: { goods: 'data/goods.csv', voice: 'data/voice.csv', updates: 'data/updates.csv', todo: 'data/todo.csv' },
    exportApp: { ledger: 'suisei-ledger', voice: 'suisei-voice' },
    exportFile: { ledger: '星詠み繳稅紀錄', voice: '星詠みVoice收集紀錄' },
    themeColor: '#003cff',

    // Solo voice projects: name (after optional 【…】 prefixes such as 【再販】) starts with "星街すいせい" /
    // "すいせい" / "Hoshimachi Suisei" / "Suisei" (not as part of a longer latin word), or with
    // "スターティングボイス" followed by her name; or the title is quoted as 「すいせいの…」 / 「星街すいせいの…」.
    soloRe: /^(?:【[^】]*】\s*)*(?:星街\s*すいせい|すいせい|Hoshimachi\s*Suisei(?![a-z])|Suisei(?![a-z])|スターティングボイス\s*(?:星街\s*)?すいせい)|「(?:星街\s*)?すいせいの/i,

    i18n: {
      'zh-Hant': {
        'ledger.doc.title': '星詠み繳稅紀錄簿｜星街すいせい 周邊收集清單',
        'ledger.doc.desc': '給星詠み們的星街すいせい周邊收集清單。非官方粉絲製作。',
        'ledger.title': '星詠み繳稅紀錄簿',
        'ledger.lead': '把每一筆為すいせい繳的稅記下來。點「繳稅」標記已入手的周邊，紀錄只存在你這台裝置的瀏覽器裡。',
        'voice.doc.title': 'すいせい Voice 收集簿｜遜炮偶像株式會社',
        'voice.doc.desc': '整理星街すいせい參與的官方ボイス商品，記錄自己收集了哪些。非官方粉絲製作。',
        'voice.title': 'すいせい Voice 收集簿',
        'voice.lead': '整理星街すいせい參與的官方ボイス商品。點「收集」標記已入手的 Voice，紀錄只存在你這台裝置的瀏覽器裡。',
        'kind.solo': 'すいせい 個人',
        footer1: '本站為星詠み自製的非官方粉絲網站，與 COVER 株式会社無關。',
      },
      ja: {
        'ledger.doc.title': '星詠み納税記録簿｜星街すいせい グッズコレクション',
        'ledger.doc.desc': '星詠みのための星街すいせいグッズ収集リスト。非公式ファンサイトです。',
        'ledger.title': '星詠み納税記録簿',
        'ledger.lead': 'すいせいのために納めた税をひとつずつ記録しよう。「納税」を押して入手済みのグッズをチェック。記録はこの端末のブラウザ内にだけ保存されます。',
        'voice.doc.title': 'すいせい ボイスコレクション｜遜炮偶像株式会社',
        'voice.doc.desc': '星街すいせいが参加した公式ボイス商品の一覧と、自分の収集記録。非公式ファンサイトです。',
        'voice.title': 'すいせい ボイスコレクション',
        'voice.lead': '星街すいせいが参加した公式ボイス商品の一覧です。「収集」を押して入手済みのボイスをチェック。記録はこの端末のブラウザ内にだけ保存されます。',
        'kind.solo': 'すいせい 単独',
        footer1: '本サイトは星詠みによる非公式のファンサイトで、カバー株式会社とは一切関係ありません。',
      },
    },
  };

  root.SITE = SITE;
  if (typeof module !== 'undefined' && module.exports) module.exports = SITE;
})(typeof window !== 'undefined' ? window : globalThis);
