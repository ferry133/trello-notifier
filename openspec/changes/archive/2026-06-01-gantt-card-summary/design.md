## Context

`gantt_sheets_sync.gs` 的 `collectItems_()` 目前回傳 flat row 陣列，每列都重複填入 board/list/card 欄位，且 bar 繪製由 `dayOverlaps_()` 決定——只有 end 時從甘特起點畫滿，造成誤讀。渲染函式 `syncTrelloGantt()` 直接迭代 rows 寫入 Sheets。

`gantt_generator.py` 有相同的 `collect_items()` / `week_overlaps()` 問題，但為 CSV 靜態輸出，影響較小。

## Goals / Non-Goals

**Goals:**
- `collectItems_()` 輸出帶 `type` 欄位的 row（`"card"` / `"item"`），card row 含 progress、整體 span、bar color
- 渲染時依 board/list 變動決定是否填 A/B 欄，card row 填 C 欄，item row 的 A/B/C 留空
- end-only items 使用淡色 bar（結束日前 7 天）
- 無標記工項的 card 插入 summary row 並以 `sheet.hideRows()` 隱藏
- `gantt_generator.py` 同步修正 end-only bar 邏輯

**Non-Goals:**
- Google Sheets row grouping（可折疊）— 複雜度過高，使用 hideRows 已足夠
- `trello_line_notifier.py` 任何修改
- Gantt 時間範圍或欄位結構的變更

## Decisions

### 1. collectItems_() 輸出結構

**決策：** 回傳 `{ type, board, list, card, label, names, start, end, state, progress?, barColor? }` 的混合陣列，card row 插在其 items 前面。

**理由：** 渲染邏輯需要知道每列的 type 才能決定 A/B/C 填值，以及套用不同底色。相較於在渲染端重新計算卡片 span，在 collectItems_ 一次算好更單純。

**替代方案：** 分開回傳 cards map + items array，渲染端組合 → 增加渲染端複雜度，沒有好處。

---

### 2. Card summary row 的 start/end

**決策：** `start = min(所有 tagged items 的 start)`，`end = max(所有 tagged items 的 end)`，忽略 card description tag。

**理由：** 與 explore 決策一致，避免依賴 card desc tag，純從 items 計算最具代表性的工期範圍。

---

### 3. End-only bar 的呈現

**決策：** `start = null, end = D` 的 item → 繪製 `[end-6, end]` 共 7 天淡色 bar，使用 `BAR_COLORS_LIGHT` 對應版本。

```javascript
const BAR_COLORS_LIGHT = {
  complete:   "#b7e1c4",
  incomplete: "#c5d9fb",
  overdue:    "#f5c6c2",
  desc:       "#fde9a2",
};
```

**理由：** 淡色 + 固定 7 天長度傳達「只知道截止日、起點不確定」的語意，比從甘特起點畫滿更誠實。

**邊界：** 若 end 在甘特範圍內但距甘特起點不足 7 天，實際顯示天數以甘特範圍為限（自然截斷）。

---

### 4. 無標記工項的 card

**決策：** 插入 summary row（progress = "0/0"，無 bar），以 `sheet.hideRows(rowNum, 1)` 隱藏。

**理由：** 不直接 skip 是為了讓使用者可以手動 unhide 確認哪些 card 尚未加上標記，提供可見性。

---

### 5. A/B 欄 grouping

**決策：** 在渲染迴圈維護 `prevBoard` / `prevList`，card row 時比對並決定是否填 A/B；item row 的 A/B/C 一律填空字串。

**理由：** 比 merge cell 簡單，不影響 Sheets 的排序/篩選功能（merge cell 會壞）。

## Risks / Trade-offs

- **hideRows 需追蹤動態行號** → 在迴圈中維護 `currentRow` 計數器，每寫一列 +1，最後批次呼叫 `sheet.hideRows()`
- **CSV 版（gantt_generator.py）無法表達淡色** → 只修正 week_overlaps 邏輯（end-only 改為只標記最後一週），視覺效果有限，但不影響主要使用的 Apps Script 版本
- **card summary row 增加列數** → lastRow 計算與 clearRange 邏輯需確保覆蓋所有舊列（已有 `sheet.getLastRow()` 機制，應無問題）

## Open Questions

（無）
