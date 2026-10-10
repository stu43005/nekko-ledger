# ねっ子繳稅紀錄簿

給桃鈴ねね粉絲「ねっ子」們使用的周邊收集清單（非官方粉絲網站，站名「遜炮偶像株式會社」）。

本專案 fork 自 [ccc15921/twkaitakusha](https://github.com/ccc15921/twkaitakusha)（原為 AZKi 粉絲「開拓者」製作的版本），感謝原作者開放程式碼。

## 檔案結構

```
index.html           繳稅紀錄簿（周邊）
voice.html           Voice 收集簿
log.html             網頁更新日記（更新紀錄＋尚未加入的周邊企劃）
css/style.css        共用樣式（主色 #c2540f / #e0661b / #e8711f，以ねね的橘色系為基調）
js/app.js            繳稅紀錄簿：讀取 data/goods.csv、分組、篩選、繳稅紀錄
js/voice.js          Voice 收集簿：讀取 data/voice.csv、分組、篩選、收集紀錄
js/log.js            更新日記：讀取 data/updates.csv 與 data/todo.csv 並顯示
js/transfer.js       紀錄轉移的編碼／解碼與 QR Code（繳稅紀錄簿用）
js/vendor/qrcode.js  QR Code 產生器（第三方，MIT）
data/goods.csv       周邊資料
data/voice.csv       Voice 資料
data/updates.csv     網頁更新紀錄
data/todo.csv        尚未加入的周邊企劃
```

## 部署到 GitHub Pages

1. 把整個專案（含 `css/`、`js/`、`data/` 資料夾）放在 repo 根目錄。
2. Settings → Pages → Source 選 `Deploy from a branch`，分支 `main`、資料夾 `/ (root)`。
3. 幾分鐘後網址會是 `https://<帳號>.github.io/<repo>/`。

本機預覽：網頁用 `fetch` 讀取 CSV，直接用 `file://` 開啟會被瀏覽器擋下，請在專案根目錄執行 `python3 -m http.server` 之類的靜態伺服器再開啟。

## 資料怎麼更新

所有資料都放在 repo 內的 `data/*.csv`，**不使用 Google 試算表**。要更新資料就直接編輯對應的 CSV 檔，commit 後 push 到 GitHub，GitHub Pages 重新部署完成後網頁就會讀到新資料。

- CSV 需為 UTF-8 編碼，第一列是欄位名稱（不分大小寫）。
- 欄位內含逗號、換行或雙引號時，整個欄位要用雙引號包起來，內文的雙引號寫成 `""`。
- 網頁讀取時使用 `cache: 'no-cache'`，但 GitHub Pages 本身仍可能有幾分鐘的快取。
- 各 CSV 路徑分別在 `js/app.js`（`CSV_URL`）、`js/voice.js`（`CSV_URL`）、`js/log.js`（`NOTES_URL`、`TODO_URL`）最上面。

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

- 介面提供繁體中文／日文，右上角切換；預設依瀏覽器語言，選擇會記在瀏覽器裡（`nene-ledger-lang`）。介面文字集中在各頁 js 檔的 `I18N`，要改字或加語言只改那裡。
- 企劃名、周邊名、備註直接取自 CSV，不做翻譯。
- 深色模式預設跟隨系統，右上角按鈕可手動切換（`nene-ledger-theme`，三頁共用）。

## 繳稅紀錄

勾選紀錄存在使用者自己瀏覽器的 localStorage（`nene-ledger-v1`），換裝置或清除瀏覽資料會不見，可用「匯出備份 / 匯入備份」搬移。
備份檔格式為 `{"app": "nene-ledger", "owned": {"企劃代號#編號": 數量}}`，例如 `{"nene_bd2026#3": 2}` 代表買了 2 個。
舊版備份檔的 `true` 會自動視為 1 個，可以直接匯入。

### 轉移到其他裝置（連結 + QR Code）

篩選區的「轉移到其他裝置」會把紀錄壓縮後放進網址的 `#t=` 後面並產生 QR Code，另一台裝置掃描或開啟連結，選「合併」或「取代」即可匯入。

- 不需要伺服器或帳號：網址 `#` 後面的內容不會被送到 GitHub，資料只存在連結本身。
- 連結內含收藏紀錄（企劃代號、編號、數量；不含金額），請只傳給自己。
- 「合併」同一件周邊取較大的數量，不會刪掉原有紀錄；「取代」則完全覆蓋。
- 這是一次性的快照，不是自動同步；兩邊都有更動時要再轉移一次。
- 連結含 CRC32 校驗，被聊天軟體截斷或損壞時會直接拒絕，不會匯入不完整的資料。
- 格式與編碼在 `js/transfer.js`（`window.NeneTransfer`）；QR Code 由 `js/vendor/qrcode.js`（[qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator)，MIT 授權）產生，已放在專案內，不依賴外部 CDN。

## Voice 收集簿（voice.html）

- 資料來自 `data/voice.csv`。
- 欄位：`project code`、`project name`、`date`、`voice name`、`price`、`project website link`、`picture link`。
- 以 `project code` 分組成一個企劃；企劃名稱、日期、網址、封面取該企劃第一列。
- 這一頁**不計算金額**，只記錄收集了哪些 Voice。
- 紀錄鍵是 `企劃代號#Voice 名稱`（忽略空白與全半形括號差異）。**已上線後請不要改既有 Voice 的名稱或企劃代號**，否則勾選紀錄會對不上。
- 企劃名稱以「桃鈴ねね」、「ねね」、「Momosuzu Nene」／「Nene」或「スターティングボイス（桃鈴）ねね」開頭會標成「ねね 個人」，名稱含「再販」會標成「再販」。
- 收集紀錄存在 localStorage（`nene-voice-v1`），和繳稅紀錄簿分開，備份檔也分開匯出／匯入（備份檔的 `app` 為 `nene-voice`）。語言與深色模式設定三頁共用。

## 網頁更新日記（log.html）

- **更新紀錄**（`data/updates.csv`）：欄位 `date`、`note`。依日期新 → 舊排列；`note` 可含換行，網址會自動變成連結。
- **尚未加入的周邊企劃**（`data/todo.csv`）：欄位 `TODO`（企劃名稱）、`Website`（官方商店網址）。企劃加進 `data/goods.csv` 後，把該列從 `data/todo.csv` 刪掉即可。
- 這一頁沒有使用者紀錄，只讀取顯示。
- 頁尾的「最後更新」日期是寫在各 html 檔裡的固定文字，改版時要一起手動更新。
