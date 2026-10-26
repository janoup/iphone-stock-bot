import os
import re
import time
import requests
from html.parser import HTMLParser
from datetime import datetime
from zoneinfo import ZoneInfo


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
# GET CURRENT TIME
# ==========================================

def current_time():
    return datetime.now(TIMEZONE).strftime("%d-%m-%Y %H:%M:%S")


# ==========================================
# EXTRACT WEBSITE TEXT
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
            print(f"Checking website (attempt {attempt}/3)...")

            response = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            response.raise_for_status()

            return response

        except requests.RequestException as error:

            print(f"Attempt {attempt} failed: {error}")

            if attempt < 3:
                print("Retrying in 5 seconds...")
                time.sleep(5)

    raise RuntimeError("Website failed after 3 attempts")


# ==========================================
# CHECK EXACT IPHONE MODEL
# ==========================================

def check_stock():

    print("Checking iPhone Duo stock...")

    response = get_with_retry(URL)

    parser = TextParser()
    parser.feed(response.text)

    text = re.sub(r"\s+", " ", parser.get_text())

    target = f"{STORAGE} {COLOR}"

    start = text.lower().find(target.lower())

    if start == -1:
        raise RuntimeError(
            "Could not find the exact iPhone model"
        )

    section = text[start + len(target):]

    next_model = re.search(
        r"(?:256|512)\s*GB\s*(?:Night Sky|Star White)|"
        r"(?:1|2)\s*TB\s*(?:Night Sky|Star White)",
        section,
        re.IGNORECASE
    )

    if next_model:
        section = section[:next_model.start()]

    section = section.lower()

    if "uitverkocht" in section:
        print("Still sold out.")
        return False

    if "op voorraad" in section:
        print("IPHONE AVAILABLE!")
        return True

    raise RuntimeError(
        "Stock status could not be determined"
    )


# ==========================================
# SEND DISCORD NOTIFICATION
# ==========================================

def send_discord_alert(status):

    timestamp = current_time()

    if status == "available":

        message = (
            "🚨 @everyone IPHONE DUO IN STOCK! 🚨\n\n"
            f"📱 {MODEL}\n"
            f"💾 {STORAGE}\n"
            f"🎨 {COLOR}\n"
            f"📍 {STORE}\n\n"
            "🟢 STATUS: IN STOCK!\n\n"
            f"🕒 Checked: {timestamp}\n\n"
            "🔥 ORDER OR RESERVE NOW!\n"
            f"🔗 {URL}"
        )

        mentions = {"parse": ["everyone"]}

    elif status == "unavailable":

        message = (
            "🔴 iPhone Duo Stock Check\n\n"
            f"📱 {MODEL
