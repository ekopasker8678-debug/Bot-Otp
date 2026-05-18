import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
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
            "ivas_sms_session": "eyJpdiI6ImVJaHFTNlp2TDMzNTB2bTNLVlQ4T1E9PSIsInZhbHVlIjoiOTQxdjFBRmlNa2kxZVl4RUpEeWc4NGdvdkcwcmdmUWxmR05tYTh4cWcwRHhLS2h4NU9MdjlMMHZWQlJDejU1MCtMUVh3L3hES1p2OWpUZHZjUnp6VFdKdERpaTB2Qy9qTERmdW9GVkFrdXFDam5CVld0emMzRFVROCtYaHFNSVQiLCJtYWMiOiI4NmExMGVjODU2NmM1MWU3MzA0MTYyMGYxNGY5M2IyNzEyMTlkNzQyNGJmODM4NzRhNzY0ODgxMzBmMDc2M2UyIiwidGFnIjoiIn0%3D"
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
def delete_later(message_id):
    return

    keyboard = {
        "inline_keyboard": [
            [{"text": f"🚀📋 {otp}", "callback_data": f"copy_{otp}"}],
            [
                {"text": "𝘿𝙀𝙑𝙀𝙇𝙊𝙋𝙀𝙍", "url": "t.me/TuanMudaEksazz"},
                {"text": "𝘾𝙃𝘼𝙉𝙉𝙀𝙇", "url": "https://t.me/eksazzgachaa"}
            ]
        ]
    }
    res = tg_session.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "reply_markup": keyboard}
    ).json()
    if res.get("ok"):
        threading.Thread(target=delete_later, args=(res["result"]["message_id"],), daemon=True).start()

def tg_active(msg):
    tg_session.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}
    )

def send_msg(chat_id, text):
    tg_session.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    )

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
        "⏱ Delay cek : 5 detik | Auto hapus : permanen menit\n\n"
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

# ================= 🔥 FIX: AMBIL FILE =================
def get_fresh_csrf(session):
    """Ambil CSRF token fresh dari halaman portal/numbers"""
    try:
        # 🔥 Minta halaman tanpa follow redirect dulu untuk deteksi expired
        r = session.get(f"{BASE}/portal/numbers", follow_redirects=False, timeout=15)

        # Redirect ke login = session expired
        if r.status_code in (301, 302):
            loc = r.headers.get("location", "")
            if "login" in loc.lower():
                return None, "session_expired"

        # Kalau redirect ke tempat lain, follow manual
        if r.status_code in (301, 302):
            r = session.get(f"{BASE}/portal/numbers", follow_redirects=True, timeout=15)

        # Parse CSRF dari HTML
        soup = BeautifulSoup(r.text, "html.parser")

        # Coba input _token
        token_input = soup.find("input", {"name": "_token"})
        if token_input and token_input.get("value"):
            return token_input["value"], None

        # Coba meta csrf-token
        meta = soup.find("meta", {"name": "csrf-token"})
        if meta and meta.get("content"):
            return meta["content"], None

        # Coba regex sebagai fallback
        m = re.search(r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']', r.text)
        if m:
            return m.group(1), None

        return None, "token_not_found"
    except Exception as e:
        return None, str(e)

