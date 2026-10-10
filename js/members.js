/* Member switcher shared by every talent site — the member list is defined only here.
 * Renders a small link group at the start of .nav-tools that points to the same page (ledger / voice / log)
 * of each member; the current member (window.SITE.id) is marked with aria-current.
 * Page scripts call MemberSwitch.render(lang) from their i18n step so the group label follows the language.
 */
(function (root) {
  'use strict';

  // base: root-relative folder of each talent site (the site is served at the domain root).
  // color: the member's accent colour, shown as a small dot so the other member is recognisable.
  const MEMBERS = [
    { id: 'nene', base: '/', name: 'ねね', full: '桃鈴ねね', color: '#e0661b' },
    { id: 'suisei', base: '/suisei/', name: 'すいせい', full: '星街すいせい', color: '#003cff' },
  ];
  const LABEL = { 'zh-Hant': '切換成員', ja: 'メンバー切り替え' };

  // Same page name for every member: '' (folder index = ledger), 'voice.html' or 'log.html'.
  function currentPage() {
    const last = root.location.pathname.split('/').pop();
    return last === 'index.html' ? '' : last;
  }

  function render(lang) {
    if (typeof document === 'undefined') return;
    const tools = document.querySelector('.nav-tools');
    if (!tools) return;
    let box = tools.querySelector('.member-switch');
    if (!box) {
      box = document.createElement('div');
      box.className = 'member-switch';
      box.setAttribute('role', 'group');
      tools.insertBefore(box, tools.firstChild);
    }
    box.setAttribute('aria-label', LABEL[lang] || LABEL['zh-Hant']);
    const cur = root.SITE && root.SITE.id;
    const page = currentPage();
    box.innerHTML = MEMBERS.map(m =>
      `<a href="${m.base}${page}" lang="ja" title="${m.full}" style="--mc:${m.color}"` +
      `${m.id === cur ? ' aria-current="page"' : ''}>${m.name}</a>`).join('');
  }

  root.MemberSwitch = { MEMBERS, render };
})(typeof window !== 'undefined' ? window : globalThis);
