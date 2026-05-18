import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
import json
import threading
import os

with open("flag.json", "r", encoding="utf-8") as f:
    FLAGS = json.load(f)

# ================= CONFIG =================
BASE = "https://ivas.tempnum.qzz.io"
LOGIN_URL = f"{BASE}/login"
GET_RANGE_URL = f"{BASE}/portal/sms/received/getsms"
GET_NUMBER_URL = f"{BASE}/portal/sms/received/getsms/number"
GET_SMS_URL = f"{BASE}/portal/sms/received/getsms/number/sms"
TEST_SMS_URL = f"{BASE}/portal/sms/test/sms"
RETURN_ALL_URL = f"{BASE}/portal/numbers/return/allnumber/bluck"

BOT_TOKEN = "8536331111:AAHKHdUS3bHdW-if-hN4tew9-uf_KgA9hKE"
CHAT_ID = "-1003984614969"
OWNER_ID = 6661810143

ADDNUM_API_URL = "https://ws.websocket.web.id/admin/addnumber"
ADDNUM_API_KEY = "112231"

os.makedirs("file", exist_ok=True)

ACCOUNTS = [
    {
        "USERNAME": "xesito4713@nixaur.com",
        "PASSWORD": "@speed123#",
        "COOKIES": {
            "_fbp": "fb.1.1778826406006.751602708452960393",
            "XSRF-TOKEN": "eyJpdiI6Ikw5dEpycEFtbnVGanF6ZVNhRnpMR2c9PSIsInZhbHVlIjoiZlVVMS8ydWV6MU5NNzRtVkxoSHdYZC9kZEhNN1RkdVlhNG1Ybi85ZGdxNmVIL2ZhMlpjY3FQQTl0TmpGYUpBRE9VYmVDMFNjTXo1bG5MZjMxdDA2eHVUaG4vbVFEZklJQU00L1FORlpHUEdEQ2c3Z3ZEK3h0d21mWk96cmFLUEEiLCJtYWMiOiIxY2YwNGY3ZjkzNTQzODYyYjgzNDFmZWYwYmFiNDUyYWFiMDgzNDQ4NDA2Mjc5MzU0NGQ5YzM2ZTA5YzY5NWFjIiwidGFnIjoiIn0%3D",
            "ivas_sms_session": "eyJpdiI6ImVJaHFTNlp2TDMzNTB2bTNLVlQ4T1E9PSIsInZhbHVlIjoiOTQxdjFBRmlNa2kxZVl4RUpEeWc4NGdvdkcwcmdmUWxmR05tYTh4cWcwRHhLS2h4NU9MdjlMMHZWQlJDejU1MCtMUVh3L3hES1p2OWpUZHZjUnp6VFdKdERpaTB2Qy9qTERmdW9GVkFrdXFCham5CVld0emMzRFVROCtYaHFNSVQiLCJtYWMiOiI4NmExMGVjODU2NmM1MWU3MzA0MTYyMGYxNGY5M2IyNzEyMTlkNzQyNGJmODM4NzRhNzY0ODgxMzBmMDc2M2UyIiwidGFnIjoiIn0%3D"
        }
    },
    {
        "USERNAME": "1",
        "PASSWORD": "1",
        "COOKIES": {
            "_fbp": "1",
            "XSRF-TOKEN": "1",
            "ivas_sms_session": "1"
        }
    }
]

SERVICE_SHORT = {
    "WHATSAPP": "WS", "TELEGRAM": "TG", "GOOGLE": "GO",
    "FACEBOOK": "FB", "INSTAGRAM": "IG", "SHOPEE": "SP",
    "TOKOPEDIA": "TP", "GRAB": "GR", "GOJEK": "GJ", "TIKTOK": "TT"
}

sent_cache = set()
last_update_id = 0
sms_stats = {"total_sms": 0, "total_otp": 0, "total_number": set()}

tg_session = httpx.Client(follow_redirects=True, timeout=15)

