# jiahd-trello-notifier

意念情境室內裝修 — Trello 自動監控 + LINE 通知系統

## 架構

每日定時由 Claude Code Remote Trigger 執行，讀取 Trello 看板，依七項條件自動發送 LINE 通知。

## 檔案說明

- `trello_line_notifier.py` — 主要通知腳本
- `run.sh` — 解密憑證並執行腳本的入口
- `secrets.enc.json` — SOPS 加密的 API 憑證
- `contacts.enc.json` — SOPS 加密的 LINE 聯絡人對應表
- `.sops.yaml` — SOPS age 加密設定

## 本機執行

需要設定環境變數 `AGE_SECRET_KEY`，然後執行：

```bash
AGE_SECRET_KEY="AGE-SECRET-KEY-..." bash run.sh
```
