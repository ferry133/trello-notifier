# jiahd-trello-notifier

意念情境室內裝修 — Trello 自動監控 + LINE 通知系統

## 架構

每日定時由 Kubernetes CronJob 執行，讀取 Trello 看板，依九項條件自動發送 LINE 通知給客戶、工班師傅、SA/Larry。

```
GitHub Actions → GHCR (ghcr.io/ferry133/trello-notifier)
         ↓
Kubernetes CronJob (jg-jiahd repo, Flux GitOps)
  ├─ morning  09:00 Mon–Sat  （今日開始、今日到期、每日摘要）
  ├─ noon     12:00 Sun–Sat  （開始/結束倒數、停滯、全完成）
  └─ evening  18:00 Mon–Sat  （今日已逾期、結束日已過期）
         ↓
trello_line_notifier.py [morning|noon|evening]
  ├─ 讀取 Trello 看板與 checklist
  ├─ 解析 [@(姓名),日期區間] 標記
  └─ 發送 LINE 通知
```

## 觸發條件摘要

| # | 時段 | 條件 | 通知對象 |
|---|------|------|---------|
| 1 | noon | 距**開始日** 1～7 天（每日） | sponsor |
| 2 | morning | 今天 = 開始日 | sponsor |
| 3 | noon | 距**結束日** 1～7 天（每日）且 card 未完成 | sponsor + SA/Larry |
| 4 | morning | 今天 = 結束日（時間未到）且 card 未完成 | sponsor + SA/Larry |
| 5 | evening | 今天 = 結束日（時間已過）且 card 未完成 | sponsor + SA/Larry |
| 6 | evening | 結束日已過期（weekday）且 card 未完成 | sponsor + SA/Larry |
| 7 | noon | Checklist 停滯 ≥ 3 天 | SA / Larry |
| 8 | noon | Checklist 全部完成 | sponsor |
| 9 | morning | 每日固定摘要 | SA / Larry |

**card 未完成定義：** 清單名稱為「未執行」或「執行中」，且 card 內至少有一個標記工項未完成。

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `trello_line_notifier.py` | 主要通知腳本 |
| `gantt_generator.py` | 產生甘特圖 CSV（可匯入 Google Sheets） |
| `gantt_sheets_sync.gs` | Google Apps Script：直接從 Trello 同步至 Google Sheets 甘特圖 |
| `Dockerfile` | 容器映像建置 |
| `trello-line-design.md` | 完整系統設計文件（觸發條件、訊息格式）|

---

## 安裝步驟

### 1. 取得 Trello API 憑證

1. 前往 https://trello.com/app-key 取得 **API Key**
2. 在同頁面點擊「Token」連結，授權後取得 **Token**
3. Trello 工作區 short name：`jiahomedesign1`（`WORKSPACE_ID` 寫在各腳本頂端）

### 2. 申請 LINE Official Account

1. 前往 https://tw.linebiz.com/ 申請免費輕用量方案（200 則/月，足夠使用）
2. 進入 LINE Developers Console → Messaging API → 取得 **Channel Access Token**
3. 通知對象需先加 LINE Official Account 為好友，才能收到推播

### 3. 取得各聯絡人的 LINE User ID

每位通知對象需先加 OA 好友，再透過 Webhook 或 LINE Developers Console 取得其 `userId`（格式為 `Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）。

### 4. 更新聯絡人資料

聯絡人存放於 NAS，路徑掛載為 `knowledge/contacts.json`，格式：

```json
{
  "Larry":  { "line_id": "U...", "projects": ["all"] },
  "SA":     { "line_id": "U...", "projects": ["all"] },
  "曾宇晟": { "line_id": "U...", "projects": ["jiahd"] },
  "張師傅": { "line_id": "U..." }
}
```

- 名字不區分大小寫（Trello 標記中的 `@(Larry)` / `@(larry)` 皆可對應）
- 以 `備` 開頭的欄位會被略過（可用於備份舊 ID）
- 舊格式 `{"名字": "U..."}` 仍相容

### 5. 更新 Kubernetes Secret

編輯 jg-jiahd repo 的 `kubernetes/apps/default/trello-notifier/app/secret.sops.yaml`，以 SOPS 加密寫入：

```
TRELLO_API_KEY
TRELLO_TOKEN
LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET
```

```bash
# 解密後編輯再重新加密
sops kubernetes/apps/default/trello-notifier/app/secret.sops.yaml
```

### 6. 推送映像（自動）

Push 到 `main` branch 後，GitHub Actions 自動建置並推送至 GHCR：

```
ghcr.io/ferry133/trello-notifier:latest
```

### 7. 部署至 Kubernetes（Flux 自動同步）

Flux 每 1 小時同步一次 jg-jiahd repo，自動套用 ConfigMap、Secret、CronJob。也可手動觸發：

```bash
flux reconcile kustomization trello-notifier
```

---

## Trello 卡片標記格式

只有含 `[@(姓名),日期區間]` 標記的項目才會觸發通知，格式如下：

```
[@(曾宇晟),20260501-20260530:1800] 拆除舊有磁磚
[@(Larry)@(SA),-20260530] 防水層施工驗收
[@(sa),20260505-20260512]
```

- 多人負責：每人前加 `@`，如 `[@(Larry)@(SA),...]`
- 結束時間（選用）：`HHMM`，如 `:1800`
- 無標籤文字：工項名稱欄位留空白
- 支援位置：checklist 項目、card description 第一行

詳見 `trello-line-design.md`。

---

## Google Sheets 甘特圖

### 方式 A：CSV 匯入（靜態）

```bash
pip3 install requests

TRELLO_API_KEY=... TRELLO_TOKEN=... python3 gantt_generator.py
# 產生 gantt.csv，匯入 Google Sheets
```

### 方式 B：Apps Script 即時同步（建議）

1. 開啟 Google Sheets → 擴充功能 → Apps Script
2. 貼上 `gantt_sheets_sync.gs` 全部內容，儲存
3. 設定 Script Properties（專案設定 → 指令碼屬性）：
   - `TRELLO_API_KEY`
   - `TRELLO_TOKEN`
4. 執行 `syncTrelloGantt()` 即可

甘特圖範圍：2026-04-26 起 26 週（182 天），每欄一天，奇偶週交替底色。

---

## 本機測試

```bash
pip3 install requests

# 發送測試訊息給 Larry
TRELLO_API_KEY=... TRELLO_TOKEN=... LINE_CHANNEL_ACCESS_TOKEN=... \
  python3 trello_line_notifier.py test

# 模擬各時段執行
TRELLO_API_KEY=... TRELLO_TOKEN=... LINE_CHANNEL_ACCESS_TOKEN=... \
  python3 trello_line_notifier.py morning
```