# ================= TELEGRAM =================
def tg_send(msg, otp):
    """Fungsi kirim OTP ke Telegram"""
    keyboard = {
        "inline_keyboard": [
            [{"text": f"🚀📋 {otp}", "callback_data": f"copy_{otp}"}],
            [
                {"text": "𝘿𝙀𝙑𝙀𝙇𝙊𝙋𝙀𝙍", "url": "t.me/TuanMudaEksazz"},
                {"text": "𝘾𝙃𝘼𝙉𝙉𝙀𝙇", "url": "https://t.me/eksazzgachaa"}
            ]
        ]
    }
    try:
        tg_session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "reply_markup": keyboard}
        )
    except Exception as e:
        print(f"[X] Gagal mengirim pesan telegram: {e}")

def tg_active(msg):
    try:
        tg_session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}
        )
    except:
        pass

def send_msg(chat_id, text):
    try:
        tg_session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        )
    except:
        pass

def delete_msg(chat_id, message_id):
    try:
        tg_session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
            data={"chat_id": chat_id, "message_id": message_id}, timeout=10
        )
    except:
        pass

# ================= UTILS =================
def extract_otp(text):
    m = re.search(r"\b(\d{3}[- ]?\d{3}|\d{4,6})\b", text)
    return m.group(1) if m else None

def format_phone_number(number):
    if len(number) >= 8:
        return f"{number[:3]}THAP{number[-4:]}"
    return number

def clean_country(rng):
    country = re.sub(r"\s*\(.*?\)", "", rng)
    country = re.sub(r"\d+", "", country)
    return country.strip().upper()

def extract_service_short(text):
    m = re.search(r"(WhatsApp|Telegram|Google|Facebook|Instagram|Shopee|Tokopedia|Grab|Gojek|TikTok)", text, re.I)
    if m:
        return SERVICE_SHORT.get(m.group(1).upper(), "Unknown")
    return "Unknown"

def mask_email(email):
    try:
        name, domain = email.split("@")
        masked = name[0] + "••••" + (name[-1] if len(name) > 2 else "")
        return f"{masked}@{domain}"
    except:
        return email

def get_flag(country):
    return FLAGS.get(country.upper(), "🏴‍☠️")

# ================= /start =================
def handle_start(chat_id):
    total_akun = len(ACCOUNTS)
    daftar_akun = ""
    for i, acc in enumerate(ACCOUNTS, 1):
        daftar_akun += f"  {i}. <code>{mask_email(acc['USERNAME'])}</code>\n"

    msg = (
        "┌─────────────────────┐\n"
        "│   🤖 <b>OTP BOT IVAS</b>      │\n"
        "└─────────────────────┘\n\n"
        f"📦 <b>Total Akun Aktif:</b> {total_akun}\n"
        f"📧 <b>Daftar Akun:</b>\n{daftar_akun}\n"
        "⚙️ <b>Status Bot:</b> 🟢 Online\n\n"
        "📌 <b>COMMAND</b>\n"
        "├ /cekivas - Cek stok IVAS WhatsApp\n"
        "├ /cekrange - Cek daftar range\n"
        "├ /addnum - Add number via API\n"
        "├ /delnumall - Return semua nomor\n"
        "├ /ambilfile - Export nomor ke Excel\n"
        "└ /statsms - Statistik SMS OTP\n\n"
        "⏱ Delay cek : 5 detik\n\n"
        "🔗 <b>Links</b>\n"
        "├ <a href='https://t.me/whizyv2'>Developer</a>\n"
        "└ <a href='https://t.me/officialwhizy'>Channel</a>"
    )
    send_msg(chat_id, msg)

# ================= CEK IVAS =================
def cek_ivas(chat_id=None):
    try:
        r = tg_session.get("http://ws.websocket.web.id/api/cekivas?platform=whatsapp", timeout=10)
        send_to = chat_id if chat_id else OWNER_ID
        if r.status_code != 200:
            send_msg(send_to, "❌ Gagal ambil data IVAS"); return
        data = r.json()
        if not data.get("success"):
            send_msg(send_to, "❌ API gagal"); return
        results = sorted(data.get("results", []), key=lambda x: x["count"], reverse=True)
        if not results:
            send_msg(send_to, "⚠️ Tidak ada data IVAS"); return
        msg = "📊 <b>CEK IVAS WHATSAPP</b>\n\n"
        for i, item in enumerate(results, 1):
            msg += f"{i}. {item.get('country','').upper()} : {item.get('count',0)} SMS\n"
        send_msg(send_to, msg)
    except Exception as e:
        send_msg(chat_id if chat_id else OWNER_ID, f"❌ Error: {e}")

