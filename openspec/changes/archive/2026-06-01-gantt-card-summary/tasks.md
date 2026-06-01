## 1. gantt_sheets_sync.gs — 資料結構

- [x] 1.1 定義 `BAR_COLORS_LIGHT` 常數（complete/incomplete/overdue/desc 各自的淡色版本）
- [x] 1.2 重構 `collectItems_()` 回傳值，加入 `type: "card" | "item"` 欄位
- [x] 1.3 在 `collectItems_()` 中，per card 計算 tagged item 數量（total/complete）、min start、max end、bar color
- [x] 1.4 為每張 card 在 items 前插入 card summary row（含 progress、span、barColor）
- [x] 1.5 無任何標記（no checklist tags, no desc tag）的 card 直接跳過，不插入任何 row

## 2. gantt_sheets_sync.gs — 渲染邏輯

- [x] 2.1 在渲染迴圈加入 `prevBoard` / `prevList` 追蹤，依規則決定 A/B 欄是否填值
- [x] 2.2 在 `collectItems_()` 建完陣列後，反向掃描標記每個 row 的 `lastInBoard` / `lastInList` / `lastItem` 旗標（供 ASCII 符號使用）
- [x] 2.3 item rows 的 C 欄填入 `├─ ` 或 `└─ `（依 `lastItem` 旗標），A/B 欄空白；card rows 的 A 欄填 `│` / `└─ `（依 `lastInBoard`），B 欄填 `├─ ` / `└─ `（依 `lastInList`，僅在 B 有值時填）
- [x] 2.4 card summary rows 的 A~H 欄套用灰色底色（`#e8e8e8`）
- [x] 2.5 實作 single-date bar 邏輯：start-only → `[start, start+6]` 7 天淡色；end-only → `[end-6, end]` 7 天淡色
- [x] 2.6 移除 hideRows 邏輯（無標記 card 已在 collectItems_() 跳過）
- [x] 2.7 確認 `clearRange` 覆蓋範圍正確（card summary rows 增加後 lastRow 仍正確清除）

## 3. gantt_generator.py — end-only 修正

- [x] 3.1 修改 `week_overlaps()` 的 end-only 分支：只標記 end date 所在週，不標記所有先前週次

## 4. 驗證

- [x] 4.1 在 Apps Script 執行 `syncTrelloGantt()`，確認 card summary rows 正確出現且有灰色底色
- [x] 4.2 確認 A/B 欄 grouping 正確（board/list 變動才填值），且 ASCII 符號 │/├─/└─ 位置正確
- [x] 4.3 找一個只有 end date 的工項，確認顯示為 7 天淡色 bar
- [x] 4.4 確認無標記的 card 直接跳過（不產生任何 row）
- [x] 4.5 執行 `gantt_generator.py` 確認 CSV end-only 欄位只標記最後一週
