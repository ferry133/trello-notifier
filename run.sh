#!/bin/bash
set -e

# 確認 age private key 已設定
if [ -z "$AGE_SECRET_KEY" ]; then
  echo "ERROR: AGE_SECRET_KEY environment variable not set"
  exit 1
fi

# 安裝依賴
pip3 install -q requests

# 確認 sops 存在
if ! command -v sops &>/dev/null; then
  curl -sL https://github.com/getsops/sops/releases/download/v3.9.4/sops-v3.9.4.linux.amd64 -o /usr/local/bin/sops
  chmod +x /usr/local/bin/sops
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 建立暫存 age key 檔
AGE_KEY_FILE=$(mktemp)
echo "$AGE_SECRET_KEY" > "$AGE_KEY_FILE"
trap "rm -f $AGE_KEY_FILE $SCRIPT_DIR/line_contacts.json" EXIT

# 解密 contacts
SOPS_AGE_KEY_FILE="$AGE_KEY_FILE" sops --decrypt "$SCRIPT_DIR/contacts.enc.json" > "$SCRIPT_DIR/line_contacts.json"

# 解密 secrets 並匯出為環境變數
eval "$(SOPS_AGE_KEY_FILE="$AGE_KEY_FILE" sops --decrypt --output-type dotenv "$SCRIPT_DIR/secrets.enc.json")"

# 執行通知腳本
python3 "$SCRIPT_DIR/trello_line_notifier.py" "$@"