def export_numbers_ivas(chat_id, email):
    # 🔥 Cari akun dari runtime accounts (bukan ACCOUNTS raw)
    # supaya pakai session yang sudah login di run_bot()
    acc_target = None
    for a in ACCOUNTS:
        if a["USERNAME"] == email and a.get("session"):
            acc_target = a
            break

    if not acc_target:
        send_msg(chat_id, "❌ Akun tidak ditemukan"); return

    session = acc_target["session"]
    send_msg(chat_id, f"⏳ Mengambil file export untuk <code>{mask_email(email)}</code>...")

    try:
        # 🔥 FIX 1: Ambil CSRF token fresh, sekaligus validasi session
        token, err = get_fresh_csrf(session)

        if err == "session_expired":
            # 🔥 FIX 2: Coba relogin dulu, lalu ambil token lagi
            print(f"[~] Session expired untuk export, relogin: {email}")
            login(acc_target)
            token, err = get_fresh_csrf(session)
            if err:
                send_msg(chat_id, f"❌ Session expired & relogin gagal\nError: {err}"); return

        if not token:
            # 🔥 FIX 3: Fallback pakai csrf_token yang tersimpan dari login
            token = acc_target.get("csrf_token", "")
            if not token:
                send_msg(chat_id, "❌ CSRF token tidak ditemukan"); return

        export_url = f"{BASE}/portal/numbers/export"

        # 🔥 FIX 4: Coba POST dulu, kalau gagal coba GET
        for method in ["POST", "GET"]:
            if method == "POST":
                r = session.post(
                    export_url,
                    data={"_token": token},
                    headers={
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": f"{BASE}/portal/numbers",
                        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*"
                    },
                    follow_redirects=False,  # 🔥 Jangan follow redirect, tangani manual
                    timeout=30
                )
            else:
                r = session.get(
                    export_url,
                    headers={
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": f"{BASE}/portal/numbers"
                    },
                    follow_redirects=False,
                    timeout=30
                )

            # Jika redirect ke login, session benar-benar expired
            if r.status_code in (301, 302):
                loc = r.headers.get("location", "")
                if "login" in loc.lower():
                    send_msg(chat_id, "❌ Session expired saat export\nCoba update cookie akun"); return
                # Redirect ke tempat lain, follow
                r = session.get(r.headers["location"], follow_redirects=True, timeout=30)

            # 🔥 FIX 5: Validasi response adalah file Excel (bukan HTML error)
            content_type = r.headers.get("Content-Type", "")
            is_excel = (
                "spreadsheet" in content_type or
                "octet-stream" in content_type or
                "excel" in content_type or
                (r.status_code == 200 and len(r.content) > 500 and not r.text[:20].strip().startswith("<"))
            )

            if r.status_code == 200 and is_excel:
                break  # Berhasil dapat file
        else:
            send_msg(chat_id, f"❌ Export gagal (HTTP {r.status_code})\nContent-Type: {content_type[:60]}"); return

        # Simpan dan kirim file
        filename = f"ivas_export_{int(time.time())}.xlsx"
        filepath = f"file/{filename}"

        with open(filepath, "wb") as f:
            f.write(r.content)

        with open(filepath, "rb") as f:
            tg_session.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data={
                    "chat_id": chat_id,
                    "caption": f"📊 <b>FILE IVAS</b>\n👤 {mask_email(email)}\n📦 {len(r.content)//1024} KB",
                    "parse_mode": "HTML"
                },
                files={"document": (filename, f)}
            )
        os.remove(filepath)

    except Exception as e:
        send_msg(chat_id, f"❌ Error export: {e}")

def ambilfile_command(chat_id):
    if not ACCOUNTS:
        send_msg(chat_id, "❌ Belum ada akun di ACCOUNTS!"); return
    keyboard = {"inline_keyboard": [[{"text": mask_email(a["USERNAME"]), "callback_data": f"EXPORT|{a['USERNAME']}"}] for a in ACCOUNTS]}
    tg_session.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": chat_id, "text": "📂 Pilih akun untuk <b>export nomor</b>:", "parse_mode": "HTML", "reply_markup": json.dumps(keyboard)}
    )

