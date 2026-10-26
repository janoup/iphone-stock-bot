import os
import re
import json
import urllib.request
from html.parser import HTMLParser

URL = "https://instockradar.com/nl/store/denhaag/iphone-duo"

class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

def check_stock():
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")

    parser = PageText()
    parser.feed(html)

    text = re.sub(r"\s+", " ", " ".join(parser.parts))

    match = re.search(
        r"256 GB Night Sky(.*?)(?=256 GB Star White)",
        text,
        re.IGNORECASE
    )

    if not match:
        raise ValueError("Cannot identify exact iPhone model")

    section = match.group(1).lower()

    if "uitverkocht" in section:
        return False

    if "op voorraad" in section:
        return True

    raise ValueError("Cannot determine stock status")

def notify():
    webhook = os.environ["DISCORD_WEBHOOK_URL"]

    message = {
        "content": (
            "🚨 @everyone IPHONE DUO IN STOCK!\n"
            "📱 iPhone Duo - 256 GB - Night Sky\n"
            "📍 Apple Den Haag\n"
            f"🔗 {URL}\n"
            "CHECK AVAILABILITY NOW!"
        )
    }

    request = urllib.request.Request(
        webhook,
        data=json.dumps(message).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    urllib.request.urlopen(request, timeout=30).close()

if __name__ == "__main__":
    print("Checking iPhone Duo stock...")

    try:
        if check_stock():
            print("AVAILABLE!")
            notify()
        else:
            print("Still sold out.")
    except Exception as error:
        print(f"Stock check failed: {error}")
        raise
