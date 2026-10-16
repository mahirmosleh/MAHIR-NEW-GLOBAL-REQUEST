#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MAHIR SQUAD BOT — PREMIUM CYBERPUNK EDITION (FIXED)
# ✅ Auto Update · Auto Emote · Auto Animation · Dual Recruit
# ✅ Web Account Manager · Stop All · Auto Kick
# ✅ Web-Editable Join Emotes · Bot Self-Emote Toggle
# ✅ Premium Cyberpunk RGB Dashboard
# ✅ Infinite Retry (Never Crash on Version Fetch)

import subprocess, sys, importlib, os, ssl, json, time, random, asyncio, threading, gc, re, struct, base64
from collections import deque
from datetime import datetime
import gzip, http.client, uuid, requests, urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import aiohttp, jwt
from rich.console import Console
from rich.panel import Panel
from cfonts import render
from protobuf_decoder.protobuf_decoder import Parser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
console = Console()

# ========== LIVE LOG BUFFER ==========
log_buffer = deque(maxlen=500)
log_lock = threading.Lock()
_orig_console_print = console.print

def _patched_console_print(*args, **kwargs):
    try: _orig_console_print(*args, **kwargs)
    except Exception: pass
    try:
        text = " ".join(str(a) for a in args)
        text = re.sub(r'\[/?[a-zA-Z0-9_#= ]+\]', '', text)
        ts = datetime.now().strftime("%H:%M:%S")
        with log_lock: log_buffer.append(f"[{ts}] {text}")
    except Exception: pass

console.print = _patched_console_print

# ================================================================
#   AUTO UPDATE (INFINITE RETRY — NEVER CRASH)
# ================================================================
try:
    from google_play_scraper import app as _gps_app
    _GPS_AVAILABLE = True
except Exception:
    _GPS_AVAILABLE = False
    console.print("[bold yellow]⚠ google-play-scraper not installed[/bold yellow]")

DYNAMIC_SERVER_URL = CURRENT_OB = FREEFIRE_VERSION_NAME = STORE_VERSION = DYNAMIC_CLIENT_URL = login_url = ob = version = ""

def _wait_for_gps(module_check_interval: int = 30):
    """google_play_scraper না থাকলে infinite loop এ wait করবে"""
    global _GPS_AVAILABLE
    while not _GPS_AVAILABLE:
        console.print("[bold red]❌ google-play-scraper missing! Installing...[/bold red]")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "google-play-scraper", "--quiet"])
            import importlib
            import google_play_scraper
            importlib.reload(google_play_scraper)
            from google_play_scraper import app as _gps_app
            globals()['_gps_app'] = _gps_app
            _GPS_AVAILABLE = True
            console.print("[bold green]✅ google-play-scraper installed![/bold green]")
        except Exception as e:
            console.print(f"[bold red]❌ Auto-install failed: {e}[/bold red]")
            console.print(f"[bold yellow]⏳ Retrying in {module_check_interval}s...[/bold yellow]")
            time.sleep(module_check_interval)

def AuToUpDaTE(retry_delay: int = 5):
    """
    Infinite retry — bot কখনো crash করবে না।
    যতক্ষণ পর্যন্ত লাইভ ডাটা না পায়, ততক্ষণ চেষ্টা করতে থাকবে।
    """
    if not _GPS_AVAILABLE:
        _wait_for_gps()

    attempt = 0
    while True:
        attempt += 1
        try:
            console.print(f"[cyan]🌐 [{attempt}] Fetching live version from Google Play...[/cyan]")
            data = _gps_app('com.dts.freefireth', lang="fr", country='CA')
            store_version = data.get("version")
            if not store_version:
                raise RuntimeError("Empty store version from Google Play")

            api_url = (
                f"https://version.ggwhitehawk.com/live/ver.php?"
                f"version={store_version}&lang=fr&device=android&channel=android"
            )
            console.print(f"[cyan]🔗 Requesting: {api_url}[/cyan]")

            r = requests.get(api_url, timeout=25)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code} from version API")

            try:
                j = r.json()
            except Exception:
                raise RuntimeError(f"Invalid JSON response: {r.text[:120]}")

            su  = j.get('server_url')
            obv = j.get('latest_release_version')
            rp  = j.get('remote_version')

            missing = [n for n, v in [("server_url", su), ("ob", obv), ("remote", rp)] if not v]
            if missing:
                raise RuntimeError(f"Missing fields: {missing}")

            console.print("[bold green]✅ Live data fetched successfully![/bold green]")
            return str(su).strip(), str(obv).strip(), str(rp).strip(), str(store_version).strip()

        except KeyboardInterrupt:
            console.print("\n[bold red]⚠️ User interrupted. Exiting...[/bold red]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold yellow]⚠️ Attempt {attempt} failed: {e}[/bold yellow]")
            console.print(f"[bold cyan]⏳ Retrying in {retry_delay}s... (Bot will NOT crash)[/bold cyan]")
            time.sleep(retry_delay)

_tmp = AuToUpDaTE()
DYNAMIC_SERVER_URL    = _tmp[0].rstrip('/')
CURRENT_OB            = _tmp[1]
FREEFIRE_VERSION_NAME = _tmp[2]
STORE_VERSION         = _tmp[3]
login_url = DYNAMIC_SERVER_URL
ob = CURRENT_OB
version = FREEFIRE_VERSION_NAME
DYNAMIC_CLIENT_URL = DYNAMIC_SERVER_URL.replace("loginbp", "clientbp")

