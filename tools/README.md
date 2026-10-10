# 資料集建置工具

用來從 **hololive production official shop**（Shopify `products.json`）、**hololive BOOTH**（`booth.pm/ja/items/<id>.json`），以及（僅限設定了 `fc_store` 的成員）**官方 FC 線上商店**（例如 HOSHIMACHI SUISEI ONLINE STORE）抓取商品資料，依成員設定檔（profile）產生網站使用的四個 CSV：

| 檔案 | 內容 |
| --- | --- |
| `goods.csv` | 周邊商品；每個企劃第一列為封面列（`goods index` = 0，名稱與價格留空），之後依序為 1、2、3…；企劃依日期**新到舊**排列 |
| `voice.csv` | 語音商品；依日期**舊到新**排列 |
| `updates.csv` | 更新紀錄（內容取自 profile 的 `updates`） |
| `todo.csv` | 需要人工確認的商品（共通商品是否含該成員、數位留言板等） |

## 檔案說明

| 檔案 | 用途 |
| --- | --- |
| `profiles.py` | 各成員設定檔（目前有 `nene`、`suisei`） |
| `build_dataset.py` | 主程式：官方商店 → 合併 BOOTH 獨有商品 → 附加 FC 商店企劃（有 `fc_store` 時）→ 輸出四個 CSV |
| `fetch_shop.py` | 下載官方商店 collection 的 `products.json`（每頁 250 筆，抓到空頁為止） |
| `fetch_booth.py` | 下載 hololive BOOTH 商品列表與每個商品的 JSON（已快取的不會重抓） |
| `fetch_fc.py` | 下載 FC 商店的商品列表 JSON、每個商品的公開詳細頁 HTML，並對列表圖片做 HEAD（記錄狀態與 `Last-Modified`）；已快取的不會重抓 |
| `sync_shop.py` | 官方商店增量同步：只把新的商品頁加進已發佈的 CSV（GitHub Actions 每天執行，見下方） |
| `shop_seen/<profile>.txt` | `sync_shop.py` 已處理過的商品 handle 清單 |
| `validate.py` | 驗證輸出（欄位、索引、排序、價格、日期、網址與圖片網址格式；可選擇用網站本身的 JS parser 解析） |

所有指令都在 repo 根目錄執行，Python 一律加 `-I`（isolated mode）。下載的原始資料請放在 repo **以外**的目錄（以下以 `$RAW` 表示），不要和腳本放在一起，也不要 commit。

## 重新抓取並重建（以すいせい為例）

```sh
RAW=/path/to/raw   # 任意 repo 外的目錄

# 1. 官方商店：成員本人的 collection，以及用來收集「其他成員名稱」的 collection
#    （profile 的 collection 與 name_collections）
python3 -I tools/fetch_shop.py "$RAW/shop" hoshimachisuisei azki momosuzunene

# 2. BOOTH（全部商品約 300 筆，所有成員共用同一份快取）
python3 -I tools/fetch_booth.py "$RAW/booth"

# 3. FC 商店（HOSHIMACHI SUISEI ONLINE STORE；profile 的 fc_store.base）
python3 -I tools/fetch_fc.py "$RAW/fc" https://hoshimachi-suisei-fc.jp/s/hs

# 4. 建置（--out 必填，避免不小心覆寫已提交的資料；有 fc_store 的 profile 必須給 --fc-raw）
python3 -I tools/build_dataset.py suisei --shop-raw "$RAW/shop" --booth-raw "$RAW/booth" \
  --fc-raw "$RAW/fc" --out suisei/data --report > /tmp/suisei_report.txt

# 5. 驗證
python3 -I tools/validate.py suisei/data --site-parsers
```

`--report` 會列出每個被排除的商品、BOOTH 重複判定、BOOTH 新增的企劃與 todo，以及 FC 商店的重複判定（`FCDUP`）、注意事項（`FCLOG`）與新增企劃（`FCGOODS`，含日期來源），建議重建後檢查一次。

快取規則：`fetch_shop.py` / `fetch_booth.py` / `fetch_fc.py` 只要檔案已存在就不會重抓。要拿到最新資料，請先刪除對應的 `$RAW/shop/<handle>_p*.json`，或 BOOTH 的 `list/` 與 `ids.txt`（商品 JSON 本身不會變動，可保留），或 FC 的 `list/`（販售狀態有變時也請刪除 `detail/`）。

## 官方商店增量同步（`sync_shop.py`）

`build_dataset.py` 每次都整份重建，不適合用來更新已發佈的資料：既有企劃的序號一變，使用者的紀錄就會對到別的商品，下架的商品也會消失。已發佈的資料改用 `sync_shop.py` 增量更新：

```sh
python3 -I tools/fetch_shop.py "$RAW/shop" momosuzunene azki hoshimachisuisei
cp -r suisei/data /tmp/before-suisei
python3 -I tools/sync_shop.py suisei --shop-raw "$RAW/shop" --summary /tmp/summary.md
python3 -I tools/validate.py suisei/data --before /tmp/before-suisei --site-parsers
```

- **新商品頁**：handle 不在 `shop_seen/<profile>.txt`，也不是 `goods.csv` / `voice.csv` 既有的企劃代碼。只有新商品頁會經過與 `build_dataset.py` 相同的規則（`Builder.build_shop`），其他商品頁完全不處理。
- **插入位置**：goods 依日期插入（同日期的排在既有企劃之後），voice 依日期插入（同日期的排在既有列之後），todo 加在最前面；有新增 goods / voice 時，`updates.csv` 加一列（日期預設為 JST 今天，可用 `--date` 指定）。
- **seen 清單**：執行後把 collection 內所有 handle 併入清單。清單不存在時會中止；新增成員時，用建立資料當時的原始資料執行 `--init-seen` 產生。
- `--data` 預設為 profile 的 `data_dir`；`--summary` 會附加 Markdown 格式的新增清單（GitHub Actions 用來當 PR 內文）。
- collection 抓到 0 筆時視為下載失敗並中止，不會當成「沒有新商品」。
- `.github/workflows/sync-shop.yml` 的 `fetch_shop.py` 參數要包含每個 profile 的 `collection` 與 `name_collections`；新增成員時記得一起加。

