import requests
import time
from datetime import datetime
import os

# ================== 配置区 ==================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

POLL_INTERVAL = 30

# LPL 队伍（精确单词匹配）
LPL_TEAMS = [
    "TES", "BLG", "EDG", "JDG", "LNG", "AL", "WBG", "IG", "OMG", "TT", "WE", "UP",
    "FPX", "RNG", "Anyone's Legend", "Top Esports", "Bilibili Gaming",
    "EDward Gaming", "JD Gaming", "Weibo Gaming", "LNG", "NIP"
]

# 国际赛事关键词（保留，正常推送）
INTERNATIONAL_KEYWORDS = ["MSI", "Worlds", "Esports World Cup", "EWC", "World Championship", "Mid-Season"]

# 【核心加强】黑名单：一次性覆盖所有常见无关联赛
BLACKLIST = [
    "LCK", "LCK Challengers", "LEC", "LCS", "CBLOL", "LFL", "Prime League",
    "EMEA Masters", "Circuito Desafiante", "North American", "Challengers League",
    "Academy", "LJL", "PCS", "LLA", "TCL", "LCL", "Arabian League", "LCO",
    "Regular Season", "Playoffs"  # 只在非LPL场景下排除，LPL有单独正向匹配
]

seen_events = set()

def is_lpl_related(title: str) -> bool:
    title_upper = title.upper()
    
    # 第一优先：明确带 "LPL" 的直接通过（最准确）
    if "LPL" in title_upper:
        return True
    
    # 第二优先：国际赛事关键词
    if any(kw.upper() in title_upper for kw in INTERNATIONAL_KEYWORDS):
        return True
    
    # 第三优先：精确单词匹配 LPL 队伍
    words = title_upper.split()
    if any(team.upper() in words for team in LPL_TEAMS):
        return True
    
    # 最后：黑名单直接排除
    if any(black.upper() in title_upper for black in BLACKLIST):
        return False
    
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
    print("🚀 LPL 扩展监控脚本启动！【最终加强过滤版 - 已覆盖所有常见无关赛事】")
    send_telegram("✅ LPL 监控已启动（最终加强过滤版）！\n现在只推送真正有LPL队伍或LPL字样的赛事～")
    
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

            if len(seen_events) > 1000:
                seen_events.clear()

        except Exception as e:
            print(f"轮询异常: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