console.print(f"""
[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 LIVE DATA LOADED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 OB         : [white]{CURRENT_OB}[/white]
🛒 Store Ver  : [white]{STORE_VERSION}[/white]
🎮 Remote Ver : [white]{FREEFIRE_VERSION_NAME}[/white]
🌐 Server     : [white]{DYNAMIC_SERVER_URL}[/white]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

TIMEOUT = aiohttp.ClientTimeout(total=30)
WEB_CONFIG_FILE = "web_config.json"
ACCOUNTS_FILE = "accounts.txt"

# ================================================================
#   EMOTE EQUIP SYSTEM
# ================================================================
EMOTE_DATA_HEX = "CA F6 83 22 2A 25 C7 BE FE B5 1F 59 54 4D B3 13"
EMOTE_BINARY = bytes.fromhex(EMOTE_DATA_HEX.replace(" ", ""))
REGION_SERVER_MAP = {
    "BD": DYNAMIC_CLIENT_URL, "IND": "https://client.ind.freefiremobile.com",
    "PK": DYNAMIC_CLIENT_URL, "ME": DYNAMIC_CLIENT_URL, "VN": DYNAMIC_CLIENT_URL,
    "SG": DYNAMIC_CLIENT_URL, "ID": DYNAMIC_CLIENT_URL, "TH": DYNAMIC_CLIENT_URL,
    "BR": "https://client.us.freefiremobile.com", "NA": "https://client.us.freefiremobile.com",
    "US": "https://client.us.freefiremobile.com", "RU": DYNAMIC_CLIENT_URL,
}
console.print(f"[green]✅ Region Servers Synced: {DYNAMIC_CLIENT_URL}[/green]")

def decode_jwt_noverify(token: str):
    try:
        parts = token.split(".")
        if len(parts) < 2: return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64).decode())
    except Exception: return None

async def equip_emote_on_login(jwt_token, logger=None):
    log = logger or console.print
    try:
        payload = decode_jwt_noverify(jwt_token)
        if not payload: log("[red]❌ Emote Equip: Invalid JWT[/red]"); return
        region_code = payload.get("noti_region") or payload.get("lock_region")
        if not region_code: log("[red]❌ Emote Equip: Region not found[/red]"); return
        base_url = REGION_SERVER_MAP.get(region_code.upper())
        if not base_url: log(f"[red]❌ Emote Equip: No mapping for {region_code}[/red]"); return
        url = f"{base_url}/ChooseEmote"
        headers = {
            "Accept-Encoding": "gzip", "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {jwt_token}",
            "ReleaseVersion": CURRENT_OB,
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; G011A Build/PI)",
            "X-GA": "v1 1",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=EMOTE_BINARY, ssl=False, timeout=10) as resp:
                if resp.status == 200: log(f"[bold green]✅ Emote Equip OK ({region_code})[/bold green]")
                else: log(f"[bold yellow]⚠ Emote Equip Failed ({resp.status})[/bold yellow]")
    except Exception as e: log(f"[red]❌ Emote Equip Error: {e}[/red]")

# ========== GLOBAL TRACKING ==========
welcome_tracking = {}
running_bots = set()
running_bots_lock = threading.Lock()
bot_status = {}
bot_lock = threading.Lock()
online_count = 0
total_accounts = 0
active_accounts = []
active_lock = threading.Lock()

# ========== SIGNAL SYSTEM ==========
signal_lock = threading.Lock()
_restart_timestamp = 0
_recreate_timestamp = 0
_stop_all_flag = False
_stop_all_lock = threading.Lock()

def trigger_restart_all():
    global _restart_timestamp
    with signal_lock: _restart_timestamp = time.time()

def trigger_recreate_all():
    global _recreate_timestamp
    with signal_lock: _recreate_timestamp = time.time()

def get_restart_timestamp():
    with signal_lock: return _restart_timestamp

def get_recreate_timestamp():
    with signal_lock: return _recreate_timestamp

def set_stop_all(v: bool):
    global _stop_all_flag
    with _stop_all_lock: _stop_all_flag = bool(v)

def is_stopped() -> bool:
    with _stop_all_lock: return _stop_all_flag

# ================================================================
#   SAFE EXTRACTORS
# ================================================================
def safe_get_data(f):
    if f is None: return None
    if isinstance(f, dict): return f.get("data")
    return f

def safe_get_int(f, default=None):
    v = safe_get_data(f)
    if v is None: return default
    if isinstance(v, bool): return int(v)
    if isinstance(v, int): return v
    if isinstance(v, (str, bytes, bytearray)):
        try: return int(v)
        except: return default
    return default

def safe_get_str(f, default=""):
    v = safe_get_data(f)
    if v is None: return default
    if isinstance(v, str): return v
    if isinstance(v, (bytes, bytearray)):
        try: return v.decode('utf-8', errors='ignore')
        except: return default
    return str(v)

def safe_dict(f):
    v = safe_get_data(f)
    return v if isinstance(v, dict) else {}

# ================================================================
#   POOLS
# ================================================================
AUTO_BUNDLE_POOL = [914000002, 914000003, 914038001, 914039001, 914042001, 914044001, 914047001, 914047002, 914048001, 914050001, 914051001, 914053001]
ANIMATION_POOL = AUTO_BUNDLE_POOL[:]
DEFAULT_JOIN_EMOTES = [909049013, 909045010, 909000020, 909000010, 909055004, 909055005, 909000062]

_last_bundle_time = {}
_BUNDLE_COOLDOWN = 3.0

# ================================================================
#   DEFAULT CONFIG
# ================================================================
DEFAULT_WELCOME_MSG = (
    "[C][FFD700]❖━━━━━━━━━━━━━━━❖\n"
    "[C][FFFFFF]Hᴇʟʟᴏ [FF0000]{user_name}\n"
    "[C][00FF7F]Wᴇʟᴄᴏᴍᴇ ᴛᴏ Oᴜʀ Sǫᴜᴀᴅ! ✨\n"
    "[C][FFD700]❖━━━━━━━━━━━━━━━❖\n"
    "[C][B][00FFFF]🔥 MAHIR AUTOMATION BOT 🔥\n"
    "[C][FFD700]────────────────\n"
    "[C][FFFF00] Type [00FF00]/store [FFFF00]to view items\n"
    "[C][FFFF00] Type [00FF00]/app [FFFF00]for Android App\n"
    "[C][FFD700]────────────────\n"
    "[C][00BFFF]📢 Telegram : [FFFFFF]@THEMAHIRWORLD\n"
    "[C][FF69B4]🎬 TikTok   : [FFFFFF]@MAHIR__222\n"
    "[C][FFD700]❖━━━━━━━━━━━━━━━❖"
)

DEFAULT_COMMANDS = {
    "/store": {"enabled": True, "match": "contains", "type": "message",
        "response": "[C][FFD700]⚡ MAHIR BOT STORE ⚡\n[C][00FF00]🤖 TCP BOT: [FFFF00]500 BDT\n[C][00FF00]🌐 Website: [FFFF00]mahir.xo.je\n[C][00FF00]👤 Owner: [FFFF00]@MAHIR0208"},
    "/app": {"enabled": True, "match": "contains", "type": "message",
        "response": "[C][B][00FFFF]📱 MAHIR TCP APP\n[C][00FF00]https://www.mediafire.com/file/lvykrek51q17hae/MAHIR_TCP.apk"},
    "st": {"enabled": True, "match": "exact", "type": "recruit_squad"}
}

# ================================================================
#   WEB CONFIG
# ================================================================
web_config = {
    "squad_size": 4,
    "world_recruit_count": 3,
    "world_recruit_type": "1",
    "squad_lifetime_sec": 5,
    "auto_recreate": True,
    "welcome_msg": DEFAULT_WELCOME_MSG,
    "auto_recruit_on_join": True,
    "auto_recruit_on_leave": True,
    "recruit_delay_sec": 1.5,
    "auto_bundle_on_join": True,
    "bundle_count_on_join": 2,
    "auto_animation": True,
    "animation_interval_sec": 10,
    "auto_emote_on_join": True,
    "emote_join_delay_sec": 0.5,
    "join_emote_pool": DEFAULT_JOIN_EMOTES[:],
    "auto_kick_on_join": False,
    "kick_delay_sec": 1.0,
    "kick_msg": "[B][C][FF0000]🚫 ACCESS DENIED!\n[FFFFFF]You have been auto-kicked.",
    "auto_welcome_on_join": True,
    "welcome_delay_sec": 0.5,
    "bot_self_emote_enabled": False,
    "bot_self_emote_pool": DEFAULT_JOIN_EMOTES[:],
    "bot_self_emote_interval": 8.0,
    "commands": {},
}
web_config_lock = threading.Lock()

def to_json_safe(obj):
    if isinstance(obj, dict): return {str(k): to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list): return [to_json_safe(i) for i in obj]
    if isinstance(obj, (bytes, bytearray)): return {"__hex__": bytes(obj).hex()}
    return obj

def from_json_safe(obj):
    if isinstance(obj, dict):
        if "__hex__" in obj and len(obj) == 1:
            try: return bytes.fromhex(obj["__hex__"])
            except: return b""
        r = {}
        for k, v in obj.items():
            try: key = int(k)
            except: key = k
            r[key] = from_json_safe(v)
        return r
    if isinstance(obj, list): return [from_json_safe(i) for i in obj]
    return obj

def load_web_config():
    try:
        saved = {}
        if os.path.exists(WEB_CONFIG_FILE):
            with open(WEB_CONFIG_FILE, "r", encoding="utf-8") as f: saved = json.load(f)
        with web_config_lock:
            int_fields = {
                "squad_size": (3, 5), "world_recruit_count": (1, 10),
                "squad_lifetime_sec": (5, 3600), "bundle_count_on_join": (1, 5),
                "animation_interval_sec": (5, 300),
            }
            for k, (lo, hi) in int_fields.items():
                v = saved.get(k)
                if isinstance(v, int) and lo <= v <= hi: web_config[k] = v

            float_fields = {
                "recruit_delay_sec": (0.5, 30), "emote_join_delay_sec": (0.1, 30),
                "kick_delay_sec": (0.1, 30), "welcome_delay_sec": (0.1, 30),
                "bot_self_emote_interval": (1, 300),
            }
            for k, (lo, hi) in float_fields.items():
                v = saved.get(k)
                if isinstance(v, (int, float)) and lo <= float(v) <= hi: web_config[k] = float(v)

            wrt = saved.get("world_recruit_type")
            if wrt in ("1", "2", "3", "half", "random"): web_config["world_recruit_type"] = wrt

            bool_fields = [
                "auto_recreate", "auto_recruit_on_join", "auto_recruit_on_leave",
                "auto_bundle_on_join", "auto_animation", "auto_emote_on_join",
                "auto_kick_on_join", "auto_welcome_on_join", "bot_self_emote_enabled"
            ]
            for bf in bool_fields:
                v = saved.get(bf)
                if isinstance(v, bool): web_config[bf] = v

            wm = saved.get("welcome_msg")
            if isinstance(wm, str) and wm: web_config["welcome_msg"] = wm

            km = saved.get("kick_msg")
            if isinstance(km, str) and km: web_config["kick_msg"] = km

            jep = saved.get("join_emote_pool")
            if isinstance(jep, list):
                cleaned = []
                for x in jep:
                    try: cleaned.append(int(x))
                    except: pass
                if cleaned: web_config["join_emote_pool"] = cleaned

            bsep = saved.get("bot_self_emote_pool")
            if isinstance(bsep, list):
                cleaned = []
                for x in bsep:
                    try: cleaned.append(int(x))
                    except: pass
                if cleaned: web_config["bot_self_emote_pool"] = cleaned

            cmds_saved = saved.get("commands", {})
            commands = {}
            for name, default_val in DEFAULT_COMMANDS.items():
                if name in cmds_saved:
                    try:
                        loaded = from_json_safe(cmds_saved[name])
                        commands[name] = loaded if isinstance(loaded, dict) else dict(default_val)
                    except: commands[name] = dict(default_val)
                else: commands[name] = dict(default_val)
            for name, val in cmds_saved.items():
                if name not in commands:
                    try:
                        loaded = from_json_safe(val)
                        if isinstance(loaded, dict): commands[name] = loaded
                    except: pass
            web_config["commands"] = commands
        console.print(f"[bold green]✅ Config Loaded[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Config Load Error: {e}[/bold red]")
        with web_config_lock:
            web_config["commands"] = {k: dict(v) for k, v in DEFAULT_COMMANDS.items()}

def save_web_config():
    try:
        with web_config_lock:
            data = {k: web_config[k] for k in [
                "squad_size", "world_recruit_count", "world_recruit_type",
                "squad_lifetime_sec", "auto_recreate", "welcome_msg",
                "auto_recruit_on_join", "auto_recruit_on_leave", "recruit_delay_sec",
                "auto_bundle_on_join", "bundle_count_on_join", "auto_animation",
                "animation_interval_sec", "auto_emote_on_join", "emote_join_delay_sec",
                "join_emote_pool", "auto_kick_on_join", "kick_delay_sec", "kick_msg",
                "auto_welcome_on_join", "welcome_delay_sec",
                "bot_self_emote_enabled", "bot_self_emote_pool", "bot_self_emote_interval",
            ]}
            data["commands"] = to_json_safe(web_config["commands"])
        with open(WEB_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        console.print(f"[bold red]Config Save Error: {e}[/bold red]"); return False

# ================================================================
#   ACCOUNT STORAGE
# ================================================================
def load_accounts(file_path=ACCOUNTS_FILE):
    try:
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f: f.write("")
            return {}
        with open(file_path, "r", encoding="utf-8") as f: lines = f.readlines()
        accounts = {}
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"): continue
            sep = ":" if ":" in line else ("|" if "|" in line else None)
            if sep is None: continue
            parts = line.split(sep, 1)
            if len(parts) != 2: continue
            uid, pwd = parts[0].strip(), parts[1].strip()
            if uid.isdigit() and pwd: accounts[uid] = pwd
        return accounts
    except Exception as e:
        console.print(f"[bold red]Acc Load Error: {e}[/bold red]"); return {}

def save_accounts(accs, file_path=ACCOUNTS_FILE):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for uid, pwd in accs.items(): f.write(f"{uid}:{pwd}\n")
        return True
    except Exception as e:
        console.print(f"[bold red]Acc Save Error: {e}[/bold red]"); return False

def save_accounts_raw(text, file_path=ACCOUNTS_FILE):
    try:
        with open(file_path, "w", encoding="utf-8") as f: f.write(text)
        return True
    except Exception as e:
        console.print(f"[bold red]Acc Save Error: {e}[/bold red]"); return False

# ================================================================
#   PROTOBUF HELPERS
# ================================================================
def read_varint(data, pos):
    result = shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
    return result, pos

def parse_pb(data):
    fields = {}; pos = 0; n = len(data)
    while pos < n:
        try: key, pos = read_varint(data, pos)
        except: break
        fn = key >> 3; wt = key & 0x07
        try:
            if wt == 0: val, pos = read_varint(data, pos)
            elif wt == 2:
                ln, pos = read_varint(data, pos); val = data[pos:pos + ln]; pos += ln
            elif wt == 5: val = data[pos:pos + 4]; pos += 4
            elif wt == 1: val = data[pos:pos + 8]; pos += 8
            else: break
        except: break
        fields.setdefault(fn, []).append(val)
    return fields

def extract_player_name(login_data_bytes):
    try:
        fields = parse_pb(login_data_bytes)
        for fn in [4, 3, 5, 6]:
            if fn in fields:
                nv = fields[fn][0]
                if isinstance(nv, (bytes, bytearray)):
                    d = nv.decode('utf-8', errors='ignore')
                    if d and len(d) < 60 and not d.startswith("0OuCe") and not d.startswith("eyJ") and all(c.isprintable() or c in '\u200b\u200c\u200d' for c in d):
                        return d
    except: pass
    return None

def Uaa():
    versions = ['5.0.1B2','5.1.0P1','5.2.0B1']
    models = ['SM-A125F','Redmi 9A','POCO M3']
    return f"GarenaMSDK/{random.choice(versions)}({random.choice(models)};Android {random.choice(['11','12','13'])};en-US;USA;)"

Hr = {
    'User-Agent': Uaa(), 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1", 'ReleaseVersion': ob
}

def xBunnEr():
    """Returns working Avatar IDs as Integer"""
    return random.choice([
        902000011, 902000013, 902047016, 902049015,
        902000154, 902000127, 902000207, 902000305,
        902037031, 902042011, 902053016, 902053018
    ])

def update_bot_info(uid, **kwargs):
    with bot_lock:
        if uid not in bot_status:
            bot_status[uid] = {"guest_uid": uid, "account_uid": "Loading...", "status": "🔄 Initializing...",
                "last_squad_id": "None", "last_active": "N/A", "squad_active": False}
        bot_status[uid].update(kwargs)

def update_active_account(uid, **kwargs):
    with active_lock:
        global online_count
        for acc in active_accounts:
            if acc['uid'] == uid:
                acc.update(kwargs); return
        active_accounts.append({
            'uid': uid, 'bot_uid': kwargs.get('bot_uid', uid),
            'name': kwargs.get('name', 'Unknown'), 'region': kwargs.get('region', 'BD'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'squad_id': kwargs.get('squad_id', 'Pending...'),
            'squad_members': kwargs.get('squad_members', '0/0')
        })

def remove_active_account(uid):
    global online_count
    with active_lock:
        active_accounts[:] = [a for a in active_accounts if a['uid'] != uid]
        if online_count > 0: online_count -= 1

def Fix_PackEt(parsed_results):
    rd = {}
    for r in parsed_results:
        fd = {'wire_type': r.wire_type}
        if r.wire_type in ["varint", "string", "bytes"]: fd['data'] = r.data
        elif r.wire_type == 'length_delimited': fd["data"] = Fix_PackEt(r.data.results)
        rd[r.field] = fd
    return rd

def DeCode_PackEt(input_text):
    try: return json.dumps(Fix_PackEt(Parser().parse(input_text)))
    except Exception: return None

async def EnC_Vr(N):
    if N < 0: return b''
    H = []
    while True:
        b = N & 0x7F; N >>= 7
        if N: b |= 0x80
        H.append(b)
        if not N: break
    return bytes(H)

async def CrEaTe_VarianT(fn, val):
    return await EnC_Vr((fn<<3)|0) + await EnC_Vr(val)

async def CrEaTe_LenGTh(fn, val):
    ev = val.encode() if isinstance(val, str) else val
    return await EnC_Vr((fn<<3)|2) + await EnC_Vr(len(ev)) + ev

async def CrEaTe_ProTo(fields):
    packet = bytearray()
    for f, v in fields.items():
        if isinstance(f, str):
            try: f = int(f)
            except: continue
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    nested = await CrEaTe_ProTo(item)
                    packet.extend(await CrEaTe_LenGTh(f, nested))
        elif isinstance(v, dict):
            nested = await CrEaTe_ProTo(v)
            packet.extend(await CrEaTe_LenGTh(f, nested))
        elif isinstance(v, int):
            packet.extend(await CrEaTe_VarianT(f, v))
        elif isinstance(v, (str, bytes)):
            packet.extend(await CrEaTe_LenGTh(f, v))
    return bytes(packet)

async def DecodE_HeX(H):
    F = str(hex(H))[2:]
    return "0" + F if len(F) == 1 else F

async def EnC_PacKeT(HeX, K, V):
    return AES.new(K, AES.MODE_CBC, V).encrypt(pad(bytes.fromhex(HeX), 16)).hex()

async def GeneRaTePk(Pk, N, K, V):
    PkEnc = await EnC_PacKeT(Pk, K, V)
    _ = await DecodE_HeX(len(PkEnc) // 2)
    HeadEr = N+"000000" if len(_)==2 else N+"00000" if len(_)==3 else N+"0000" if len(_)==4 else N+"000"
    return bytes.fromhex(HeadEr + _ + PkEnc)

async def encrypt_packet(packet_hex, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(bytes.fromhex(packet_hex), AES.block_size)).hex()

# ================================================================
#   BUNDLE / ANIMATION
# ================================================================
async def mahir_animation_packet(animation_id, key, iv):
    try:
        fields = {1: 88, 2: {1: {1: int(animation_id)}}}
        packet_hex = (await CrEaTe_ProTo(fields)).hex()
        encrypted = await encrypt_packet(packet_hex, key, iv)
        pl = len(encrypted) // 2
        hl = format(pl, 'x')
        return bytes.fromhex("051500" + "0" * (6 - len(hl)) + hl + encrypted)
    except Exception as e:
        console.print(f"[red]animation err: {e}[/red]"); return None

async def Mahir_bundle_packet(bundle_id, key, iv, region="bd"):
    try:
        fields = {1: 88, 2: {1: {1: bundle_id, 2: 1}, 2: 2}}
        encrypted = await encrypt_packet((await CrEaTe_ProTo(fields)).hex(), key, iv)
        hl = await DecodE_HeX(len(encrypted) // 2)
        pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
        fh = f"{pt}000000" if len(hl) == 2 else f"{pt}00000" if len(hl) == 3 else f"{pt}0000" if len(hl) == 4 else f"{pt}000" if len(hl) == 5 else f"{pt}000000"
        return bytes.fromhex(fh + hl + encrypted)
    except Exception as e:
        console.print(f"[red]bundle err: {e}[/red]"); return None

async def Mahir_bundle_packet_2(bundle_id, key, iv, region="bd"):
    try:
        fields = {1: 88, 2: {1: {1: bundle_id, 2: 2}, 2: 2}}
        encrypted = await encrypt_packet((await CrEaTe_ProTo(fields)).hex(), key, iv)
        hl = await DecodE_HeX(len(encrypted) // 2)
        pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
        fh = f"{pt}000000" if len(hl) == 2 else f"{pt}00000" if len(hl) == 3 else f"{pt}0000" if len(hl) == 4 else f"{pt}000" if len(hl) == 5 else f"{pt}000000"
        return bytes.fromhex(fh + hl + encrypted)
    except Exception as e:
        console.print(f"[red]bundle2 err: {e}[/red]"); return None

# ================================================================
#   SQUAD PACKETS
# ================================================================
async def MAHIR_OPenSq(key, iv, region, version_):
    fields = {
        1: 1,
        2: {
            2: "\u0001", 3: 43, 4: 1, 5: "en",
            8: [{1: "IDC2", 2: 171, 3: "BD"}], 9: 1,
            10: "rYUW\u0017\t\u0007NR\u000f\u0005\u0004\\W\u0002\u000fV\u0004TPQ\u0003\u000f\u0005\u0004]\u0005\u000b\u0000\u0002W\u0005\r\nVY\u0004\u0007\u0007\u0007\u0017\u0001\bNQ\fS\u0005\u000e\u0006\f\u0005\rT\u0002\r\u0000TS\u0007U\u0004X\u0006RY\u0005\u0003\u0003SW\u0000\u000eQ\u0000^\u0014\u0003\u0004JXS\u000f\u0000g{gqfePblEZJp{_xU\bmQW\f\u0007\u000f\u0015\u0007H\\U^CHXh@Ax`\u000f~\rPN~Nz\\\u001fr_ckPU\u000b\u0015\u0005\u0003Ekfp\u007fcY\u0001nWV\u0002\u0005azE~N\u0007HTg\u0007w}@\u0002{\t\u0013\u0001NeNP]DUf|]ugINs{\u0001\\rAgB_\u0004fA]\u0004\r\u001a\u0000HpOv\\\u0005|gS\u0019\\A\u007fWW\u0003\u007fTqFGi\u0004Qr\u0019dW\u0004\u0011\rD\u0002yeZ]A\u0016a\u0007Ungeg\u0007E\\P\u001b\u000b\u0004\u0005dd\ff\r\u000f\u0017\t\u000fNRyZd\u0012tZ\fe\u0007AGv\u007fw]{P\u001c\u007f\u000ff\u0005ZJK\u0004\u0005\u0014\u0001Jgq\u001frymsB\u0001\u000fd`\u001bj~[}\u0004SDZ|IxKB\u0000\n\u0011\u0002J^`tjYN\u0007WQdE[PQ\u0002_{VP`S\t\u007f\u001dP\n\u000f\u000f\u0015\u0004\u0004L{V\u0003@yP[rgJ{Hpk\u0001\u000bw\u0001Agt_\u0003HxPc\u000b\u0017\u0005E`y\ngWoy\u0006S{A\u001b``Y\u0002Xzw}dDWOKsg\t\u0013\u000eNf\u000e\\`\u0005AwJc\u0003BM\u0001^\u0000R\u0002Qoh]tbS~`G\r\u001a\u0004HibAQ\u000f^XNt~kDUWaeaNqcLQ]Py[G\u0004",
            11: 1, 13: 1,
            14: {
                1: "08FAA33B035B3F16020859055555000200030001000000004AFA7572105C674946762514220104186fa2e8770e748c3f6a68ed75000000ff18470f0bcacfa16d",
                2: 681,
                3: {14: {11: "1106064f50055401030f03020403060155070d01540e060e020607540706030354530f041003064d715c46434b1f061f031e1205034a1c40677c5f554775755f504e677446185b584901534144685b67620f", 0: 72}},
                4: "x\\\\R", 6: 13, 7: {2: 80}, 8: version_, 9: 2, 10: 1,
                11: "03626253513677542b504e4635416456324b796f566c576a326567507844414c33507138513031762b66536c626a587648434e3348414e376c472b72474637794165676e72436b553671626b694538706f534e5a582b2f7a44675a547475465650542b384d69565a507151312b444b53576f786f6d592f7156394f76755254482b7154486a78486f664169734267564970454d454e6b4c326a4763445a4a5176416d687947356b7669564e544d71515745754b32324d4e384e4931424d437445395532415156694b667948314574412b32644536464b53773132554155596363372b7753652b66676c393742756544446a58496d6e35666d45444a51535948326644484c5650676755472f51794b776e77545151324a505265352f72314830616d374264424f556b712f523246734d635475516d47364c684a547a4379345774444245795268305754366f68532f785a48736a4c7a4366506378372f386a534133352b67787642657450397a4f6f463639344945386e6e77336b507344357a6e6337593649776b4142435761776f6d572b6948594f5939686d647632706975584168416d6d6a74496f5945444c6e506e5738616f7153304f74486b732f5a3953543252447345507a3343655438774e6874756d57634b4438585445376649386c305173726a772f4a57514f76394b50307257644538593375422f2b495836757675452b487a6a4853466c75726f33515432536567595758535854714674495a61454d476c51314b7639666c59525539465047366c30663045314f7a2b2b36324339644b664c4d39315a782f6f625938726a6e682b77524a3962636e544e41715466486f72354b714d3d"
            },
            19: 329, 21: "374f5219", 24: {1: 21}, 27: "a_6534489873065906362"
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', key, iv)

# ================================================================
#   UPDATED cHSq FUNCTIONS (FROM IMAGE)
# ================================================================
async def MAHIR_cHSq11(Nu, bot_uid, key, iv, region):
    fields = {1: 17, 2: {1: int(bot_uid), 2: 1, 3: 1, 4: 1, 5: "\x01", 8: 2}}
    pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, key, iv)

async def MAHIR_cHSq22(Nu, bot_uid, key, iv, region):
    fields = {1: 17, 2: {1: int(bot_uid), 2: 1, 3: 1, 4: 1, 5: "\x01", 8: 2}}
    pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, key, iv)

async def MAHIR_cHSq33(Nu, bot_uid, key, iv, region):
    fields = {1: 17, 2: {1: int(bot_uid), 2: 1, 3: 3, 4: 1, 5: "\x01", 8: 2}}
    pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, key, iv)

async def MAHIR_cHSq44(Nu, bot_uid, key, iv, region):
    fields = {1: 17, 2: {1: int(bot_uid), 2: 1, 3: 3, 4: 15, 5: "\x01", 8: 6, 18: 42}}
    pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, key, iv)

async def MAHIR_cHSq55(Nu, bot_uid, key, iv, region):
    fields = {1: 17, 2: {1: int(bot_uid), 2: 1, 3: 3, 4: 15, 5: "\x01", 8: 1}}
    pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, key, iv)

async def MAHIR_cHSq66(Nu, bot_uid, key, iv, region):
    fields = {1: 17, 2: {1: int(bot_uid), 2: 1, 3: 1, 4: 43, 5: "\x0b", 8: 1}}
    pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, key, iv)

async def MAHIR_cHSq77(Nu, bot_uid, key, iv, region):
    fields = {1: 17, 2: {1: int(bot_uid), 2: 1, 3: 3, 4: 46, 5: "\x0a", 7: 6, 8: 12, 16: 1}}
    pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, key, iv)

# ================================================================
#   WORLD RECRUIT + STOP REQUEST
# ================================================================
async def MAHIR_World_Recruit(tid, key, iv):
    try:
        fields = {1: 66, 2: {1: int(tid), 5: {}, 9: "", 10: 1}}
        return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', key, iv)
    except: return None

async def MAHIR_World_Recruit2(tid, key, iv):
    try:
        fields = {1: 66, 2: {1: int(tid), 5: "\u0007", 9: {}, 10: 1}}
        return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', key, iv)
    except: return None

async def MAHIR_World_Recruit3(tid, key, iv):
    try:
        fields = {1: 66, 2: {1: int(tid), 2: 301, 3: 303, 5: "\x07", 9: "", 10: 1}}
        return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', key, iv)
    except: return None

async def MAHIR_StopRequest(key, iv, region, bot_own_id):
    try:
        fields = {1: 70, 2: {1: int(bot_own_id)}}
        pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
        return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, key, iv)
    except: return None

async def MAHIR_LeaveSquad(key, iv, region, bot_own_id):
    fields = {1: 7, 2: {1: int(bot_own_id)}}
    pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, key, iv)

# ================================================================
#   SQUAD CHAT MESSAGE
# ================================================================
async def MAHIR_SendSquadMsg(squad_owner, message, bot_uid, key, iv):
    try:
        if not squad_owner or not bot_uid:
            return None
        squad_owner = int(squad_owner)
        bot_uid = int(bot_uid)
        avatar_id = xBunnEr()
        if not isinstance(avatar_id, int):
            avatar_id = 902000011

        msg_str = str(message)
        preview = msg_str[:15] if len(msg_str) > 15 else msg_str

        fields = {
            1: 1,
            2: {
                1: squad_owner,
                2: bot_uid,
                3: 0,
                4: msg_str,
                5: int(datetime.now().timestamp()),
                7: 6,
                9: {
                    1: f"[C][FF0000]{preview}",
                    2: avatar_id,
                    3: 2,
                    4: 330,
                    5: 800000304,
                    6: 66,
                    7: 66,
                    8: "MAHIR",
                    9: 66,
                    10: 1,
                    11: 1,
                    13: {1: 68, 2: 67},
                    14: {
                        1: 1158053040,
                        2: 8,
                        3: b"\x10\x15\x08\x0A\x0B\x15\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
                    }
                },
                10: "en",
                13: {3: 1},
                14: {}
            }
        }
        proto = await CrEaTe_ProTo(fields)
        pk = "080112" + (await EnC_Vr(len(proto))).hex() + proto.hex()
        return await GeneRaTePk(pk, '1215', key, iv)
    except Exception as e:
        console.print(f"[red]Squad msg err: {e}[/red]")
        return None

async def MAHIR_OpenSquadChat(squad_id, chat_code, key, iv):
    try:
        squad_id = int(squad_id)
        fields = {1: 3, 2: {1: squad_id, 2: 3, 3: "en", 4: str(chat_code)}}
        proto = await CrEaTe_ProTo(fields)
        pk = "080112" + (await EnC_Vr(len(proto))).hex() + proto.hex()
        return await GeneRaTePk(pk, '1215', key, iv)
    except Exception as e:
        console.print(f"[red]OpenSquadChat err: {e}[/red]")
        return None

async def Emote_k(TarGeT, idT, K, V, region):
    try:
        bot_self_id = int(BOT_OWN_ID) if 'BOT_OWN_ID' in globals() and globals().get('BOT_OWN_ID') else 0
    except:
        bot_self_id = 0
    fields = {1: 21, 2: {1: bot_self_id, 2: 909000001, 5: {1: int(TarGeT), 3: int(idT)}}}
    if region.lower() == "ind": pkt = '0514'
    elif region.lower() == "bd": pkt = "0519"
    else: pkt = "0515"
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pkt, K, V)

async def KickTarget(target_uid, key, iv):
    fields = {1: 35, 2: {1: int(target_uid)}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', key, iv)

# ================================================================
#   HELP MENU
# ================================================================
async def build_help_menu(nickname="User", bot_uid="0"):
    def pg(bdr, ttl_col, ttl, items):
        out = f"[b][c][{bdr}]┌───────────────┐\n[{ttl_col}][b][c]●  {ttl} ●\n[{bdr}][b][c]└───────────────┘\n"
        CLR = [("ff6600","ffd700","ffff55","00ffcc"),("aaff00","ff9944","ffffff","55ff99"),
               ("00ffaa","ff66bb","aaffff","ff88ff"),("00ccff","ffee88","ffaa44","44ddff")]
        for i, (d, c) in enumerate(items):
            bc, dc, ac, cc = CLR[i % 4]
            out += f"\n[{bc}]◆ [{dc}][b]{d}[/b] [{ac}]→  [{cc}]{c}"
        out += f"\n\n[{bdr}][b][c]◆───────────────◆"
        return out
    sn = nickname if nickname and nickname != "Unknown" else "User"
    pages = [f"[FF0000][b][c]◉\n[b][c][0dffd0]Hey {sn} Welcome To [ffffff]MAHIR [0dffd0] BOT\n[FF0000]• [0dffd0]বট চালাতে চাইলে [ffffff]help [0dffd0]লিখুন\n[FF0000][b][c]◉\n\n[C][B][0dffd0]+------ 📊 PLAYER PROFILE ------+\n[C][0dffd0] » Name        : [ffffff]{sn}\n[C][0dffd0] » UID         : [ffffff]{bot_uid}\n[C][B][0dffd0]+--------------------------------+"]
    pages.append(pg("ff9900", "ffee00", "GENERAL", [("Help Menu","help / hello"),("Welcome","HI"),("Time",".time"),("My Info","my id")]))
    pages.append(pg("00aaff", "00eeff", "SHOP", [("Store","/store"),("App","/app"),("Owner","MAHIR"),("Version",".ffv")]))
    pages.append(pg("ff44aa", "ff99dd", "SQUAD", [("Invite","/inv"),("Recruit","st"),("Size","/5  /6"),("Leave","/exit")]))
    pages.append(f"[b][c][FF1493]╔═══════════════════════╗\n[b][c][FF1493]║      👑 OWNER INFO 👑      ║\n[b][c][FF1493]╠═══════════════════════╣\n[b][c][FFFFFF]║ 👤 Name     : [FFD700]MAHIR\n[b][c][FFFFFF]║ 📱 Telegram : [00FFFF]@MAHIR0208\n[b][c][FFFFFF]║ 🎵 TikTok   : [00FFFF]@MAHIR__222\n[b][c][FFFFFF]║ 🌐 Website  : [00FFFF]mahir.xo.je\n[b][c][FF1493]╚═══════════════════════╝")
    return pages

# ================================================================
#   AUTH HELPERS
# ================================================================
async def GeNeRaTeAccAccess(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {"Host":"100067.connect.garena.com","User-Agent":Uaa(),"Content-Type":"application/x-www-form-urlencoded","Connection":"close"}
    data = {"uid":uid,"password":password,"response_type":"token","client_type":"2","client_secret":"2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3","client_id":"100067"}
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.post(url, headers=headers, data=data) as resp:
                if resp.status != 200: return None, None
                d = await resp.json()
                return d.get("open_id"), d.get("access_token")
    except: return None, None

def encode_varint(value):
    result = []
    if value < 0: value &= (1 << 64) - 1
    while True:
        byte = value & 0x7F; value >>= 7
        if value: byte |= 0x80
        result.append(byte)
        if not value: break
    return bytes(result)

def create_proto(fields):
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(value, dict):
            nested = create_proto(value)
            packet.extend(encode_varint((field << 3) | 2))
            packet.extend(encode_varint(len(nested))); packet.extend(nested)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    nested = create_proto(item)
                    packet.extend(encode_varint((field << 3) | 2))
                    packet.extend(encode_varint(len(nested))); packet.extend(nested)
        elif isinstance(value, int):
            packet.extend(encode_varint((field << 3) | 0)); packet.extend(encode_varint(value))
        elif isinstance(value, str):
            encoded = value.encode('utf-8')
            packet.extend(encode_varint((field << 3) | 2))
            packet.extend(encode_varint(len(encoded))); packet.extend(encoded)
        elif isinstance(value, bytes):
            packet.extend(encode_varint((field << 3) | 2))
            packet.extend(encode_varint(len(value))); packet.extend(value)
    return bytes(packet)

def encrypt_aes(hex_data: str) -> str:
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(bytes.fromhex(hex_data), AES.block_size)).hex()

async def EncRypTMajoRLoGin(open_id, access_token, version_):
    fields = {
        3: str(datetime.now())[:-7], 4: "free fire", 5: 1, 7: str(version_),
        8: "Android OS 11 / API-30 (RP1A.200720.011/230921V810)", 9: "Handheld",
        10: "Grameenphone", 11: "WIFI", 12: 1708, 13: 750, 14: "480",
        15: "ARM64 FP ASIMD AES | 2000 | 8", 16: 5767, 17: "Mali-G52 MC2",
        18: "OpenGL ES 3.2 v1.r26p0-01eac0.f143e3f9482527bbad36b3ec27f93e59",
        19: "Google|3f10d414-be33-4ac3-b9fc-fcbf47c183b5", 20: "103.200.36.134",
        21: "en", 22: str(open_id), 23: "4", 24: "Handheld",
        25: "INFINIX MOBILITY LIMITED Infinix X6812", 26: "BD", 29: str(access_token), 30: 1,
        41: "Grameenphone", 42: "WIFI", 57: "7428b253defc164018c604a1ebbfebdf",
        60: 110962, 61: 80611, 62: 1051, 64: 80829, 65: 110962, 66: 80829, 67: 110962, 73: 2,
        74: "/data/app/~~MxBbX9YA6AkFscre_RExgw==/com.dts.freefireth-hLOkTeh1Q46L_oLV4UXQTg==/lib/arm64", 76: 1,
        77: "b8e0cd5e295eee42f5860d3c86e483dd|/data/app/~~MxBbX9YA6AkFscre_RExgw==/com.dts.freefireth-hLOkTeh1Q46L_oLV4UXQTg==/base.apk",
        78: 3, 79: 2, 81: "64", 83: "2019121229", 85: 3, 86: "OpenGLES2", 87: 4095, 88: 4,
        91: {9: 65}, 92: 10508, 93: "android",
        94: "KqsHT76RdsVKvnpkirzc2FQs3eu0OZChfZxMTZn+Rjv06Ri2qeOQkyPcdk5JceWKmXhOFFUPuNy9S8esTr37yCT5piY32iUcehVw0bL4F4lzAmyD",
        95: 111207, 96: '{"cur_rate":[60,90],"support_etc2":false}', 97: 1, 98: 1, 99: "4", 100: "4",
        102: "B\\FFP[[\tf", 103: 1, 104: 28754, 105: 1,
        106: "https://dl.ak.freefiremobile.com/live/ABHotUpdates/|https://core-ak.freefiremobile.com/live/ABHotUpdates/|a4332cb1c1a84e51dd77441e4856ed5a",
        107: "1.477aa00e98bf924c"
    }
    return bytes.fromhex(encrypt_aes(create_proto(fields).hex()))

async def MajorLogin(payload):
    base = login_url.rstrip("/")
    if not base.startswith(("http://", "https://")): base = "https://" + base
    url = f"{base}/MajorLogin"
    Hr["X-GA-SV"] = str(int(time.time()))
    Hr["ReleaseVersion"] = ob
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False; ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as r:
            if r.status != 200: return None
            raw = await r.read()
            return raw[64:] if len(raw) > 64 else raw

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False; ssl_context.verify_mode = ssl.CERT_NONE
    Hr['Authorization'] = f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as r:
            if r.status == 200: return await r.read()
            return None

async def DecRypTMajoRLoGin(MajoRLoGinResPonsE):
    class P:
        def __init__(self, f):
            self.account_uid = int(f.get(1, 0)); self.region = str(f.get(2, ""))
            self.token = str(f.get(8, "")); self.url = str(f.get(10, ""))
            self.timestamp = int(f.get(21, 0))
            rk = f.get(22, b"")
            if isinstance(rk, str):
                try: self.key = bytes.fromhex(rk.replace(" ", ""))
                except: self.key = rk.encode()
            else: self.key = bytes(rk)
            riv = f.get(23, b"")
            if isinstance(riv, str):
                try: self.iv = bytes.fromhex(riv.replace(" ", ""))
                except: self.iv = riv.encode()
            else: self.iv = bytes(riv)
    def dv(buf, off):
        res, sh, st = 0, 0, off
        while True:
            if off >= len(buf): raise IndexError
            b = buf[off]; off += 1
            res += (b & 0x7F) << sh; sh += 7
            if b < 0x80: break
        return res, off - st
    def dp(buf):
        off, parts, blen = 0, [], len(buf)
        try:
            while off < blen:
                it, vl = dv(buf, off); off += vl
                wt, fn = it & 7, it >> 3
                if wt == 0: val, vl = dv(buf, off); off += vl
                elif wt == 2:
                    length, vl = dv(buf, off); off += vl
                    if off + length > blen: return None
                    val = buf[off:off+length]; off += length
                elif wt == 5:
                    if off + 4 > blen: return None
                    val = struct.unpack_from("<I", buf, off)[0]; off += 4
                elif wt == 1:
                    if off + 8 > blen: return None
                    val = struct.unpack_from("<Q", buf, off)[0]; off += 8
                else: return None
                parts.append((fn, wt, val))
            return parts
        except: return None
    def td(parts):
        r = {}
        for fn, wt, v in parts:
            if wt == 2:
                try: val = v.decode("utf-8")
                except: val = v
            else: val = v
            r[fn] = val
        return r
    buf = MajoRLoGinResPonsE
    try:
        c = AES.new(b'Yg&tc%DEuh6%Zc^8', AES.MODE_CBC, b'6oyZDr22E3ychjM%')
        buf = unpad(c.decrypt(buf), AES.block_size)
    except: pass
    p = dp(buf)
    if p:
        d = td(p)
        if 1 in d or 8 in d or 10 in d: return P(d)
    for o in range(len(buf)):
        p = dp(buf[o:])
        if p:
            d = td(p)
            if 1 in d or 8 in d or 10 in d: return P(d)
    return P({})

def create_auth_token_chat(account_id, jwt_token, timestamp, key, iv):
    try:
        K = bytes.fromhex(key) if isinstance(key, str) else key
        V = bytes.fromhex(iv)  if isinstance(iv, str) else iv
        ct = AES.new(K, AES.MODE_CBC, V).encrypt(pad(jwt_token.encode('utf-8'), AES.block_size))
        header = bytes.fromhex('6d19') + int(account_id).to_bytes(8, 'big') + int(timestamp).to_bytes(4, 'big') + len(ct).to_bytes(4, 'big')
        return (header + ct).hex()
    except Exception as e:
        print(f"❌ CHAT AUTH: {e}"); return None

def create_auth_token_online(account_uid, token, kts, key, iv):
    try:
        K = bytes.fromhex(key) if isinstance(key, str) else key
        V = bytes.fromhex(iv)  if isinstance(iv, str) else iv
        enc_token = AES.new(K, AES.MODE_CBC, V).encrypt(pad(token.encode("utf-8"), 16))
        opcode = bytes.fromhex("830c")
        return (opcode + int(account_uid).to_bytes(8, byteorder="big") + int(kts).to_bytes(4, byteorder="big") + len(enc_token).to_bytes(8, byteorder="big") + enc_token).hex()
    except Exception as e:
        print(f"❌ ONLINE AUTH: {e}"); return None

# ================================================================
#   BATCH LOADER
# ================================================================
async def batch_account_loader():
    global total_accounts
    active_bots, bot_tasks, last_passwords = {}, {}, {}
    console.print("[bold cyan]🚀 Batch Account Loader started...[/bold cyan]")
    while True:
        try:
            accounts = load_accounts()
            total_accounts = len(accounts)
            stopped = is_stopped()

            for uid, pwd in accounts.items():
                if uid in last_passwords and last_passwords[uid] != pwd:
                    console.print(f"[bold yellow]🔑 UID {uid} pwd changed → restart[/bold yellow]")
                    if uid in active_bots:
                        try: active_bots[uid].is_running = False
                        except: pass
                        del active_bots[uid]
                    if uid in bot_tasks:
                        if not bot_tasks[uid].done(): bot_tasks[uid].cancel()
                        del bot_tasks[uid]
                last_passwords[uid] = pwd

            if not stopped:
                for uid, pwd in accounts.items():
                    with running_bots_lock: running_bots.add(uid)
                    if uid in bot_tasks and not bot_tasks[uid].done(): continue
                    if uid in bot_tasks: del bot_tasks[uid]
                    if uid in active_bots:
                        try: active_bots[uid].is_running = False
                        except: pass
                        del active_bots[uid]
                    bot = SquadBot(uid=uid, password=pwd, server='bd', index=len(bot_tasks)+1)
                    active_bots[uid] = bot
                    bot_tasks[uid] = asyncio.create_task(bot.keep_online_forever())
                    console.print(f"[bold green]✨ UID {uid} → Launched[/bold green]")
                    await asyncio.sleep(0.05)
            else:
                for uid in list(bot_tasks.keys()):
                    try:
                        if uid in active_bots: active_bots[uid].is_running = False
                        if not bot_tasks[uid].done(): bot_tasks[uid].cancel()
                    except: pass
                    remove_active_account(uid)
                    with running_bots_lock: running_bots.discard(uid)
                    del bot_tasks[uid]
                    if uid in active_bots: del active_bots[uid]

            if not stopped:
                for uid in list(bot_tasks.keys()):
                    if bot_tasks[uid].done():
                        try: exc = bot_tasks[uid].exception()
                        except: exc = None
                        if exc: console.print(f"[bold red]⚠️ UID {uid} crashed → retry[/bold red]")
                        if uid in active_bots:
                            try: active_bots[uid].is_running = False
                            except: pass
                            del active_bots[uid]
                        del bot_tasks[uid]
                for uid in list(bot_tasks.keys()):
                    if uid not in accounts:
                        console.print(f"[bold red]🗑️ UID {uid} removed → stop[/bold red]")
                        if uid in active_bots:
                            try: active_bots[uid].is_running = False
                            except: pass
                            del active_bots[uid]
                        if not bot_tasks[uid].done(): bot_tasks[uid].cancel()
                        del bot_tasks[uid]
                        with running_bots_lock: running_bots.discard(uid)
                        last_passwords.pop(uid, None)

            if stopped: console.print(f"[bold red]🛑 STOPPED — {len(accounts)} idle[/bold red]", end="\r")
            elif accounts: console.print(f"[dim]📊 Active: {len(bot_tasks)}/{len(accounts)}[/dim]", end="\r")
        except Exception as e:
            console.print(f"[bold red]Loader Err: {e}[/bold red]")
        await asyncio.sleep(2)

def ResTarTinG():
    console.print("[bold yellow]♻️ Restarting...[/bold yellow]")
    time.sleep(0.5); os.execl(sys.executable, sys.executable, *sys.argv)

def AuTo_ResTartinG():
    while True:
        time.sleep(3600)
        console.print("[bold red]⚠️ Auto restart...[/bold red]")
        ResTarTinG()

# ================================================================
#   SQUAD BOT CLIENT
# ================================================================
class SquadBot:
    def __init__(self, uid, password, server='bd', index=0):
        self.uid, self.password, self.server, self.index = uid, password, server, index
        self.is_running = True
        self.online_writer = self.chat_writer = self.reader = None
        self.key = self.iv = self.region = None
        self.tasks = []
        self.is_online = False
        self.Nm = "Unknown"
        self.bot_uid = None
        self.chat_reader = None
        self.squad_created = False
        self.squad_members = set()
        self.member_names = {}
        self.current_squad_id = self.current_chat_code = None
        self.seen_recreate_ts = self.seen_restart_ts = 0
        self.squad_created_at = 0
        self.last_recruit_at = self.last_bundle_at = 0
        self.last_emote_on_join_at = 0
        self.jwt_token = None
        self._recruit_lock = asyncio.Lock()
        self._bundle_lock = asyncio.Lock()
        self._recreate_lock = asyncio.Lock()
        self._animation_task = None
        self._self_emote_task = None
        update_bot_info(self.uid, status="🔄 Initializing...", squad_active=False)

    async def _send_emote_on_join(self, target_uid):
        try:
            with web_config_lock:
                enabled = web_config.get("auto_emote_on_join", True)
                delay = float(web_config.get("emote_join_delay_sec", 0.5))
                pool = list(web_config.get("join_emote_pool", DEFAULT_JOIN_EMOTES))
            if not enabled or not pool: return False
            if not self.online_writer or not self.bot_uid: return False
            global BOT_OWN_ID
            try: BOT_OWN_ID = int(self.bot_uid)
            except: pass
            await asyncio.sleep(max(0.05, delay))
            emote_id = random.choice(pool)
            pkt = await Emote_k(int(target_uid), int(emote_id), self.key, self.iv, self.region or "bd")
            if pkt and self.online_writer and not self.online_writer.is_closing():
                self.online_writer.write(pkt); await self.online_writer.drain()
                self.last_emote_on_join_at = time.time()
                console.print(f"[bold magenta]🎭 [{self.uid}] Join Emote → {target_uid} (id={emote_id}, delay={delay}s)[/bold magenta]")
                return True
        except Exception as e:
            console.print(f"[yellow]⚠ [{self.uid}] Join emote err: {e}[/yellow]")
        return False

    async def _send_bundle_on_join(self):
        if not self.online_writer or not self.bot_uid: return False
        async with self._bundle_lock:
            now = time.time()
            if now - self.last_bundle_at < _BUNDLE_COOLDOWN: return False
            with web_config_lock:
                enabled = web_config.get("auto_bundle_on_join", True)
                count = web_config.get("bundle_count_on_join", 2)
            if not enabled: return False
            count = max(1, min(5, int(count)))
            sent = 0
            for i in range(count):
                try:
                    bid = random.choice(AUTO_BUNDLE_POOL)
                    pkt = await (Mahir_bundle_packet if i == 0 else Mahir_bundle_packet_2)(bid, self.key, self.iv, self.region or "bd")
                    if pkt:
                        self.online_writer.write(pkt); await self.online_writer.drain()
                        sent += 1; await asyncio.sleep(0.5)
                except: break
            self.last_bundle_at = time.time()
            if sent: console.print(f"[bold magenta]👗 [{self.uid}] Bundle × {sent}[/bold magenta]")
            return sent > 0

    async def _auto_kick_member(self, target_uid, target_name="Player"):
        try:
            with web_config_lock:
                enabled = web_config.get("auto_kick_on_join", False)
                delay = float(web_config.get("kick_delay_sec", 1.0))
                km = web_config.get("kick_msg", "")
            if not enabled:
                return False
            if not self.online_writer:
                return False
            await asyncio.sleep(max(0.05, delay))

            try:
                kick_pkt = await KickTarget(int(target_uid), self.key, self.iv)
                if kick_pkt and self.online_writer and not self.online_writer.is_closing():
                    self.online_writer.write(kick_pkt)
                    await self.online_writer.drain()
                    console.print(f"[bold red]🚫 [{self.uid}] Auto-kicked → {target_name} ({target_uid})[/bold red]")
            except Exception as e:
                console.print(f"[yellow]⚠ Kick pkt err: {e}[/yellow]")

            try:
                km2 = str(km).replace("{user_name}", str(target_name)).replace("{user_id}", str(target_uid))
                sq_id = self.current_squad_id
                if sq_id and self.chat_writer and self.bot_uid:
                    msg_pkt = await MAHIR_SendSquadMsg(
                        int(sq_id), km2, int(self.bot_uid), self.key, self.iv
                    )
                    if msg_pkt:
                        self.chat_writer.write(msg_pkt)
                        await self.chat_writer.drain()
            except Exception as e:
                console.print(f"[yellow]⚠ Kick msg err: {e}[/yellow]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Auto-kick err: {e}[/red]")
            return False

    async def _auto_welcome_member(self, squad_id, chat_code, target_uid, target_name="Player"):
        try:
            with web_config_lock:
                enabled = web_config.get("auto_welcome_on_join", True)
                delay = float(web_config.get("welcome_delay_sec", 0.5))
            if not enabled:
                return False
            if not self.chat_writer:
                return False
            if not self.bot_uid:
                return False

            await asyncio.sleep(max(0.05, delay))

            try:
                if chat_code:
                    op = await MAHIR_OpenSquadChat(int(squad_id), chat_code, self.key, self.iv)
                    if op:
                        self.chat_writer.write(op)
                        await self.chat_writer.drain()
                        await asyncio.sleep(0.2)
            except Exception as e:
                console.print(f"[yellow]⚠ Chat open err: {e}[/yellow]")

            with web_config_lock:
                wt = web_config.get("welcome_msg", DEFAULT_WELCOME_MSG)
            wm = wt.replace("{user_name}", str(target_name))

            mp = await MAHIR_SendSquadMsg(
                int(squad_id), wm, int(self.bot_uid), self.key, self.iv
            )
            if mp:
                self.chat_writer.write(mp)
                await self.chat_writer.drain()
                console.print(f"[bold green]✅ [{self.uid}] Welcome → {target_name}[/bold green]")
                return True
            return False
        except Exception as e:
            console.print(f"[red]❌ Welcome err: {e}[/red]")
            return False

    async def _bot_self_emote_loop(self):
        while self.is_running and self.is_online:
            try:
                with web_config_lock:
                    enabled = web_config.get("bot_self_emote_enabled", False)
                    pool = list(web_config.get("bot_self_emote_pool", DEFAULT_JOIN_EMOTES))
                    interval = float(web_config.get("bot_self_emote_interval", 8.0))
                if not enabled or not pool:
                    await asyncio.sleep(2); continue
                if not self.online_writer or not self.bot_uid:
                    await asyncio.sleep(2); continue
                emote_id = random.choice(pool)
                pkt = await Emote_k(int(self.bot_uid), int(emote_id), self.key, self.iv, self.region or "bd")
                if pkt and self.online_writer and not self.online_writer.is_closing():
                    self.online_writer.write(pkt); await self.online_writer.drain()
                    console.print(f"[bold cyan]🤖 [{self.uid}] Self Emote ({emote_id})[/bold cyan]")
                await asyncio.sleep(max(2.0, interval))
            except asyncio.CancelledError: break
            except: await asyncio.sleep(5)

    async def _send_world_recruit(self, reason="manual", count=None):
        if not self.online_writer or not self.bot_uid: return False
        async with self._recruit_lock:
            with web_config_lock:
                dc = web_config.get("world_recruit_count", 3)
                rt = web_config.get("world_recruit_type", "1")
            n = count if count is not None else dc
            n = max(1, min(10, int(n)))
            now = time.time()
            if now - self.last_recruit_at < 2.0 and reason != "initial": return False
            s1, s2, s3 = 0, 0, 0
            for i in range(n):
                try:
                    # Choose recruit type
                    if rt in ("1", "2", "3"):
                        ut = rt
                    elif rt == "half":
                        ut = "1" if i % 2 == 0 else "2"
                    else:  # random
                        ut = random.choice(["1", "2", "3"])

                    if ut == "1":
                        pkt = await MAHIR_World_Recruit(self.bot_uid, self.key, self.iv)
                        if pkt: s1 += 1
                    elif ut == "2":
                        pkt = await MAHIR_World_Recruit2(self.bot_uid, self.key, self.iv)
                        if pkt: s2 += 1
                    else:
                        pkt = await MAHIR_World_Recruit3(self.bot_uid, self.key, self.iv)
                        if pkt: s3 += 1

                    if pkt:
                        self.online_writer.write(pkt); await self.online_writer.drain()
                        await asyncio.sleep(0.35)
                except: break
            self.last_recruit_at = time.time()
            total = s1 + s2 + s3
            if total:
                icon = {"join":"🟢","leave":"🔴","initial":"🚀","manual":"📢"}.get(reason, "📢")
                console.print(f"[cyan]{icon} [{self.uid}] Recruit × {total} (T1={s1} T2={s2} T3={s3} | {reason})[/cyan]")
            return total > 0

    async def _build_and_send_squad(self):
        try:
            with web_config_lock:
                sc = web_config.get("squad_size", 4)
                rcc = web_config.get("world_recruit_count", 3)
            op = await MAHIR_OPenSq(self.key, self.iv, self.region, FREEFIRE_VERSION_NAME)
            if not op or not self.online_writer: return False
            self.online_writer.write(op); await self.online_writer.drain()
            await asyncio.sleep(0.4)
            console.print(f"[cyan]ℹ [{self.uid}] Squad Created ✅[/cyan]")
            try:
                op2 = await MAHIR_OPenSq(self.key, self.iv, self.region, FREEFIRE_VERSION_NAME)
                self.online_writer.write(op2); await self.online_writer.drain()
                await asyncio.sleep(0.3)
            except: pass
            try:
                sq_funcs = [MAHIR_cHSq11, MAHIR_cHSq22, MAHIR_cHSq33, MAHIR_cHSq44,
                            MAHIR_cHSq55, MAHIR_cHSq66, MAHIR_cHSq77]
                sq_func = random.choice(sq_funcs)
                sp = await sq_func(sc, self.bot_uid, self.key, self.iv, self.region)
                self.online_writer.write(sp); await self.online_writer.drain()
                await asyncio.sleep(0.3)
            except: pass
            await self._send_world_recruit(reason="initial", count=rcc)
            self.squad_created = True
            self.squad_created_at = time.time()
            self.squad_members.clear()
            self.member_names.clear()
            update_bot_info(self.uid, status="✅ Squad Active", squad_active=True)
            return True
        except Exception as e:
            console.print(f"[red]Squad create err [{self.uid}]: {e}[/red]"); return False

    async def _do_recreate(self):
        if self._recreate_lock.locked(): return False
        async with self._recreate_lock:
            try:
                console.print(f"[yellow]🔄 [{self.uid}] Recreating squad...[/yellow]")
                if self.online_writer and self.bot_uid:
                    try:
                        ep = await MAHIR_LeaveSquad(self.key, self.iv, self.region, self.bot_uid)
                        if ep:
                            self.online_writer.write(ep); await self.online_writer.drain()
                            console.print(f"[red]🚪 [{self.uid}] Exited[/red]")
                    except: pass
                self.squad_members.clear(); self.member_names.clear()
                self.current_squad_id = self.current_chat_code = None
                self.squad_created = False
                update_active_account(self.uid, squad_id='Pending...', squad_members='0/0')
                await asyncio.sleep(0.5)
                return await self._build_and_send_squad()
            except Exception as e:
                console.print(f"[red]Recreate err [{self.uid}]: {e}[/red]")
            return False

    async def send_team_msg(self, message: str, squad_id=None):
        try:
            if not self.chat_writer:
                return False
            if not self.bot_uid:
                return False
            sq_id = squad_id or self.current_squad_id
            if not sq_id:
                return False

            pkt = await MAHIR_SendSquadMsg(
                int(sq_id), message, int(self.bot_uid), self.key, self.iv
            )
            if pkt:
                self.chat_writer.write(pkt)
                await self.chat_writer.drain()
                return True
        except Exception as e:
            console.print(f"[yellow]⚠ [{self.uid}] send_team_msg err: {e}[/yellow]")
        return False

    async def handle_team_command(self, cmd_raw: str, sender_uid, sender_name="Player"):
        try:
            cl = cmd_raw.strip().lower()
            if cl in ("/help", "help"):
                for p in await build_help_menu(nickname=sender_name, bot_uid=str(sender_uid)):
                    await self.send_team_msg(p); await asyncio.sleep(0.5)
                return True
            if cl in ("/app", "app"):
                await self.send_team_msg("[B][C][00FFFF]MAHIR TCP OFFICIAL APP\n[FFFFFF]Download লিংক নিচে")
                await asyncio.sleep(0.4)
                await self.send_team_msg("https://www.mediafire.com/file/lvykrek51q17hae/MAHIR_TCP.apk")
                return True
            if cl in ("/store", "store"):
                await self.send_team_msg("[C][FFD700]⚡ MAHIR BOT STORE ⚡\n[C][00FF00]🤖 TCP BOT: [FFFF00]500 BDT\n[C][00FF00]🌐 Website: [FFFF00]mahir.xo.je\n[C][00FF00]👤 Owner: [FFFF00]@MAHIR0208")
                return True
            if cl == "hi":
                await self.send_team_msg("[00FFFF][b][c]😊 হাই! আপনার দিনটি কেমন যাচ্ছে?\n[FFD700]Telegram: @MAHIR0208\n[FFD700]TikTok: @MAHIR__222")
                return True
            if cl == ".time":
                await self.send_team_msg(f"[B][C][00FFFF]╔═══════════════╗\n[B][C][FFFFFF]🕒 TIME: [00FF00]{datetime.now().strftime('%I:%M %p')}\n[B][C][00FFFF]╚═══════════╝")
                return True
            if cl == "my id":
                await self.send_team_msg(f"[B][C][00FFFF]👤 YOUR INFO\n[B][C][FFFFFF]Name: [00FF00]{sender_name}\n[B][C][FFFFFF]UID : [FFFF00]{sender_uid}")
                return True
            with web_config_lock:
                cmds = dict(web_config.get("commands", {}))
            for trig, cfg in cmds.items():
                if not cfg.get("enabled", True): continue
                mm = cfg.get("match", "contains")
                t, m = trig.lower(), cl
                matched = (mm == "exact" and m == t) or (mm == "startswith" and m.startswith(t)) or (mm == "contains" and t in m)
                if matched:
                    ct = cfg.get("type", "message")
                    if ct == "message":
                        await self.send_team_msg(cfg.get("response", "").replace("{user_name}", str(sender_name)))
                        return True
                    elif ct == "recruit_squad":
                        await self._send_world_recruit(reason="manual"); return True
            return False
        except Exception as e:
            console.print(f"[red]handle_team_command err: {e}[/red]"); return False

    async def tcp_online(self, ip, port, auth_token):
        self.current_squad_id = None
        self.squad_members = set()
        self.member_names = {}
        self.seen_recreate_ts = get_recreate_timestamp()
        while self.is_running:
            if is_stopped(): break
            try:
                reader, writer = await asyncio.open_connection(ip, int(port))
                writer.write(bytes.fromhex(auth_token)); await writer.drain()
                self.reader, self.online_writer = reader, writer
                self.is_online = True
                update_bot_info(self.uid, status="✅ Online")
                console.print(f"[cyan]ℹ [{self.uid}] ONLINE Connected ✅[/cyan]")
                if not await self._build_and_send_squad():
                    self.is_online = False; await asyncio.sleep(10); continue
                if self._animation_task and not self._animation_task.done(): self._animation_task.cancel()
                self._animation_task = asyncio.create_task(self._animation_loop())
                if self._self_emote_task and not self._self_emote_task.done(): self._self_emote_task.cancel()
                self._self_emote_task = asyncio.create_task(self._bot_self_emote_loop())

                while self.is_running and self.is_online:
                    if is_stopped(): break
                    cur_ts = get_recreate_timestamp()
                    if cur_ts > self.seen_recreate_ts:
                        self.seen_recreate_ts = cur_ts
                        await self._do_recreate(); continue
                    with web_config_lock:
                        ar = web_config.get("auto_recreate", True)
                        lt = web_config.get("squad_lifetime_sec", 10)
                    if ar and self.squad_created and (time.time() - self.squad_created_at > lt):
                        console.print(f"[yellow]⏰ [{self.uid}] Lifetime {lt}s → recreate[/yellow]")
                        await self._do_recreate(); continue
                    try:
                        data = await asyncio.wait_for(self.reader.read(65536), timeout=1.0)
                        if not data: break
                        data_hex = data.hex()
                        if data_hex.startswith("0e00") or data_hex.startswith("0500"):
                            decoded = DeCode_PackEt(data_hex[10:])
                            if decoded:
                                try:
                                    pj = json.loads(decoded)
                                    f5 = pj.get('5')
                                    if not isinstance(f5, dict): continue
                                    f5_data = f5.get('data')
                                    if not isinstance(f5_data, dict): continue
                                    soi = safe_get_int(f5_data.get('1'))
                                    so = str(soi) if soi is not None else None
                                    if so and so != str(self.bot_uid): self.current_squad_id = so
                                    c_code = safe_get_str(f5_data.get('14')) or safe_get_str(f5_data.get('17')) or safe_get_str(f5_data.get('31')) or safe_get_str(f5_data.get('33'))
                                    cm = {}
                                    for pk in ('6','2','3','5','7'):
                                        cand = safe_dict(f5_data.get(pk))
                                        if not cand: continue
                                        cu = safe_get_int(cand.get('1'))
                                        cn = safe_get_str(cand.get('2'))
                                        if cu and str(cu) != str(self.bot_uid) and len(str(cu)) > 8 and cn:
                                            us, pn = str(cu), cn
                                            cm[us] = pn
                                            if us not in self.squad_members:
                                                sq_id = soi or (int(self.current_squad_id) if self.current_squad_id else None)
                                                console.print(f"[cyan][{self.uid}][/cyan] [green]➜ Joined:[/green] [yellow]{pn}[/yellow] ({us})")
                                                asyncio.create_task(self._send_emote_on_join(us))
                                                asyncio.create_task(self._send_bundle_on_join())
                                                with web_config_lock:
                                                    kick_on = web_config.get("auto_kick_on_join", False)
                                                    welcome_on = web_config.get("auto_welcome_on_join", True)
                                                if kick_on:
                                                    asyncio.create_task(self._auto_kick_member(us, pn))
                                                if welcome_on and sq_id and c_code:
                                                    asyncio.create_task(self._auto_welcome_member(int(sq_id), c_code, us, target_name=pn))
                                            break
                                    if cm:
                                        jn = {u:n for u,n in cm.items() if u not in self.squad_members}
                                        if jn:
                                            for u, n in jn.items():
                                                self.squad_members.add(u); self.member_names[u] = n
                                            with web_config_lock:
                                                rj = web_config.get("auto_recruit_on_join", True)
                                                sz = web_config.get('squad_size', 4)
                                            if rj: asyncio.create_task(self._send_world_recruit(reason="join"))
                                            update_active_account(self.uid, **{'squad_members': f"{len(self.squad_members)}/{sz+1}"})
                                    nsq = safe_get_int(f5_data.get('1'))
                                    if nsq and 10000000 < nsq < 999999999:
                                        if str(nsq) != str(self.current_squad_id):
                                            self.current_squad_id = str(nsq)
                                            console.print(Panel(f"[green]🆔 Squad ID: [yellow]{self.current_squad_id}[/yellow]", title=f"[magenta]✨ ESTABLISHED ({self.uid})[/magenta]", border_style="cyan"))
                                            update_bot_info(self.uid, last_squad_id=str(nsq), squad_active=True)
                                            with web_config_lock: sz = web_config.get('squad_size', 4)
                                            update_active_account(self.uid, **{'squad_id': self.current_squad_id, 'squad_members': f"0/{sz+1}"})
                                except Exception: pass
                    except asyncio.TimeoutError: continue
                    except Exception: break
            except Exception as e:
                if not is_stopped(): console.print(f"[red][{self.uid}] tcp_online err: {e}[/red]")
                self.is_online = False
            for t in [self._animation_task, self._self_emote_task]:
                if t and not t.done(): t.cancel()
            if is_stopped(): break
            await asyncio.sleep(8)

    async def _animation_loop(self):
        while self.is_running and self.is_online:
            try:
                if is_stopped(): break
                with web_config_lock:
                    enabled = web_config.get("auto_animation", True)
                    interval = web_config.get("animation_interval_sec", 10)
                if not enabled or not self.online_writer or not self.bot_uid:
                    await asyncio.sleep(2); continue
                anim_id = random.choice(ANIMATION_POOL)
                pkt = await mahir_animation_packet(anim_id, self.key, self.iv)
                if pkt and self.online_writer and not self.online_writer.is_closing():
                    self.online_writer.write(pkt); await self.online_writer.drain()
                    console.print(f"[cyan]✨ [{self.uid}] Animation ({anim_id})[/cyan]")
                await asyncio.sleep(max(5, int(interval)))
            except asyncio.CancelledError: break
            except: await asyncio.sleep(5)

    async def tcp_chat(self, ip, port, auth_token, key, iv, ready_event):
        while self.is_running:
            if is_stopped(): break
            try:
                reader, writer = await asyncio.open_connection(ip, int(port))
                writer.write(bytes.fromhex(auth_token)); await writer.drain()
                self.chat_reader, self.chat_writer = reader, writer
                ready_event.set()
                console.print(f"[cyan]ℹ [{self.uid}] CHAT Connected ✅[/cyan]")
                while self.is_running:
                    if is_stopped(): break
                    try:
                        data = await asyncio.wait_for(self.chat_reader.read(4096), timeout=5.0)
                        if not data: break
                        dh = data.hex()
                        if dh.startswith("1200"):
                            dec = DeCode_PackEt(dh[10:])
                            if dec:
                                try:
                                    pj = json.loads(dec)
                                    f5 = pj.get('5')
                                    if not isinstance(f5, dict): continue
                                    fd = f5.get('data')
                                    if not isinstance(fd, dict): continue
                                    mt = safe_get_str(fd.get('4')).strip()
                                    ci = safe_get_int(fd.get('2'))
                                    su = safe_get_int(fd.get('1'))
                                    f9 = safe_dict(fd.get('9'))
                                    sn = safe_get_str(f9.get('1'), "Player") if f9 else "Player"
                                    if not mt or not su: continue
                                    if str(su) == str(self.bot_uid): continue
                                    console.print(f"[cyan][{self.uid}][/cyan] [white]{sn}[/white]: [yellow]{mt}[/yellow]")
                                    await self.handle_team_command(mt, su, sn)
                                except: pass
                    except asyncio.TimeoutError: continue
                    except Exception: break
            except: pass
            if is_stopped(): break
            await asyncio.sleep(8)

    async def keep_online_forever(self):
        global online_count, BOT_OWN_ID
        while self.is_running:
            if is_stopped():
                console.print(f"[red]🛑 [{self.uid}] Stopped by user[/red]"); break
            try:
                self.seen_restart_ts = get_restart_timestamp()
                self.tasks = []
                oi, at = await GeNeRaTeAccAccess(self.uid, self.password)
                if not oi: update_bot_info(self.uid, status="❌ Auth Failed"); await asyncio.sleep(10); continue
                payload = await EncRypTMajoRLoGin(oi, at, FREEFIRE_VERSION_NAME)
                resp = await MajorLogin(payload)
                if not resp: update_bot_info(self.uid, status="❌ Login Failed"); await asyncio.sleep(10); continue
                try: auth = await DecRypTMajoRLoGin(resp)
                except: update_bot_info(self.uid, status="❌ Decrypt Failed"); await asyncio.sleep(10); continue
                if not getattr(auth, 'token', None) or not getattr(auth, 'url', None):
                    update_bot_info(self.uid, status="❌ Empty Auth"); await asyncio.sleep(10); continue
                ld = await GetLoginData(auth.url, payload, auth.token)
                if not ld: update_bot_info(self.uid, status="❌ Data Failed"); await asyncio.sleep(10); continue
                from Pb2 import PorTs_pb2
                pd = PorTs_pb2.GetLoginData(); pd.ParseFromString(ld)
                self.key, self.iv = auth.key, auth.iv
                self.region, self.bot_uid = auth.region, auth.account_uid
                self.jwt_token = auth.token
                try: BOT_OWN_ID = int(auth.account_uid)
                except: pass
                en = extract_player_name(ld)
                if en and len(en) < 60: self.Nm = en
                else:
                    try:
                        dj = jwt.decode(auth.token, options={"verify_signature": False})
                        fb = dj.get('nickname')
                        self.Nm = str(fb) if fb and len(str(fb)) < 30 else f"Player_{str(auth.account_uid)[-4:]}"
                    except: self.Nm = f"Player_{str(auth.account_uid)[-4:]}"
                update_bot_info(self.uid, account_uid=str(auth.account_uid))
                oip, opp = pd.Online_IP_Port.split(":")
                cip, cpp = pd.AccountIP_Port.split(":")
                oa = create_auth_token_online(auth.account_uid, auth.token, auth.timestamp, auth.key, auth.iv)
                ca = create_auth_token_chat(auth.account_uid, auth.token, auth.timestamp, auth.key, auth.iv)
                if not oa or not ca: update_bot_info(self.uid, status="❌ Token Failed"); await asyncio.sleep(10); continue
                console.print(f"[green]✔ Online: {self.Nm} | {self.region}[/green]")
                try: await equip_emote_on_login(auth.token, logger=lambda m: console.print(f"[cyan][{self.uid}] {m}[/cyan]"))
                except: pass
                with active_lock:
                    if not any(a['uid'] == self.uid for a in active_accounts):
                        online_count += 1
                        active_accounts.append({'uid': self.uid, 'bot_uid': str(auth.account_uid), 'name': self.Nm,
                            'region': self.region or 'BD', 'time': datetime.now().strftime('%H:%M:%S'),
                            'squad_id': 'Pending...', 'squad_members': '0/0'})
                update_bot_info(self.uid, status="✅ Online", account_uid=str(auth.account_uid), squad_active=True)
                ready = asyncio.Event()
                t1 = asyncio.create_task(self.tcp_chat(cip, cpp, ca, auth.key, auth.iv, ready))
                self.tasks.append(t1)
                await ready.wait()
                t2 = asyncio.create_task(self.tcp_online(oip, opp, oa))
                self.tasks.append(t2)
                monitor = asyncio.create_task(self._monitor_restart())
                try: await asyncio.gather(t1, t2, return_exceptions=True)
                finally:
                    if not monitor.done(): monitor.cancel()
            except Exception as e:
                if not is_stopped(): console.print(f"[red]❌ UID {self.uid} Err: {e}[/red]")
                update_bot_info(self.uid, status="❌ Error", squad_active=False)
            remove_active_account(self.uid)
            if is_stopped(): console.print(f"[red]🛑 [{self.uid}] Halted[/red]"); break
            if get_restart_timestamp() > self.seen_restart_ts:
                console.print(f"[green]♻️ [{self.uid}] Reconnecting...[/green]"); continue
            await asyncio.sleep(10)

    async def _monitor_restart(self):
        while self.is_running:
            await asyncio.sleep(2)
            if is_stopped():
                console.print(f"[red]🛑 [{self.uid}] Stop signal[/red]")
                for t in [self._animation_task, self._self_emote_task]:
                    if t and not t.done(): t.cancel()
                for t in self.tasks:
                    if not t.done(): t.cancel()
                return
            cur_ts = get_restart_timestamp()
            if cur_ts > self.seen_restart_ts:
                self.seen_restart_ts = cur_ts
                for t in [self._animation_task, self._self_emote_task]:
                    if t and not t.done(): t.cancel()
                for t in self.tasks:
                    if not t.done(): t.cancel()
                return

# ================================================================
#   WEB SERVER
# ================================================================
class BotHandler(BaseHTTPRequestHandler):
    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _text_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(data if isinstance(data, bytes) else data.encode('utf-8'))

    def _read_body(self):
        try:
            cl = int(self.headers.get('Content-Length', 0))
            return self.rfile.read(cl).decode('utf-8')
        except: return ""

    def _esc(self, s):
        return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with active_lock:
                cur_online, cur_total, cur_threads = online_count, total_accounts, len(active_accounts)
            with web_config_lock:
                cur_size = web_config.get("squad_size", 4)
                cur_recruit = web_config.get("world_recruit_count", 3)
                cur_recruit_type = web_config.get("world_recruit_type", "1")
                cur_lifetime = web_config.get("squad_lifetime_sec", 5)
                cur_auto = web_config.get("auto_recreate", True)
                rc_welcome = web_config.get("welcome_msg", DEFAULT_WELCOME_MSG)
                rc_join = web_config.get("auto_recruit_on_join", True)
                rc_leave = web_config.get("auto_recruit_on_leave", True)
                rc_delay = web_config.get("recruit_delay_sec", 1.5)
                rc_bundle = web_config.get("auto_bundle_on_join", True)
                rc_bundle_count = web_config.get("bundle_count_on_join", 2)
                cur_anim = web_config.get("auto_animation", True)
                cur_anim_int = web_config.get("animation_interval_sec", 10)
                cur_emote_join = web_config.get("auto_emote_on_join", True)
                cur_emote_delay = web_config.get("emote_join_delay_sec", 0.5)
                cur_kick_join = web_config.get("auto_kick_on_join", False)
                cur_kick_delay = web_config.get("kick_delay_sec", 1.0)
                kick_msg_raw = web_config.get("kick_msg", "")
                cur_welcome_join = web_config.get("auto_welcome_on_join", True)
                cur_welcome_delay = web_config.get("welcome_delay_sec", 0.5)
                cur_self_emote = web_config.get("bot_self_emote_enabled", False)
                cur_self_emote_int = web_config.get("bot_self_emote_interval", 8.0)
                join_emote_pool = list(web_config.get("join_emote_pool", DEFAULT_JOIN_EMOTES))
                self_emote_pool = list(web_config.get("bot_self_emote_pool", DEFAULT_JOIN_EMOTES))
            welcome_esc = self._esc(rc_welcome)
            kick_msg_esc = self._esc(kick_msg_raw)
            join_emote_csv = ",".join(str(x) for x in join_emote_pool)
            self_emote_csv = ",".join(str(x) for x in self_emote_pool)
            stopped_now = is_stopped()

            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MAHIR · Control Center</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-0:#05070F; --bg-1:#0A0F1E; --panel:#0F1628; --panel-2:#131B33;
  --line:#1E2A44; --line-hi:rgba(56,189,248,0.35);
  --cyan:#22D3EE; --blue:#3B82F6; --violet:#A855F7; --magenta:#EC4899;
  --green:#10B981; --amber:#F59E0B; --red:#EF4444;
  --txt:#F8FAFC; --txt-2:#94A3B8; --txt-3:#64748B;
  --r:16px; --r-sm:10px;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{font-family:'Rajdhani',system-ui,sans-serif;background:var(--bg-0);color:var(--txt);min-height:100vh;overflow-x:hidden;position:relative;font-weight:500}}
body::before{{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background:radial-gradient(1000px 700px at -5% -10%,rgba(34,211,238,0.10),transparent 55%),radial-gradient(1000px 700px at 105% 110%,rgba(168,85,247,0.10),transparent 55%),radial-gradient(800px 600px at 50% 50%,rgba(236,72,153,0.05),transparent 70%)}}
.layout{{display:flex;min-height:100vh;position:relative;z-index:1}}
.sidebar{{width:250px;flex-shrink:0;background:linear-gradient(180deg,rgba(10,15,30,0.98),rgba(5,7,15,0.98));border-right:1px solid var(--line);padding:24px 16px;position:sticky;top:0;height:100vh;overflow-y:auto;transition:transform 0.35s cubic-bezier(.4,0,.2,1);z-index:100}}
.sb-logo{{display:flex;align-items:center;gap:12px;padding:8px 8px 24px;border-bottom:1px solid var(--line);margin-bottom:20px}}
.sb-mark{{width:46px;height:46px;border-radius:14px;display:grid;place-items:center;font-size:1.5em;background:linear-gradient(135deg,var(--cyan),var(--violet) 55%,var(--magenta));box-shadow:0 0 24px rgba(34,211,238,0.5),inset 0 0 12px rgba(255,255,255,0.15)}}
.sb-logo h2{{font-family:'Orbitron',sans-serif;font-size:1.05em;font-weight:900;letter-spacing:1.8px;line-height:1.1;background:linear-gradient(135deg,#fff,var(--cyan));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.sb-logo p{{font-size:0.62em;color:var(--txt-3);letter-spacing:2px;text-transform:uppercase;font-weight:700}}
.sb-nav{{display:flex;flex-direction:column;gap:5px}}
.sb-link{{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;color:var(--txt-2);text-decoration:none;font-weight:600;font-size:0.92em;letter-spacing:0.5px;cursor:pointer;transition:all 0.22s;border:1px solid transparent}}
.sb-link:hover{{background:rgba(34,211,238,0.07);color:var(--txt);border-color:rgba(34,211,238,0.15)}}
.sb-link.active{{background:linear-gradient(90deg,rgba(34,211,238,0.18),rgba(168,85,247,0.12));color:var(--cyan);border-color:rgba(34,211,238,0.4);box-shadow:inset 3px 0 0 var(--cyan),0 0 22px rgba(34,211,238,0.15)}}
.sb-link .ico{{font-size:1.15em;width:22px;text-align:center}}
.main{{flex:1;padding:22px 26px 44px;min-width:0}}
.topbar{{position:relative;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:20px 26px;background:linear-gradient(135deg,rgba(15,22,40,0.92),rgba(19,27,51,0.75));backdrop-filter:blur(22px);border:1px solid var(--line);border-radius:var(--r);margin-bottom:20px;flex-wrap:wrap;overflow:hidden}}
.tb-left{{display:flex;align-items:center;gap:14px;flex-wrap:wrap}}
.tb-right{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.tb-menu{{display:none;width:38px;height:38px;border-radius:10px;background:rgba(34,211,238,0.08);border:1px solid var(--line-hi);color:var(--cyan);cursor:pointer;font-size:1.15em}}
.tb-title{{font-family:'Orbitron',sans-serif;font-size:1.1em;font-weight:900;letter-spacing:2px}}
.tb-title span{{background:linear-gradient(135deg,#fff,var(--cyan));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.pill{{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:999px;font-size:0.7em;font-weight:700;letter-spacing:1.4px;text-transform:uppercase;border:1px solid var(--line-hi);background:rgba(34,211,238,0.06);color:var(--cyan)}}
.pill.green{{background:rgba(16,185,129,0.08);color:var(--green);border-color:rgba(16,185,129,0.35)}}
.pill.red{{background:rgba(239,68,68,0.08);color:var(--red);border-color:rgba(239,68,68,0.35)}}
.pill.violet{{background:rgba(168,85,247,0.08);color:var(--violet);border-color:rgba(168,85,247,0.35)}}
.pill.amber{{background:rgba(245,158,11,0.08);color:var(--amber);border-color:rgba(245,158,11,0.35)}}
.dot{{width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 9px currentColor;animation:blink 1.4s infinite}}
@keyframes blink{{50%{{opacity:0.4;transform:scale(0.85)}}}}
.status-banner{{position:relative;overflow:hidden;display:flex;align-items:center;justify-content:center;gap:14px;padding:18px 24px;border-radius:var(--r);margin-bottom:22px;font-family:'Orbitron',sans-serif;font-weight:900;letter-spacing:3px;font-size:1em;color:#fff;border:1px solid rgba(255,255,255,0.15);text-transform:uppercase}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-bottom:22px}}
.stat-card{{position:relative;overflow:hidden;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:22px;display:flex;align-items:center;gap:16px;transition:all 0.3s cubic-bezier(.2,.7,.3,1)}}
.stat-card:hover{{transform:translateY(-3px);border-color:var(--line-hi);box-shadow:0 14px 42px rgba(0,0,0,0.4)}}
.stat-ico{{width:52px;height:52px;flex-shrink:0;border-radius:14px;display:grid;place-items:center;font-size:1.45em;background:rgba(255,255,255,0.04);border:1px solid var(--line-hi)}}
.stat-body{{display:flex;flex-direction:column;gap:3px;min-width:0}}
.stat-value{{font-family:'Orbitron',sans-serif;font-size:1.85em;font-weight:900;line-height:1;color:var(--vc,var(--cyan));text-shadow:0 0 22px var(--vc,var(--cyan));word-break:break-all}}
.stat-label{{font-size:0.68em;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--txt-2)}}
.stat-card.s-green{{--vc:#34D399}} .stat-card.s-blue{{--vc:#60A5FA}} .stat-card.s-violet{{--vc:#C084FC}} .stat-card.s-cyan{{--vc:#22D3EE}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:24px;margin-bottom:20px}}
.panel-head{{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;padding-bottom:16px;margin-bottom:20px;border-bottom:1px solid var(--line)}}
.panel-title{{display:flex;align-items:center;gap:12px;font-family:'Orbitron',sans-serif;font-size:0.98em;font-weight:700;letter-spacing:2px;text-transform:uppercase}}
.panel-ico{{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;font-size:1.05em;background:linear-gradient(135deg,rgba(34,211,238,0.18),rgba(168,85,247,0.14));border:1px solid var(--line-hi)}}
.panel-ico.amber{{background:linear-gradient(135deg,rgba(245,158,11,0.18),rgba(251,146,60,0.14))}}
.panel-ico.pink{{background:linear-gradient(135deg,rgba(236,72,153,0.18),rgba(168,85,247,0.14))}}
.panel-ico.green{{background:linear-gradient(135deg,rgba(16,185,129,0.18),rgba(5,150,105,0.14))}}
.panel-ico.red{{background:linear-gradient(135deg,rgba(239,68,68,0.18),rgba(220,38,38,0.14))}}
.btn{{position:relative;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;gap:10px;padding:13px 24px;border:1px solid rgba(255,255,255,0.12);border-radius:12px;font-family:'Rajdhani',sans-serif;font-size:0.9em;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#fff;cursor:pointer;transition:transform 0.2s,box-shadow 0.28s;background:linear-gradient(135deg,var(--red),#B91C1C)}}
.btn:hover:not(:disabled){{transform:translateY(-2px);border-color:rgba(255,255,255,0.3);box-shadow:0 12px 30px rgba(0,0,0,0.45)}}
.btn:disabled{{opacity:0.55;cursor:not-allowed}}
.btn.green{{background:linear-gradient(135deg,var(--green),#047857)}}
.btn.amber{{background:linear-gradient(135deg,var(--amber),#D97706)}}
.btn.pink{{background:linear-gradient(135deg,var(--magenta),#BE185D)}}
.btn.blue{{background:linear-gradient(135deg,var(--blue),#1D4ED8)}}
.btn.violet{{background:linear-gradient(135deg,var(--violet),#7E22CE)}}
.btn.ghost{{background:rgba(255,255,255,0.04);border:1px solid var(--line-hi);color:var(--txt)}}
.action-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}}
.action-tile{{display:flex!important;align-items:center;justify-content:flex-start!important;gap:16px;padding:18px 22px!important;text-transform:none!important;letter-spacing:0!important;min-height:80px;border-radius:14px!important}}
.action-tile .t-ico{{font-size:1.7em;flex-shrink:0}}
.action-tile .t-txt{{display:flex;flex-direction:column;gap:3px;text-align:left;min-width:0}}
.action-tile .t-main{{font-family:'Orbitron',sans-serif;font-size:0.92em;font-weight:900;letter-spacing:1.3px;text-transform:uppercase;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.action-tile .t-sub{{font-size:0.72em;font-weight:600;opacity:0.8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.action-tile.stop{{background:linear-gradient(135deg,var(--red),#7F1D1D)!important}}
.action-tile.start{{background:linear-gradient(135deg,var(--green),#065F46)!important}}
.action-tile.amber{{background:linear-gradient(135deg,var(--amber),#C2410C)!important}}
.action-tile.pink{{background:linear-gradient(135deg,var(--magenta),#9D174D)!important}}
.field{{display:flex;flex-direction:column;gap:8px}}
.field-label{{font-size:0.72em;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--txt-2)}}
input,textarea,select{{width:100%;padding:13px 15px;background:rgba(5,7,15,0.8);border:1px solid var(--line);border-radius:12px;font-family:'JetBrains Mono',monospace;font-size:0.88em;color:var(--cyan);outline:none}}
input:focus,textarea:focus{{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(34,211,238,0.12)}}
textarea{{line-height:1.75;resize:vertical;font-size:0.82em}}
input[type="file"]{{padding:14px;border-style:dashed;cursor:pointer;color:var(--txt-2);font-family:'Rajdhani',sans-serif;font-weight:600}}
.chips{{display:flex;flex-wrap:wrap;gap:10px}}
.chip{{display:inline-flex;align-items:center;gap:10px;padding:11px 15px;border-radius:12px;border:1px solid var(--line);background:rgba(5,7,15,0.6);color:var(--txt-2);font-weight:600;font-size:0.85em;cursor:pointer;user-select:none}}
.chip:hover{{border-color:var(--cyan);color:var(--txt)}}
.chip:has(input:checked){{border-color:var(--cyan);background:linear-gradient(135deg,rgba(34,211,238,0.18),rgba(168,85,247,0.14));color:var(--txt)}}
.chip input{{width:15px;height:15px;accent-color:var(--cyan);cursor:pointer}}
.stack{{display:flex;flex-direction:column;gap:18px}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.acc-box{{padding:20px;border-radius:14px;border:1px solid var(--line);background:linear-gradient(135deg,rgba(5,7,15,0.5),rgba(15,22,40,0.4))}}
.acc-box.cyan{{border-color:rgba(34,211,238,0.3)}}
.acc-box.pink{{border-color:rgba(236,72,153,0.3)}}
.acc-box.violet{{border-color:rgba(168,85,247,0.3)}}
.acc-box.green{{border-color:rgba(16,185,129,0.3)}}
.box-title{{display:flex;align-items:center;gap:10px;font-family:'Orbitron',sans-serif;font-size:0.85em;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px}}
.box-title.cyan{{color:var(--cyan)}} .box-title.pink{{color:var(--magenta)}} .box-title.violet{{color:var(--violet)}} .box-title.green{{color:var(--green)}}
.row{{display:grid;grid-template-columns:1fr 1fr auto;gap:12px;align-items:end}}
.btn-row{{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}}
.hint{{color:var(--txt-3);font-size:0.76em;line-height:1.65;font-style:italic;margin-top:6px}}
.hint b{{color:var(--amber);font-style:normal}}
.hint code{{background:rgba(168,85,247,0.15);color:#C084FC;padding:2px 7px;border-radius:5px;font-family:'JetBrains Mono',monospace;font-size:0.9em}}
.table-shell{{overflow-x:auto;max-height:480px;overflow-y:auto;border-radius:12px;border:1px solid var(--line);background:rgba(5,7,15,0.55)}}
table{{width:100%;border-collapse:collapse;text-align:left}}
th,td{{padding:13px 15px;border-bottom:1px solid var(--line);font-size:0.86em;white-space:nowrap}}
th{{position:sticky;top:0;z-index:5;background:linear-gradient(180deg,rgba(19,27,51,0.98),rgba(15,22,40,0.98));color:var(--cyan);font-family:'Orbitron',sans-serif;font-size:0.68em;font-weight:700;letter-spacing:1.6px;text-transform:uppercase}}
tbody tr:hover{{background:rgba(34,211,238,0.06)}}
.badge-live{{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;border-radius:999px;background:rgba(16,185,129,0.16);color:var(--green);font-size:0.7em;font-weight:700;border:1px solid rgba(16,185,129,0.35)}}
.empty-row td{{text-align:center;padding:40px 20px;color:var(--txt-3);font-style:italic}}
.log-shell{{height:420px;overflow-y:auto;padding:18px;border-radius:12px;border:1px solid var(--line);background:#02040A;font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.8;color:#4ADE80}}
.log-shell > div{{padding:3px 10px;border-left:2px solid transparent;word-break:break-word}}
.log-shell > div:hover{{background:rgba(34,211,238,0.06);border-left-color:var(--cyan)}}
.foot{{text-align:center;padding:24px;color:var(--txt-3);font-size:0.8em;letter-spacing:1.6px;border-top:1px solid var(--line);margin-top:14px}}
.foot b{{color:var(--cyan)}}
.toast{{visibility:hidden;position:fixed;right:22px;bottom:22px;z-index:9999;min-width:280px;padding:16px 22px;border-radius:12px;color:#fff;font-weight:700;font-size:0.95em;background:linear-gradient(135deg,var(--green),#059669);box-shadow:0 14px 42px rgba(0,0,0,0.6);opacity:0;transform:translateY(20px);transition:all 0.35s}}
.toast.show{{visibility:visible;opacity:1;transform:translateY(0)}}
.section{{scroll-margin-top:20px}}
@media (max-width:900px){{
  .sidebar{{position:fixed;left:0;top:0;transform:translateX(-100%)}}
  .sidebar.open{{transform:translateX(0)}}
  .tb-menu{{display:grid;place-items:center}}
  .main{{padding:14px}}
  .row{{grid-template-columns:1fr}}
  .grid-2{{grid-template-columns:1fr}}
}}
.overlay{{position:fixed;inset:0;background:rgba(0,0,0,0.65);z-index:99;display:none;backdrop-filter:blur(3px)}}
.overlay.show{{display:block}}
</style>
</head>
<body>
<div class="overlay" id="overlay" onclick="toggleSidebar()"></div>
<div class="layout">
  <aside class="sidebar" id="sidebar">
    <div class="sb-logo">
      <div class="sb-mark">🔥</div>
      <div><h2>MAHIR</h2><p>Squad Bot</p></div>
    </div>
    <nav class="sb-nav">
      <a class="sb-link active" href="#section-dashboard" onclick="navTo(this)"><span class="ico">⚡</span> Dashboard</a>
      <a class="sb-link" href="#section-accounts" onclick="navTo(this)"><span class="ico">👥</span> Accounts</a>
      <a class="sb-link" href="#section-config" onclick="navTo(this)"><span class="ico">⚙️</span> Squad Config</a>
      <a class="sb-link" href="#section-emotes" onclick="navTo(this)"><span class="ico">🎭</span> Emotes</a>
      <a class="sb-link" href="#section-bots" onclick="navTo(this)"><span class="ico">📋</span> Active Bots</a>
      <a class="sb-link" href="#section-logs" onclick="navTo(this)"><span class="ico">📜</span> Live Logs</a>
    </nav>
  </aside>
  <main class="main">
    <header class="topbar">
      <div class="tb-left">
        <button class="tb-menu" onclick="toggleSidebar()">☰</button>
        <div class="tb-title"><span>CONTROL CENTER</span></div>
        <span class="pill green"><span class="dot"></span> System Online</span>
      </div>
      <div class="tb-right">
        <span class="pill violet">📦 {FREEFIRE_VERSION_NAME}</span>
        <span class="pill">{CURRENT_OB}</span>
      </div>
    </header>
    <div class="status-banner" id="status-banner" style="background:{'linear-gradient(135deg,#EF4444,#7F1D1D)' if stopped_now else 'linear-gradient(135deg,#10B981,#065F46)'};">
      <span>{'🛑 BOTS STOPPED' if stopped_now else '🟢 BOTS RUNNING'}</span>
    </div>
    <section class="section" id="section-dashboard">
      <div class="stats-grid">
        <div class="stat-card s-green"><div class="stat-ico">🟢</div><div class="stat-body"><div class="stat-value" id="stat-online">{cur_online}</div><div class="stat-label">Online Bots</div></div></div>
        <div class="stat-card s-blue"><div class="stat-ico">📊</div><div class="stat-body"><div class="stat-value" id="stat-total">{cur_total}</div><div class="stat-label">Total Accounts</div></div></div>
        <div class="stat-card s-violet"><div class="stat-ico">⚙️</div><div class="stat-body"><div class="stat-value" id="stat-threads">{cur_threads}</div><div class="stat-label">Active Threads</div></div></div>
        <div class="stat-card s-cyan"><div class="stat-ico">📦</div><div class="stat-body"><div class="stat-value" id="stat-version" style="font-size:1.15em;">{FREEFIRE_VERSION_NAME}</div><div class="stat-label">{CURRENT_OB} · Build</div></div></div>
      </div>
    </section>
    <section class="panel">
      <div class="panel-head">
        <div class="panel-title"><div class="panel-ico amber">⚡</div> Quick Actions</div>
        <span class="pill green"><span class="dot"></span> Live</span>
      </div>
      <div class="action-grid">
        <button class="btn action-tile stop" id="btn-stop-all" onclick="doStopAll()" style="display:{'none' if stopped_now else 'inline-flex'};">
          <span class="t-ico">🛑</span><span class="t-txt"><span class="t-main">Stop All Bots</span><span class="t-sub">Disconnect every bot</span></span>
        </button>
        <button class="btn action-tile start" id="btn-start-all" onclick="doStartAll()" style="display:{'inline-flex' if stopped_now else 'none'};">
          <span class="t-ico">🚀</span><span class="t-txt"><span class="t-main">Start All Bots</span><span class="t-sub">Resume every account</span></span>
        </button>
        <button class="btn action-tile amber" onclick="doAccountRestart()">
          <span class="t-ico">♻️</span><span class="t-txt"><span class="t-main">Account Restart</span><span class="t-sub">Reconnect all bots</span></span>
        </button>
        <button class="btn action-tile pink" onclick="doSquadRecreate()">
          <span class="t-ico">🔄</span><span class="t-txt"><span class="t-main">Squad Recreate</span><span class="t-sub">Rebuild every squad</span></span>
        </button>
      </div>
    </section>
    <section class="panel section" id="section-accounts">
      <div class="panel-head">
        <div class="panel-title"><div class="panel-ico">👥</div> Account Manager</div>
        <span class="pill"><span class="dot"></span> <span id="acc-count">0</span> Accounts</span>
      </div>
      <div class="stack">
        <div class="acc-box cyan">
          <div class="box-title cyan">➕ Add Single Account</div>
          <div class="row">
            <div class="field"><label class="field-label">UID</label><input type="text" id="new-uid" placeholder="e.g. 1234567890"></div>
            <div class="field"><label class="field-label">Password</label><input type="text" id="new-pwd" placeholder="Account Password"></div>
            <button class="btn green" onclick="addSingleAccount()">➕ Add</button>
          </div>
        </div>
        <div class="acc-box pink">
          <div class="box-title pink">📂 Upload TXT (Bulk)</div>
          <div class="hint">Format: প্রতি লাইনে <b>uid:password</b> অথবা <b>uid|password</b></div>
          <div class="row" style="grid-template-columns:1fr auto; margin-top:10px;">
            <input type="file" id="acc-file" accept=".txt">
            <button class="btn pink" onclick="uploadAccFile()">📤 Upload & Replace</button>
          </div>
        </div>
        <div class="acc-box violet">
          <div class="box-title violet">✏️ Edit / View All Accounts</div>
          <textarea id="acc-content" style="height:240px; color:#4ADE80; background:#02040A;" spellcheck="false"></textarea>
          <div class="hint">Format: <b>uid:password</b> প্রতি লাইনে · <code>#</code> দিয়ে comment</div>
          <div class="btn-row">
            <button class="btn green" onclick="saveAllAccounts()" id="acc-save-btn">💾 Save All</button>
            <button class="btn amber" onclick="reloadAccounts()">🔄 Reload</button>
            <button class="btn blue" onclick="downloadAccounts()">📥 Download TXT</button>
          </div>
        </div>
      </div>
    </section>
    <section class="panel section" id="section-config">
      <div class="panel-head">
        <div class="panel-title"><div class="panel-ico green">⚙️</div> Squad Configuration</div>
        <span class="pill violet"><span class="dot"></span> Auto Save</span>
      </div>
      <form id="squad-form" onsubmit="saveSquadConfig(event)">
        <div class="stack">
          <div class="field">
            <label class="field-label">👥 Squad Size</label>
            <div class="chips">
              <label class="chip"><input type="radio" name="squad_size" value="3" {'checked' if cur_size==3 else ''}><span>4 Players</span></label>
              <label class="chip"><input type="radio" name="squad_size" value="4" {'checked' if cur_size==4 else ''}><span>5 Players</span></label>
              <label class="chip"><input type="radio" name="squad_size" value="5" {'checked' if cur_size==5 else ''}><span>6 Players</span></label>
            </div>
          </div>
          <div class="field">
            <label class="field-label">📢 World Recruit Type</label>
            <div class="chips">
              <label class="chip"><input type="radio" name="world_recruit_type" value="1" {'checked' if cur_recruit_type=="1" else ''}><span>Type 1</span></label>
              <label class="chip"><input type="radio" name="world_recruit_type" value="2" {'checked' if cur_recruit_type=="2" else ''}><span>Type 2</span></label>
              <label class="chip"><input type="radio" name="world_recruit_type" value="3" {'checked' if cur_recruit_type=="3" else ''}><span>Type 3</span></label>
              <label class="chip"><input type="radio" name="world_recruit_type" value="half" {'checked' if cur_recruit_type=="half" else ''}><span>Half</span></label>
              <label class="chip"><input type="radio" name="world_recruit_type" value="random" {'checked' if cur_recruit_type=="random" else ''}><span>Random</span></label>
            </div>
          </div>
          <div class="grid-2">
            <div class="field"><label class="field-label">📢 Recruit Count</label><input type="number" min="1" max="10" id="world_recruit_count" value="{cur_recruit}"></div>
            <div class="field"><label class="field-label">⏱️ Squad Lifetime (sec)</label><input type="number" min="5" max="3600" id="squad_lifetime_sec" value="{cur_lifetime}"></div>
          </div>
          <div class="grid-2">
            <div class="field"><label class="field-label">✨ Animation Interval (sec)</label><input type="number" min="5" max="300" id="animation_interval_sec" value="{cur_anim_int}"></div>
            <div class="field"><label class="field-label">👗 Bundle Count</label><input type="number" min="1" max="5" id="bundle_count_on_join" value="{rc_bundle_count}"></div>
          </div>
          <div class="grid-2">
            <div class="field"><label class="field-label">⏱️ Recruit Delay (sec)</label><input type="number" min="0.5" max="30" step="0.5" id="recruit_delay_sec" value="{rc_delay}"></div>
            <div class="field"><label class="field-label">🎭 Emote Delay (sec)</label><input type="number" min="0.1" max="30" step="0.1" id="emote_join_delay_sec" value="{cur_emote_delay}"></div>
          </div>
          <div class="grid-2">
            <div class="field"><label class="field-label">💬 Welcome Delay (sec)</label><input type="number" min="0.1" max="30" step="0.1" id="welcome_delay_sec" value="{cur_welcome_delay}"></div>
            <div class="field"><label class="field-label">🚫 Kick Delay (sec)</label><input type="number" min="0.1" max="30" step="0.1" id="kick_delay_sec" value="{cur_kick_delay}"></div>
          </div>
          <div class="field"><label class="field-label">🚫 Kick Message</label><input type="text" id="kick_msg" value="{kick_msg_esc}"></div>
          <div class="field">
            <label class="field-label">🔧 Feature Toggles</label>
            <div class="chips">
              <label class="chip"><input type="checkbox" id="auto_recreate_chk" {'checked' if cur_auto else ''}><span>🔁 Auto Recreate</span></label>
              <label class="chip"><input type="checkbox" id="auto_recruit_on_join_chk" {'checked' if rc_join else ''}><span>🟢 Recruit on Join</span></label>
              <label class="chip"><input type="checkbox" id="auto_recruit_on_leave_chk" {'checked' if rc_leave else ''}><span>🔴 Recruit on Leave</span></label>
              <label class="chip"><input type="checkbox" id="auto_bundle_on_join_chk" {'checked' if rc_bundle else ''}><span>👗 Bundle on Join</span></label>
              <label class="chip"><input type="checkbox" id="auto_emote_on_join_chk" {'checked' if cur_emote_join else ''}><span>🎭 Emote on Join</span></label>
              <label class="chip"><input type="checkbox" id="auto_animation_chk" {'checked' if cur_anim else ''}><span>✨ Auto Animation</span></label>
              <label class="chip"><input type="checkbox" id="auto_welcome_on_join_chk" {'checked' if cur_welcome_join else ''}><span>💬 Welcome on Join</span></label>
              <label class="chip"><input type="checkbox" id="auto_kick_on_join_chk" {'checked' if cur_kick_join else ''}><span>🚫 Auto Kick on Join</span></label>
            </div>
          </div>
          <div class="field">
            <label class="field-label">💬 Welcome Message</label>
            <textarea id="welcome_msg_ta" style="height:170px; color:#F59E0B;" spellcheck="false">{welcome_esc}</textarea>
            <div class="hint">Placeholder: <b>{{user_name}}</b></div>
          </div>
          <button type="submit" class="btn green" id="squad-save-btn" style="padding:15px; width:100%;">💾 Save Squad Config</button>
        </div>
      </form>
    </section>
    <section class="panel section" id="section-emotes">
      <div class="panel-head">
        <div class="panel-title"><div class="panel-ico pink">🎭</div> Emote Manager</div>
        <span class="pill amber"><span class="dot"></span> Web Editable</span>
      </div>
      <div class="stack">
        <div class="acc-box cyan">
          <div class="box-title cyan">🎭 Join Emote Pool</div>
          <div class="hint">Member join হলে এই emote গুলোর যেকোনো একটি random ভাবে পাঠাবে। Comma দিয়ে separate করুন।</div>
          <textarea id="join_emote_pool" style="height:80px; color:#22D3EE; margin-top:10px;" spellcheck="false">{join_emote_csv}</textarea>
        </div>
        <div class="acc-box green">
          <div class="box-title green">🤖 Bot Self-Emote</div>
          <div class="hint">Bot নিজের উপর period ভিত্তিক emote পাঠাবে।</div>
          <div class="chips" style="margin-top:10px;">
            <label class="chip"><input type="checkbox" id="bot_self_emote_enabled" {'checked' if cur_self_emote else ''}><span>🤖 Enable Self-Emote</span></label>
          </div>
          <div class="field" style="margin-top:12px;">
            <label class="field-label">⏱️ Self-Emote Interval (sec)</label>
            <input type="number" min="1" max="300" step="0.5" id="bot_self_emote_interval" value="{cur_self_emote_int}">
          </div>
          <div class="field" style="margin-top:12px;">
            <label class="field-label">🎭 Self-Emote Pool</label>
            <textarea id="bot_self_emote_pool" style="height:80px; color:#10B981;" spellcheck="false">{self_emote_csv}</textarea>
          </div>
        </div>
        <button type="button" class="btn pink" onclick="saveEmotePool()" id="emote-save-btn" style="padding:15px; width:100%;">💾 Save Emote Pool</button>
      </div>
    </section>
    <section class="panel section" id="section-bots">
      <div class="panel-head">
        <div class="panel-title"><div class="panel-ico">📋</div> Active Bots</div>
        <span class="pill green"><span class="dot"></span> Live</span>
      </div>
      <div class="table-shell">
        <table>
          <thead><tr>
            <th>Bot UID</th><th>UID</th><th>Name</th><th>Region</th>
            <th>Squad ID</th><th>Members</th><th>Time</th><th>Status</th>
          </tr></thead>
          <tbody id="accounts-tbody">
            <tr class="empty-row"><td colspan="8">🔄 Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="panel section" id="section-logs">
      <div class="panel-head">
        <div class="panel-title"><div class="panel-ico red">📜</div> Live Log</div>
        <div style="display:flex; gap:10px; align-items:center;">
          <button class="btn ghost" onclick="clearLogView()" style="padding:8px 16px; font-size:0.8em;">🗑️ Clear</button>
          <span class="pill green"><span class="dot"></span> Auto-Sync</span>
        </div>
      </div>
      <div id="live-log" class="log-shell">📡 Waiting for logs...</div>
    </section>
    <footer class="foot">© 2026 <b>MAHIR SQUAD BOT</b> · Premium Cyberpunk Edition</footer>
  </main>
</div>
<div class="toast" id="toast"></div>
<script>
let CURRENT_STOPPED = {str(stopped_now).lower()};
function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('show');
}}
function navTo(el) {{
  document.querySelectorAll('.sb-link').forEach(a => a.classList.remove('active'));
  el.classList.add('active');
  if (window.innerWidth <= 900) toggleSidebar();
}}
function showToast(msg, color) {{
  const t = document.getElementById('toast');
  t.innerText = msg;
  if (color) t.style.background = `linear-gradient(135deg, ${{color}}, ${{color}}cc)`;
  t.classList.add('show');
  clearTimeout(window._tt);
  window._tt = setTimeout(() => t.classList.remove('show'), 3500);
}}
async function doStopAll() {{
  if (!confirm('🛑 Stop ALL BOTS?')) return;
  const b = document.getElementById('btn-stop-all'); b.disabled = true;
  try {{
    const r = await fetch('/stop_all_bots', {{method:'POST'}});
    if (r.ok) {{ showToast('🛑 All Bots Stopped!', '#EF4444'); await refreshStatus(); }}
  }} catch(e) {{ showToast('❌ Network Error', '#EF4444'); }}
  b.disabled = false;
}}
async function doStartAll() {{
  if (!confirm('🚀 Start ALL BOTS?')) return;
  const b = document.getElementById('btn-start-all'); b.disabled = true;
  try {{
    const r = await fetch('/start_all_bots', {{method:'POST'}});
    if (r.ok) {{ showToast('🚀 All Bots Starting!', '#10B981'); await refreshStatus(); }}
  }} catch(e) {{ showToast('❌ Network Error', '#EF4444'); }}
  b.disabled = false;
}}
async function refreshStatus() {{
  try {{
    const r = await fetch('/api/status');
    if (!r.ok) return;
    const d = await r.json();
    CURRENT_STOPPED = d.stopped;
    updateStatusUI();
  }} catch(e) {{}}
}}
function updateStatusUI() {{
  const banner = document.getElementById('status-banner');
  const sb = document.getElementById('btn-stop-all');
  const stb = document.getElementById('btn-start-all');
  if (CURRENT_STOPPED) {{
    banner.innerText = '🛑 BOTS STOPPED';
    banner.style.background = 'linear-gradient(135deg,#EF4444,#7F1D1D)';
    sb.style.display = 'none'; stb.style.display = 'inline-flex';
  }} else {{
    banner.innerText = '🟢 BOTS RUNNING';
    banner.style.background = 'linear-gradient(135deg,#10B981,#065F46)';
    sb.style.display = 'inline-flex'; stb.style.display = 'none';
  }}
}}
async function doAccountRestart() {{
  if (!confirm('♻️ Restart ALL accounts?')) return;
  try {{
    const r = await fetch('/restart_accounts', {{method:'POST'}});
    if (r.ok) showToast('♻️ Account Restart Triggered!', '#F59E0B');
  }} catch(e) {{ showToast('❌ Error', '#EF4444'); }}
}}
async function doSquadRecreate() {{
  if (!confirm('🔄 Recreate ALL squads?')) return;
  try {{
    const r = await fetch('/recreate_squads', {{method:'POST'}});
    if (r.ok) showToast('🔄 Squad Recreate Triggered!', '#EC4899');
  }} catch(e) {{ showToast('❌ Error', '#EF4444'); }}
}}
async function saveSquadConfig(e) {{
  e.preventDefault();
  const btn = document.getElementById('squad-save-btn');
  btn.disabled = true; btn.innerText = '⏳ Saving...';
  const form = document.getElementById('squad-form');
  const size = form.querySelector('input[name="squad_size"]:checked').value;
  const rtype = form.querySelector('input[name="world_recruit_type"]:checked').value;
  const body = new URLSearchParams();
  body.append('squad_size', size);
  body.append('world_recruit_type', rtype);
  body.append('world_recruit_count', document.getElementById('world_recruit_count').value);
  body.append('squad_lifetime_sec', document.getElementById('squad_lifetime_sec').value);
  body.append('animation_interval_sec', document.getElementById('animation_interval_sec').value);
  body.append('bundle_count_on_join', document.getElementById('bundle_count_on_join').value);
  body.append('recruit_delay_sec', document.getElementById('recruit_delay_sec').value);
  body.append('emote_join_delay_sec', document.getElementById('emote_join_delay_sec').value);
  body.append('welcome_delay_sec', document.getElementById('welcome_delay_sec').value);
  body.append('kick_delay_sec', document.getElementById('kick_delay_sec').value);
  body.append('kick_msg', document.getElementById('kick_msg').value);
  body.append('auto_recreate', document.getElementById('auto_recreate_chk').checked ? '1' : '0');
  body.append('auto_recruit_on_join', document.getElementById('auto_recruit_on_join_chk').checked ? '1' : '0');
  body.append('auto_recruit_on_leave', document.getElementById('auto_recruit_on_leave_chk').checked ? '1' : '0');
  body.append('auto_bundle_on_join', document.getElementById('auto_bundle_on_join_chk').checked ? '1' : '0');
  body.append('auto_emote_on_join', document.getElementById('auto_emote_on_join_chk').checked ? '1' : '0');
  body.append('auto_animation', document.getElementById('auto_animation_chk').checked ? '1' : '0');
  body.append('auto_welcome_on_join', document.getElementById('auto_welcome_on_join_chk').checked ? '1' : '0');
  body.append('auto_kick_on_join', document.getElementById('auto_kick_on_join_chk').checked ? '1' : '0');
  body.append('welcome_msg', document.getElementById('welcome_msg_ta').value);
  try {{
    const r = await fetch('/save_squad_config', {{method:'POST', headers:{{'Content-Type':'application/x-www-form-urlencoded'}}, body: body.toString()}});
    if (r.ok) showToast('⚙️ Squad Config Saved!', '#10B981');
    else showToast('❌ Save failed', '#EF4444');
  }} catch(err) {{ showToast('❌ Error', '#EF4444'); }}
  btn.disabled = false; btn.innerText = '💾 Save Squad Config';
}}
async function saveEmotePool() {{
  const btn = document.getElementById('emote-save-btn');
  btn.disabled = true; btn.innerText = '⏳ Saving...';
  const body = new URLSearchParams();
  body.append('join_emote_pool', document.getElementById('join_emote_pool').value);
  body.append('bot_self_emote_pool', document.getElementById('bot_self_emote_pool').value);
  body.append('bot_self_emote_enabled', document.getElementById('bot_self_emote_enabled').checked ? '1' : '0');
  body.append('bot_self_emote_interval', document.getElementById('bot_self_emote_interval').value);
  try {{
    const r = await fetch('/save_emote_pool', {{method:'POST', headers:{{'Content-Type':'application/x-www-form-urlencoded'}}, body: body.toString()}});
    if (r.ok) showToast('🎭 Emote Pool Saved!', '#EC4899');
    else showToast('❌ Save failed', '#EF4444');
  }} catch(e) {{ showToast('❌ Error', '#EF4444'); }}
  btn.disabled = false; btn.innerText = '💾 Save Emote Pool';
}}
async function loadAccountsList() {{
  try {{
    const r = await fetch('/api/accounts');
    if (!r.ok) return;
    const d = await r.json();
    document.getElementById('acc-content').value = d.content || '';
    document.getElementById('acc-count').innerText = d.count || 0;
  }} catch(e) {{}}
}}
async function addSingleAccount() {{
  const uid = document.getElementById('new-uid').value.trim();
  const pwd = document.getElementById('new-pwd').value.trim();
  if (!uid || !pwd) {{ showToast('❌ UID / Password দিন', '#EF4444'); return; }}
  if (!/^[0-9]+$/.test(uid)) {{ showToast('❌ UID শুধু number', '#EF4444'); return; }}
  try {{
    const body = new URLSearchParams();
    body.append('uid', uid); body.append('password', pwd);
    const r = await fetch('/add_account', {{method:'POST', body: body.toString()}});
    if (r.ok) {{
      showToast('✅ Account যোগ হয়েছে!', '#10B981');
      document.getElementById('new-uid').value = '';
      document.getElementById('new-pwd').value = '';
      await loadAccountsList();
    }} else showToast('❌ Failed', '#EF4444');
  }} catch(e) {{ showToast('❌ Error', '#EF4444'); }}
}}
async function saveAllAccounts() {{
  const content = document.getElementById('acc-content').value;
  const btn = document.getElementById('acc-save-btn');
  btn.disabled = true; btn.innerText = '⏳ Saving...';
  try {{
    const body = new URLSearchParams();
    body.append('content', content);
    const r = await fetch('/save_accounts', {{method:'POST', body: body.toString()}});
    if (r.ok) {{
      const res = await r.text();
      showToast('💾 ' + res, '#10B981');
      await loadAccountsList();
    }} else showToast('❌ Save failed', '#EF4444');
  }} catch(e) {{ showToast('❌ Error', '#EF4444'); }}
  btn.disabled = false; btn.innerText = '💾 Save All';
}}
async function reloadAccounts() {{
  await loadAccountsList();
  showToast('🔄 Reloaded', '#3B82F6');
}}
function downloadAccounts() {{
  const content = document.getElementById('acc-content').value;
  const blob = new Blob([content], {{type: 'text/plain'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'accounts.txt';
  a.click();
  URL.revokeObjectURL(a.href);
  showToast('📥 Downloaded!', '#22D3EE');
}}
async function uploadAccFile() {{
  const fi = document.getElementById('acc-file');
  if (!fi.files || !fi.files[0]) {{ showToast('❌ File select করুন', '#EF4444'); return; }}
  const reader = new FileReader();
  reader.onload = async (e) => {{
    const content = e.target.result;
    document.getElementById('acc-content').value = content;
    try {{
      const body = new URLSearchParams();
      body.append('content', content);
      const r = await fetch('/save_accounts', {{method:'POST', body: body.toString()}});
      if (r.ok) {{
        const res = await r.text();
        showToast('📤 Uploaded — ' + res, '#EC4899');
        await loadAccountsList();
        fi.value = '';
      }} else showToast('❌ Upload failed', '#EF4444');
    }} catch(err) {{ showToast('❌ Error', '#EF4444'); }}
  }};
  reader.readAsText(fi.files[0]);
}}
async function fetchStats() {{
  try {{
    const r = await fetch('/api/stats');
    if (!r.ok) return;
    const d = await r.json();
    document.getElementById('stat-online').innerText = d.online;
    document.getElementById('stat-total').innerText = d.total;
    document.getElementById('stat-threads').innerText = d.threads;
    document.getElementById('stat-version').innerText = d.version;
    const tb = document.getElementById('accounts-tbody');
    if (d.accounts && d.accounts.length) {{
      tb.innerHTML = d.accounts.map(a => `<tr>
        <td style="font-family:'JetBrains Mono',monospace; color:var(--txt-2);">${{a.bot_uid}}</td>
        <td style="font-family:'JetBrains Mono',monospace; color:var(--txt-2);">${{a.uid}}</td>
        <td style="color:var(--cyan); font-weight:700;">${{a.name}}</td>
        <td><span style="color:var(--amber); font-weight:700;">${{a.region}}</span></td>
        <td style="color:#FACC15; font-family:'JetBrains Mono',monospace; font-weight:600;">${{a.squad_id||'Pending...'}}</td>
        <td style="color:#C084FC; font-weight:700;">${{a.squad_members||'0/0'}}</td>
        <td style="color:var(--txt-3); font-family:'JetBrains Mono',monospace;">${{a.time}}</td>
        <td><span class="badge-live">ONLINE</span></td>
      </tr>`).join('');
    }} else {{
      tb.innerHTML = '<tr class="empty-row"><td colspan="8">⚠️ No active bots</td></tr>';
    }}
  }} catch(e) {{}}
}}
async function fetchLogs() {{
  try {{
    const r = await fetch('/api/logs');
    if (!r.ok) return;
    const d = await r.json();
    const el = document.getElementById('live-log');
    const logs = d.logs || [];
    if (!logs.length) {{ el.innerHTML = '📡 Waiting for logs...'; return; }}
    const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 30;
    el.innerHTML = logs.map(l => `<div>${{l.replace(/&/g,'&amp;').replace(/</g,'&lt;')}}</div>`).join('');
    if (atBottom) el.scrollTop = el.scrollHeight;
  }} catch(e) {{}}
}}
function clearLogView() {{
  document.getElementById('live-log').innerHTML = '📡 Cleared.';
  showToast('🗑️ Log cleared', '#F59E0B');
}}
loadAccountsList(); setInterval(loadAccountsList, 15000);
fetchStats();       setInterval(fetchStats, 2000);
fetchLogs();        setInterval(fetchLogs, 2500);
refreshStatus();    setInterval(refreshStatus, 3000);
</script>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
            return

        if self.path == '/api/stats':
            with active_lock:
                accs = list(active_accounts); oc = online_count
            try: total = len(load_accounts())
            except: total = 0
            self._json_response({'online': oc, 'total': total, 'threads': len(accs),
                'version': FREEFIRE_VERSION_NAME or "loading...",
                'release': CURRENT_OB or "loading...", 'accounts': accs})
            return

        if self.path == '/api/logs':
            with log_lock: logs = list(log_buffer)
            self._json_response({'logs': logs}); return

        if self.path == '/api/accounts':
            try:
                with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f: content = f.read()
            except: content = ""
            accs = load_accounts()
            self._json_response({'content': content, 'count': len(accs),
                'accounts': [{'uid': u, 'password': p} for u, p in accs.items()]})
            return

        if self.path == '/api/status':
            self._json_response({'stopped': is_stopped(), 'online': online_count, 'total': total_accounts})
            return

        self.send_response(404); self.end_headers()

    def do_POST(self):
        raw = self._read_body()

        if self.path == '/restart_accounts':
            trigger_restart_all()
            console.print("[yellow]♻️ Account restart triggered[/yellow]")
            self._text_response('OK'); return

        if self.path == '/recreate_squads':
            trigger_recreate_all()
            console.print("[yellow]🔄 Squad recreate triggered[/yellow]")
            self._text_response('OK'); return

        if self.path == '/stop_all_bots':
            set_stop_all(True)
            console.print("[red]🛑 STOP ALL BOTS TRIGGERED[/red]")
            self._text_response('OK'); return

        if self.path == '/start_all_bots':
            set_stop_all(False)
            console.print("[green]🚀 START ALL BOTS TRIGGERED[/green]")
            self._text_response('OK'); return

        if self.path == '/save_accounts':
            params = parse_qs(raw)
            new_content = params.get('content', [''])[0]
            try:
                save_accounts_raw(new_content)
                cnt = len(load_accounts())
                console.print(f"[green]💾 Accounts saved ({cnt})[/green]")
                self._text_response(f'OK:{cnt}')
            except Exception as e:
                self._text_response(f'Error: {e}', 500)
            return

        if self.path == '/add_account':
            params = parse_qs(raw)
            uid = params.get('uid', [''])[0].strip()
            pwd = params.get('password', [''])[0].strip()
            if not uid.isdigit() or not pwd:
                self._text_response('Invalid', 400); return
            try:
                accs = load_accounts(); accs[uid] = pwd; save_accounts(accs)
                console.print(f"[green]➕ Account added: {uid}[/green]")
                self._text_response('OK')
            except Exception as e:
                self._text_response(f'Error: {e}', 500)
            return

        if self.path == '/save_squad_config':
            params = parse_qs(raw)
            try:
                size = int(params.get('squad_size', ['4'])[0])
                if size not in (3, 4, 5): size = 4
                rc = int(params.get('world_recruit_count', ['3'])[0])
                if rc < 1 or rc > 10: rc = 3
                wrt = params.get('world_recruit_type', ['1'])[0]
                if wrt not in ('1', '2', '3', 'half', 'random'): wrt = '1'
                lt = int(params.get('squad_lifetime_sec', ['5'])[0])
                if lt < 5 or lt > 3600: lt = 5
                ar  = params.get('auto_recreate', ['0'])[0] == '1'
                ajo = params.get('auto_recruit_on_join', ['0'])[0] == '1'
                alv = params.get('auto_recruit_on_leave', ['0'])[0] == '1'
                abj = params.get('auto_bundle_on_join', ['0'])[0] == '1'
                aej = params.get('auto_emote_on_join', ['0'])[0] == '1'
                aan = params.get('auto_animation', ['0'])[0] == '1'
                awj = params.get('auto_welcome_on_join', ['0'])[0] == '1'
                ako = params.get('auto_kick_on_join', ['0'])[0] == '1'
                bcj = int(params.get('bundle_count_on_join', ['2'])[0])
                if bcj < 1 or bcj > 5: bcj = 2
                ais = int(params.get('animation_interval_sec', ['10'])[0])
                if ais < 5 or ais > 300: ais = 10
                rds = float(params.get('recruit_delay_sec', ['1.5'])[0] or 1.5)
                if rds < 0.5 or rds > 30: rds = 1.5
                ejd = float(params.get('emote_join_delay_sec', ['0.5'])[0] or 0.5)
                if ejd < 0.1 or ejd > 30: ejd = 0.5
                wds = float(params.get('welcome_delay_sec', ['0.5'])[0] or 0.5)
                if wds < 0.1 or wds > 30: wds = 0.5
                kds = float(params.get('kick_delay_sec', ['1.0'])[0] or 1.0)
                if kds < 0.1 or kds > 30: kds = 1.0
                km = params.get('kick_msg', [''])[0] or "[B][C][FF0000]🚫 Auto-Kicked!"
                wm = params.get('welcome_msg', [''])[0] or DEFAULT_WELCOME_MSG
                with web_config_lock:
                    web_config['squad_size'] = size
                    web_config['world_recruit_count'] = rc
                    web_config['world_recruit_type'] = wrt
                    web_config['squad_lifetime_sec'] = lt
                    web_config['auto_recreate'] = ar
                    web_config['auto_recruit_on_join'] = ajo
                    web_config['auto_recruit_on_leave'] = alv
                    web_config['auto_bundle_on_join'] = abj
                    web_config['auto_emote_on_join'] = aej
                    web_config['auto_animation'] = aan
                    web_config['animation_interval_sec'] = ais
                    web_config['bundle_count_on_join'] = bcj
                    web_config['recruit_delay_sec'] = rds
                    web_config['welcome_msg'] = wm
                    web_config['auto_welcome_on_join'] = awj
                    web_config['auto_kick_on_join'] = ako
                    web_config['emote_join_delay_sec'] = ejd
                    web_config['welcome_delay_sec'] = wds
                    web_config['kick_delay_sec'] = kds
                    web_config['kick_msg'] = km
                save_web_config()
                console.print(f"[green]⚙️ Config Updated[/green]")
                self._text_response('OK')
            except Exception as e:
                self._text_response(f"Error: {e}", 400)
            return

        if self.path == '/save_emote_pool':
            params = parse_qs(raw)
            try:
                join_raw = params.get('join_emote_pool', [''])[0]
                self_raw = params.get('bot_self_emote_pool', [''])[0]
                bse = params.get('bot_self_emote_enabled', ['0'])[0] == '1'
                bsi = float(params.get('bot_self_emote_interval', ['8.0'])[0] or 8.0)
                if bsi < 1 or bsi > 300: bsi = 8.0

                def parse_ids(text):
                    ids = []
                    for part in re.split(r'[,\s\n;|]+', text or ''):
                        part = part.strip()
                        if part.isdigit():
                            v = int(part)
                            if 100000000 <= v <= 999999999:
                                ids.append(v)
                    return ids

                jids = parse_ids(join_raw)
                sids = parse_ids(self_raw)
                if not jids: jids = DEFAULT_JOIN_EMOTES[:]
                if not sids: sids = DEFAULT_JOIN_EMOTES[:]

                with web_config_lock:
                    web_config['join_emote_pool'] = jids
                    web_config['bot_self_emote_pool'] = sids
                    web_config['bot_self_emote_enabled'] = bse
                    web_config['bot_self_emote_interval'] = bsi

                save_web_config()
                console.print(f"[green]🎭 Emote Pool Updated (Join={len(jids)}, Self={len(sids)}, SelfOn={bse})[/green]")
                self._text_response('OK')
            except Exception as e:
                self._text_response(f'Error: {e}', 400)
            return

        self.send_response(404); self.end_headers()

    def log_message(self, format, *args): pass

# ================================================================
#   MAIN
# ================================================================
def start_web_server():
    port = 8080
    try:
        server = HTTPServer(('0.0.0.0', port), BotHandler)
        console.print(f"[bold green]🌐 Dashboard: http://localhost:{port}[/bold green]")
        webbrowser.open(f'http://localhost:{port}')
        server.serve_forever()
    except OSError:
        console.print(f"[bold red]❌ Port {port} in use.[/bold red]")

async def main_async():
    print(render('MAHIR', colors=['white', 'red'], align='center'))
    load_web_config()
    threading.Thread(target=AuTo_ResTartinG, daemon=True).start()
    threading.Thread(target=start_web_server, daemon=True).start()
    await asyncio.sleep(1)
    asyncio.create_task(batch_account_loader())
    console.print(Panel(
        "[bold green]✅ Squad System Active[/bold green]\n"
        "[cyan]🌐 http://localhost:8080[/cyan]\n"
        f"[white]📦 {CURRENT_OB} | {FREEFIRE_VERSION_NAME}[/white]\n"
        "[magenta]👥 Squad: OpEnSq + cHSq11..77[/magenta]\n"
        "[yellow]📢 Recruit: Type 1 / 2 / 3 / Half / Random[/yellow]\n"
        "[blue]💬 Team Chat: ENABLED ✅[/blue]\n"
        "[bold magenta]👗 Auto Bundle · 🎭 Join Emote · ✨ Animation[/bold magenta]\n"
        "[bold green]🎭 Auto Emote Equip ON LOGIN ✅[/bold green]\n"
        "[bold red]🛑 STOP ALL BOTS: Web One-Click ✅[/bold red]\n"
        "[bold cyan]🎭 Web-Editable Join Emote Pool ✅[/bold cyan]\n"
        "[bold violet]🤖 Bot Self-Emote Toggle ✅[/bold violet]\n"
        "[bold yellow]⚠️ NO FALLBACK — Infinite Retry Mode[/bold yellow]",
        title="[bold red]🔥 MAHIR SQUAD BOT — CYBERPUNK 🔥[/bold red]",
        border_style="bright_red", expand=False))
    while True: await asyncio.sleep(3600)

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try: loop.run_until_complete(main_async())
    except KeyboardInterrupt: console.print("\n[bold red]Shutdown.[/bold red]")

if __name__ == "__main__":
    main()