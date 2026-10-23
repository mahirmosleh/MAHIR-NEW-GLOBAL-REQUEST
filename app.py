#!/usr/bin/env python3
# MAHIR SQUAD JOIN BOT — Scan → Join → Bundle → Welcome → Emote → Exit → Ghost

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

from xC4 import (
    Join_Sq, Ghost_Final_Packet, ExiT,
    yasser_Chat, yasser_Msg, yasser_quitcaht, xBunnEr
)

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
#   AUTO UPDATE
# ================================================================
try:
    from google_play_scraper import app as _gps_app
    _GPS_AVAILABLE = True
except Exception:
    _GPS_AVAILABLE = False
    console.print("[bold yellow]⚠ google-play-scraper not installed[/bold yellow]")

DYNAMIC_SERVER_URL = CURRENT_OB = FREEFIRE_VERSION_NAME = STORE_VERSION = DYNAMIC_CLIENT_URL = login_url = ob = version = ""

def AuToUpDaTE(max_retries: int = 6, retry_delay: int = 5):
    if not _GPS_AVAILABLE:
        console.print("[bold red]❌ google-play-scraper missing![/bold red]"); sys.exit(1)
    for attempt in range(1, max_retries + 1):
        try:
            console.print(f"[cyan]🌐 [{attempt}/{max_retries}] Fetching live version...[/cyan]")
            data = _gps_app('com.dts.freefireth', lang="fr", country='CA')
            store_version = data.get("version")
            if not store_version: raise RuntimeError("Empty store version")
            api_url = f"https://version.ggwhitehawk.com/live/ver.php?version={store_version}&lang=fr&device=android&channel=android"
            r = requests.get(api_url, timeout=20)
            if r.status_code != 200: raise RuntimeError(f"HTTP {r.status_code}")
            j = r.json()
            su, obv, rp = j.get('server_url'), j.get('latest_release_version'), j.get('remote_version')
            if not all([su, obv, rp]): raise RuntimeError("Missing server data")
            return str(su).strip(), str(obv).strip(), str(rp).strip(), str(store_version).strip()
        except Exception as e:
            console.print(f"[bold yellow]⚠ Attempt {attempt} failed: {e}[/bold yellow]")
            if attempt < max_retries: time.sleep(retry_delay)
            else: console.print("[bold red]❌ All retries failed[/bold red]"); sys.exit(1)

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
📦 OB         : {CURRENT_OB}
🛒 Store Ver  : {STORE_VERSION}
🎮 Remote Ver : {FREEFIRE_VERSION_NAME}
🌐 Server     : {DYNAMIC_SERVER_URL}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

TIMEOUT = aiohttp.ClientTimeout(total=30)
WEB_CONFIG_FILE = "web_config.json"
ACCOUNTS_FILE = "accounts.txt"
GHOST_CONFIG_FILE = "ghost_config.json"

# ================================================================
#   EMOTE EQUIP
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
        if not payload: return
        region_code = payload.get("noti_region") or payload.get("lock_region")
        if not region_code: return
        base_url = REGION_SERVER_MAP.get(region_code.upper())
        if not base_url: return
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
    except Exception as e: log(f"[red]❌ Emote Equip: {e}[/red]")

# ========== TRACKING ==========
running_bots = set()
running_bots_lock = threading.Lock()
bot_status = {}
bot_lock = threading.Lock()
online_count = 0
total_accounts = 0
active_accounts = []
active_lock = threading.Lock()

# ========== SIGNAL ==========
signal_lock = threading.Lock()
_restart_timestamp = 0
_stop_all_flag = False
_stop_all_lock = threading.Lock()

def trigger_restart_all():
    global _restart_timestamp
    with signal_lock: _restart_timestamp = time.time()

def get_restart_timestamp():
    with signal_lock: return _restart_timestamp

def set_stop_all(v: bool):
    global _stop_all_flag
    with _stop_all_lock: _stop_all_flag = bool(v)

def is_stopped() -> bool:
    with _stop_all_lock: return _stop_all_flag

# ========== GHOST CONFIG ==========
GHOST_NAME = "TIKTOK : MAHIR__222"
ghost_lock = threading.Lock()

def load_ghost_config():
    global GHOST_NAME
    try:
        if os.path.exists(GHOST_CONFIG_FILE):
            with open(GHOST_CONFIG_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                if isinstance(d.get('ghost_name'), str) and d['ghost_name'].strip():
                    GHOST_NAME = d['ghost_name']
                    console.print(f"[green]👻 Ghost name loaded: {GHOST_NAME}[/green]")
    except Exception: pass

def save_ghost_config():
    try:
        with ghost_lock: d = {'ghost_name': GHOST_NAME}
        with open(GHOST_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=4)
        return True
    except: return False

# ================================================================
#   CLAIM + UID BLOCK SYSTEM
# ================================================================
claim_lock         = threading.Lock()
claimed_targets    = {}
MAX_BOTS_PER_GROUP = 4
CLAIM_WINDOW       = 3.0
CLAIM_COOLDOWN     = 3.0

# ═══════════════════════════════════════════════════════════
#   UID BLOCK SYSTEM  (web controllable)
# ═══════════════════════════════════════════════════════════
blocked_uids      = {}   # {uid_str: expiry_ts}  (0 = permanent)
blocked_uids_lock = threading.Lock()

def is_uid_blocked(uid):
    """Check if UID is currently blocked (respects web_config toggle)."""
    with web_config_lock:
        if not web_config.get("block_uid_enabled", True):
            return False
    u = str(uid); now = time.time()
    with blocked_uids_lock:
        exp = blocked_uids.get(u)
        if exp is None:
            return False
        if exp == 0 or exp > now:
            return True
        # expired → remove
        del blocked_uids[u]
        return False

def block_uid(uid):
    """Block a UID based on current web_config settings."""
    with web_config_lock:
        if not web_config.get("block_uid_enabled", True):
            return
        dur = int(web_config.get("block_uid_duration_sec", 30))
    u = str(uid)
    with blocked_uids_lock:
        blocked_uids[u] = 0 if dur <= 0 else (time.time() + dur)

def clear_blocked_uids():
    with blocked_uids_lock:
        n = len(blocked_uids); blocked_uids.clear(); return n

def get_blocked_count():
    now = time.time()
    with blocked_uids_lock:
        for u in [k for k, v in blocked_uids.items() if v != 0 and v <= now]:
            del blocked_uids[u]
        return len(blocked_uids)

def try_claim_target(owner_uid, squad_code, code):
    now = time.time()
    with claim_lock:
        # Expired claims → block UID (respecting web config)
        for u in [k for k, v in claimed_targets.items() if now - v['first_time'] > CLAIM_WINDOW]:
            block_uid(u)
            del claimed_targets[u]
        # Blocked → skip
        if is_uid_blocked(owner_uid):
            return 0
        if owner_uid in claimed_targets:
            info = claimed_targets[owner_uid]
            if info['count'] >= MAX_BOTS_PER_GROUP:
                block_uid(owner_uid); return 0
            info['count'] += 1
            return info['count']
        claimed_targets[owner_uid] = {
            'count': 1, 'first_time': now, 'msg_sent': False,
            'squad_code': squad_code, 'code': code
        }
        return 1

def try_send_welcome(owner_uid, force=False):
    with claim_lock:
        info = claimed_targets.get(owner_uid)
        if not info or info['msg_sent']: return False
        if info['count'] >= MAX_BOTS_PER_GROUP or force:
            info['msg_sent'] = True
            return True
        return False

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
    "[B][C][00FFFF]╔━━━──[FF0000] • [00FFFF]──━━━╗\n"
    "[C][FFFFFF]        ⚡ WELCOME  ⚡\n"
    "\n"
    "[C][FF0000]            {user_name}\n"
    "\n"
    "[C][00FF00]  WELCOME TO MAHIR BOT\n"
    "\n"
    "[C][00FFFF]╚━━━──[FF0000] • [00FFFF]──━━━╝\n"
    "\n"
    "[C][FFFF00]★ PREMIUM AUTO SYSTEM ★\n"
    "\n"
    "[C][FFFFFF]🎯 STATUS   : [00FF00]ONLINE 24/7\n"
    "[C][FFFFFF]🤖 SPEED    : [00FF00]ULTRA FAST\n"
    "[C][FFFFFF]🔒 SECURITY : [00FF00]PROTECTED\n"
    "\n"
    "[C][FF0000]👑 OWNER    : [00FFFF]MAHIR\n"
    "[C][FFFFFF]📱 CONTACT  : [FFFF00]@MAHIR0208\n"
    "\n"
    "[C][FFFFFF]━━━━━━━━━━━━━\n"
    "\n"
    "[C][00FF00]TYPE [FF0000]HELP [00FF00]TO VIEW COMMANDS\n"
    "\n"
    "[C][00FFFF]💚 TYPE [FF0000]APP[00FFFF] AND DOWNLOAD 💚\n"
    "[C][FF0000]🔥 ENJOY THE EXPERIENCE 🔥\n"
    "\n"
    "[C][FFFFFF]━━━━━━━━━━━━━"
)

DEFAULT_COMMANDS = {
    "/store": {"enabled": True, "match": "contains", "type": "message",
        "response": "[C][FFD700]⚡ MAHIR BOT STORE ⚡\n[C][00FF00]🤖 TCP BOT: [FFFF00]500 BDT\n[C][00FF00]🌐 Website: [FFFF00]mahir.xo.je\n[C][00FF00]👤 Owner: [FFFF00]@MAHIR0208"},
    "/app": {"enabled": True, "match": "contains", "type": "message",
        "response": "[C][B][00FFFF]📱 MAHIR TCP APP\n[C][00FF00]https://www.mediafire.com/file/lvykrek51q17hae/MAHIR_TCP.apk"},
}

