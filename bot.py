
import os
import re
import time
from datetime import datetime
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

import requests


# ==========================================
# SETTINGS
# ==========================================

URL = "https://instockradar.com/nl/store/denhaag/iphone-duo"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

MODEL = "iPhone Duo"
STORAGE = "256 GB"
COLOR = "Night Sky"
STORE = "Apple Den Haag"

TIMEZONE = ZoneInfo("Europe/Amsterdam")


# ==========================================
# CURRENT TIME
# ==========================================

def current_time():
    return datetime.now(TIMEZONE).strftime(
        "%d-%m-%Y %H:%M:%S"
    )


# ==========================================
# PARSE WEBSITE TEXT
# ==========================================

class TextParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


# ==========================================
# FETCH WEBSITE WITH RETRIES
# ==========================================

def get_with_retry(url):

    for attempt in range(1, 4):
        try:
            print(f"Website attempt {attempt}/3", flush=True)

            response = requests.get(
                url,
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            response.raise_for_status()
            return response

        except requests.RequestException as error:
            print(f"Attempt {attempt} failed: {error}", flush=True)

            if attempt < 3:
                print("Retrying in 5 seconds...")
                time.sleep(5)

    raise RuntimeError(
        "Website unavailable after 3 attempts"
    )


# ==========================================
# CHECK STOCK
# ==========================================

def check_stock():

    print("Checking iPhone Duo stock...", flush=True)

    response = get_with_retry(URL)

    parser = TextParser()
    parser.feed(response.text)

    text = re.sub(
        r"\s+", " ", parser.get_text()
    )

    target = f"{STORAGE} {COLOR}"

    match = re.search(
        re.escape(target).replace(r"\ ", r"\s+"),
        text,
        re.IGNORECASE
    )

    if not match:
        raise RuntimeError(
            "Could not locate exact iPhone variant on page"
        )

    section = text[match.end():]

    next_model = re.search(
        r"(?:256|512)\s*GB\s*(?:Night Sky|Star White)|"
        r"(?:1|2)\s*TB\s*(?:Night Sky|Star White)",
        section,
        re.IGNORECASE
    )

    if next_model:
        section = section[:next_model.start()]

    status = re.search(
        r"uitverkocht|op voorraad",
        section,
        re.IGNORECASE
    )

    if not status:
        raise RuntimeError(
            "Stock status could not be determined"
        )

    if status.group(0).lower() == "uitverkocht":
        print("STILL OUT OF STOCK", flush=True)
        return False

    print("POSSIBLY IN STOCK!", flush=True)
    return True


# ==========================================
# SEND DISCORD NOTIFICATION
# ==========================================

def send_discord_alert(status, details=""):

    timestamp = current_time()

    if status == "available":

        message = (
            "🚨 @everyone POSSIBLE STOCK ALERT! 🚨\n\n"
            f"📱 {MODEL} | {STORAGE} | {COLOR}\n"
            f"📍 {STORE}\n"
            "🟢 Website indicates: IN STOCK\n"
            f"🕒 {timestamp}\n\n"
            "🔥 VERIFY AVAILABILITY NOW!\n"
            f"🔗 {URL}"
        )

        mentions = {"parse": ["everyone"]}

    elif status == "unavailable":

        message = (
            "🔴 iPhone Duo Stock Check\n\n"
            f"📱 {MODEL} | {STORAGE} | {COLOR}\n"
            f"📍 {STORE}\n"
            "❌ Status: OUT OF STOCK\n"
            f"🕒 Checked: {timestamp}\n\n"
            "🔄 Waiting for next scheduled check."
        )

        mentions = {"parse": []}

    else:

        message = (
            "⚠️ iPhone Duo Stock Check FAILED\n\n"
            f"📱 {STORAGE} | {COLOR}\n"
            f"📍 {STORE}\n"
            f"🕒 Checked: {timestamp}\n"
            f"Reason: {details[:500]}"
        )

        mentions = {"parse": []}

    response = requests.post(
        WEBHOOK_URL,
        json={
            "content": message,
            "allowed_mentions": mentions
        },
        timeout=20
    )

    response.raise_for_status()

    print(
        f"Discord notification sent: {status}",
        flush=True
    )


# ==========================================
# RUN THE BOT
# ==========================================

def main():

    try:
        available = check_stock()

    except Exception as error:
        print(
            f"Stock check failed: {error}",
            flush=True
        )

        send_discord_alert("error", str(error))
        raise

    if available:
        send_discord_alert("available")
    else:
        send_discord_alert("unavailable")


# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    main()
