#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGE_KEY_FILE="$SCRIPT_DIR/key.txt"

# 確認 key.txt 存在
if [ ! -f "$AGE_KEY_FILE" ]; then
  echo "ERROR: key.txt not found at $AGE_KEY_FILE"
  exit 1
fi

# 安裝依賴（若環境允許）
pip3 install -q requests backports.zoneinfo 2>/dev/null || true

# 確認 sops 存在
if ! command -v sops &>/dev/null; then
  curl -sL https://github.com/getsops/sops/releases/download/v3.9.4/sops-v3.9.4.linux.amd64 -o /usr/local/bin/sops
  chmod +x /usr/local/bin/sops
fi

trap "rm -f $SCRIPT_DIR/line_contacts.json" EXIT

# 解密 contacts
SOPS_AGE_KEY_FILE="$AGE_KEY_FILE" sops --decrypt "$SCRIPT_DIR/contacts.enc.json" > "$SCRIPT_DIR/line_contacts.json"

# 解密 secrets 並匯出為環境變數
set -a
eval "$(SOPS_AGE_KEY_FILE="$AGE_KEY_FILE" sops --decrypt --output-type dotenv "$SCRIPT_DIR/secrets.enc.json")"
set +a

# 執行腳本
if [ "$1" = "gantt" ]; then
  python3 "$SCRIPT_DIR/gantt_generator.py"
else
  python3 "$SCRIPT_DIR/trello_line_notifier.py" "$@"
fi
