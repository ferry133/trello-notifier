## ADDED Requirements

### Requirement: End-only items render as faded short bar
當 item 只有結束日（start = null）時，甘特圖 SHALL 在結束日前 7 天（含結束日）繪製淡色 bar，取代原本從甘特起點畫到結束日的行為。淡色定義為對應狀態顏色的淺色版本：

| 狀態 | 正常色 | 淡色 |
|------|--------|------|
| complete | #34a853 | #b7e1c4 |
| incomplete | #4285f4 | #c5d9fb |
| overdue | #ea4335 | #f5c6c2 |
| desc | #fbbc04 | #fde9a2 |

#### Scenario: Item with end date only, incomplete
- **WHEN** item 的 start = null，end = 2026-06-15，state = incomplete
- **THEN** 甘特圖在 2026-06-09 至 2026-06-15 的 7 個欄位填入淡藍色（#c5d9fb），其餘欄位不填

#### Scenario: Item with end date only, overdue
- **WHEN** item 的 start = null，end 早於今日，state = incomplete
- **THEN** 甘特圖在 end-6 至 end 的 7 個欄位填入淡紅色（#f5c6c2）

#### Scenario: End date near Gantt start
- **WHEN** item 的 end 距甘特起點不足 7 天
- **THEN** 只繪製甘特範圍內的部分（自然截斷），不超出甘特左邊界

---

### Requirement: Items with both start and end use normal bar
當 item 同時有 start 和 end 時，甘特圖 SHALL 使用正常實色 bar（現有行為），不受本功能影響。

#### Scenario: Item with start and end
- **WHEN** item 的 start = 2026-06-01，end = 2026-06-15
- **THEN** 甘特圖在 2026-06-01 至 2026-06-15 填入正常實色 bar

---

### Requirement: gantt_generator.py end-only week overlap
`gantt_generator.py` 的 `week_overlaps()` SHALL 修正 end-only 情況：只標記包含 end date 當週，取代原本標記所有 end date 以前的週次。

#### Scenario: CSV gantt end-only item
- **WHEN** 以 gantt_generator.py 產生 CSV，item 只有 end date
- **THEN** 只有 end date 所在週的欄位有標記
