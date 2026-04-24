#!/usr/bin/env python3
import os
import json
import re
import requests
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo("Asia/Taipei")
LINE_API = "https://api.line.me/v2/bot/message/push"
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
TRELLO_KEY = os.environ.get("TRELLO_API_KEY", "")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN", "")
WORKSPACE_ID = "69e43323c25d72247983debe"

CONTACTS_FILE = os.path.join(os.path.dirname(__file__), "line_contacts.json")


def load_contacts():
    with open(CONTACTS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if v and not k.startswith("備")}


def send_line(user_id, message):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}],
    }
    resp = requests.post(LINE_API, headers=headers, json=body)
    return resp.status_code, resp.text


def get_boards():
    url = f"https://api.trello.com/1/organizations/{WORKSPACE_ID}/boards"
    params = {"key": TRELLO_KEY, "token": TRELLO_TOKEN, "filter": "open"}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


def get_cards(board_id):
    url = f"https://api.trello.com/1/boards/{board_id}/cards"
    params = {
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
        "checklists": "all",
        "fields": "name,desc,dateLastActivity",
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


# 解析 [@(名1)@(名2),yyyymmdd-yyyymmdd(:HHMM)] 格式
ITEM_RE = re.compile(
    r"\[@((?:\([^)]+\))+),(\d{8})?-?(\d{8})?(?::(\d{4}))?\](.+)"
)
NAME_RE = re.compile(r"\(([^)]+)\)")


def parse_tag(text):
    """回傳 (names[], start_date, end_date, label) 或 None"""
    m = ITEM_RE.match(text.strip())
    if not m:
        return None
    names = NAME_RE.findall(m.group(1))
    start = datetime.strptime(m.group(2), "%Y%m%d").date() if m.group(2) else None
    end = datetime.strptime(m.group(3), "%Y%m%d").date() if m.group(3) else None
    label = m.group(5).strip()
    return names, start, end, label


def days_diff(d):
    return (d - date.today()).days


def check_item(names, start, end, label, contacts, card_name, notifications):
    """比對七項條件，產生通知清單"""
    sponsors = [contacts[n] for n in names if n in contacts]
    sa_larry = [uid for n, uid in contacts.items() if n in ("SA", "Larry")]

    if start:
        diff = days_diff(start)
        if diff in (7, 3, 1):
            msg = f"【{card_name}】\n「{label}」{diff} 天後開始，請準備"
            for uid in sponsors:
                notifications.append((uid, msg))
        elif diff == 0:
            msg = f"【{card_name}】\n「{label}」今日開始，請確認"
            for uid in sponsors:
                notifications.append((uid, msg))

    if end:
        diff = days_diff(end)
        if diff in (7, 3, 1):
            msg = f"【{card_name}】\n「{label}」{diff} 天後到期"
            for uid in set(sponsors + sa_larry):
                notifications.append((uid, msg))
        elif diff < 0:
            msg = f"【{card_name}】\n「{label}」已逾期 {abs(diff)} 天，請確認"
            for uid in set(sponsors + sa_larry):
                notifications.append((uid, msg))


def run_checks():
    contacts = load_contacts()
    boards = get_boards()
    notifications = []
    summary_items = []

    for board in boards:
        cards = get_cards(board["id"])
        for card in cards:
            # 掃描 card description
            if card.get("desc"):
                first_line = card["desc"].split("\n")[0]
                parsed = parse_tag(first_line)
                if parsed:
                    names, start, end, label = parsed
                    check_item(names, start, end, label, contacts, card["name"], notifications)
                    summary_items.append(f"・{card['name']}（{label}）")

            # 掃描 checklists
            for checklist in card.get("checklists", []):
                items = checklist.get("checkItems", [])
                for item in items:
                    parsed = parse_tag(item["name"])
                    if not parsed:
                        continue
                    names, start, end, label = parsed
                    check_item(names, start, end, label, contacts, card["name"], notifications)

                # 停滯偵測：最後異動超過 3 天
                last_activity = card.get("dateLastActivity")
                if last_activity:
                    last_dt = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
                    days_stale = (datetime.now(TAIPEI) - last_dt.astimezone(TAIPEI)).days
                    incomplete = [i for i in items if i["state"] == "incomplete"]
                    if incomplete and days_stale >= 3:
                        msg = f"【{card['name']}】已停滯 {days_stale} 天，請追蹤"
                        for uid in [contacts.get("SA"), contacts.get("Larry")]:
                            if uid:
                                notifications.append((uid, msg))

                # 全部完成偵測
                if items and all(i["state"] == "complete" for i in items):
                    # 找第一個有標注的 item 的 sponsor
                    for item in items:
                        parsed = parse_tag(item["name"])
                        if parsed:
                            names, _, _, _ = parsed
                            sponsors = [contacts[n] for n in names if n in contacts]
                            msg = f"【{card['name']}】所有工項已全部完成 ✓"
                            for uid in sponsors:
                                notifications.append((uid, msg))
                            break

    # 每日摘要
    now_str = datetime.now(TAIPEI).strftime("%Y/%m/%d")
    if summary_items:
        summary = f"📋 {now_str} 每日工程摘要\n\n" + "\n".join(summary_items)
    else:
        summary = f"📋 {now_str} 今日無進行中工項"

    for uid in [contacts.get("SA"), contacts.get("Larry")]:
        if uid:
            notifications.append((uid, summary))

    # 去除重複通知（同一人同一則訊息）
    seen = set()
    unique = []
    for uid, msg in notifications:
        key = (uid, msg)
        if key not in seen:
            seen.add(key)
            unique.append((uid, msg))

    return unique


def test_send():
    """發一則測試訊息給 Larry，確認 LINE API 正常"""
    contacts = load_contacts()
    larry_id = contacts.get("Larry")
    if not larry_id:
        print("找不到 Larry 的 LINE ID")
        return
    now_str = datetime.now(TAIPEI).strftime("%Y/%m/%d %H:%M")
    msg = f"✅ LINE 通知系統測試成功！\n時間：{now_str}\n\n意念情境自動通知系統已就緒。"
    status, resp = send_line(larry_id, msg)
    print(f"狀態碼：{status}")
    print(f"回應：{resp}")


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_send()
    else:
        notifications = run_checks()
        print(f"共 {len(notifications)} 則通知待發送")
        for uid, msg in notifications:
            status, resp = send_line(uid, msg)
            print(f"→ {uid[:8]}... 狀態:{status}")


if __name__ == "__main__":
    main()