## ねね版資料（`data/`）的注意事項

`data/` 是已發佈的ねね版資料，**不要直接用 `--out data` 覆寫**。若修改了共用規則，請先輸出到暫存目錄，再與 `data/` 比對：

```sh
python3 -I tools/build_dataset.py nene --shop-raw "$RAW/nene-shop" --booth-raw "$RAW/booth" --out /tmp/nene_check
for f in goods voice todo updates; do cmp /tmp/nene_check/$f.csv data/$f.csv; done
```

用建立 `data/` 當時的原始資料重跑，四個檔案應該完全相同（byte-identical）。若改用新抓的資料，差異應只來自商店上的新商品／新變體。

## 新增成員

在 `profiles.py` 加一組設定。各欄位：

| 欄位 | 說明 |
| --- | --- |
| `full_name` | 全名，需與 Shopify 的 `Talent_<全名>` 標籤一致 |
| `short_name` | todo / updates 文字中使用的稱呼 |
| `name_re` | 變體名稱中代表本人的寫法（全名、暱稱、英文名、角色名等） |
| `booth_tag_re` | BOOTH 商品標籤中代表本人的寫法 |
| `extra_other_names` | 其他成員的簡稱（全名會自動從 `Talent_*` 標籤取得），用來排除他人的變體 |
| `own_group_re` | 包含本人的期別／組合標記（例如 `0期生`、`miComet`） |
| `collection` | 官方商店的 collection handle（`/collections/<handle>`） |
| `name_collections` | 用來收集其他成員全名的 collection 清單 |
| `solo_handle_hints` | 商品沒有 `Talent_*` 標籤時，用 handle 判斷是否為個人商品 |
| `data_dir` | 建議的輸出目錄（僅供參考，實際輸出位置以 `--out` 為準） |
| `fc_store` | （選填）FC 商店設定：`base`（例如 `https://hoshimachi-suisei-fc.jp/s/hs`）與 `campaigns`（`(商品名 regex, 企劃代碼, 企劃名稱, project type)` 清單，見下方 FC 規則） |
| `updates` | `updates.csv` 的內容；`{booth_added}` 會代入 BOOTH 新增企劃數 |

建立規則前，先實際檢查資料再決定寫法：

1. 確認 collection handle：抓下來後檢查每個商品是否都有 `Talent_<全名>` 標籤。
2. 統計變體名稱中出現的本人寫法與期別／組合標記，只放入資料中確實出現的標記。
3. 檢查簡稱是否會撞到其他詞（例如「スイ」會比對到「ボイスインドネシア語」，所以すいせい的規則不使用單獨的「すい／スイ」）。
4. 建置後用 `--report` 與 `todo.csv` 檢查排除與保留的結果。

## 共用規則摘要

- **個人／組合／團體**：`Talent_*` 只有本人為個人商品；包含本人且 5 人以下為組合；其他為團體。團體商品只收本人的變體與本人所屬期別／組合的變體，其他共通變體寫進 `todo.csv`。
- **媒體商品**：團體的 Blu-ray／CD／アルバム／カレンダー若只有 1～2 個共通變體，直接收錄。
- **排除**：數位留言板（個人／組合的會寫進 todo）、【ホロプラス】、PC 桌布。語音商品中的套組不收。
- **BOOTH**：只收與本人相關（標籤、商品名或變體名含本人）且不與官方商店企劃重複的商品，企劃代碼為 `booth_<id>`；圖片使用商品第一張圖。
- **FC 商店**（`fc_store`）：個人 FC 商店的商品全部收錄，接在官方商店＋BOOTH 之後合併（新企劃排在同日期既有企劃之後）。
  - **企劃**：一個販售檔期一個企劃。商品名去掉開頭的 `【…】`／`(※…)` 標籤後，用 `campaigns` 的 regex 決定企劃代碼與名稱；原始商品名以 `【二次販売…】`／`【再販…】` 開頭的歸到 `<代碼>_2nd`，名稱前加上該標籤（與官方商店把再販當獨立企劃的做法一致）。對不到規則的商品會各自成為 `fc_<品番>` 企劃並在 `FCLOG unmapped` 列出，請補規則。
  - **日期**：說明文中【受注期間】／【販売期間】的第一個日期（JST）。說明沒寫販售期間時（在庫販売、FC 會員限定商品），改用商品圖片的 `Last-Modified`（換算 JST；圖片在開賣時上架，已有日期的商品兩者一致），取企劃內最多商品的那一天。
  - **網址**：封面列（企劃連結）是企劃第一個商品的詳細頁；每個商品列保留自己的詳細頁，網站會顯示「商品頁」連結。
  - **商品**：名稱為去掉標籤後的商品名；同價的尺寸變體合併成一列，不同價才分列；價格為稅込整數（會員限定商品頁看不到變體，用列表的 `min_price`）；圖片為列表圖。需要 FC 會員登入才能購買的商品（詳細頁顯示登入表單）在 `note` 欄寫 `FC会員限定`。
  - **重複**：與既有企劃同名，或商品（名稱、價格）大量重複時跳過，列在 `FCDUP`。