# ================================================================
#   WEB CONFIG
# ================================================================
web_config = {
    "skip_level_max": 20,
    "max_bots_per_group": 4,
    "block_uid_enabled": True,          # 🛡️ UID block on/off (web)
    "block_uid_duration_sec": 30,       # 🛡️ 0 = permanent, else seconds (web)
    "welcome_msg": DEFAULT_WELCOME_MSG,
    "auto_emote_on_join": True,
    "emote_join_delay_sec": 0.3,
    "auto_bundle_on_join": True,
    "bundle_count_on_join": 2,
    "auto_animation": True,
    "animation_interval_sec": 5,
    "join_emote_pool": DEFAULT_JOIN_EMOTES[:],
    "bot_self_emote_enabled": False,
    "bot_self_emote_pool": DEFAULT_JOIN_EMOTES[:],
    "bot_self_emote_interval": 0,
    "welcome_delay_sec": 0.1,
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
            if isinstance(saved.get("skip_level_max"), int) and 0 <= saved["skip_level_max"] <= 100:
                web_config["skip_level_max"] = saved["skip_level_max"]
            if isinstance(saved.get("max_bots_per_group"), int) and 1 <= saved["max_bots_per_group"] <= 10:
                web_config["max_bots_per_group"] = saved["max_bots_per_group"]
            globals()['MAX_BOTS_PER_GROUP'] = web_config["max_bots_per_group"]
            # 🛡️ UID Block config load
            if isinstance(saved.get("block_uid_enabled"), bool):
                web_config["block_uid_enabled"] = saved["block_uid_enabled"]
            if isinstance(saved.get("block_uid_duration_sec"), int) and 0 <= saved["block_uid_duration_sec"] <= 3600:
                web_config["block_uid_duration_sec"] = saved["block_uid_duration_sec"]
            if isinstance(saved.get("bundle_count_on_join"), int) and 1 <= saved["bundle_count_on_join"] <= 5:
                web_config["bundle_count_on_join"] = saved["bundle_count_on_join"]
            for k, (lo, hi) in {"animation_interval_sec": (5, 300), "bot_self_emote_interval": (1, 300)}.items():
                v = saved.get(k)
                if isinstance(v, (int, float)) and lo <= float(v) <= hi: web_config[k] = float(v)
            for k, (lo, hi) in {"emote_join_delay_sec": (0.1, 30), "welcome_delay_sec": (0.1, 30)}.items():
                v = saved.get(k)
                if isinstance(v, (int, float)) and lo <= float(v) <= hi: web_config[k] = float(v)
            for bf in ["auto_emote_on_join", "auto_bundle_on_join", "auto_animation", "bot_self_emote_enabled"]:
                v = saved.get(bf)
                if isinstance(v, bool): web_config[bf] = v
            wm = saved.get("welcome_msg")
            if isinstance(wm, str) and wm: web_config["welcome_msg"] = wm
            for fld in ["join_emote_pool", "bot_self_emote_pool"]:
                if isinstance(saved.get(fld), list):
                    cleaned = []
                    for x in saved[fld]:
                        try: cleaned.append(int(x))
                        except: pass
                    if cleaned: web_config[fld] = cleaned
        console.print("[bold green]✅ Config Loaded[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Config Load Error: {e}[/bold red]")

def save_web_config():
    try:
        with web_config_lock:
            data = {
                "skip_level_max": web_config["skip_level_max"],
                "max_bots_per_group": web_config["max_bots_per_group"],
                "block_uid_enabled": web_config["block_uid_enabled"],
                "block_uid_duration_sec": web_config["block_uid_duration_sec"],
                "welcome_msg": web_config["welcome_msg"],
                "auto_emote_on_join": web_config["auto_emote_on_join"],
                "emote_join_delay_sec": web_config["emote_join_delay_sec"],
                "auto_bundle_on_join": web_config["auto_bundle_on_join"],
                "bundle_count_on_join": web_config["bundle_count_on_join"],
                "auto_animation": web_config["auto_animation"],
                "animation_interval_sec": web_config["animation_interval_sec"],
                "join_emote_pool": web_config["join_emote_pool"],
                "bot_self_emote_enabled": web_config["bot_self_emote_enabled"],
                "bot_self_emote_pool": web_config["bot_self_emote_pool"],
                "bot_self_emote_interval": web_config["bot_self_emote_interval"],
                "welcome_delay_sec": web_config["welcome_delay_sec"],
            }
        with open(WEB_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        console.print(f"[bold red]Config Save Error: {e}[/bold red]"); return False

# ================================================================
#   ACCOUNTS
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
    except: return {}

def save_accounts(accs, file_path=ACCOUNTS_FILE):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for uid, pwd in accs.items(): f.write(f"{uid}:{pwd}\n")
        return True
    except: return False

def save_accounts_raw(text, file_path=ACCOUNTS_FILE):
    try:
        with open(file_path, "w", encoding="utf-8") as f: f.write(text)
        return True
    except: return False

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

def xBunnEr_sync():
    return random.choice([902000011, 902000013, 902047016, 902049015, 902000154, 902000127, 902000207, 902000305, 902037031, 902042011, 902053016, 902053018])

def update_bot_info(uid, **kwargs):
    with bot_lock:
        if uid not in bot_status:
            bot_status[uid] = {"guest_uid": uid, "account_uid": "Loading...", "status": "🔄 Initializing...",
                "last_target": "None", "last_active": "N/A"}
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
            'last_target': kwargs.get('last_target', '—'),
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
    except: return None

async def Mahir_bundle_packet(bundle_id, key, iv, region="bd"):
    try:
        fields = {1: 88, 2: {1: {1: bundle_id, 2: 1}, 2: 2}}
        encrypted = await encrypt_packet((await CrEaTe_ProTo(fields)).hex(), key, iv)
        hl = await DecodE_HeX(len(encrypted) // 2)
        pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
        fh = f"{pt}000000" if len(hl) == 2 else f"{pt}00000" if len(hl) == 3 else f"{pt}0000" if len(hl) == 4 else f"{pt}000" if len(hl) == 5 else f"{pt}000000"
        return bytes.fromhex(fh + hl + encrypted)
    except: return None

async def Mahir_bundle_packet_2(bundle_id, key, iv, region="bd"):
    try:
        fields = {1: 88, 2: {1: {1: bundle_id, 2: 2}, 2: 2}}
        encrypted = await encrypt_packet((await CrEaTe_ProTo(fields)).hex(), key, iv)
        hl = await DecodE_HeX(len(encrypted) // 2)
        pt = '0514' if region.lower() == "ind" else ("0519" if region.lower() == "bd" else "0515")
        fh = f"{pt}000000" if len(hl) == 2 else f"{pt}00000" if len(hl) == 3 else f"{pt}0000" if len(hl) == 4 else f"{pt}000" if len(hl) == 5 else f"{pt}000000"
        return bytes.fromhex(fh + hl + encrypted)
    except: return None

# ================================================================
#   SQUAD HELPERS
# ================================================================
async def MAHIR_SendSquadMsg(squad_owner, message, bot_uid, key, iv):
    try:
        squad_owner = int(squad_owner); bot_uid = int(bot_uid)
        avatar_id = xBunnEr_sync()
        msg_str = str(message)
        preview = msg_str[:15] if len(msg_str) > 15 else msg_str
        fields = {
            1: 1, 2: {
                1: squad_owner, 2: bot_uid, 3: 0, 4: msg_str,
                5: int(datetime.now().timestamp()), 7: 6,
                9: {1: f"[C][FF0000]{preview}", 2: avatar_id, 3: 2, 4: 330, 5: 800000304,
                    6: 66, 7: 66, 8: "MAHIR", 9: 66, 10: 1, 11: 1,
                    13: {1: 68, 2: 67},
                    14: {1: 1158053040, 2: 8, 3: b"\x10\x15\x08\x0A\x0B\x15\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"}},
                10: "en", 13: {3: 1}, 14: {}
            }
        }
        proto = await CrEaTe_ProTo(fields)
        pk = "080112" + (await EnC_Vr(len(proto))).hex() + proto.hex()
        return await GeneRaTePk(pk, '1215', key, iv)
    except Exception as e:
        console.print(f"[red]Squad msg err: {e}[/red]"); return None

async def MAHIR_OpenSquadChat(squad_id, chat_code, key, iv):
    try:
        squad_id = int(squad_id)
        fields = {1: 3, 2: {1: squad_id, 2: 3, 3: "en", 4: str(chat_code)}}
        proto = await CrEaTe_ProTo(fields)
        pk = "080112" + (await EnC_Vr(len(proto))).hex() + proto.hex()
        return await GeneRaTePk(pk, '1215', key, iv)
    except Exception as e:
        console.print(f"[red]OpenSquadChat err: {e}[/red]"); return None

async def Emote_k(TarGeT, idT, K, V, region, bot_self_id=0):
    try:
        fields = {1: 21, 2: {1: int(bot_self_id), 2: 909000001, 5: {1: int(TarGeT), 3: int(idT)}}}
        pt = '0514' if region.lower() == "ind" else ('0519' if region.lower() == "bd" else "0515")
        return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pt, K, V)
    except: return None

# ================================================================
#   JOIN PACKETS
# ================================================================
async def Join_Group_Packet(owner_uid, K, V):
    fields = {
        1: 4, 2: {
            1: int(owner_uid), 4: "01090a0b1219202729", 6: 1, 8: 1,
            9: {
                1: "08038037628D5581020100000000000000050001000400003CFD28AF0F0000004676251400000000000000000000000000000000000000ff00000000cacfa16d",
                2: 167, 3: {10: 10}, 4: "}\\V]", 6: 14, 7: "136f6370797b1c1c", 8: "2.132.13",
                9: 2, 10: 2,
                11: "036262535136396432356c7331416456324b796f566c5272394873314344596e2b414c35587a376d52576f52586150536147794c416f7a4155474e644f5a597a5a7457527a44484d647161615366477538706f372b737354794851746f78364647707a75506f48784d5264567161727775316a4b3150484f664c5a44317a3943767662443332764372774453555a667569796e7145757872574b3171526e77517a45644f4c35456c4c4b6a6339745059706e73643932434777585a394c35315a5230373351315246366d332b786944596d372f54316d52796d46722b41302b52654b353956686641577156324c3438324474775952653955755931395539747943523677344d4c6275514778465a4f3049344d673775667278666a6f6e4e59302f68526649772f66355a6c3344694b70424f485a4557386877517a6852673748416c374a64704c6751447375784c55334d654d364c465137666b6554697a71565777664a397678562b545a68413053613369656650722f4d3878766f62687551444a6c5a68427a51637969714e736b35433271306a4c534f54756d4764437568526a394d5947796478464a594e4275673542716d6432764d7247546f4a31554973305367524130627a3036686e6c2f45742f6470564a773477324b325876347765315a374241746777545063416f32683648494a6265726b5a7a6c614c7033315a335867304251363930354c4a356848514e6d647a463449542b7a6c344e72643456694a7a336d6f4c526b655977556d58537230534a6c5a724b72336479494c4875504a464a5966574b766871537978564c59395978373572757a48522f6a455a394672642f624c632f316c356e316276684446423343496c2b37436f4f354c7575676e76434941786d3473324d6232752b56524b7756734435682b564854424c453431304a426373624d3233"
            },
            11: {1: "IDC4", 2: 384, 3: "ME"}, 13: "en",
            15: "1792699287773478920_mqysdg0li7", 16: "374f521955",
            20: {1: 21}, 23: "a_817834292384574578", 27: {1: 2, 2: 4}
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', K, V)

async def Join_CS_Packet(owner_uid, K, V):
    fields = {
        1: 4, 2: {
            1: int(owner_uid), 4: "01090a0b1219202729", 6: 5, 8: 1,
            9: {
                1: "08FBA33B62B6CCC802062E04444400000048000200460006ADDD28AF135522AF467625141101030e2d3f8d71ca3ca4f96aa054630000004f0d0e0801cacfa16d",
                2: 612, 3: {10: 80}, 4: "}\\V]", 6: 14, 7: "166e727d60661c1c", 8: "2.132.13",
                9: 2, 10: 2,
                11: "0362625351362f384c6b4a7246417456324b796f566c665068312f33463556374e686961305a664b4679777a6651795863594b7859633673537974644c4a365948622b54387375426c5961653934574b592b57493576647442312f487064647170396b4d343457656c636c3330314d463030654358427a47634530386c396e63635162536e6571664658564f31305453337a2f646d79455a7434584c342f49345743306d337033477743566843676c345844594e4b495954794976692b507332764f36364954786f3272753279394b79393468326a774d346b6a376731624b673161314d36494d3870646249785a3151376d2f6c555058517a536b48565254777a42596d534d644b724c694f302b66306e456d384c6c45706f4d35522f35774a71667155424b2f716c3167623536634b457567443349792f2f76466262502b6e737a506b6c446f436646466c6635445272644b6f376346547142515263574a716d6c4c44304f3956484e6a7470706236493533686658636c787a4e465252412b4c554d493148374a3231424c33717542512f396331705a4e4e4a5179307a464855696735446c676b6a686a412f6942696d427778427965414471793745675031335a42634f38576a39667072416e523948694d73563238554d753368707450614f6f6c6944765730626f332f616d78432b6935304d79494e30586d7039666135456b526d64657758377054355a70503756536b7265586644697342307574626a6b45303731333179735a424362663472507168597a6e4f3456784c74435179555547774467707144326e72504952712f756c4c556b4f4f47644646676d335265483648746447725736435071422b68433079496b37674c594774595850354262473970367470446b58534653344b78324c5457476931364a6c766c6362652f387530624377613676323559777339336c4d442f7a5a4b647a397665302b4e707a6d4e413d3d"
            },
            11: {1: "IDC1", 2: 144, 3: "ME"}, 13: "en",
            15: "1792699782490913531_a05rgcbeuf", 16: "374f521955",
            20: {1: 21}, 23: "a_817834292384574578", 27: {1: 2, 2: 4}
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', K, V)

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
    except: return None

def create_auth_token_online(account_uid, token, kts, key, iv):
    try:
        K = bytes.fromhex(key) if isinstance(key, str) else key
        V = bytes.fromhex(iv)  if isinstance(iv, str) else iv
        enc_token = AES.new(K, AES.MODE_CBC, V).encrypt(pad(token.encode("utf-8"), 16))
        opcode = bytes.fromhex("830c")
        return (opcode + int(account_uid).to_bytes(8, byteorder="big") + int(kts).to_bytes(4, byteorder="big") + len(enc_token).to_bytes(8, byteorder="big") + enc_token).hex()
    except: return None

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
                        if uid in active_bots:
                            try: active_bots[uid].is_running = False
                            except: pass
                            del active_bots[uid]
                        del bot_tasks[uid]
                for uid in list(bot_tasks.keys()):
                    if uid not in accounts:
                        if uid in active_bots:
                            try: active_bots[uid].is_running = False
                            except: pass
                            del active_bots[uid]
                        if not bot_tasks[uid].done(): bot_tasks[uid].cancel()
                        del bot_tasks[uid]
                        with running_bots_lock: running_bots.discard(uid)
                        last_passwords.pop(uid, None)
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
        self.current_target = None
        self.seen_restart_ts = 0
        self.last_emote_at = 0
        self.jwt_token = None
        self._animation_task = None
        self._self_emote_task = None
        update_bot_info(self.uid, status="🔄 Initializing...")

    async def _send_greeting_emote(self, target_uid):
        try:
            with web_config_lock:
                enabled = web_config.get("auto_emote_on_join", True)
                delay = float(web_config.get("emote_join_delay_sec", 0.3))
                pool = list(web_config.get("join_emote_pool", DEFAULT_JOIN_EMOTES))
            if not enabled or not pool or not self.online_writer: return
            if delay > 0: await asyncio.sleep(max(0.03, delay))
            emote_id = random.choice(pool)
            pkt = await Emote_k(int(target_uid), int(emote_id), self.key, self.iv, self.region or "bd", int(self.bot_uid or 0))
            if pkt and self.online_writer and not self.online_writer.is_closing():
                self.online_writer.write(pkt); await self.online_writer.drain()
                self.last_emote_at = time.time()
                console.print(f"[magenta][{self.uid}] 🎭 Emote → owner[/magenta]")
        except Exception as e:
            console.print(f"[yellow]⚠ [{self.uid}] emote err: {e}[/yellow]")

    async def _send_bundle(self):
        if not self.online_writer or not self.bot_uid: return
        with web_config_lock:
            enabled = web_config.get("auto_bundle_on_join", True)
            count = web_config.get("bundle_count_on_join", 2)
        if not enabled: return
        count = max(1, min(5, int(count)))
        for i in range(count):
            try:
                bid = random.choice(AUTO_BUNDLE_POOL)
                pkt = await (Mahir_bundle_packet if i == 0 else Mahir_bundle_packet_2)(bid, self.key, self.iv, self.region or "bd")
                if pkt and self.online_writer:
                    self.online_writer.write(pkt); await self.online_writer.drain()
                    if i < count - 1: await asyncio.sleep(0.12)
            except: break

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
                pkt = await Emote_k(int(self.bot_uid), int(emote_id), self.key, self.iv, self.region or "bd", int(self.bot_uid))
                if pkt and self.online_writer and not self.online_writer.is_closing():
                    self.online_writer.write(pkt); await self.online_writer.drain()
                await asyncio.sleep(max(2.0, interval))
            except asyncio.CancelledError: break
            except: await asyncio.sleep(5)

    async def _animation_loop(self):
        while self.is_running and self.is_online:
            try:
                with web_config_lock:
                    enabled = web_config.get("auto_animation", True)
                    interval = web_config.get("animation_interval_sec", 10)
                if not enabled or not self.online_writer or not self.bot_uid:
                    await asyncio.sleep(2); continue
                anim_id = random.choice(ANIMATION_POOL)
                pkt = await mahir_animation_packet(anim_id, self.key, self.iv)
                if pkt and self.online_writer and not self.online_writer.is_closing():
                    self.online_writer.write(pkt); await self.online_writer.drain()
                await asyncio.sleep(max(5, int(interval)))
            except asyncio.CancelledError: break
            except: await asyncio.sleep(5)

    async def _send_welcome(self, target_uid, target_name, chat_code):
        try:
            if not self.chat_writer: return False
            with web_config_lock:
                delay = float(web_config.get("welcome_delay_sec", 0.1))
                wt = web_config.get("welcome_msg", DEFAULT_WELCOME_MSG)
            if delay > 0: await asyncio.sleep(max(0.03, delay))

            # 1) Open squad chat
            chat_pkt = await yasser_Chat(int(target_uid), chat_code, self.key, self.iv)
            if chat_pkt and self.chat_writer:
                self.chat_writer.write(chat_pkt)
                await self.chat_writer.drain()
                await asyncio.sleep(0.06)

            # 2) Send welcome message
            welcome = wt.replace("{user_name}", str(target_name))
            msg_pkt = await yasser_Msg(welcome, int(target_uid), int(self.bot_uid), self.key, self.iv)
            if msg_pkt and self.chat_writer:
                self.chat_writer.write(msg_pkt)
                await self.chat_writer.drain()
                await asyncio.sleep(0.06)

            # 3) Quit chat
            quit_pkt = await yasser_quitcaht(int(target_uid), self.key, self.iv)
            if quit_pkt and self.chat_writer:
                self.chat_writer.write(quit_pkt)
                await self.chat_writer.drain()
            return True
        except Exception as e:
            console.print(f"[yellow]⚠ [{self.uid}] welcome err: {e}[/yellow]")
            return False

    def _socket_ok(self):
        try:
            return bool(
                self.is_online
                and self.online_writer is not None
                and not self.online_writer.is_closing()
            )
        except Exception:
            return False

    async def _handle_squad_response(self, pj):
        """JOIN → settle → EMOTE(owner) → BUNDLE(self) → ANIM → wait(≤3s) → WELCOME(slot1) → EXIT → GHOST(slot1)"""
        try:
            f5 = pj.get('5')
            if not isinstance(f5, dict): return False
            s_data = f5.get('data')
            if not isinstance(s_data, dict): return False

            target_uid = safe_get_int(s_data.get('1'))
            if not target_uid: return False

            p_info = safe_dict(s_data.get('6'))
            target_name   = safe_get_str(p_info.get('2'), 'MAHIR')
            target_region = safe_get_str(p_info.get('3'), self.region or 'BD')
            target_level  = safe_get_int(p_info.get('5'), 0)
            squad_code    = safe_get_str(s_data.get('31'))
            chat_code     = safe_get_str(s_data.get('17'))

            if not (target_uid and squad_code and chat_code): return False

            # 🆕 EARLY UID BLOCK CHECK (respects web toggle)
            if is_uid_blocked(target_uid):
                console.print(f"[dim][{self.uid}] ⏭ Skip UID {target_uid} (blocked)[/dim]")
                return False

            with web_config_lock:
                skip_lvl = web_config.get("skip_level_max", 2)
            if 0 < target_level <= skip_lvl: return False

            slot = try_claim_target(str(target_uid), squad_code, chat_code)
            if slot == 0: return False

            console.print(f"[bold green]═════ [{self.uid}] TARGET ═════[/bold green]")
            console.print(f"[cyan]Slot :[/cyan] {slot}/{MAX_BOTS_PER_GROUP}  [cyan]Name:[/cyan] {target_name}")
            console.print(f"[white]Owner:[/white] {target_uid}  [magenta]Region:[/magenta] {target_region}  [yellow]Lvl:[/yellow] {target_level}")
            console.print(f"[dim]Bot Self UID: {self.bot_uid} | Bot Region: {self.region}[/dim]")

            # ── STEP 1: JOIN ──
            try:
                if str(target_region).lower() in ('id', 'ind', 'idc1'):
                    join_pkt = await Join_CS_Packet(target_uid, self.key, self.iv)
                else:
                    join_pkt = await Join_Group_Packet(target_uid, self.key, self.iv)
                if join_pkt and self._socket_ok():
                    self.online_writer.write(join_pkt)
                    await self.online_writer.drain()
                    console.print(f"[green][{self.uid}] ✓ JOIN sent (slot {slot})[/green]")
                    update_active_account(self.uid, last_target=str(target_uid))
                else:
                    console.print(f"[red][{self.uid}] ✗ JOIN fail: pkt={join_pkt is not None} socket={self._socket_ok()}[/red]")
                    return False
            except (BrokenPipeError, ConnectionResetError, ConnectionError):
                self.is_online = False
                console.print(f"[yellow]⚠ [{self.uid}] join socket dead[/yellow]")
                return False
            except Exception as e:
                console.print(f"[red][{self.uid}] join err: {e}[/red]")
                return False

            # ── STEP 2: SETTLE (server must register bot in squad) ──
            await asyncio.sleep(0.35)

            # ── STEP 3: EMOTE → owner (FIRST, immediate) ──
            try:
                if self.bot_uid and self._socket_ok():
                    with web_config_lock:
                        emote_enabled = web_config.get("auto_emote_on_join", True)
                        emote_pool = list(web_config.get("join_emote_pool", DEFAULT_JOIN_EMOTES))
                    if emote_enabled and emote_pool:
                        emote_id = random.choice(emote_pool)
                        emote_pkt = await Emote_k(int(target_uid), int(emote_id), self.key, self.iv, self.region or "bd", int(self.bot_uid))
                        if emote_pkt and self._socket_ok():
                            self.online_writer.write(emote_pkt)
                            await self.online_writer.drain()
                            console.print(f"[magenta][{self.uid}] 🎭 EMOTE → owner ({target_uid}) id={emote_id}[/magenta]")
                        else:
                            console.print(f"[yellow]⚠ [{self.uid}] emote pkt None[/yellow]")
                    else:
                        console.print(f"[dim][{self.uid}] emote disabled or empty pool[/dim]")
                else:
                    console.print(f"[yellow]⚠ [{self.uid}] emote skipped: bot_uid={self.bot_uid}[/yellow]")
            except Exception as e:
                console.print(f"[yellow]⚠ [{self.uid}] emote err: {e}[/yellow]")

            # ── STEP 4: BUNDLE → self (immediate) ──
            try:
                if self.bot_uid and self._socket_ok():
                    with web_config_lock:
                        bundle_enabled = web_config.get("auto_bundle_on_join", True)
                        count = web_config.get("bundle_count_on_join", 2)
                    if bundle_enabled:
                        count = max(1, min(5, int(count)))
                        sent = 0
                        for i in range(count):
                            bid = random.choice(AUTO_BUNDLE_POOL)
                            pkt = await (Mahir_bundle_packet if i == 0 else Mahir_bundle_packet_2)(bid, self.key, self.iv, self.region or "bd")
                            if pkt and self._socket_ok():
                                self.online_writer.write(pkt)
                                await self.online_writer.drain()
                                sent += 1
                                await asyncio.sleep(0.15)
                        console.print(f"[blue][{self.uid}] 👗 BUNDLE x{sent}/{count}[/blue]")
                    else:
                        console.print(f"[dim][{self.uid}] bundle disabled[/dim]")
                else:
                    console.print(f"[yellow]⚠ [{self.uid}] bundle skipped: bot_uid={self.bot_uid}[/yellow]")
            except Exception as e:
                console.print(f"[yellow]⚠ [{self.uid}] bundle err: {e}[/yellow]")

            # ── STEP 5: ANIMATION (immediate) ──
            try:
                with web_config_lock:
                    anim_enabled = web_config.get("auto_animation", True)
                if anim_enabled and self._socket_ok() and self.bot_uid:
                    anim_id = random.choice(ANIMATION_POOL)
                    anim_pkt = await mahir_animation_packet(anim_id, self.key, self.iv)
                    if anim_pkt and self._socket_ok():
                        self.online_writer.write(anim_pkt)
                        await self.online_writer.drain()
                        console.print(f"[cyan][{self.uid}] ✨ ANIM → squad[/cyan]")
            except Exception as e:
                console.print(f"[yellow]⚠ [{self.uid}] anim err: {e}[/yellow]")

            # ── STEP 6: WAIT for other bots (up to CLAIM_COOLDOWN) ──
            waited = 0.35
            sock_alive = True
            while waited < CLAIM_COOLDOWN:
                if is_stopped(): break
                if not self._socket_ok():
                    sock_alive = False; break
                await asyncio.sleep(0.15)
                waited += 0.15
                with claim_lock:
                    info = claimed_targets.get(str(target_uid))
                    if not info: break
                    if info['count'] >= MAX_BOTS_PER_GROUP: break

            # ── STEP 7: WELCOME (slot 1 only) ──
            is_sender = (slot == 1)
            if is_sender and sock_alive and self._socket_ok():
                try:
                    ok = await self._send_welcome(target_uid, target_name, chat_code)
                    if ok:
                        console.print(f"[green][{self.uid}] ✓ WELCOME → {target_name}[/green]")
                    else:
                        console.print(f"[yellow]⚠ [{self.uid}] welcome returned False[/yellow]")
                except Exception as e:
                    console.print(f"[yellow]⚠ [{self.uid}] welcome err: {e}[/yellow]")

            # ── STEP 8: EXIT (all bots) ──
            if sock_alive and self._socket_ok():
                try:
                    exit_pkt = await ExiT(target_uid, self.key, self.iv)
                    if exit_pkt and self._socket_ok():
                        self.online_writer.write(exit_pkt)
                        await self.online_writer.drain()
                        await asyncio.sleep(0.05)
                        console.print(f"[cyan][{self.uid}] ✓ EXIT (uid={target_uid})[/cyan]")
                    else:
                        console.print(f"[yellow]⚠ [{self.uid}] exit pkt None[/yellow]")
                except (BrokenPipeError, ConnectionResetError, ConnectionError):
                    self.is_online = False
                    console.print(f"[yellow]⚠ [{self.uid}] exit skipped (socket dead)[/yellow]")
                except Exception as e:
                    console.print(f"[red][{self.uid}] exit err: {e}[/red]")

            # ── STEP 9: GHOST (slot 1 only) ──
            if sock_alive and is_sender and self._socket_ok():
                try:
                    with ghost_lock: gname = GHOST_NAME
                    ghost_pkt = await Ghost_Final_Packet(target_uid, gname, squad_code, self.key, self.iv)
                    if ghost_pkt and self._socket_ok():
                        self.online_writer.write(ghost_pkt)
                        await self.online_writer.drain()
                        console.print(f"[magenta][{self.uid}] 👻 GHOST ({gname})[/magenta]")
                except (BrokenPipeError, ConnectionResetError, ConnectionError):
                    self.is_online = False
                    console.print(f"[yellow]⚠ [{self.uid}] ghost skipped (socket dead)[/yellow]")
                except Exception as e:
                    console.print(f"[red][{self.uid}] ghost err: {e}[/red]")

            return True
        except Exception as e:
            console.print(f"[red]_handle_squad err: {e}[/red]")
            return False

    async def tcp_online(self, ip, port, auth_token):
        while self.is_running:
            if is_stopped(): break
            try:
                reader, writer = await asyncio.open_connection(ip, int(port))
                writer.write(bytes.fromhex(auth_token))
                await writer.drain()
                self.reader, self.online_writer = reader, writer
                self.is_online = True
                update_bot_info(self.uid, status="✅ Online")
                console.print(f"[cyan]ℹ [{self.uid}] ONLINE Connected ✅[/cyan]")

                # Start background tasks
                if self._animation_task and not self._animation_task.done(): self._animation_task.cancel()
                self._animation_task = asyncio.create_task(self._animation_loop())
                if self._self_emote_task and not self._self_emote_task.done(): self._self_emote_task.cancel()
                self._self_emote_task = asyncio.create_task(self._bot_self_emote_loop())

                # Send initial bundle (all bots look cool from connect)
                asyncio.create_task(self._send_bundle())

                # ── SCAN → JOIN LOOP ──
                while self.is_running and self.is_online:
                    if is_stopped(): break

                    if get_restart_timestamp() > self.seen_restart_ts:
                        break

                    # SCAN
                    try:
                        scan = await Join_Sq(self.key, self.iv)
                        if scan and self.online_writer:
                            self.online_writer.write(scan)
                            await self.online_writer.drain()
                    except Exception as e:
                        break

                    # Wait for 0500 response (max 3s)
                    got_target = False
                    deadline = time.time() + 3.0
                    while self.is_running and self.is_online and not got_target and time.time() < deadline:
                        if is_stopped(): break
                        try:
                            data = await asyncio.wait_for(self.reader.read(65536), timeout=0.4)
                            if not data: raise ConnectionError("EOF")
                            dh = data.hex()
                            if dh.startswith('0500'):
                                decoded = DeCode_PackEt(dh[10:])
                                if decoded:
                                    try:
                                        pj = json.loads(decoded)
                                        ok = await self._handle_squad_response(pj)
                                        if ok: got_target = True
                                    except (BrokenPipeError, ConnectionResetError):
                                        raise ConnectionError("socket dead mid-handle")
                                    except Exception as ex:
                                        console.print(f"[dim][{self.uid}] handle skip: {ex}[/dim]")
                        except asyncio.TimeoutError:
                            continue
                        except (BrokenPipeError, ConnectionResetError, ConnectionError, OSError):
                            raise

                    await asyncio.sleep(0.2 if got_target else 0.5)

            except Exception as e:
                if not is_stopped():
                    console.print(f"[yellow][{self.uid}] conn err: {e}[/yellow]")
                self.is_online = False

            for t in [self._animation_task, self._self_emote_task]:
                if t and not t.done(): t.cancel()

            if is_stopped(): break
            await asyncio.sleep(3)

    async def tcp_chat(self, ip, port, auth_token, ready_event):
        while self.is_running:
            if is_stopped(): break
            try:
                reader, writer = await asyncio.open_connection(ip, int(port))
                writer.write(bytes.fromhex(auth_token))
                await writer.drain()
                self.chat_reader, self.chat_writer = reader, writer
                ready_event.set()
                console.print(f"[cyan]ℹ [{self.uid}] CHAT Connected ✅[/cyan]")
                while self.is_running:
                    if is_stopped(): break
                    try:
                        data = await asyncio.wait_for(self.chat_reader.read(4096), timeout=5.0)
                        if not data: break
                    except asyncio.TimeoutError: continue
                    except: break
            except: pass
            if is_stopped(): break
            await asyncio.sleep(5)

    async def keep_online_forever(self):
        global online_count, BOT_OWN_ID
        while self.is_running:
            if is_stopped():
                console.print(f"[red]🛑 [{self.uid}] Stopped[/red]"); break
            try:
                self.seen_restart_ts = get_restart_timestamp()
                self.tasks = []
                oi, at = await GeNeRaTeAccAccess(self.uid, self.password)
                if not oi:
                    update_bot_info(self.uid, status="❌ Auth Failed")
                    await asyncio.sleep(15); continue
                payload = await EncRypTMajoRLoGin(oi, at, FREEFIRE_VERSION_NAME)
                resp = await MajorLogin(payload)
                if not resp:
                    update_bot_info(self.uid, status="❌ Login Failed")
                    await asyncio.sleep(15); continue
                try: auth = await DecRypTMajoRLoGin(resp)
                except:
                    update_bot_info(self.uid, status="❌ Decrypt Failed")
                    await asyncio.sleep(15); continue
                if not getattr(auth, 'token', None) or not getattr(auth, 'url', None):
                    update_bot_info(self.uid, status="❌ Empty Auth")
                    await asyncio.sleep(15); continue
                ld = await GetLoginData(auth.url, payload, auth.token)
                if not ld:
                    update_bot_info(self.uid, status="❌ Data Failed")
                    await asyncio.sleep(15); continue
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
                oip, opp = pd.Online_IP_Port.split(":")
                cip, cpp = pd.AccountIP_Port.split(":")
                oa = create_auth_token_online(auth.account_uid, auth.token, auth.timestamp, auth.key, auth.iv)
                ca = create_auth_token_chat(auth.account_uid, auth.token, auth.timestamp, auth.key, auth.iv)
                if not oa or not ca:
                    update_bot_info(self.uid, status="❌ Token Failed")
                    await asyncio.sleep(15); continue
                console.print(f"[green]✔ Online: {self.Nm} | {self.region}[/green]")
                try: await equip_emote_on_login(auth.token, logger=lambda m: console.print(f"[cyan][{self.uid}] {m}[/cyan]"))
                except: pass
                with active_lock:
                    if not any(a['uid'] == self.uid for a in active_accounts):
                        online_count += 1
                        active_accounts.append({'uid': self.uid, 'bot_uid': str(auth.account_uid), 'name': self.Nm,
                            'region': self.region or 'BD', 'time': datetime.now().strftime('%H:%M:%S'),
                            'last_target': '—'})
                update_bot_info(self.uid, status="✅ Online", account_uid=str(auth.account_uid))
                ready = asyncio.Event()
                t1 = asyncio.create_task(self.tcp_chat(cip, cpp, ca, ready))
                self.tasks.append(t1)
                await ready.wait()
                t2 = asyncio.create_task(self.tcp_online(oip, opp, oa))
                self.tasks.append(t2)
                try: await asyncio.gather(t1, t2, return_exceptions=True)
                except: pass
            except Exception as e:
                if not is_stopped():
                    console.print(f"[red]❌ UID {self.uid}: {e}[/red]")
                update_bot_info(self.uid, status="❌ Error")
            remove_active_account(self.uid)
            if is_stopped(): break
            await asyncio.sleep(3)

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
                cur_online, cur_total = online_count, total_accounts
            with web_config_lock:
                cfg = dict(web_config)
            with ghost_lock:
                cur_ghost = GHOST_NAME
            try:
                with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f: accs_raw = f.read()
            except: accs_raw = ""
            stopped_now = is_stopped()
            join_emote_csv = ",".join(str(x) for x in cfg["join_emote_pool"])
            self_emote_csv = ",".join(str(x) for x in cfg["bot_self_emote_pool"])
            welcome_esc = self._esc(cfg["welcome_msg"])
            ghost_esc = self._esc(cur_ghost)
            accs_esc = self._esc(accs_raw)

            html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>MAHIR JOIN BOT</title>
<style>
:root{{--bg:#05070F;--panel:#0F1628;--line:#1E2A44;--cyan:#22D3EE;--violet:#A855F7;--green:#10B981;--amber:#F59E0B;--red:#EF4444;--txt:#F8FAFC;--txt2:#94A3B8;--txt3:#64748B}}
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Rajdhani',system-ui,sans-serif}}
body{{background:var(--bg);color:var(--txt);min-height:100vh;padding:20px}}
.container{{max-width:1400px;margin:0 auto}}
.header{{text-align:center;padding:30px;background:linear-gradient(135deg,#0F1628,#1A2540);border:1px solid var(--line);border-radius:16px;margin-bottom:22px}}
.header h1{{font-family:'Orbitron',sans-serif;font-size:2.2em;font-weight:900;letter-spacing:3px;background:linear-gradient(135deg,#FFF,#22D3EE);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header p{{color:var(--txt2);margin-top:8px;letter-spacing:2px;font-size:0.85em;font-weight:700;text-transform:uppercase}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:22px}}
.stat{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;text-align:center}}
.stat .icon{{font-size:1.8em}}
.stat .val{{font-family:'Orbitron',sans-serif;font-size:2em;font-weight:900;color:#34D399;margin:6px 0}}
.stat .lbl{{color:var(--txt2);font-size:0.7em;letter-spacing:2px;text-transform:uppercase;font-weight:700}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:24px;margin-bottom:20px}}
.panel h2{{font-family:'Orbitron',sans-serif;font-size:1em;color:var(--cyan);letter-spacing:2px;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--line)}}
.banner{{padding:18px;border-radius:14px;text-align:center;font-family:'Orbitron',sans-serif;font-weight:900;letter-spacing:3px;font-size:1em;margin-bottom:20px;color:#FFF;text-transform:uppercase}}
.banner.run{{background:linear-gradient(135deg,#10B981,#065F46)}}
.banner.stop{{background:linear-gradient(135deg,#EF4444,#7F1D1D)}}
.actions{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:20px}}
.btn{{padding:14px 22px;border:none;border-radius:12px;font-size:0.9em;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#FFF;cursor:pointer;transition:transform 0.2s;display:inline-flex;align-items:center;justify-content:center;gap:10px}}
.btn:hover:not(:disabled){{transform:translateY(-2px)}}
.btn:disabled{{opacity:0.55;cursor:not-allowed}}
.btn.red{{background:linear-gradient(135deg,#EF4444,#7F1D1D)}}
.btn.green{{background:linear-gradient(135deg,#10B981,#065F46)}}
.btn.amber{{background:linear-gradient(135deg,#F59E0B,#C2410C)}}
.btn.violet{{background:linear-gradient(135deg,#A855F7,#7E22CE)}}
.btn.cyan{{background:linear-gradient(135deg,#06B6D4,#0891B2)}}
.field{{display:flex;flex-direction:column;gap:8px;margin-bottom:14px}}
.field-label{{color:var(--txt2);font-size:0.72em;font-weight:700;letter-spacing:2px;text-transform:uppercase}}
input,textarea,select{{width:100%;padding:12px 15px;background:rgba(5,7,15,0.8);border:1px solid var(--line);border-radius:10px;color:var(--cyan);font-family:'JetBrains Mono',monospace;font-size:0.85em;outline:none}}
input:focus,textarea:focus{{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(34,211,238,0.12)}}
textarea{{line-height:1.6;resize:vertical}}
.row2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.chip{{display:inline-flex;align-items:center;gap:8px;padding:10px 16px;border:1px solid var(--line);border-radius:10px;background:rgba(5,7,15,0.6);cursor:pointer;margin:0 8px 8px 0;font-weight:600}}
.chip input{{width:16px;height:16px;accent-color:var(--cyan)}}
.chip:has(input:checked){{border-color:var(--cyan);background:rgba(34,211,238,0.1);box-shadow:0 0 20px rgba(34,211,238,0.2)}}
table{{width:100%;border-collapse:collapse}}
th{{background:rgba(19,27,51,0.98);color:var(--cyan);font-size:0.7em;font-weight:700;letter-spacing:1.6px;text-transform:uppercase;padding:12px 15px;text-align:left}}
td{{padding:12px 15px;border-bottom:1px solid var(--line);font-size:0.85em;white-space:nowrap}}
.badge{{padding:4px 10px;border-radius:999px;background:rgba(16,185,129,0.15);color:#34D399;font-size:0.7em;font-weight:700;border:1px solid rgba(16,185,129,0.35)}}
.log{{height:400px;overflow-y:auto;background:#02040A;padding:15px;border-radius:10px;font-family:'JetBrains Mono',monospace;font-size:12px;color:#4ADE80;line-height:1.7;border:1px solid var(--line)}}
.log > div{{padding:2px 8px}}
.toast{{position:fixed;right:20px;bottom:20px;z-index:9999;min-width:250px;padding:16px 22px;border-radius:12px;background:linear-gradient(135deg,#10B981,#065F46);color:#FFF;font-weight:700;box-shadow:0 14px 42px rgba(0,0,0,0.6);opacity:0;transform:translateY(20px);transition:all 0.3s;pointer-events:none}}
.toast.show{{opacity:1;transform:translateY(0)}}
.tabs{{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}}
.tab{{padding:10px 18px;background:rgba(34,211,238,0.08);border:1px solid var(--line);border-radius:10px;color:var(--txt2);font-weight:700;cursor:pointer;font-size:0.85em;letter-spacing:1px}}
.tab.active{{background:linear-gradient(135deg,#22D3EE,#0891B2);color:#FFF;border-color:var(--cyan)}}
.tcontent{{display:none}}.tcontent.active{{display:block}}
</style></head><body>
<div class="container">
<div class="header"><h1>🔥 MAHIR JOIN BOT 🔥</h1><p>Scan → Join → Bundle → Welcome → Emote → Exit → Ghost</p></div>
<div class="banner {'stop' if stopped_now else 'run'}" id="banner">{'🛑 BOTS STOPPED' if stopped_now else '🟢 BOTS RUNNING'}</div>

<div class="stats">
<div class="stat"><div class="icon">🟢</div><div class="val" id="s-online">{cur_online}</div><div class="lbl">Online</div></div>
<div class="stat"><div class="icon">📊</div><div class="val" id="s-total">{cur_total}</div><div class="lbl">Total</div></div>
<div class="stat"><div class="icon">📦</div><div class="val" style="font-size:1.1em;">{FREEFIRE_VERSION_NAME}</div><div class="lbl">{CURRENT_OB}</div></div>
</div>

<div class="actions">
<button class="btn red" id="btn-stop" onclick="doStop()" style="display:{'none' if stopped_now else 'inline-flex'}">🛑 STOP ALL</button>
<button class="btn green" id="btn-start" onclick="doStart()" style="display:{'inline-flex' if stopped_now else 'none'}">🚀 START ALL</button>
<button class="btn amber" onclick="doRestart()">♻️ RESTART ALL</button>
</div>

<div class="panel">
<h2>⚙️ Configuration</h2>
<div class="tabs">
<button class="tab active" onclick="switchTab(event,'tc-join')">🎯 Join</button>
<button class="tab" onclick="switchTab(event,'tc-welcome')">💬 Welcome</button>
<button class="tab" onclick="switchTab(event,'tc-ghost')">👻 Ghost</button>
<button class="tab" onclick="switchTab(event,'tc-emote')">🎭 Emotes</button>
</div>

<div id="tc-join" class="tcontent active">
<div class="row2">
<div class="field"><label class="field-label">Skip Level Max (0-100)</label><input type="number" id="skip_level_max" value="{cfg['skip_level_max']}" min="0" max="100"></div>
<div class="field"><label class="field-label">Max Bots per Group (1-10)</label><input type="number" id="max_bots_per_group" value="{cfg['max_bots_per_group']}" min="1" max="10"></div>
</div>
<div class="row2">
<div class="field"><label class="field-label">Welcome Delay (s)</label><input type="number" id="welcome_delay_sec" value="{cfg['welcome_delay_sec']}" step="0.1" min="0.1" max="30"></div>
<div class="field"><label class="field-label">Emote Delay (s)</label><input type="number" id="emote_join_delay_sec" value="{cfg['emote_join_delay_sec']}" step="0.1" min="0.1" max="30"></div>
</div>
<div class="row2">
<div class="field"><label class="field-label">Animation Interval (s)</label><input type="number" id="animation_interval_sec" value="{cfg['animation_interval_sec']}" min="5" max="300"></div>
<div class="field"><label class="field-label">Bundle Count (1-5)</label><input type="number" id="bundle_count_on_join" value="{cfg['bundle_count_on_join']}" min="1" max="5"></div>
</div>
<div style="margin-bottom:10px;">
<label class="chip"><input type="checkbox" id="auto_emote_on_join" {'checked' if cfg['auto_emote_on_join'] else ''}><span>🎭 Greeting Emote on Join</span></label>
<label class="chip"><input type="checkbox" id="auto_bundle_on_join" {'checked' if cfg['auto_bundle_on_join'] else ''}><span>👗 Bundle on Join</span></label>
<label class="chip"><input type="checkbox" id="auto_animation" {'checked' if cfg['auto_animation'] else ''}><span>✨ Auto Animation</span></label>
</div>

<div style="border-top:1px solid var(--line); margin-top:16px; padding-top:16px;">
<div class="field-label" style="margin-bottom:10px; color:var(--cyan);">🛡️ UID BLOCK SYSTEM</div>
<label class="chip"><input type="checkbox" id="block_uid_enabled" {'checked' if cfg['block_uid_enabled'] else ''}><span>Enable UID Block (skip recently processed targets)</span></label>
<div class="row2" style="margin-top:10px;">
<div class="field"><label class="field-label">Block Duration (seconds — 0 = permanent)</label><input type="number" id="block_uid_duration_sec" value="{cfg['block_uid_duration_sec']}" min="0" max="3600"></div>
<div class="field"><label class="field-label">Currently Blocked</label><input type="text" id="blocked_count_display" value="Loading..." readonly style="color:#F59E0B;"></div>
</div>
<div style="display:flex; gap:10px; margin-top:10px;">
<button class="btn cyan" onclick="saveUidBlock()" id="block-save-btn" style="flex:1">💾 SAVE BLOCK CONFIG</button>
<button class="btn red" onclick="clearBlocked()" style="flex:1">🗑️ CLEAR ALL BLOCKED</button>
</div>
</div>

<button class="btn cyan" onclick="saveJoin()" id="join-save-btn" style="width:100%; margin-top:14px;">💾 SAVE JOIN CONFIG</button>
</div>

<div id="tc-welcome" class="tcontent">
<div class="field"><label class="field-label">Welcome Message</label>
<textarea id="welcome_msg" style="height:220px;color:#F59E0B;">{welcome_esc}</textarea>
<div style="color:var(--txt3);font-size:0.75em;margin-top:6px;">Placeholder: <b>{{user_name}}</b></div></div>
<button class="btn cyan" onclick="saveWelcome()" id="welcome-save-btn" style="width:100%">💾 SAVE WELCOME</button>
</div>

<div id="tc-ghost" class="tcontent">
<div class="field"><label class="field-label">Ghost Name</label>
<textarea id="ghost_name" style="height:80px;color:#A855F7;">{ghost_esc}</textarea>
<div style="color:var(--txt3);font-size:0.75em;margin-top:6px;">Final format: <code style="background:rgba(168,85,247,0.15);padding:2px 6px;border-radius:4px;">[b][c][color]Name</code> — color auto-random.</div></div>
<button class="btn violet" onclick="saveGhost()" id="ghost-save-btn" style="width:100%">💾 SAVE GHOST NAME</button>
</div>

<div id="tc-emote" class="tcontent">
<div class="field"><label class="field-label">Join Emote Pool (comma-separated)</label>
<textarea id="join_emote_pool" style="height:80px;color:#22D3EE;">{join_emote_csv}</textarea></div>
<div class="field"><label class="field-label">Bot Self-Emote Pool</label>
<textarea id="bot_self_emote_pool" style="height:80px;color:#10B981;">{self_emote_csv}</textarea></div>
<label class="chip"><input type="checkbox" id="bot_self_emote_enabled" {'checked' if cfg['bot_self_emote_enabled'] else ''}><span>🤖 Enable Self-Emote</span></label>
<div class="field" style="margin-top:10px;"><label class="field-label">Self-Emote Interval (s)</label>
<input type="number" id="bot_self_emote_interval" value="{cfg['bot_self_emote_interval']}" step="0.5" min="1" max="300"></div>
<button class="btn violet" onclick="saveEmotes()" id="emote-save-btn" style="width:100%">💾 SAVE EMOTES</button>
</div>
</div>

<div class="panel">
<h2>👥 Account Manager</h2>
<form onsubmit="saveAccounts(event)">
<div class="field"><label class="field-label">accounts.txt content (uid:password per line)</label>
<textarea id="accounts_content" style="height:200px;color:#4ADE80;">{accs_esc}</textarea></div>
<button type="submit" class="btn green" id="acc-save-btn" style="width:100%">💾 SAVE ACCOUNTS</button>
</form>
</div>

<div class="panel">
<h2>📋 Active Bots</h2>
<div style="overflow-x:auto;"><table>
<thead><tr><th>BOT UID</th><th>UID</th><th>NAME</th><th>REGION</th><th>LAST TARGET</th><th>TIME</th><th>STATUS</th></tr></thead>
<tbody id="tb"><tr><td colspan="7" style="text-align:center;padding:30px;color:var(--txt3);">Loading...</td></tr></tbody>
</table></div>
</div>

<div class="panel">
<h2>📜 Live Log</h2>
<div class="log" id="log">📡 Waiting...</div>
</div>
</div>
<div class="toast" id="toast"></div>

<script>
let CURRENT_STOPPED = {str(stopped_now).lower()};
function showToast(msg, color){{const t=document.getElementById('toast');t.innerText=msg;if(color)t.style.background=`linear-gradient(135deg,${{color}},${{color}}cc)`;else t.style.background='linear-gradient(135deg,#10B981,#065F46)';t.classList.add('show');clearTimeout(window._tt);window._tt=setTimeout(()=>t.classList.remove('show'),3000);}}
function switchTab(e,id){{document.querySelectorAll('.tcontent').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');e.currentTarget.classList.add('active');}}
function updateBanner(){{const b=document.getElementById('banner');const sb=document.getElementById('btn-stop');const stb=document.getElementById('btn-start');if(CURRENT_STOPPED){{b.innerText='🛑 BOTS STOPPED';b.className='banner stop';sb.style.display='none';stb.style.display='inline-flex';}}else{{b.innerText='🟢 BOTS RUNNING';b.className='banner run';sb.style.display='inline-flex';stb.style.display='none';}}}}
async function refreshStatus(){{try{{const r=await fetch('/api/status');if(!r.ok)return;const d=await r.json();CURRENT_STOPPED=d.stopped;updateBanner();}}catch(e){{}}}}
async function doStop(){{if(!confirm('🛑 Stop ALL bots?'))return;try{{await fetch('/stop_all_bots',{{method:'POST'}});showToast('🛑 Stopped','#EF4444');await refreshStatus();}}catch(e){{}}}}
async function doStart(){{if(!confirm('🚀 Start ALL bots?'))return;try{{await fetch('/start_all_bots',{{method:'POST'}});showToast('🚀 Started','#10B981');await refreshStatus();}}catch(e){{}}}}
async function doRestart(){{if(!confirm('♻️ Restart all accounts?'))return;try{{await fetch('/restart_accounts',{{method:'POST'}});showToast('♻️ Triggered','#F59E0B');}}catch(e){{}}}}
async function saveJoin(){{const btn=document.getElementById('join-save-btn');btn.disabled=true;const b=new URLSearchParams();b.append('skip_level_max',document.getElementById('skip_level_max').value);b.append('max_bots_per_group',document.getElementById('max_bots_per_group').value);b.append('welcome_delay_sec',document.getElementById('welcome_delay_sec').value);b.append('emote_join_delay_sec',document.getElementById('emote_join_delay_sec').value);b.append('animation_interval_sec',document.getElementById('animation_interval_sec').value);b.append('bundle_count_on_join',document.getElementById('bundle_count_on_join').value);b.append('auto_emote_on_join',document.getElementById('auto_emote_on_join').checked?'1':'0');b.append('auto_bundle_on_join',document.getElementById('auto_bundle_on_join').checked?'1':'0');b.append('auto_animation',document.getElementById('auto_animation').checked?'1':'0');try{{const r=await fetch('/save_join_config',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:b.toString()}});if(r.ok)showToast('✅ Saved','#10B981');else showToast('❌ Failed','#EF4444');}}catch(e){{showToast('❌ Error','#EF4444');}}btn.disabled=false;}}
async function saveWelcome(){{const b=new URLSearchParams();b.append('welcome_msg',document.getElementById('welcome_msg').value);try{{const r=await fetch('/save_welcome',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:b.toString()}});if(r.ok)showToast('✅ Saved','#10B981');}}catch(e){{}}}}
async function saveGhost(){{const b=new URLSearchParams();b.append('ghost_name',document.getElementById('ghost_name').value);try{{const r=await fetch('/save_ghost',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:b.toString()}});if(r.ok)showToast('👻 Ghost Saved','#A855F7');}}catch(e){{}}}}
async function saveEmotes(){{const b=new URLSearchParams();b.append('join_emote_pool',document.getElementById('join_emote_pool').value);b.append('bot_self_emote_pool',document.getElementById('bot_self_emote_pool').value);b.append('bot_self_emote_enabled',document.getElementById('bot_self_emote_enabled').checked?'1':'0');b.append('bot_self_emote_interval',document.getElementById('bot_self_emote_interval').value);try{{const r=await fetch('/save_emotes',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:b.toString()}});if(r.ok)showToast('🎭 Saved','#A855F7');}}catch(e){{}}}}
async function saveAccounts(e){{e.preventDefault();const btn=document.getElementById('acc-save-btn');btn.disabled=true;const b=new URLSearchParams();b.append('content',document.getElementById('accounts_content').value);try{{const r=await fetch('/save_accounts',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:b.toString()}});if(r.ok)showToast('💾 Accounts Saved','#10B981');}}catch(e){{}}btn.disabled=false;}}

async function saveUidBlock(){{
  const btn = document.getElementById('block-save-btn'); btn.disabled = true;
  const b = new URLSearchParams();
  b.append('block_uid_enabled', document.getElementById('block_uid_enabled').checked ? '1' : '0');
  b.append('block_uid_duration_sec', document.getElementById('block_uid_duration_sec').value);
  try {{
    const r = await fetch('/save_uid_block', {{method:'POST', headers:{{'Content-Type':'application/x-www-form-urlencoded'}}, body:b.toString()}});
    if (r.ok) showToast('🛡️ UID Block Config Saved', '#10B981');
    else showToast('❌ Failed', '#EF4444');
  }} catch(e) {{ showToast('❌ Error', '#EF4444'); }}
  btn.disabled = false;
}}
async function clearBlocked(){{
  if (!confirm('🗑️ Clear ALL blocked UIDs?')) return;
  try {{
    const r = await fetch('/clear_blocked', {{method:'POST'}});
    if (r.ok) {{ showToast('🗑️ Blocked UIDs cleared', '#F59E0B'); fetchBlockedCount(); }}
  }} catch(e) {{}}
}}
async function fetchBlockedCount(){{
  try {{
    const r = await fetch('/api/blocked_count');
    if (!r.ok) return;
    const d = await r.json();
    const el = document.getElementById('blocked_count_display');
    if (el) el.value = `${{d.count}} UID(s) blocked`;
  }} catch(e) {{}}
}}

async function fetchStats(){{try{{const r=await fetch('/api/stats');if(!r.ok)return;const d=await r.json();document.getElementById('s-online').innerText=d.online;document.getElementById('s-total').innerText=d.total;const tb=document.getElementById('tb');if(d.accounts&&d.accounts.length){{tb.innerHTML=d.accounts.map(a=>`<tr><td style="color:#94A3B8;">${{a.bot_uid}}</td><td style="color:#94A3B8;">${{a.uid}}</td><td style="color:#22D3EE;font-weight:700;">${{a.name}}</td><td style="color:#F59E0B;font-weight:700;">${{a.region}}</td><td style="color:#FCD34D;font-family:monospace;">${{a.last_target||'—'}}</td><td style="color:#64748B;">${{a.time}}</td><td><span class="badge">ONLINE</span></td></tr>`).join('');}}else{{tb.innerHTML='<tr><td colspan="7" style="text-align:center;padding:30px;color:#64748B;">No active bots</td></tr>';}}}}catch(e){{}}}}
async function fetchLogs(){{try{{const r=await fetch('/api/logs');if(!r.ok)return;const d=await r.json();const el=document.getElementById('log');const logs=d.logs||[];if(!logs.length){{el.innerHTML='📡 Waiting...';return;}}const atBottom=el.scrollTop+el.clientHeight>=el.scrollHeight-30;el.innerHTML=logs.map(l=>`<div>${{l.replace(/&/g,'&amp;').replace(/</g,'&lt;')}}</div>`).join('');if(atBottom)el.scrollTop=el.scrollHeight;}}catch(e){{}}}}
fetchStats();setInterval(fetchStats,2000);
fetchLogs();setInterval(fetchLogs,2500);
refreshStatus();setInterval(refreshStatus,3000);
fetchBlockedCount();setInterval(fetchBlockedCount,3000);
</script></body></html>"""
            self.wfile.write(html.encode('utf-8')); return

        if self.path == '/api/stats':
            with active_lock:
                accs = list(active_accounts); oc = online_count
            try: total = len(load_accounts())
            except: total = 0
            self._json_response({'online': oc, 'total': total, 'accounts': accs}); return

        if self.path == '/api/logs':
            with log_lock: logs = list(log_buffer)
            self._json_response({'logs': logs}); return

        if self.path == '/api/status':
            self._json_response({'stopped': is_stopped(), 'online': online_count, 'total': total_accounts}); return

        if self.path == '/api/blocked_count':
            with web_config_lock:
                enabled = web_config.get('block_uid_enabled', True)
                duration = web_config.get('block_uid_duration_sec', 30)
            self._json_response({
                'count': get_blocked_count(),
                'enabled': enabled,
                'duration': duration,
            }); return

        self.send_response(404); self.end_headers()

    def do_POST(self):
        raw = self._read_body()
        params = parse_qs(raw)

        if self.path == '/restart_accounts':
            trigger_restart_all(); self._text_response('OK'); return

        if self.path == '/stop_all_bots':
            set_stop_all(True); console.print("[red]🛑 STOP ALL[/red]")
            self._text_response('OK'); return

        if self.path == '/start_all_bots':
            set_stop_all(False); console.print("[green]🚀 START ALL[/green]")
            self._text_response('OK'); return

        if self.path == '/save_accounts':
            new_content = params.get('content', [''])[0]
            try:
                save_accounts_raw(new_content)
                cnt = len(load_accounts())
                console.print(f"[green]💾 Accounts saved ({cnt})[/green]")
                self._text_response(f'OK:{cnt}')
            except Exception as e: self._text_response(f'Error: {e}', 500)
            return

        if self.path == '/save_join_config':
            try:
                with web_config_lock:
                    slm = int(params.get('skip_level_max', ['2'])[0] or 2)
                    web_config['skip_level_max'] = max(0, min(100, slm))
                    mbg = int(params.get('max_bots_per_group', ['4'])[0] or 4)
                    web_config['max_bots_per_group'] = max(1, min(10, mbg))
                    globals()['MAX_BOTS_PER_GROUP'] = web_config['max_bots_per_group']
                    wd = float(params.get('welcome_delay_sec', ['0.1'])[0] or 0.1)
                    web_config['welcome_delay_sec'] = max(0.1, min(30, wd))
                    ed = float(params.get('emote_join_delay_sec', ['0.3'])[0] or 0.3)
                    web_config['emote_join_delay_sec'] = max(0.1, min(30, ed))
                    ai = int(params.get('animation_interval_sec', ['10'])[0] or 10)
                    web_config['animation_interval_sec'] = max(5, min(300, ai))
                    bc = int(params.get('bundle_count_on_join', ['2'])[0] or 2)
                    web_config['bundle_count_on_join'] = max(1, min(5, bc))
                    web_config['auto_emote_on_join'] = params.get('auto_emote_on_join', ['0'])[0] == '1'
                    web_config['auto_bundle_on_join'] = params.get('auto_bundle_on_join', ['0'])[0] == '1'
                    web_config['auto_animation'] = params.get('auto_animation', ['0'])[0] == '1'
                save_web_config()
                console.print("[green]⚙️ Join Config Updated[/green]")
                self._text_response('OK')
            except Exception as e: self._text_response(f'Err: {e}', 400)
            return

        if self.path == '/save_uid_block':
            try:
                with web_config_lock:
                    web_config['block_uid_enabled'] = params.get('block_uid_enabled', ['1'])[0] == '1'
                    dur = int(params.get('block_uid_duration_sec', ['30'])[0] or 0)
                    web_config['block_uid_duration_sec'] = max(0, min(3600, dur))
                save_web_config()
                onoff = 'ON' if web_config['block_uid_enabled'] else 'OFF'
                console.print(f"[green]🛡️ UID Block: {onoff} | Duration: {web_config['block_uid_duration_sec']}s[/green]")
                self._text_response('OK')
            except Exception as e:
                self._text_response(f'Err: {e}', 400)
            return

        if self.path == '/clear_blocked':
            n = clear_blocked_uids()
            console.print(f"[yellow]🗑️ Cleared {n} blocked UID(s)[/yellow]")
            self._text_response(f'OK:{n}')
            return

        if self.path == '/save_welcome':
            wm = params.get('welcome_msg', [''])[0] or DEFAULT_WELCOME_MSG
            with web_config_lock: web_config['welcome_msg'] = wm
            save_web_config(); self._text_response('OK'); return

        if self.path == '/save_ghost':
            gn = params.get('ghost_name', [''])[0].strip()
            if gn:
                with ghost_lock: globals()['GHOST_NAME'] = gn
                save_ghost_config()
                console.print(f"[green]👻 Ghost: {gn}[/green]")
            self._text_response('OK'); return

        if self.path == '/save_emotes':
            def parse_ids(text):
                ids = []
                for p in re.split(r'[,\s\n;|]+', text or ''):
                    p = p.strip()
                    if p.isdigit():
                        v = int(p)
                        if 100000000 <= v <= 999999999: ids.append(v)
                return ids
            jids = parse_ids(params.get('join_emote_pool', [''])[0]) or DEFAULT_JOIN_EMOTES[:]
            sids = parse_ids(params.get('bot_self_emote_pool', [''])[0]) or DEFAULT_JOIN_EMOTES[:]
            bse = params.get('bot_self_emote_enabled', ['0'])[0] == '1'
            bsi = float(params.get('bot_self_emote_interval', ['8.0'])[0] or 8.0)
            bsi = max(1, min(300, bsi))
            with web_config_lock:
                web_config['join_emote_pool'] = jids
                web_config['bot_self_emote_pool'] = sids
                web_config['bot_self_emote_enabled'] = bse
                web_config['bot_self_emote_interval'] = bsi
            save_web_config(); self._text_response('OK'); return

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
    load_ghost_config()
    threading.Thread(target=AuTo_ResTartinG, daemon=True).start()
    threading.Thread(target=start_web_server, daemon=True).start()
    await asyncio.sleep(1)
    asyncio.create_task(batch_account_loader())
    blk_state = 'ON' if web_config['block_uid_enabled'] else 'OFF'
    blk_dur = web_config['block_uid_duration_sec']
    blk_disp = f"{blk_dur}s" if blk_dur > 0 else "permanent"
    console.print(Panel(
        "[bold green]✅ Squad JOIN System Active[/bold green]\n"
        "[cyan]🌐 http://localhost:8080[/cyan]\n"
        f"[white]📦 {CURRENT_OB} | {FREEFIRE_VERSION_NAME}[/white]\n"
        "[magenta]🎯 Flow: Scan → Join → Bundle → Welcome → Emote → Exit → Ghost[/magenta]\n"
        f"[yellow]⚡ Skip Level ≤ {web_config['skip_level_max']}[/yellow]\n"
        f"[blue]👥 Max Bots per Group: {web_config['max_bots_per_group']}[/blue]\n"
        f"[green]🛡️ UID Block: {blk_state} | {blk_disp}[/green]\n"
        "[bold cyan]👻 Ghost (web editable)[/bold cyan]",
        title="[bold red]🔥 MAHIR JOIN BOT 🔥[/bold red]",
        border_style="bright_red", expand=False))
    while True: await asyncio.sleep(3600)

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try: loop.run_until_complete(main_async())
    except KeyboardInterrupt: console.print("\n[bold red]Shutdown.[/bold red]")

if __name__ == "__main__":
    main()