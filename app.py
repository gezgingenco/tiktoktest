from flask import Flask, request, jsonify
from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import GiftEvent
import asyncio
import threading
import requests
from bs4 import BeautifulSoup
import re
import time

app = Flask(__name__)

# Global sandık bilgisi
sandik_verisi = {
    "kullanici": None,
    "coin": None,
    "kalan_saniye": None,
    "guncellenme": None
}

client = None
loop = asyncio.new_event_loop()

def get_username_from_short_url(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', r.url)
        if match:
            return match.group(1)
    except:
        return None
    return None

def listen_to_live(username):
    global client, sandik_verisi

    client = TikTokLiveClient(unique_id=username)

    @client.on("gift")
    async def on_gift(event: GiftEvent):
        if event.gift.describe.lower().startswith("treasure"):
            sandik_verisi.update({
                "kullanici": username,
                "coin": event.gift.diamond_count,
                "kalan_saniye": 30,  # Not: Gerçek süreyi alamazsak örnek veriyoruz
                "guncellenme": int(time.time())
            })

    loop.run_until_complete(client.start())

@app.route("/baslat", methods=["POST"])
def baslat():
    data = request.json
    url = data.get("url")
    username = get_username_from_short_url(url)

    if not username:
        return jsonify({"hata": "Kullanıcı adı çözülemedi."}), 400

    thread = threading.Thread(target=listen_to_live, args=(username,))
    thread.start()

    return jsonify({"mesaj": f"Dinleniyor: {username}"}), 200

@app.route("/sandik", methods=["GET"])
def sandik():
    if not sandik_verisi["kullanici"]:
        return jsonify({"mesaj": "Henüz veri alınmadı."}), 404
    return jsonify(sandik_verisi)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
