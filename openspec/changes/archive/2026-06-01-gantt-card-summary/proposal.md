## Why

甘特圖目前所有工項以 flat 列表呈現，card 與其 checklist items 沒有視覺層次，且只有結束日（無開始日）的工項會從甘特起點畫出整條 bar，造成誤讀。需要引入卡片摘要列與修正 bar 渲染邏輯，讓甘特圖更易讀。

## What Changes

- 新增 **card summary row**：每張有標記工項的 card 前插入一列，顯示 `a/b 完成` 進度、整體工期 span、依完成狀態變色的 bar
- **欄位 grouping**：A（案件）欄只在 board 變動時填值，B（清單）欄只在 list 變動時填值，C（卡片）欄只在 card summary row 填值；item rows 的 A/B/C 一律留空
- **end-only faded bar**：只有結束日（無開始日）的工項，改為在結束日前 7 天繪製淡色 bar，取代原本從甘特起點畫到結束日的錯誤行為
- 無標記工項的 card：仍插入 summary row 但預設隱藏

## Capabilities

### New Capabilities

- `gantt-card-summary-row`: card 摘要列，包含進度計數、工期 span、依完成度變色 bar、欄位 grouping 邏輯
- `gantt-end-only-bar`: 只有結束日的工項改以淡色 7 天 bar 呈現

### Modified Capabilities

（無現有 spec 需要修改）

## Impact

- `gantt_sheets_sync.gs`：`collectItems_()` 重構為輸出 card/item 兩種 row type；渲染邏輯加入 grouping、隱藏列、淡色 bar
- `gantt_generator.py`：`collect_items()` 同步修改 end-only bar 邏輯（CSV 版）
- `trello_line_notifier.py`：不受影響
