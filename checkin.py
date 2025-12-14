
import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://run.claw.cloud/auth/login"
CHECKIN_URL = "https://run.claw.cloud/user/checkin"

MAX_RETRY = 3

def telegram_notify(message: str):
    bot_token = os.getenv("TG_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if not bot_token or not chat_id:
        print("未配置 Telegram，跳过通知")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
        print("Telegram 通知已发送")
    except Exception as e:
        print("Telegram 通知失败：", e)

def check_success(text: str) -> bool:
    return any(k in text for k in ["成功", "签到", "流量", "获得", "Traffic"])

def random_sleep(a=1, b=10):
    sec = random.randint(a, b)
    print(f"随机等待 {sec} 秒防封...")
    time.sleep(sec)

def try_checkin():
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("打开登录页面...")
            page.goto(LOGIN_URL, timeout=30000)

            page.fill("input[name='email']", username)
            page.fill("input[name='passwd']", password)
            page.click("button[type='submit']")

            print("登录中...")
            random_sleep(2, 6)

            print("前往签到页面...")
            page.goto(CHECKIN_URL, timeout=30000)

            random_sleep(1, 5)

            result_text = page.content()
            print("签到返回内容：")
            print(result_text)

            return result_text

        except Exception as e:
            print("签到过程出现异常：", e)
            return f"ERROR: {e}"

        finally:
            browser.close()

def run_checkin_with_retry():
    for i in range(1, MAX_RETRY + 1):
        print(f"========== 第 {i} 次尝试签到 ==========")
        result = try_checkin()

        if check_success(result):
            msg = f"Claw Cloud 签到成功（第 {i} 次尝试）\n\n返回内容：\n{result}"
            telegram_notify(msg)
            print(msg)
            return

        print("签到似乎失败，将重试...")
        random_sleep(5, 12)

    fail_msg = f"Claw Cloud 签到失败（已尝试 {MAX_RETRY} 次）\n最后返回内容：\n{result}"
    telegram_notify(fail_msg)
    print(fail_msg)

if __name__ == "__main__":
    run_checkin_with_retry()
