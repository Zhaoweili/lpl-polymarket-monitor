import requests
import time
from datetime import datetime

# ================== 配置区 ==================
TELEGRAM_BOT_TOKEN = ""          # ← 后面在 Railway 里填
TELEGRAM_CHAT_ID = ""            # ← 后面在 Railway 里填

POLL_INTERVAL = 30
LPL_SERIES_ID = "10448"

seen_events = set()

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def main():
    print("🚀 LPL 全赛事监控脚本启动！")
    send_telegram("✅ 测试推送成功！LPL 监控脚本已正常运行 🚀")
    url = f"https://gamma-api.polymarket.com/events?series_id={LPL_SERIES_ID}&active=true&closed=false&limit=100&order=createdAt&ascending=false"

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

                if event_id and event_id not in seen_events:
                    link = f"https://polymarket.com/{slug}"
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    msg = f"🔥 <b>新 LPL 赛事上线！</b>\n\n📌 {title}\n🔗 <a href='{link}'>立即前往 Polymarket 下单</a>\n⏰ 上线时间: {timestamp}"
                    print(f"✅ 检测到新 LPL 赛事 → {title}")
                    send_telegram(msg)
                    seen_events.add(event_id)

            if len(seen_events) > 500:
                seen_events.clear()

        except Exception as e:
            print(f"轮询异常: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
