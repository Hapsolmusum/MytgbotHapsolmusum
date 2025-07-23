import telebot
from telebot import types
import requests
import threading
import re
import urllib.request
import os
import random
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

BOT_TOKEN = "7829162674:AAGK4z2v3A_BXFl2SU-6s5ntRTEA269NxOM"
ADMIN_ID = 7836866111  # Senin Telegram ID’in

CHANNEL = "kalbimdesaklisin"  # Zorunlu kanal

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

proxy_file = "proxy.txt"
live_file = "live_proxy.txt"
ccgen_file = "generated_cc.txt"
live_cc_file = "live.txt"
dead_cc_file = "dead.txt"

proxy_sources = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=anonymous",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
]

# Key Sistemi
keys = {}
active_keys = {}

def is_valid_key(user_id):
    if user_id in active_keys:
        key_info = active_keys[user_id]
        if datetime.now() < key_info["expires"]:
            return True
        else:
            del active_keys[user_id]
    return False

@app.route('/')
def home():
    return "Bot Aktif!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

class Proxy:
    def __init__(self, proxy):
        self.proxy = proxy

    def is_valid(self):
        return re.match(r"\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}", self.proxy)

    def check(self, timeout=5):
        try:
            proxy_support = urllib.request.ProxyHandler({"http": f"http://{self.proxy}"})
            opener = urllib.request.build_opener(proxy_support)
            urllib.request.install_opener(opener)
            req = urllib.request.Request("http://example.com")
            req.add_header("User-Agent", "Mozilla/5.0")
            urllib.request.urlopen(req, timeout=timeout)
            return True
        except:
            return False

def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL}", user_id)
        return member.status != "left"
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_user_in_channel(user_id):
        markup = types.InlineKeyboardMarkup()
        btn_join = types.InlineKeyboardButton(f"➡️ @{CHANNEL} Kanalına Katıl", url=f"https://t.me/{CHANNEL}")
        btn_check = types.InlineKeyboardButton("✅ Katıldım", callback_data="check_channel")
        markup.add(btn_join)
        markup.add(btn_check)
        bot.send_message(chat_id,
                         f"🚨 Botu kullanmak için önce @{CHANNEL} kanalına katılmalısın.\n"
                         "Katıldıysan ✅ Katıldım butonuna bas.",
                         reply_markup=markup)
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧪 Proxy Çek", "✅ Proxy Kontrol")
    markup.row("💳 CC Generator", "♻️ CC Checker")
    markup.row("👑 Sahip")
    bot.send_message(chat_id, "🔧 Hoş geldin! Aşağıdan bir işlem seç:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_channel")
def check_channel(call):
    if is_user_in_channel(call.from_user.id):
        bot.answer_callback_query(call.id, "🎉 Katılım doğrulandı!")
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Hala kanala katılmamışsın!", show_alert=True)