# ================= CEK RANGE =================
def cek_range_command(chat_id, text):
    try:
        parts = text.split()
        search_query = ""
        target_apps = ["WhatsApp", "Telegram"]
        if len(parts) > 1:
            first_arg = parts[1].upper()
            if first_arg in ["TG", "TELEGRAM", "#TG"]:
                target_apps = ["Telegram"]
                search_query = " ".join(parts[2:]).strip().upper()
            elif first_arg in ["WS", "WA", "WHATSAPP", "#WS"]:
                target_apps = ["WhatsApp"]
                search_query = " ".join(parts[2:]).strip().upper()
            else:
                search_query = " ".join(parts[1:]).strip().upper()

        acc_target = next((a for a in ACCOUNTS if a.get("csrf_token")), None)
        if not acc_target:
            send_msg(chat_id, "❌ Tidak ada akun aktif"); return

        session = acc_target["session"]
        now_ms = int(time.time() * 1000)
        all_results_raw = []
        unique_ranges_count = set()

        for app_name in target_apps:
            params = {"app": app_name, "draw": "1", "start": "0", "length": "400",
                      "search[value]": search_query, "_": str(now_ms)}
            headers = {"X-Requested-With": "XMLHttpRequest",
                       "Accept": "application/json, text/javascript, */*; q=0.01",
                       "Referer": f"{BASE}/portal/sms/test/sms?app={app_name}"}
            resp = session.get(TEST_SMS_URL, params=params, headers=headers, timeout=30)
            items = resp.json().get("data", [])
            tag_service = "#WS" if app_name == "WhatsApp" else "#TG"

            for item in items:
                range_raw = item.get("range", "") if isinstance(item, dict) else ""
                if not range_raw: continue
                range_clean = BeautifulSoup(str(range_raw), "html.parser").text.strip()
                m = re.search(r"^(.*?)\s*\(?(\d{2,})\)?$", range_clean)
                country = m.group(1).strip().upper() if m else range_clean.strip().upper()
                code = m.group(2) if m else "N/A"
                if search_query and search_query not in country: continue
                if code != "N/A": unique_ranges_count.add(f"{tag_service}_{code}")

                all_text = BeautifulSoup(
                    " ".join([str(v) for v in (item.values() if isinstance(item, dict) else item)]),
                    "html.parser"
                ).text.strip().lower()
                m_sec = re.search(r"(\d+)\s*(sec|detik)", all_text)
                m_min = re.search(r"(\d+)\s*(min|menit)", all_text)
                m_hr  = re.search(r"(\d+)\s*(hour|jam)", all_text)
                diff = 0
                if "just now" in all_text or "baru saja" in all_text: diff = 0
                elif m_sec: diff = int(m_sec.group(1))
                elif m_min: diff = int(m_min.group(1)) * 60
                elif m_hr:  diff = int(m_hr.group(1)) * 3600
                all_results_raw.append({"diff": diff, "tag": tag_service, "country": country, "code": code})

        if not all_results_raw:
            send_msg(chat_id, "❌ Data tidak ditemukan."); return

        unique_map = {}
        for item in all_results_raw:
            key = (item["tag"], item["country"], item["code"])
            if key not in unique_map or item["diff"] < unique_map[key]["diff"]:
                unique_map[key] = item

        final = sorted(unique_map.values(), key=lambda x: x["diff"])
        lines = []
        for item in final:
            d = item["diff"]
            wt = f"{d} detik" if d < 60 else (f"{d//60} menit {d%60} detik" if d < 3600 else f"{d//3600} jam {(d%3600)//60} menit")
            lines.append(f"{item['tag']} {item['country']}  {item['code']}  {wt}")

        msg = f"📱 RANGE TERBARU ({len(unique_ranges_count)} unik):\n\n"
        msg += "\n".join(lines[:40])
        if len(lines) > 40: msg += f"\n\n... dan {len(lines)-40} lainnya"
        send_msg(chat_id, msg)
    except Exception as e:
        send_msg(chat_id, f"❌ Error cek range: {e}")

# ================= LOGIN =================
def login(acc):
    session = acc["session"]
    try:
        r = session.get(LOGIN_URL)
        soup = BeautifulSoup(r.text, "html.parser")
        csrf_token = soup.find("input", {"name": "_token"})["value"]
        acc["csrf_token"] = csrf_token
        session.post(LOGIN_URL, data={"_token": csrf_token, "email": acc["USERNAME"], "password": acc["PASSWORD"]})
        print(f"[✓] Login Berhasil: {acc['USERNAME']}")
    except Exception as e:
        print(f"[X] Gagal login untuk {acc['USERNAME']}: {e}")

# ================= GET DATA =================
def get_ranges(acc):
    today = datetime.now().strftime("%Y-%m-%d")
    r = acc["session"].post(GET_RANGE_URL, data={"_token": acc["csrf_token"], "from": today, "to": today})
    soup = BeautifulSoup(r.text, "html.parser")
    ranges = []
    for div in soup.find_all("div", onclick=True):
        if "toggleRange" in div["onclick"]:
            try: ranges.append(div["onclick"].split("'")[1])
            except: pass
    return list(set(ranges))

def get_numbers(acc, rng):
    today = datetime.now().strftime("%Y-%m-%d")
    r = acc["session"].post(GET_NUMBER_URL, data={"_token": acc["csrf_token"], "start": today, "end": today, "range": rng})
    soup = BeautifulSoup(r.text, "html.parser")
    numbers = []
    for div in soup.find_all("div", onclick=True):
        try:
            val = div["onclick"].split("'")[1]
            if val and val != rng: numbers.append(val)
        except: pass
    return list(set(numbers))

def get_sms(acc, rng, number):
    today = datetime.now().strftime("%Y-%m-%d")
    r = acc["session"].post(GET_SMS_URL, data={"_token": acc["csrf_token"], "start": today, "end": today, "Number": number, "Range": rng})
    soup = BeautifulSoup(r.text, "html.parser")
    sms_texts = [p.get_text(strip=True) for p in soup.find_all("p")]
    if not sms_texts:
        raw_text = soup.get_text(separator="\n", strip=True)
        if raw_text: sms_texts = raw_text.split('\n')
    return list(set(sms_texts))