# ================= STATSMS =================
def stats_sms(chat_id):
    msg = (
        "📊 <b>STATISTIK SMS OTP</b>\n\n"
        f"📩 Total SMS Masuk : {sms_stats['total_sms']}\n"
        f"🔑 Total OTP       : {sms_stats['total_otp']}\n"
        f"📞 Total Nomor     : {len(sms_stats['total_number'])}\n"
        f"👤 Total Akun      : {len(ACCOUNTS)}\n"
    )
    send_msg(chat_id, msg)

# ================= ADD NUM =================
def addnum_api(target, email):
    from httpx import ConnectError, TimeoutException
    MAX_RETRY = 3
    last_error = ""
    for attempt in range(1, MAX_RETRY + 1):
        try:
            r = tg_session.get(ADDNUM_API_URL, params={"target": target, "email": email, "apikey": ADDNUM_API_KEY}, timeout=20)
            try: res = r.json()
            except: res = {}
            if r.status_code == 200:
                return True, res.get("target_number", target)
            return False, f"HTTP {r.status_code}"
        except ConnectError as e:
            last_error = f"DNS/koneksi gagal ({attempt}/{MAX_RETRY}): {str(e)[:80]}"
        except TimeoutException:
            last_error = f"Timeout ({attempt}/{MAX_RETRY})"
        except Exception as e:
            last_error = str(e)[:100]; break
        if attempt < MAX_RETRY: time.sleep(3)
    return False, last_error

def addnum_command(text, chat_id, msg_id):
    if not ACCOUNTS:
        send_msg(chat_id, "❌ Belum ada akun di ACCOUNTS!")
        delete_msg(chat_id, msg_id); return
    parts = text.split()
    if len(parts) < 2:
        send_msg(chat_id, "❌ Format:\n/addnum SAUDI ARABIA 15022")
        delete_msg(chat_id, msg_id); return
    target = " ".join(parts[1:])
    keyboard = {"inline_keyboard": [[{"text": mask_email(a["USERNAME"]), "callback_data": f"ADDNUM|{target}|{a['USERNAME']}"}] for a in ACCOUNTS]}
    tg_session.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": chat_id, "text": f"📌 Pilih akun:\n\n<b>{target}</b>", "parse_mode": "HTML", "reply_markup": json.dumps(keyboard)}
    )
    delete_msg(chat_id, msg_id)

# ================= DEL NUM ALL =================
def return_all_number(acc):
    try:
        r = acc["session"].post(RETURN_ALL_URL, headers={"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/portal/numbers", "Origin": BASE})
        return (True, r.text) if r.status_code == 200 else (False, f"HTTP {r.status_code}")
    except Exception as e:
        return False, str(e)

def delnumall_command(chat_id):
    if not ACCOUNTS:
        send_msg(chat_id, "❌ Belum ada akun di ACCOUNTS!"); return
    keyboard = {"inline_keyboard": [[{"text": mask_email(a["USERNAME"]), "callback_data": f"DELNUMALL|{a['USERNAME']}"}] for a in ACCOUNTS]}
    tg_session.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": chat_id, "text": "⚠️ Pilih akun untuk <b>return semua nomor</b>:", "parse_mode": "HTML", "reply_markup": json.dumps(keyboard)}
    )

# ================= AMBIL FILE =================
def get_fresh_csrf(session):
    try:
        r = session.get(f"{BASE}/portal/numbers", follow_redirects=False, timeout=15)
        if r.status_code in (301, 302):
            loc = r.headers.get("location", "")
            if "login" in loc.lower():
                return None, "session_expired"
        if r.status_code in (301, 302):
            r = session.get(f"{BASE}/portal/numbers", follow_redirects=True, timeout=15)
        soup = BeautifulSoup(r.
