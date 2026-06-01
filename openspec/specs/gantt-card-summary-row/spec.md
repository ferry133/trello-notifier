## ADDED Requirements

### Requirement: Card summary row inserted before item rows
每張 card 在甘特圖中 SHALL 插入一列 card summary row，位於該 card 所有 item rows 之前。Card summary row 的欄位值為：
- A（案件）：board 與上一 card summary row 不同時填值，否則空白
- B（清單）：list 與上一 card summary row 不同時填值，否則空白
- C（卡片）：永遠填入 card 名稱
- D（工項名稱）：`a/b 完成`，a = 已完成的 tagged items 數，b = 全部 tagged items 數
- E（負責人）：空白（desc-only card 時填入 desc tag 的負責人）
- F（開始日）：所有 tagged items 中最早的 start date（desc-only card 時使用 desc tag 的 start）
- G（結束日）：所有 tagged items 中最晚的 end date（desc-only card 時使用 desc tag 的 end）
- H（狀態）：✓ 完成 / 逾期 / 未開始 / 未完成（詳見狀態規則）
- 甘特 bar：依完成度決定顏色，從 F 到 G 繪製

#### Scenario: Card with multiple tagged items
- **WHEN** card 有 3 個 tagged items，2 個 complete、1 個 incomplete
- **THEN** card summary row 的工項名稱顯示 "2/3 完成"，bar 為藍色（進行中）

#### Scenario: All items complete
- **WHEN** card 的所有 tagged items 皆為 complete
- **THEN** card summary row bar 顏色為綠色（#34a853）

#### Scenario: Any item overdue
- **WHEN** card 有至少一個 incomplete item 且其 end date 早於今日
- **THEN** card summary row bar 顏色為紅色（#ea4335）

---

### Requirement: Item rows omit board/list/card columns
Card 的 item rows（checklist items）A、B、C 欄 SHALL 填入空字串，不重複顯示 board/list/card 名稱。

#### Scenario: Checklist item row
- **WHEN** 渲染 checklist item row
- **THEN** 該列 A、B、C 欄為空白，D 欄起填入工項名稱等資料

---

### Requirement: Column A/B grouping by change
A 欄（案件）SHALL 只在 board 名稱與前一個 card summary row 不同時填值。B 欄（清單）SHALL 只在 list 名稱與前一個 card summary row 不同時填值。

#### Scenario: Same board, different list
- **WHEN** 連續兩張 card 屬於同一 board 但不同 list
- **THEN** 第二張 card summary row 的 A 欄空白，B 欄填入新 list 名稱

#### Scenario: Different board
- **WHEN** card 的 board 與前一張 card 不同
- **THEN** A 欄與 B 欄皆填入新值

---

### Requirement: Card summary row background
Card summary row 的 A~H 欄 SHALL 使用淡灰底色（`#e8e8e8`）以區別 item rows（白色底色）。

#### Scenario: Card row background
- **WHEN** syncTrelloGantt 完成渲染
- **THEN** 所有 card summary rows 的 A~H 欄背景為 #e8e8e8

---

### Requirement: Cards with no tagged items are skipped
無任何 tagged items 且無 card description tag 的 card SHALL 直接跳過，不插入任何列。

#### Scenario: Card with no tagged items
- **WHEN** card 的所有 checklist items 皆無 `[@...]` 標記，且 card description 也無標記
- **THEN** 該 card 不產生任何輸出列

---

### Requirement: Desc-only card merges tag into summary row
當 card 只有 desc tag（無任何 checklist tagged items）時，desc tag 的 names / start / end SHALL 直接填入 card summary row 的 E / F / G 欄，不單獨輸出 desc item row。

#### Scenario: Card with desc tag only
- **WHEN** card 的 desc 有 `[@...]` 標記，但 checklist 中無任何 tagged items
- **THEN** card summary row 的 E 填入 names、F 填入 start、G 填入 end；無額外 desc item row

#### Scenario: Card with both desc tag and checklist items
- **WHEN** card 的 desc 有 `[@...]` 標記，且 checklist 也有 tagged items
- **THEN** desc tag 仍單獨輸出為 item row，card summary row 的日期由 checklist items 決定

---

### Requirement: Card-level completion via dueComplete
Trello 的「標示為完成」按鈕（`card.dueComplete = true`）SHALL 覆蓋 checklist 統計，將 card summary row 視為完成。

#### Scenario: Card marked complete in Trello
- **WHEN** card.dueComplete === true，不論 checklist 勾選比例
- **THEN** card summary row H 欄顯示「✓ 完成」，bar 為綠色

---

### Requirement: H column status values
Card summary row 和 item row 的 H 欄 SHALL 依下列優先順序填入狀態文字：

| 優先順序 | 條件 | 顯示文字 | 字體顏色 |
|----------|------|----------|----------|
| 1 | card.dueComplete = true 或 all items complete / state = complete | ✓ 完成 | 黑色 |
| 2 | card 在「未執行」清單（名稱含「未執行」）且 start date 已過且未完成 | 未開始 | 紅色 |
| 3 | 有 incomplete item 且 end < today（card） / end < today && state ≠ complete（item） | 逾期 | 紅色 |
| 4 | 其他未完成 | 未完成 | 黑色 |

F 欄（開始日）在「未開始」情況下同樣顯示紅色字體。

#### Scenario: Overdue item
- **WHEN** item 的 end date 早於今日且 state = incomplete
- **THEN** H 欄顯示紅色「逾期」

#### Scenario: Not started card
- **WHEN** card 所在 list 名稱含「未執行」，card start date 已過，且未完成
- **THEN** H 欄顯示紅色「未開始」，F 欄（開始日）也顯示紅色