# ================= LISTENER COMMAND =================
def listen_command():
    global last_update_id
    while True:
        try:
            r = tg_session.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": last_update_id + 1, "timeout": 30}, timeout=35
            )
            data = r.json()
            for upd in data.get("result", []):
                last_update_id = upd["update_id"]

                # ===== CALLBACK =====
                if "callback_query" in upd:
                    try:
                        cb = upd["callback_query"]
                        data_cb = cb.get("data", "")
                        chat_id = cb["message"]["chat"]["id"]
                        msg_id  = cb["message"]["message_id"]

                        if data_cb.startswith("ADDNUM"):
                            _, target, email = data_cb.split("|", 2)
                            delete_msg(chat_id, msg_id)
                            success, result = addnum_api(target, email)
                            if success:
                                send_msg(chat_id, f"✅ ADD NUMBER BERHASIL\n\n📌 Range: {result}\n📧 {mask_email(email)}")
                            else:
                                send_msg(chat_id, f"❌ GAGAL: {result}")

                        elif data_cb.startswith("DELNUMALL"):
                            _, email = data_cb.split("|", 1)
                            delete_msg(chat_id, msg_id)
                            acc_target = next((a for a in ACCOUNTS if a["USERNAME"] == email), None)
                            if not acc_target:
                                send_msg(chat_id, "❌ Akun tidak ditemukan"); continue
                            ok, res = return_all_number(acc_target)
                            send_msg(chat_id, f"✅ DELETE ALL BERHASIL\n📧 {mask_email(email)}" if ok else f"❌ GAGAL: {res[:100]}")

                        elif data_cb.startswith("EXPORT"):
                            _, email = data_cb.split("|", 1)
                            delete_msg(chat_id, msg_id)
                            # 🔥 Jalankan di thread agar tidak block listener
                            threading.Thread(target=export_numbers_ivas, args=(chat_id, email), daemon=True).start()

                    except Exception as e:
                        print(f"Callback error: {e}")
                    continue

                if "message" not in upd:
                    continue

                msg     = upd["message"]
                text    = msg.get("text", "") or ""
                chat_id = msg["chat"]["id"]
                msg_id  = msg["message_id"]

                if text.strip().startswith("/start"):
                    handle_start(chat_id)
                elif text.startswith("/cekivas"):
                    cek_ivas(chat_id)
                elif text.startswith("/statsms"):
                    stats_sms(chat_id)
                elif text.startswith("/cekrange"):
                    cek_range_command(chat_id, text)
                elif text.startswith("/addnum"):
                    addnum_command(text, chat_id, msg_id)
                elif text.startswith("/delnumall"):
                    delnumall_command(chat_id)
                elif text.startswith("/ambilfile"):
                    ambilfile_command(chat_id)

        except Exception as e:
            print("[LISTENER ERROR]", e)
        time.sleep(2)

# ================= BOT LOOP =================
def run_bot():
    for acc in ACCOUNTS:
        acc["session"] = httpx.Client(
            follow_redirects=True, timeout=10,
            headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
        )
        acc["session"].cookies.update(acc["COOKIES"])
        acc["csrf_token"] = ""
        login(acc)

    print("[✓] Bot Multi-Akun Berjalan..")

    while True:
        for acc in ACCOUNTS:
            try:
                if not acc.get("csrf_token"):
                    continue

                for rng in get_ranges(acc):
                    country = clean_country(rng)
                    flag = get_flag(country)

                    for num in get_numbers(acc, rng):
                        for sms in get_sms(acc, rng, num):
                            if "$" in sms and len(sms) < 15: continue
                            otp = extract_otp(sms)
                            if not otp: continue
                            unique_id = f"{num}-{otp}"
                            if unique_id in sent_cache: continue

                            service = extract_service_short(sms)
                            msg = (
                                f"<b>{flag} {country} | {service} | {format_phone_number(num)}</b>\n"
                                f"<i>Penerima: {mask_email(acc['USERNAME'])}</i>\n"
                            )
                            tg_send(msg, otp)
                            sent_cache.add(unique_id)
                            sms_stats["total_sms"] += 1
                            sms_stats["total_otp"] += 1
                            sms_stats["total_number"].add(num)
                            print(f"[{acc['USERNAME']}] [Otp Terkirim] {otp} ke {num}")

                time.sleep(2)
            except Exception as e:
                print(f"[ERROR pada {acc['USERNAME']}]", e)
                time.sleep(2)

        time.sleep(5)

# ================= START =================
threading.Thread(target=listen_command, daemon=True).start()
run_bot()