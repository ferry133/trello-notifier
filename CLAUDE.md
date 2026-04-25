# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trello 自動監控 + LINE 通知系統，專為「意念情境室內裝修」設計。

定時讀取 Trello 看板上的卡片與 checklist，依七項觸發條件自動發送 LINE 訊息給客戶、工班師傅、SA/Larry。

**核心前提：只有含 `[@(姓名),日期區間]` 標記的項目，才觸發任何通知。**

## Commands

```bash
# 安裝依賴
pip3 install requests

# 執行通知（需先設定環境變數）
python3 trello_line_notifier.py

# 測試 LINE 發送（只發一則測試訊息給 Larry）
python3 trello_line_notifier.py test

# 透過 run.sh 執行（含 SOPS 解密，需提供 AGE_SECRET_KEY）
AGE_SECRET_KEY="..." bash run.sh
AGE_SECRET_KEY="..." bash run.sh test
```

## Architecture

```
run.sh
  └─ 解密 contacts.enc.json → line_contacts.json（執行結束後自動刪除）
  └─ 解密 secrets.enc.json → 環境變數（TRELLO_API_KEY、TRELLO_TOKEN、LINE_*）
  └─ python3 trello_line_notifier.py

trello_line_notifier.py
  ├─ get_boards()         讀取工作區所有看板
  ├─ get_cards()          讀取每張看板的卡片（含 checklists）
  ├─ parse_tag()          解析 [@(名1)@(名2),yyyymmdd-yyyymmdd(:HHMM)] 格式
  ├─ check_item()         比對六項日期觸發條件，產生通知
  ├─ run_checks()         主流程：掃描所有卡片，產生通知清單 + 每日摘要
  └─ send_line()          呼叫 LINE Messaging API 推播訊息
```

### 關鍵檔案

| 檔案 | 說明 |
|------|------|
| `trello_line_notifier.py` | 主腳本 |
| `run.sh` | 執行入口，含 SOPS 解密邏輯 |
| `line_contacts.json` | 姓名 → LINE User ID（runtime 解密產生，不 commit）|
| `contacts.enc.json` | 加密的聯絡人對應表 |
| `secrets.enc.json` | 加密的 API 金鑰 |
| `trello-line-design.md` | 完整系統設計文件（觸發條件、格式說明）|

### 七項觸發條件

1. 距開始日 7 / 3 / 1 天 → 通知 sponsor
2. 今天 = 開始日 → 通知 sponsor
3. 距結束日 7 / 3 / 1 天 → 通知 sponsor + SA/Larry
4. 結束日已過期 → 通知 sponsor + SA/Larry
5. Checklist 停滯超過 3 天（需有 `[@...]` 標記）→ 通知 SA/Larry
6. Checklist 全部完成（需有 `[@...]` 標記）→ 通知 sponsor
7. 每日摘要（無條件）→ 通知 SA/Larry

### 安全注意事項

- AGE 私鑰（`AGE_SECRET_KEY`）只能透過環境變數傳遞，**絕對不能明文出現在任何 prompt 或工具呼叫中**
- `~/.claude/settings.json` 已設定 PreToolUse hook 自動偵測並阻止

### 環境變數（由 settings.json 或 run.sh 注入）

- `TRELLO_API_KEY` / `TRELLO_TOKEN`
- `LINE_CHANNEL_ACCESS_TOKEN` / `LINE_CHANNEL_SECRET`
- `AGE_SECRET_KEY`（只在 run.sh 執行時需要）
