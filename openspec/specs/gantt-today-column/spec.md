## ADDED Requirements

### Requirement: Today column highlighted in Gantt
甘特圖中對應今日日期的欄位 SHALL 使用特殊底色（`#f9cb9c`，橙色），取代奇偶週交替底色。此顏色同時套用於 header rows（列 1、2）和所有資料列中無 bar 的格子。有 bar 的格子仍顯示 bar 顏色。

#### Scenario: Today within Gantt range
- **WHEN** 今日日期在甘特起始日（GANTT_START）與結束日（GANTT_START + 181 天）之間
- **THEN** 今日對應欄的所有無 bar 格子（含 header）顯示橙色 `#f9cb9c`

#### Scenario: Today outside Gantt range
- **WHEN** 今日日期不在甘特時間範圍內
- **THEN** 所有欄位維持正常奇偶週底色，無特殊標記

#### Scenario: Today column with bar
- **WHEN** 某 item 的 bar 覆蓋今日欄
- **THEN** 該格顯示 bar 顏色（bar 優先於 today 底色）
