import requests
import time
from datetime import datetime
import os

# ================== 配置区 ==================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

POLL_INTERVAL = 30  # 秒，可改成15更激进

# LPL 队伍关键词（2026赛季常见队伍，已覆盖主流）
LPL_TEAMS = [
    "TES", "BLG", "EDG", "JDG", "LNG", "AL", "WBG", "IG", "OMG",
    "TT", "WE", "UP", "FPX", "RNG", "Anyone's Legend", "Top Esports",
    "Bilibili Gaming", "EDward Gaming", "JD Gaming", "Weibo Gaming"
]

# 国际赛事关键词（自动捕捉 MSI、Worlds、EWC 等）
INTERNATIONAL_KEYWORDS = ["MSI", "Worlds", "Esports World Cup", "EWC", "World Championship"]

seen_events = set()

def is_lpl_related(title: str) -> bool:
    title_upper = title.upper()
    # 包含任意 LPL 队伍
    if any(team.upper() in title_upper for team in LPL_TEAMS):
        return True
    # 包含国际赛事关键词（这些赛事基本都有 LPL 队伍参与）
    if any(kw in title for kw in INTERNATIONAL_KEYWORDS):
        return True
    return False

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TOKEN 或 CHAT_ID 为空！")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"📨 Telegram 响应: {resp.status_code}")
    except Exception as e:
        print(f"❌ Telegram 异常: {e}")

def main():
    print("🚀 LPL 扩展监控脚本启动！【监控所有有LPL队伍的赛事】")
    print(f"监控范围：LPL联赛 + MSI + Worlds + Esports World Cup + 所有LPL队伍参赛赛事")
    
    # 启动时发一条确认消息
    send_telegram("✅ LPL 扩展监控已启动！\n现在监控**所有有LPL队伍参加的赛事**（LPL + MSI + Worlds + EWC 等）")

    # 新 URL：拉取所有 LoL 赛事（去掉 series_id，改用 tag_slug）
    url = (
        "https://gamma-api.polymarket.com/events"
        "?tag_slug=league-of-legends"
        "&active=true&closed=false"
        "&limit=200"
        "&order=createdAt&ascending=false"
    )

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
                title = event.get("title", "未知赛事")
                slug = event.get("slug", "")

                # 核心过滤：只推送 LPL 相关赛事
                if event_id and event_id not in seen_events and is_lpl_related(title):
                    link = f"https://polymarket.com/{slug}"
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    msg = (
                        f"🔥 <b>新 LPL 相关赛事上线！</b>\n\n"
                        f"📌 {title}\n"
                        f"🔗 <a href='{link}'>立即前往 Polymarket 下单</a>\n"
                        f"⏰ 上线时间: {timestamp}"
                    )
                    print(f"✅ 检测到新 LPL 相关赛事 → {title}")
                    send_telegram(msg)
                    seen_events.add(event_id)

            if len(seen_events) > 800:
                seen_events.clear()

        except Exception as e:
            print(f"轮询异常: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