@bot.message_handler(commands=['keyolustur'])
def key_olustur(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, dakika, keyadi = m.text.split()
        dakika = int(dakika)
        keys[keyadi] = datetime.now() + timedelta(minutes=dakika)
        bot.reply_to(m, f"✅ {keyadi} adlı key {dakika} dakika geçerli.")
    except:
        bot.reply_to(m, "❌ Hatalı kullanım: /keyolustur <dakika> <keyadi>")

@bot.message_handler(commands=['keysil'])
def key_sil(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, keyadi = m.text.split()
        if keyadi in keys:
            del keys[keyadi]
            bot.reply_to(m, f"🗑️ {keyadi} keyi silindi.")
        else:
            bot.reply_to(m, "❌ Böyle bir key yok.")
    except:
        bot.reply_to(m, "❌ Hatalı kullanım: /keysil <keyadi>")

@bot.message_handler(commands=['keykullan'])
def key_kullan(m):
    try:
        _, keyadi = m.text.split()
        if keyadi in keys:
            active_keys[m.from_user.id] = {"expires": keys[keyadi]}
            bot.reply_to(m, f"✅ Key aktif edildi. Süre: {keys[keyadi]}")
        else:
            bot.reply_to(m, "❌ Geçersiz key.")
    except:
        bot.reply_to(m, "❌ Hatalı kullanım: /keykullan <keyadi>")

@bot.message_handler(func=lambda m: m.text == "🧪 Proxy Çek")
def proxycek(m):
    if not is_valid_key(m.from_user.id):
        return bot.reply_to(m, "🔐 Bu özelliği kullanmak için geçerli key kullanmalısın!")
    proxies = []
    for url in proxy_sources:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for line in r.text.strip().split("\n"):
                    if Proxy(line.strip()).is_valid():
                        proxies.append(line.strip())
        except:
            continue
    random.shuffle(proxies)
    selected = proxies[:100]
    with open(proxy_file, "w") as f:
        f.write("\n".join(selected))
    with open(proxy_file, "rb") as f:
        bot.send_document(m.chat.id, f, caption=f"✅ {len(selected)} proxy çekildi.")

@bot.message_handler(func=lambda m: m.text == "✅ Proxy Kontrol")
def proxykontrol(m):
    if not is_valid_key(m.from_user.id):
        return bot.reply_to(m, "🔐 Bu özelliği kullanmak için geçerli key kullanmalısın!")
    if not os.path.exists(proxy_file):
        return bot.reply_to(m, "❌ Önce proxy çekmelisin.")
    with open(proxy_file, "r") as f:
        raw_proxies = [p.strip() for p in f.readlines()]
    live = []

    def check(p):
        if Proxy(p).check():
            live.append(p)

    threads = [threading.Thread(target=check, args=(p,)) for p in raw_proxies]
    for t in threads: t.start()
    for t in threads: t.join()

    with open(live_file, "w") as f:
        f.write("\n".join(live))
    with open(live_file, "rb") as f:
        bot.send_document(m.chat.id, f, caption=f"✅ {len(live)} geçerli proxy bulundu.")

@bot.message_handler(func=lambda m: m.text == "💳 CC Generator")
def cc_gen_iste(m):
    if not is_valid_key(m.from_user.id):
        return bot.reply_to(m, "🔐 Bu özelliği kullanmak için geçerli key kullanmalısın!")
    bot.send_message(m.chat.id, "Kaç adet CC üretmek istersin? (1-5000):")
    bot.register_next_step_handler(m, cc_generate)

def cc_generate(m):
    try:
        if not is_valid_key(m.from_user.id):
            return bot.reply_to(m, "🔐 Key süresi bitmiş!")
        adet = int(m.text)
        if not (1 <= adet <= 5000):
            return bot.reply_to(m, "❌ 1 ile 5000 arasında sayı gir.")
        cc_list = [f"{random.randint(4000000000000000,4999999999999999)}|{random.randint(1,12):02d}|{random.randint(25,30)}|{random.randint(100,999)}" for _ in range(adet)]
        with open(ccgen_file, "w") as f:
            f.write("\n".join(cc_list))
        with open(ccgen_file, "rb") as f:
            bot.send_document(m.chat.id, f, caption=f"💳 {adet} sahte kart üretildi.")
    except:
        bot.send_message(m.chat.id, "❌ Hatalı giriş.")

@bot.message_handler(func=lambda m: m.text == "♻️ CC Checker")
def cc_checker_iste(m):
    if not is_valid_key(m.from_user.id):
        return bot.reply_to(m, "🔐 Bu özelliği kullanmak için geçerli key kullanmalısın!")
    bot.send_message(m.chat.id, "📄 CC listeni gönder (.txt ya da metin olarak).")

@bot.message_handler(content_types=['document'])
def handle_txt(m):
    if not is_valid_key(m.from_user.id):
        return
    file_info = bot.get_file(m.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    lines = downloaded.decode("utf-8").splitlines()
    check_cards(m.chat.id, lines)

@bot.message_handler(content_types=['text'])
def handle_text(m):
    if "|" in m.text and is_valid_key(m.from_user.id):
        cards = m.text.strip().split("\n")
        check_cards(m.chat.id, cards)

def check_cards(chat_id, card_list):
    live, dead = [], []

    def kontrol(card):
        try:
            r = requests.get(f"https://xchecker.cc/api.php?cc={card}", timeout=10)
            if "Live" in r.text or "Charged" in r.text:
                live.append(card)
            else:
                dead.append(card)
        except:
            dead.append(card)

    threads = [threading.Thread(target=kontrol, args=(c,)) for c in card_list]
    for t in threads: t.start()
    for t in threads: t.join()

    with open(live_cc_file, "w") as f:
        f.write("\n".join(live))
    with open(dead_cc_file, "w") as f:
        f.write("\n".join(dead))

    if live:
        with open(live_cc_file, "rb") as f:
            bot.send_document(chat_id, f, caption=f"✅ {len(live)} LIVE kart.")
    if dead:
        with open(dead_cc_file, "rb") as f:
            bot.send_document(chat_id, f, caption=f"❌ {len(dead)} DEAD kart.")

@bot.message_handler(func=lambda m: m.text == "👑 Sahip")
def sahip(m):
    bot.send_message(m.chat.id, "@Hapsolmusum Kraldır 👑")

# Başlat
keep_alive()
print("🤖 Bot çalışıyor...")
try:
    bot.infinity_polling()
except Exception as e:
    print(f"Bot durdu: {e}")