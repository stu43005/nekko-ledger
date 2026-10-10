# ねっ子繳稅紀錄簿

給 hololive 粉絲使用的周邊收集清單（非官方粉絲網站，站名「遜炮偶像株式會社」）。目前收錄兩位成員：

- 桃鈴ねね（粉絲「ねっ子」）：網站根目錄 `/`，「ねっ子繳稅紀錄簿」
- 星街すいせい（粉絲「星詠み」）：`/suisei/`，「星詠み繳稅紀錄簿」

本專案 fork 自 [ccc15921/twkaitakusha](https://github.com/ccc15921/twkaitakusha)（原為 AZKi 粉絲「開拓者」製作的版本），感謝原作者開放程式碼。

## 檔案結構

```
index.html           ねね：繳稅紀錄簿（周邊）
voice.html           ねね：Voice 收集簿
log.html             ねね：網頁更新日記（更新紀錄＋尚未加入的周邊企劃）
site.js              ねね的成員設定（window.SITE，見下方「多成員結構」）
data/*.csv           ねね的資料（goods / voice / updates / todo）
suisei/index.html    すいせい：繳稅紀錄簿
suisei/voice.html    すいせい：Voice 收集簿
suisei/log.html      すいせい：網頁更新日記
suisei/site.js       すいせい的成員設定
suisei/theme.css     すいせい的配色（覆寫 css/style.css 的顏色變數）
suisei/data/*.csv    すいせい的資料
css/style.css        共用樣式（預設配色為ねね的橘色系 #c2540f / #e0661b / #e8711f）
js/app.js            繳稅紀錄簿（共用）：讀取周邊 CSV、分組、篩選、繳稅紀錄
js/voice.js          Voice 收集簿（共用）：讀取 Voice CSV、分組、篩選、收集紀錄
js/log.js            更新日記（共用）：讀取更新紀錄與 TODO CSV 並顯示
js/members.js        成員切換按鈕（共用）；成員清單只定義在這裡
js/transfer.js       紀錄轉移的編碼／解碼與 QR Code（繳稅紀錄簿用）
js/vendor/qrcode.js  QR Code 產生器（第三方，MIT）
```

## 多成員結構

每位成員一個資料夾（ねね在根目錄，其他成員在 `/<id>/`），頁面 HTML 各自一份，js 與 css 共用：

- **`site.js`**：定義 `window.SITE`，放所有和成員有關的設定，共用的 js 從這裡讀取：
  - `id`：成員代號（成員切換按鈕用來標示目前成員）
  - `storage.ledger` / `storage.voice`：localStorage 鍵（ねね為 `nene-ledger-v1` / `nene-voice-v1`，すいせい為 `suisei-ledger-v1` / `suisei-voice-v1`）
  - `data.goods` / `data.voice` / `data.updates` / `data.todo`：CSV 路徑（相對於頁面）
  - `exportApp` / `exportFile`：備份檔的 `app` 值與檔名開頭
  - `themeColor`：淺色模式的 `<meta name="theme-color">`（深色模式固定 `#09090a`）
  - `soloRe`：Voice 收集簿判斷「個人企劃」的正規表示式
  - `i18n`：`{ 'zh-Hant': {...}, ja: {...} }`，成員專屬的文字（標題、說明、頁尾、「個人」標籤等）。鍵可加頁面前綴（`ledger.` / `voice.` / `log.`），有前綴的優先；沒定義的文字會使用各 js 檔 `I18N` 內的通用文字
- **`theme.css`**：在 `../css/style.css` 之後載入，只覆寫顏色變數（`--accent`、`--accent-text`、`--bg` 等）。深色模式區塊必須把 style.css 深色區塊設定過的成員色變數（`--accent-text`、`--accent-soft`、`--accent-faint`、`--header-glow*`）全部重設，否則會殘留ねね的橘色。ねね直接使用 style.css 的預設值，不需要 theme.css
- **語言與深色模式設定所有成員共用**（`nene-ledger-lang`、`nene-ledger-theme`），各 html `<head>` 裡防閃白的小 script 也讀同一個鍵
- **成員切換按鈕**：`js/members.js` 的 `MEMBERS` 清單（`id`、`base` 資料夾路徑、名稱、代表色），會在導覽列的語言切換左邊產生連結，連到另一位成員的同一頁（繳稅↔繳稅、Voice↔Voice、日記↔日記）。路徑使用 `/`、`/suisei/` 這種從網域根目錄開始的寫法，所以網站必須部署在網域根目錄

### 新增成員

1. 建立 `/<id>/` 資料夾，從 `suisei/` 複製 `index.html`、`voice.html`、`log.html`、`site.js`、`theme.css`
2. 修改 `site.js`：`id`、storage 鍵、`exportApp`、`exportFile`、`themeColor`、`soloRe`、`i18n`
3. 修改 `theme.css` 的配色，並確認強調文字（`--accent-text`）在淺色與深色背景的對比都至少 4.5:1
4. 修改三個 html 的 `<title>`、description、theme-color、eyebrow、`<h1>`、Voice 頁的「個人」篩選按鈕文字，以及官方連結（YouTube、X、ホロライブ公式）
5. 放入 `/<id>/data/*.csv`
6. 在 `js/members.js` 的 `MEMBERS` 加一筆

## 部署到 GitHub Pages

網站網址：<https://nekko-ledger.shiaupiau.tw/>

1. 把整個專案（含 `css/`、`js/`、`data/`、`suisei/` 資料夾）放在 repo 根目錄。
2. Settings → Pages → Source 選 `Deploy from a branch`，分支 `main`、資料夾 `/ (root)`。
3. 自訂網域寫在根目錄的 `CNAME` 檔（`nekko-ledger.shiaupiau.tw`）。DNS（Cloudflare）需要一筆 `CNAME nekko-ledger → stu43005.github.io`，建議設為 DNS only（灰雲），讓 GitHub 能簽發 HTTPS 憑證。

本機預覽：網頁用 `fetch` 讀取 CSV，直接用 `file://` 開啟會被瀏覽器擋下，請在專案根目錄執行 `python3 -m http.server` 之類的靜態伺服器再開啟。

## 資料怎麼更新

所有資料都放在 repo 內的 `data/*.csv`（ねね）與 `suisei/data/*.csv`（すいせい），**不使用 Google 試算表**。要更新資料就直接編輯對應的 CSV 檔，commit 後 push 到 GitHub，GitHub Pages 重新部署完成後網頁就會讀到新資料。以下欄位說明兩位成員通用。

- CSV 需為 UTF-8 編碼，第一列是欄位名稱（不分大小寫）。
- 欄位內含逗號、換行或雙引號時，整個欄位要用雙引號包起來，內文的雙引號寫成 `""`。
- 網頁讀取時使用 `cache: 'no-cache'`，但 GitHub Pages 本身仍可能有幾分鐘的快取。
- 各 CSV 路徑設定在各成員 `site.js` 的 `data`。

### 官方商店自動同步

`.github/workflows/sync-shop.yml` 每天 12:17（JST）抓 hololive production official shop，由 `tools/sync_shop.py` 把**新的商品頁**加到兩位成員的 CSV（也可以在 Actions 頁面手動執行）：

- 只新增、不修改：已經在 CSV 裡的企劃一律不動（商店不會在既有商品頁加新變體），所以使用者的紀錄鍵不會錯位；下架的商品也會保留。
- 新企劃依日期插入 `goods.csv` / `voice.csv`，待確認項目加在 `todo.csv` 最前面，`updates.csv` 自動加一列「官方商店新增 N 個企劃：…」。
- 處理過的商品頁記在 `tools/shop_seen/<成員>.txt`，沒產生資料的商品頁（例如團體商品裡沒有本人）或已經從 todo 刪掉的項目，之後不會再被加回來。
- 有新增時會開（或更新）`shop-sync` 分支的 PR，內文列出新企劃、各件商品與待確認項目。**合併前請人工確認**：變體是否真的是本人的（新成員的簡稱可能還不在 `tools/profiles.py` 的 `extra_other_names`）、`goods type` 是否需要補。這個分支每次執行都會從 main 重建，要修改請合併後在 main 上改。
- BOOTH 與 FC 商店不在自動同步範圍內，仍用 `tools/` 的腳本手動更新（見 `tools/README.md`）。

### 周邊資料（data/goods.csv）

欄位：`goods project code`、`goods project name`、`project type`、`date`、`goods official website`、`x link`、`goods index`、`goods name`、`goods type`、`price`、`goods picture`、`note`、`project note`、`oversea`。

- 以 `goods project code` 分組成一個企劃。
- `goods index` 為 0 或沒有 `goods name` 的列 = 企劃封面；企劃名稱、日期、網址以封面列為準。
- 每件周邊的紀錄鍵是 `企劃代號#goods index`，**已上線後請不要更改既有周邊的代號或編號**，否則使用者的勾選紀錄會對不上。
- `project type`：`anniversary` 周年紀念、`birthday` 生日紀念，其他值歸為「其他」。
- `price` 可含千分位逗號；`date` 接受 `2025/7/1`、`2025/07/01` 等格式。
- `goods type`：`acrylic stand` 壓克力立牌、`badge` 徽章、`plushie` 娃娃、`keychain` 吊飾；其他值會原樣顯示成篩選選項。
- `oversea` 填 yes / true 即標為海外合作。

## 語言與主題

- 介面提供繁體中文／日文，右上角切換；預設依瀏覽器語言，選擇會記在瀏覽器裡（`nene-ledger-lang`，所有成員共用）。通用的介面文字在各頁 js 檔的 `I18N`，成員專屬的文字在各成員 `site.js` 的 `i18n`。
- 企劃名、周邊名、備註直接取自 CSV，不做翻譯。
- 深色模式預設跟隨系統，右上角按鈕可手動切換（`nene-ledger-theme`，所有成員的所有頁面共用）。

## 繳稅紀錄

每件周邊按「繳稅」後可用 +／− 調整數量，也可以直接在數量欄輸入（1～99999，輸入 0 等同取消繳稅）。

勾選紀錄存在使用者自己瀏覽器的 localStorage（ねね為 `nene-ledger-v1`，すいせい為 `suisei-ledger-v1`，彼此獨立），換裝置或清除瀏覽資料會不見，可用「匯出備份 / 匯入備份」搬移。
備份檔格式為 `{"app": "nene-ledger", "owned": {"企劃代號#編號": 數量}}`（すいせい的 `app` 為 `suisei-ledger`），例如 `{"nene_bd2026#3": 2}` 代表買了 2 個。
舊版備份檔的 `true` 會自動視為 1 個，可以直接匯入。

### 轉移到其他裝置（連結 + QR Code）

篩選區的「轉移到其他裝置」會把紀錄壓縮後放進網址的 `#t=` 後面並產生 QR Code，另一台裝置掃描或開啟連結，選「合併」或「取代」即可匯入。

- 不需要伺服器或帳號：網址 `#` 後面的內容不會被送到 GitHub，資料只存在連結本身。
- 連結內含收藏紀錄（企劃代號、編號、數量；不含金額），請只傳給自己。
- 「合併」同一件周邊取較大的數量，不會刪掉原有紀錄；「取代」則完全覆蓋。
- 這是一次性的快照，不是自動同步；兩邊都有更動時要再轉移一次。
- 連結含 CRC32 校驗，被聊天軟體截斷或損壞時會直接拒絕，不會匯入不完整的資料。
- 轉移連結指向產生它的那位成員的頁面（例如 `/suisei/#t=…`），匯入到該成員的紀錄。
- 格式與編碼在 `js/transfer.js`（`window.LedgerTransfer`）；QR Code 由 `js/vendor/qrcode.js`（[qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator)，MIT 授權）產生，已放在專案內，不依賴外部 CDN。

## Voice 收集簿（voice.html）

- 資料來自 `data/voice.csv`（すいせい為 `suisei/data/voice.csv`）。
- 欄位：`project code`、`project name`、`date`、`voice name`、`price`、`project website link`、`picture link`。
- 以 `project code` 分組成一個企劃；企劃名稱、日期、網址、封面取該企劃第一列。
- 這一頁**不計算金額**，只記錄收集了哪些 Voice。
- 紀錄鍵是 `企劃代號#Voice 名稱`（忽略空白與全半形括號差異）。**已上線後請不要改既有 Voice 的名稱或企劃代號**，否則勾選紀錄會對不上。
- 「個人企劃」的判斷規則是各成員 `site.js` 的 `soloRe`：ねね為企劃名稱以「桃鈴ねね」、「ねね」、「Momosuzu Nene」／「Nene」或「スターティングボイス（桃鈴）ねね」開頭，或含「ねねの…」；すいせい為以「星街すいせい」、「すいせい」、「Hoshimachi Suisei」／「Suisei」或「スターティングボイス（星街）すいせい」開頭，或含「（星街）すいせいの…」（開頭的【再販】等【…】前綴會略過）。符合的企劃標成「ねね 個人」／「すいせい 個人」，名稱含「再販」會標成「再販」。
- 收集紀錄存在 localStorage（`nene-voice-v1` / `suisei-voice-v1`），和繳稅紀錄簿分開，備份檔也分開匯出／匯入（備份檔的 `app` 為 `nene-voice` / `suisei-voice`）。語言與深色模式設定所有頁面共用。

## 網頁更新日記（log.html）

- 每位成員各有一份（`data/` 或 `suisei/data/` 底下的 `updates.csv`、`todo.csv`）。
- **更新紀錄**（`data/updates.csv`）：欄位 `date`、`note`。依日期新 → 舊排列；`note` 可含換行，網址會自動變成連結。
- **尚未加入的周邊企劃**（`data/todo.csv`）：欄位 `TODO`（企劃名稱）、`Website`（官方商店網址）。企劃加進 `data/goods.csv` 後，把該列從 `data/todo.csv` 刪掉即可。
- 這一頁沒有使用者紀錄，只讀取顯示。
- 頁尾的「最後更新」日期是寫在各 html 檔裡的固定文字，改版時要一起手動更新。
