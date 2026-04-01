import requests
import time
from datetime import datetime
import os
import json

# ================== 配置区 ==================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")   # ← 新增微信推送

POLL_INTERVAL = 30

STRICT_MATCH_MODE = True   # True = 只推送实际对战赛事

LPL_TEAMS = ["TES", "BLG", "EDG", "JDG", "LNG", "AL", "WBG", "IG", "OMG", "TT", "WE", "UP", "FPX", "RNG", "Anyone's Legend", "Top Esports", "Bilibili Gaming", "EDward Gaming", "JD Gaming", "Weibo Gaming", "NIP"]
INTERNATIONAL_KEYWORDS = ["MSI", "Worlds", "Esports World Cup", "EWC", "World Championship", "Mid-Season"]

seen_events = set()
SEEN_FILE = "/app/seen_events.json"

if os.path.exists(SEEN_FILE):
    try:
        with open(SEEN_FILE, "r") as f:
            seen_events = set(json.load(f))
    except:
        pass

def save_seen_events():
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(seen_events), f)
    except:
        pass

def is_lpl_related(title: str) -> bool:
    title_upper = title.upper()
    if "LPL" in title_upper:
        return True
    if any(kw.upper() in title_upper for kw in INTERNATIONAL_KEYWORDS):
        return True
    words = title_upper.split()
    if any(team.upper() in words for team in LPL_TEAMS):
        return True
    return False

def is_actual_match(title: str) -> bool:
    title_lower = title.lower()
    return "vs" in title_lower and ("(bo" in title_lower or "bo3" in title_lower or "bo5" in title_lower)

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_wechat(message: str):
    """微信推送（PushPlus）"""
    if not PUSHPLUS_TOKEN:
        return
    url = "https://www.pushplus.plus/send"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": "🔥 新 LPL 对战赛事上线！",
        "content": message.replace("<b>", "**").replace("</b>", "**"),  # 微信不支持 HTML，转成 Markdown
        "template": "markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print("📱 微信推送已发送")
    except:
        pass

def main():
    print("🚀 LPL 监控脚本启动！【Telegram + 微信推送 最终版】")
    
    # 启动测试消息
    test_msg = "✅ LPL 监控已启动！\nTelegram + 微信 同时推送已开启\n开始监控所有 LPL 对战赛事～"
    send_telegram(test_msg)
    send_wechat(test_msg)

    url = "https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=200&order=createdAt&ascending=false"

    while True:
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                time.sleep(POLL_INTERVAL)
                continue

            data = resp.json()
            events = data.get("data", []) if isinstance(data, dict) else data

            for event in events:
                event_id = event.get("id")
                title = event.get("title", "")
                slug = event.get("slug", "")

                if (event_id and event_id not in seen_events and 
                    is_lpl_related(title) and 
                    (not STRICT_MATCH_MODE or is_actual_match(title))):

                    link = f"https://polymarket.com/{slug}"
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    msg = f"🔥 **新 LPL 对战赛事上线！**\n\n📌 {title}\n🔗 [立即前往 Polymarket 下单]({link})\n⏰ {timestamp}"

                    print(f"✅ 新对战 → {title}")
                    send_telegram(msg.replace("**", "<b>").replace("</b>", ""))  # Telegram 用 HTML
                    send_wechat(msg)  # 微信用 Markdown
                    seen_events.add(event_id)
                    save_seen_events()

            if len(seen_events) > 1000:
                seen_events.clear()
                save_seen_events()

        except Exception as e:
            print(f"轮询异常: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
