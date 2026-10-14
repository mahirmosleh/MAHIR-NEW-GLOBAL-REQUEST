#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MAHIR SQUAD BOT — GROUP CREATE + WORLD RECRUIT + TEAM CHAT + AUTO BUNDLE
# ✅ AUTO RECREATE EVERY 5 SECONDS (EXIT → CREATE → RECRUIT)

import subprocess
import sys
import importlib
import os
import ssl
import json
import time
import random
import asyncio
import threading
import gc
import re
import struct
from collections import deque
from datetime import datetime
from io import BytesIO
import gzip
import http.client
import uuid
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

import aiohttp
import jwt
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from cfonts import render

from protobuf_decoder.protobuf_decoder import Parser

console = Console()

# ========== LIVE LOG BUFFER ==========
log_buffer = deque(maxlen=500)
log_lock = threading.Lock()
_orig_console_print = console.print

def _patched_console_print(*args, **kwargs):
    try:
        _orig_console_print(*args, **kwargs)
    except Exception:
        pass
    try:
        text = " ".join(str(a) for a in args)
        text = re.sub(r'\[/?[a-zA-Z0-9_#= ]+\]', '', text)
        ts = datetime.now().strftime("%H:%M:%S")
        with log_lock:
            log_buffer.append(f"[{ts}] {text}")
    except Exception:
        pass

console.print = _patched_console_print

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

login_url, ob, version = "https://loginbp.ppmainecoonghj.com/", "OB55", "1.132.1"
TIMEOUT = aiohttp.ClientTimeout(total=30)
WEB_CONFIG_FILE = "web_config.json"

# ========== SIGNAL SYSTEM ==========
signal_lock = threading.Lock()
_restart_timestamp = 0
_recreate_timestamp = 0

def trigger_restart_all():
    global _restart_timestamp
    with signal_lock:
        _restart_timestamp = time.time()

def trigger_recreate_all():
    global _recreate_timestamp
    with signal_lock:
        _recreate_timestamp = time.time()

def get_restart_timestamp():
    with signal_lock:
        return _restart_timestamp

def get_recreate_timestamp():
    with signal_lock:
        return _recreate_timestamp

# ================================================================
#   ✅ SAFE FIELD EXTRACTORS
# ================================================================
def safe_get_data(field):
    if field is None:
        return None
    if isinstance(field, dict):
        return field.get("data")
    return field


def safe_get_int(field, default=None):
    val = safe_get_data(field)
    if val is None:
        return default
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return val
    if isinstance(val, (str, bytes, bytearray)):
        try:
            return int(val)
        except (ValueError, TypeError):
            return default
    return default


def safe_get_str(field, default=""):
    val = safe_get_data(field)
    if val is None:
        return default
    if isinstance(val, str):
        return val
    if isinstance(val, (bytes, bytearray)):
        try:
            return val.decode('utf-8', errors='ignore')
        except Exception:
            return default
    return str(val)


def safe_dict(field):
    val = safe_get_data(field)
    if isinstance(val, dict):
        return val
    return {}


# ================================================================
#   ✅ AUTO BUNDLE SYSTEM
# ================================================================
AUTO_BUNDLE_POOL = [
    914000002, 914000003, 914038001, 914039001,
    914042001, 914044001, 914047001, 914047002,
    914048001, 914050001, 914051001, 914053001,
]

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
    "/store": {
        "enabled": True, "match": "contains", "type": "message",
        "response": (
            "[C][FFD700]❖━━━━━━━━━━━━━━━❖\n"
            "[C][B][00FFFF]⚡ MAHIR BOT STORE ⚡\n"
            "[C][FFD700]────────────────\n"
            "[C][00FF00]🤖 TCP BOT Price : [FFFF00]500 BDT\n"
            "[C][00FF00]🌐 Website       : [FFFF00]mahir.xo.je\n"
            "[C][00FF00]👤 Owner Telegram : [FFFF00]@MAHIR0208\n"
            "[C][FFD700]❖━━━━━━━━━━━━━━━❖"
        )
    },
    "/app": {
        "enabled": True, "match": "contains", "type": "message",
        "response": (
            "[C][FFD700]❖━━━━━━━━━━━━━━━❖\n"
            "[C][B][00FFFF]📱 MAHIR TCP OFFICIAL APP 📱\n"
            "[C][FFD700]────────────────\n"
            "[C][FFFFFF]Download Link:\n"
            "[C][00FF00]https://www.mediafire.com/file/lvykrek51q17hae/MAHIR_TCP.apk\n"
            "[C][FFD700]❖━━━━━━━━━━━━━━━❖"
        )
    },
    "st": {"enabled": True, "match": "exact", "type": "recruit_squad"}
}

# ================================================================
#   WEB CONFIG
# ================================================================
# ✅ squad_lifetime_sec = 5 (৫ সেকেন্ড পরপর Auto Recreate)
web_config = {
    "squad_size": 4,
    "world_recruit_count": 3,
    "squad_lifetime_sec": 5,
    "auto_recreate": True,
    "welcome_msg": DEFAULT_WELCOME_MSG,
    "auto_recruit_on_join": True,
    "auto_recruit_on_leave": True,
    "recruit_delay_sec": 1.5,
    "auto_bundle_on_join": True,
    "bundle_count_on_join": 2,
    "commands": {},
}
web_config_lock = threading.Lock()

def to_json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_safe(item) for item in obj]
    elif isinstance(obj, (bytes, bytearray)):
        return {"__hex__": bytes(obj).hex()}
    else:
        return obj

def from_json_safe(obj):
    if isinstance(obj, dict):
        if "__hex__" in obj and len(obj) == 1:
            try: return bytes.fromhex(obj["__hex__"])
            except Exception: return b""
        result = {}
        for k, v in obj.items():
            try: key = int(k)
            except (ValueError, TypeError): key = k
            result[key] = from_json_safe(v)
        return result
    elif isinstance(obj, list):
        return [from_json_safe(item) for item in obj]
    return obj

def load_web_config():
    try:
        saved = {}
        if os.path.exists(WEB_CONFIG_FILE):
            with open(WEB_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
        with web_config_lock:
            ss = saved.get("squad_size")
            if isinstance(ss, int) and 3 <= ss <= 5:
                web_config["squad_size"] = ss
            wrc = saved.get("world_recruit_count")
            if isinstance(wrc, int) and 1 <= wrc <= 10:
                web_config["world_recruit_count"] = wrc
            slt = saved.get("squad_lifetime_sec")
            # ✅ এখন 5 সেকেন্ড থেকে অনুমোদিত
            if isinstance(slt, int) and 5 <= slt <= 3600:
                web_config["squad_lifetime_sec"] = slt
            ar = saved.get("auto_recreate")
            if isinstance(ar, bool):
                web_config["auto_recreate"] = ar
            wm = saved.get("welcome_msg")
            if isinstance(wm, str) and wm:
                web_config["welcome_msg"] = wm
            aro = saved.get("auto_recruit_on_join")
            if isinstance(aro, bool):
                web_config["auto_recruit_on_join"] = aro
            arl = saved.get("auto_recruit_on_leave")
            if isinstance(arl, bool):
                web_config["auto_recruit_on_leave"] = arl
            rds = saved.get("recruit_delay_sec")
            if isinstance(rds, (int, float)) and 0.5 <= rds <= 30:
                web_config["recruit_delay_sec"] = float(rds)
            abj = saved.get("auto_bundle_on_join")
            if isinstance(abj, bool):
                web_config["auto_bundle_on_join"] = abj
            bcj = saved.get("bundle_count_on_join")
            if isinstance(bcj, int) and 1 <= bcj <= 5:
                web_config["bundle_count_on_join"] = bcj
            cmds_saved = saved.get("commands", {})
            commands = {}
            for name, default_val in DEFAULT_COMMANDS.items():
                if name in cmds_saved:
                    try:
                        loaded = from_json_safe(cmds_saved[name])
                        if isinstance(loaded, dict): commands[name] = loaded
                        else: commands[name] = dict(default_val)
                    except Exception: commands[name] = dict(default_val)
                else:
                    commands[name] = dict(default_val)
            for name, val in cmds_saved.items():
                if name not in commands:
                    try:
                        loaded = from_json_safe(val)
                        if isinstance(loaded, dict): commands[name] = loaded
                    except Exception: pass
            web_config["commands"] = commands
        console.print(f"[bold green]✅ Squad Config Loaded (Auto-Recreate: {web_config['squad_lifetime_sec']}s)[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Config Load Error: {e}[/bold red]")
        with web_config_lock:
            web_config["commands"] = {k: dict(v) for k, v in DEFAULT_COMMANDS.items()}

def save_web_config():
    try:
        with web_config_lock:
            data = {
                "squad_size": web_config["squad_size"],
                "world_recruit_count": web_config["world_recruit_count"],
                "squad_lifetime_sec": web_config["squad_lifetime_sec"],
                "auto_recreate": web_config["auto_recreate"],
                "welcome_msg": web_config["welcome_msg"],
                "auto_recruit_on_join": web_config.get("auto_recruit_on_join", True),
                "auto_recruit_on_leave": web_config.get("auto_recruit_on_leave", True),
                "recruit_delay_sec": web_config.get("recruit_delay_sec", 1.5),
                "auto_bundle_on_join": web_config.get("auto_bundle_on_join", True),
                "bundle_count_on_join": web_config.get("bundle_count_on_join", 2),
                "commands": to_json_safe(web_config["commands"]),
            }
        with open(WEB_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        console.print(f"[bold red]Config Save Error: {e}[/bold red]")
        return False

# ================================================================
#   PROTOBUF PARSER
# ================================================================
def read_varint(data, pos):
    result = 0; shift = 0
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
        for field_num in [4, 3, 5, 6]:
            if field_num in fields:
                name_val = fields[field_num][0]
                if isinstance(name_val, (bytes, bytearray)):
                    decoded = name_val.decode('utf-8', errors='ignore')
                    if (decoded and len(decoded) < 60 and
                        not decoded.startswith("0OuCe") and
                        not decoded.startswith("eyJ") and
                        all(c.isprintable() or c in '\u200b\u200c\u200d' for c in decoded)):
                        return decoded
    except Exception: pass
    return None

def Uaa():
    versions = ['5.0.1B2','5.1.0P1','5.2.0B1']
    models = ['SM-A125F','Redmi 9A','POCO M3']
    android = random.choice(['11','12','13'])
    return f"GarenaMSDK/{random.choice(versions)}({random.choice(models)};Android {android};en-US;USA;)"

Hr = {
    'User-Agent': Uaa(), 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1", 'ReleaseVersion': ob
}

def get_random_color():
    colors = ["[FF0000]","[00FF00]","[0000FF]","[FFFF00]","[FF00FF]","[00FFFF]","[FFFFFF]","[FFA500]","[FFC0CB]","[FFD700]"]
    return random.choice(colors)

def xBunnEr():
    return int(random.choice(['902000016','902000031','902000011','902000065','902000204','902000192','902000191','902000179','902000133','902045001','902038023','902048004','902039014','902000063','902000306','902047009']))

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
    result_dict = {}
    for result in parsed_results:
        field_data = {'wire_type': result.wire_type}
        if result.wire_type in ["varint", "string", "bytes"]: field_data['data'] = result.data
        elif result.wire_type == 'length_delimited': field_data["data"] = Fix_PackEt(result.data.results)
        result_dict[result.field] = field_data
    return result_dict

def DeCode_PackEt(input_text):
    try:
        return json.dumps(Fix_PackEt(Parser().parse(input_text)))
    except Exception:
        return None

async def EnC_Vr(N):
    if N<0: return b''
    H = []
    while True:
        RedZed = N & 0x7F; N >>= 7
        if N: RedZed |= 0x80
        H.append(RedZed)
        if not N: break
    return bytes(H)

async def CrEaTe_VarianT(fn, val):
    return await EnC_Vr((fn<<3)|0) + await EnC_Vr(val)

async def CrEaTe_LenGTh(fn, val):
    ev = val.encode() if isinstance(val,str) else val
    return await EnC_Vr((fn<<3)|2) + await EnC_Vr(len(ev)) + ev

async def CrEaTe_ProTo(fields):
    packet = bytearray()
    for f, v in fields.items():
        if isinstance(f, str):
            try:
                f = int(f)
            except (ValueError, TypeError):
                continue

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
    return "0"+F if len(F)==1 else F

async def EnC_PacKeT(HeX, K, V):
    cipher = AES.new(K, AES.MODE_CBC, V)
    return cipher.encrypt(pad(bytes.fromhex(HeX),16)).hex()

async def GeneRaTePk(Pk, N, K, V):
    PkEnc = await EnC_PacKeT(Pk, K, V)
    _ = await DecodE_HeX(len(PkEnc)//2)
    HeadEr = N+"000000" if len(_)==2 else N+"00000" if len(_)==3 else N+"0000" if len(_)==4 else N+"000"
    return bytes.fromhex(HeadEr+_+PkEnc)

# ================================================================
#   ✅ ENCRYPT_PACKET (for bundle functions)
# ================================================================
async def encrypt_packet(packet_hex, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    packet_bytes = bytes.fromhex(packet_hex)
    padded_packet = pad(packet_bytes, AES.block_size)
    return cipher.encrypt(padded_packet).hex()

# ================================================================
#   ✅ BUNDLE PACKET FUNCTIONS
# ================================================================
async def mahir_animation_packet(animation_id, key, iv):
    try:
        fields = {
            1: 88,
            2: {
                1: {
                    1: int(animation_id)
                }
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()
        encrypted_packet = await encrypt_packet(packet_hex, key, iv)
        packet_length = len(encrypted_packet) // 2
        hex_length = format(packet_length, 'x')
        final_packet = "051500" + "0" * (6 - len(hex_length)) + hex_length + encrypted_packet
        return bytes.fromhex(final_packet)
    except Exception as e:
        console.print(f"[red]animation err: {e}[/red]")
        return None


async def Mahir_bundle_packet(bundle_id, key, iv, region="bd"):
    try:
        fields = {
            1: 88,
            2: {
                1: {
                    1: bundle_id,
                    2: 1
                },
                2: 2
            }
        }
        packet = await CrEaTe_ProTo(fields)
        packet_hex = packet.hex()
        encrypted = await encrypt_packet(packet_hex, key, iv)
        header_length = len(encrypted) // 2
        header_length_hex = await DecodE_HeX(header_length)

        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"

        if len(header_length_hex) == 2:
            final_header = f"{packet_type}000000"
        elif len(header_length_hex) == 3:
            final_header = f"{packet_type}00000"
        elif len(header_length_hex) == 4:
            final_header = f"{packet_type}0000"
        elif len(header_length_hex) == 5:
            final_header = f"{packet_type}000"
        else:
            final_header = f"{packet_type}000000"

        final_packet_hex = final_header + header_length_hex + encrypted
        return bytes.fromhex(final_packet_hex)
    except Exception as e:
        console.print(f"[red]bundle err: {e}[/red]")
        return None


async def Mahir_bundle_packet_2(bundle_id, key, iv, region="bd"):
    try:
        fields = {
            1: 88,
            2: {
                1: {
                    1: bundle_id,
                    2: 2
                },
                2: 2
            }
        }
        packet = await CrEaTe_ProTo(fields)
        packet_hex = packet.hex()
        encrypted = await encrypt_packet(packet_hex, key, iv)
        header_length = len(encrypted) // 2
        header_length_hex = await DecodE_HeX(header_length)

        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"

        if len(header_length_hex) == 2:
            final_header = f"{packet_type}000000"
        elif len(header_length_hex) == 3:
            final_header = f"{packet_type}00000"
        elif len(header_length_hex) == 4:
            final_header = f"{packet_type}0000"
        elif len(header_length_hex) == 5:
            final_header = f"{packet_type}000"
        else:
            final_header = f"{packet_type}000000"

        final_packet_hex = final_header + header_length_hex + encrypted
        return bytes.fromhex(final_packet_hex)
    except Exception as e:
        console.print(f"[red]bundle2 err: {e}[/red]")
        return None


# ================================================================
#   SQUAD / GROUP PACKETS
# ================================================================
async def MAHIR_OPenSq(key, iv, region, version):
    fields = {
        1: 1,
        2: {
            2: "\u0001",
            3: 43,
            4: 1,
            5: "en",
            8: [
                {1: "IDC2", 2: 171, 3: "BD"}
            ],
            9: 1,
            10: "rYUW\u0017\t\u0007NR\u000f\u0005\u0004\\W\u0002\u000fV\u0004TPQ\u0003\u000f\u0005\u0004]\u0005\u000b\u0000\u0002W\u0005\r\nVY\u0004\u0007\u0007\u0007\u0017\u0001\bNQ\fS\u0005\u000e\u0006\f\u0005\rT\u0002\r\u0000TS\u0007U\u0004X\u0006RY\u0005\u0003\u0003SW\u0000\u000eQ\u0000^\u0014\u0003\u0004JXS\u000f\u0000g{gqfePblEZJp{_xU\bmQW\f\u0007\u000f\u0015\u0007H\\U^CHXh@Ax`\u000f~\rPN~Nz\\\u001fr_ckPU\u000b\u0015\u0005\u0003Ekfp\u007fcY\u0001nWV\u0002\u0005azE~N\u0007HTg\u0007w}@\u0002{\t\u0013\u0001NeNP]DUf|]ugINs{\u0001\\rAgB_\u0004fA]\u0004\r\u001a\u0000HpOv\\\u0005|gS\u0019\\A\u007fWW\u0003\u007fTqFGi\u0004Qr\u0019dW\u0004\u0011\rD\u0002yeZ]A\u0016a\u0007Ungeg\u0007E\\P\u001b\u000b\u0004\u0005dd\ff\r\u000f\u0017\t\u000fNRyZd\u0012tZ\fe\u0007AGv\u007fw]{P\u001c\u007f\u000ff\u0005ZJK\u0004\u0005\u0014\u0001Jgq\u001frymsB\u0001\u000fd`\u001bj~[}\u0004SDZ|IxKB\u0000\n\u0011\u0002J^`tjYN\u0007WQdE[PQ\u0002_{VP`S\t\u007f\u001dP\n\u000f\u000f\u0015\u0004\u0004L{V\u0003@yP[rgJ{Hpk\u0001\u000bw\u0001Agt_\u0003HxPc\u000b\u0017\u0005E`y\ngWoy\u0006S{A\u001b``Y\u0002Xzw}dDWOKsg\t\u0013\u000eNf\u000e\\`\u0005AwJc\u0003BM\u0001^\u0000R\u0002Qoh]tbS~`G\r\u001a\u0004HibAQ\u000f^XNt~kDUWaeaNqcLQ]Py[G\u0004",
            11: 1,
            13: 1,
            14: {
                1: "08FAA33B035B3F16020859055555000200030001000000004AFA7572105C674946762514220104186fa2e8770e748c3f6a68ed75000000ff18470f0bcacfa16d",
                2: 681,
                3: {14: {11: "1106064f50055401030f03020403060155070d01540e060e020607540706030354530f041003064d715c46434b1f061f031e1205034a1c40677c5f554775755f504e677446185b584901534144685b67620f", 0: 72}},
                4: "x\\\\R",
                6: 13,
                7: {2: 80},
                8: version,
                9: 2,
                10: 1,
                11: "03626253513677542b504e4635416456324b796f566c576a326567507844414c33507138513031762b66536c626a587648434e3348414e376c472b72474637794165676e72436b553671626b694538706f534e5a582b2f7a44675a547475465650542b384d69565a507151312b444b53576f786f6d592f7156394f76755254482b7154486a78486f664169734267564970454d454e6b4c326a4763445a4a5176416d687947356b7669564e544d71515745754b32324d4e384e4931424d437445395532415156694b667948314574412b32644536464b53773132554155596363372b7753652b66676c393742756544446a58496d6e35666d45444a51535948326644484c5650676755472f51794b776e77545151324a505265352f72314830616d374264424f556b712f523246734d635475516d47364c684a547a4379345774444245795268305754366f68532f785a48736a4c7a4366506378372f386a534133352b67787642657450397a4f6f463639344945386e6e77336b507344357a6e6337593649776b4142435761776f6d572b6948594f5939686d647632706975584168416d6d6a74496f5945444c6e506e5738616f7153304f74486b732f5a3953543252447345507a3343655438774e6874756d57634b4438585445376649386c305173726a772f4a57514f76394b50307257644538593375422f2b495836757675452b487a6a4853466c75726f33515432536567595758535854714674495a61454d476c51314b7639666c59525539465047366c30663045314f7a2b2b36324339644b664c4d39315a782f6f625938726a6e682b77524a3962636e544e41715466486f72354b714d3d"
            },
            19: 329,
            21: "374f5219",
            24: {1: 21},
            27: "a_6534489873065906362"
        }
    }
    proto = await CrEaTe_ProTo(fields)
    return await GeneRaTePk(proto.hex(), '0515', key, iv)

async def MAHIR_cHSq22(Nu, bot_uid, key, iv, region):
    fields = {
        1: 17,
        2: {
            1: int(bot_uid),
            2: 1,
            3: 3,
            4: 1,
            5: "\x1a",
            8: 1
        }
    }
    if region.lower() == "ind": ptype = '0514'
    elif region.lower() == "bd": ptype = "0519"
    else: ptype = "0515"
    proto = await CrEaTe_ProTo(fields)
    return await GeneRaTePk(proto.hex(), ptype, key, iv)

async def MAHIR_World_Recruit(target_id, key, iv):
    try:
        fields = {
            1: 66,
            2: {
                1: int(target_id),
                5: {},
                9: "",
                10: 1
            }
        }
        proto = await CrEaTe_ProTo(fields)
        return await GeneRaTePk(proto.hex(), '0515', key, iv)
    except Exception as e:
        print(f"❌ World Recruit Packet Error: {e}")
        return None

async def MAHIR_LeaveSquad(key, iv, region, bot_own_id):
    fields = {1: 7, 2: {1: int(bot_own_id)}}
    if region.lower() == "ind": ptype = '0514'
    elif region.lower() == "bd": ptype = "0519"
    else: ptype = "0515"
    proto = await CrEaTe_ProTo(fields)
    return await GeneRaTePk(proto.hex(), ptype, key, iv)

async def MAHIR_SendSquadMsg(squad_owner, message, bot_uid, key, iv):
    try:
        timestamp = int(datetime.now().timestamp())
        avatar = xBunnEr()
        fields = {
            1: 1,
            2: {
                1: int(squad_owner),
                2: int(bot_uid),
                3: 0,
                4: message,
                5: timestamp,
                7: 6,
                9: {
                    1: f"[C][FF0000]{message[:15]}",
                    2: avatar,
                    3: 2,
                    4: 330,
                    5: 800000304,
                    6: 66, 7: 66,
                    8: "MAHIR",
                    9: 66, 10: 1, 11: 1,
                    13: {1: 68, 2: 67},
                    14: {1: 1158053040, 2: 8,
                         3: b"\x10\x15\x08\x0A\x0B\x15\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"}
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
        console.print(f"[bold red]❌ Squad msg error: {e}[/bold red]")
        return None

async def MAHIR_OpenSquadChat(squad_id, chat_code, key, iv):
    try:
        fields = {
            1: 3,
            2: {
                1: int(squad_id),
                2: 3,
                3: "en",
                4: str(chat_code)
            }
        }
        proto = await CrEaTe_ProTo(fields)
        pk = "080112" + (await EnC_Vr(len(proto))).hex() + proto.hex()
        return await GeneRaTePk(pk, '1215', key, iv)
    except Exception as e:
        console.print(f"[bold red]❌ OpenSquadChat error: {e}[/bold red]")
        return None

# ================================================================
#   HELP MENU
# ================================================================
async def build_help_menu(nickname="User", bot_uid="0"):
    def pg(bdr, ttl_col, ttl, items):
        out  = f"[b][c][{bdr}]┌───────────────┐\n"
        out += f"[{ttl_col}][b][c]●  {ttl} ●\n"
        out += f"[{bdr}][b][c]└───────────────┘\n"
        CLR = [
            ("ff6600", "ffd700", "ffff55", "00ffcc"),
            ("aaff00", "ff9944", "ffffff", "55ff99"),
            ("00ffaa", "ff66bb", "aaffff", "ff88ff"),
            ("00ccff", "ffee88", "ffaa44", "44ddff"),
        ]
        for i, (desc, cmd) in enumerate(items):
            bc, dc, ac, cc = CLR[i % 4]
            out += f"\n[{bc}]◆ [{dc}][b]{desc}[/b] [{ac}]→  [{cc}]{cmd}"
        out += f"\n\n[{bdr}][b][c]◆───────────────◆"
        return out

    pages = []
    safe_name = nickname if nickname and nickname != "Unknown" else "User"

    p1 = (
        f"[FF0000][b][c]◉\n"
        f"[b][c][0dffd0]Hey {safe_name} Welcome To [ffffff]MAHIR [0dffd0] BOT\n"
        f"[FF0000]• [0dffd0]আপনার কি সাহায্য লাগবে?\n"
        f"[FF0000]• [0dffd0]আপনি কি বট কিনতে চান?\n"
        f"[FF0000]• [0dffd0]নাকি বট ব্যবহার করতে চান?\n"
        f"[FF0000]• [0dffd0]বট কিনতে চাইলে কন্টাক্ট করুন\n"
        f"[FF0000]• [0dffd0]বট চালাতে চাইলে [ffffff]help [0dffd0]লিখুন\n"
        f"[FF0000][b][c]◉\n\n"
        f"[C][B][0dffd0]+------ 📊 PLAYER PROFILE ------+\n"
        f"[C][0dffd0] » Name        : [ffffff]{safe_name}\n"
        f"[C][0dffd0] » UID         : [ffffff]{bot_uid}\n"
        f"[C][B][0dffd0]+--------------------------------+"
    )
    pages.append(p1)

    pages.append(pg("ff9900", "ffee00", "GENERAL", [
        ("Help Menu",       "help / hello"),
        ("Welcome Message", "HI"),
        ("Time & Uptime",   ".time"),
        ("My Info",         "my id"),
    ]))

    pages.append(pg("00aaff", "00eeff", "SHOP & DOWNLOAD", [
        ("Bot Store",       "/store"),
        ("Android App",     "/app"),
        ("Owner Info",      "MAHIR"),
        ("Version",         ".ffv"),
    ]))

    pages.append(pg("ff44aa", "ff99dd", "SQUAD ACTIONS", [
        ("Squad Invite",    "/inv"),
        ("Auto Recruit",    "st"),
        ("Squad Size",      "/5  /6"),
        ("Leave Squad",     "/exit"),
    ]))

    footer = (
        f"[b][c][FF1493]╔═══════════════════════╗\n"
        f"[b][c][FF1493]║      👑 OWNER INFO 👑      ║\n"
        f"[b][c][FF1493]╠═══════════════════════╣\n"
        f"[b][c][FFFFFF]║ 👤 Name     : [FFD700]MAHIR\n"
        f"[b][c][FFFFFF]║ 📱 Telegram : [00FFFF]@MAHIR0208\n"
        f"[b][c][FFFFFF]║ 🎵 TikTok   : [00FFFF]@MAHIR__222\n"
        f"[b][c][FFFFFF]║ 🌐 Website  : [00FFFF]mahir.xo.je\n"
        f"[b][c][FF1493]╠═══════════════════════╣\n"
        f"[b][c][FFD700]║  ⚡ MAHIR VIP SYSTEM ONLINE ✔\n"
        f"[b][c][FFD700]║  🛡️ Thank You For Using 🛡️\n"
        f"[b][c][FF1493]╚═══════════════════════╝"
    )
    pages.append(footer)
    return pages

# ================================================================
#   AUTH / LOGIN HELPERS
# ================================================================
async def GeNeRaTeAccAccess(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {"Host":"100067.connect.garena.com","User-Agent":Uaa(),"Content-Type":"application/x-www-form-urlencoded","Connection":"close"}
    data = {"uid":uid,"password":password,"response_type":"token","client_type":"2","client_secret":"2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3","client_id":"100067"}
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.post(url, headers=headers, data=data) as resp:
                if resp.status != 200: return None, None
                data = await resp.json()
                return data.get("open_id"), data.get("access_token")
    except Exception:
        return None, None

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

async def EncRypTMajoRLoGin(open_id: str, access_token: str, version: str) -> bytes:
    fields = {
        3: str(datetime.now())[:-7], 4: "free fire", 5: 1, 7: str(version),
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
    global login_url
    base = login_url.rstrip("/")
    if not base.startswith(("http://", "https://")): base = "https://" + base
    url = f"{base}/MajorLogin"
    Hr["X-GA-SV"] = str(int(time.time()))
    Hr["ReleaseVersion"] = ob
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status != 200: return None
            raw = await response.read()
            return raw[64:] if len(raw) > 64 else raw

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    Hr['Authorization'] = f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status == 200: return await response.read()
            return None

async def DecRypTMajoRLoGin(MajoRLoGinResPonsE):
    class ParsedMajorLogin:
        def __init__(self, fields):
            self.account_uid = int(fields.get(1, 0))
            self.region = str(fields.get(2, ""))
            self.token = str(fields.get(8, ""))
            self.url = str(fields.get(10, ""))
            self.timestamp = int(fields.get(21, 0))
            raw_key = fields.get(22, b"")
            if isinstance(raw_key, str):
                try: self.key = bytes.fromhex(raw_key.replace(" ", ""))
                except: self.key = raw_key.encode()
            else: self.key = bytes(raw_key)
            raw_iv = fields.get(23, b"")
            if isinstance(raw_iv, str):
                try: self.iv = bytes.fromhex(raw_iv.replace(" ", ""))
                except: self.iv = raw_iv.encode()
            else: self.iv = bytes(raw_iv)

    def _dec_vr(buf, off):
        res, sh, st = 0, 0, off
        while True:
            if off >= len(buf): raise IndexError("Out")
            b = buf[off]; off += 1
            res += (b & 0x7F) << sh; sh += 7
            if b < 0x80: break
        return res, off - st

    def _dec_proto(buf):
        off, parts, blen = 0, [], len(buf)
        try:
            while off < blen:
                it, vl = _dec_vr(buf, off); off += vl
                wt, fn = it & 7, it >> 3
                if wt == 0: val, vl = _dec_vr(buf, off); off += vl
                elif wt == 2:
                    length, vl = _dec_vr(buf, off); off += vl
                    if off + length > blen: return None
                    val = buf[off:off + length]; off += length
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

    def _to_dict(parts):
        res = {}
        for fn, wt, v in parts:
            if wt == 2:
                try: val = v.decode("utf-8")
                except: val = v
            else: val = v
            res[fn] = val
        return res

    buf = MajoRLoGinResPonsE
    try:
        c = AES.new(b'Yg&tc%DEuh6%Zc^8', AES.MODE_CBC, b'6oyZDr22E3ychjM%')
        buf = unpad(c.decrypt(buf), AES.block_size)
    except: pass

    parsed = _dec_proto(buf)
    if parsed:
        d = _to_dict(parsed)
        if 1 in d or 8 in d or 10 in d: return ParsedMajorLogin(d)

    for o in range(len(buf)):
        parsed = _dec_proto(buf[o:])
        if parsed:
            d = _to_dict(parsed)
            if 1 in d or 8 in d or 10 in d: return ParsedMajorLogin(d)

    return ParsedMajorLogin({})

def create_auth_token_chat(account_id, jwt_token, timestamp, key, iv):
    try:
        K = bytes.fromhex(key) if isinstance(key, str) else key
        V = bytes.fromhex(iv)  if isinstance(iv,  str) else iv
        ct = AES.new(K, AES.MODE_CBC, V).encrypt(pad(jwt_token.encode('utf-8'), AES.block_size))
        header = bytes.fromhex('6d19') + int(account_id).to_bytes(8, 'big') + int(timestamp).to_bytes(4, 'big') + len(ct).to_bytes(4, 'big')
        return (header + ct).hex()
    except Exception as e:
        print(f"❌ CHAT AUTH: {e}"); return None

def create_auth_token_online(account_uid, token, kts, key, iv):
    try:
        K = bytes.fromhex(key) if isinstance(key, str) else key
        V = bytes.fromhex(iv)  if isinstance(iv,  str) else iv
        enc_token = AES.new(K, AES.MODE_CBC, V).encrypt(pad(token.encode("utf-8"), 16))
        opcode = bytes.fromhex("830c")
        return (opcode + int(account_uid).to_bytes(8, byteorder="big") + int(kts).to_bytes(4, byteorder="big") + len(enc_token).to_bytes(8, byteorder="big") + enc_token).hex()
    except Exception as e:
        print(f"❌ ONLINE AUTH: {e}"); return None

def load_accounts(file_path="accs.json"):
    try:
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f: f.write("{}")
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if str(k).isdigit()}
            return {}
    except Exception as e:
        console.print(f"[bold red]Acc Load Error: {e}[/bold red]")
        return {}

async def process_single_bot(uid, pwd, index):
    for attempt in range(1, 3):
        bot = SquadBot(uid=uid, password=pwd, server='bd', index=index)
        bot_task = asyncio.create_task(bot.keep_online_forever())
        wait_time = 0
        while wait_time < 20:
            await asyncio.sleep(0.5); wait_time += 0.5
            if bot.is_online: return True
        bot.is_running = False; bot_task.cancel()
        await asyncio.sleep(0.2)
    console.print(f"[bold red]🚫 Skipping UID {uid}.[/bold red]")
    return False

async def batch_account_loader():
    global total_accounts
    launched_accounts = set()
    active_tasks = {}
    while True:
        try:
            accounts = load_accounts()
            total_accounts = len(accounts)
            new_accounts = [(uid, pwd) for uid, pwd in accounts.items() if uid not in launched_accounts]
            for uid, pwd in new_accounts:
                if uid in launched_accounts: continue
                launched_accounts.add(uid)
                with running_bots_lock: running_bots.add(uid)
                console.print(f"[bold green]✨ New Account → UID {uid} → Launching...[/bold green]")
                task = asyncio.create_task(process_single_bot(uid, pwd, len(launched_accounts)))
                active_tasks[uid] = task
                await asyncio.sleep(0.15)
            for uid in list(active_tasks.keys()):
                if active_tasks[uid].done(): del active_tasks[uid]
        except Exception as e:
            console.print(f"[bold red]Loader Err: {e}[/bold red]")
        await asyncio.sleep(1)

def ResTarTinG():
    console.print("[bold yellow]♻️ Restarting...[/bold yellow]")
    time.sleep(0.5)
    os.execl(sys.executable, sys.executable, *sys.argv)

def AuTo_ResTartinG():
    while True:
        time.sleep(3600)
        console.print("[bold red]⚠️ Auto restart...[/bold red]")
        ResTarTinG()

# ================================================================
#   ✅ SQUAD BOT CLIENT
# ================================================================
class SquadBot:
    def __init__(self, uid, password, server='bd', index=0):
        self.uid = uid; self.password = password; self.server = server; self.index = index
        self.is_running = True
        self.online_writer = None; self.chat_writer = None; self.reader = None
        self.key = None; self.iv = None; self.region = None; self.tasks = []
        self.is_online = False; self.Nm = "Unknown"; self.bot_uid = None
        self.chat_reader = None
        self.squad_created = False
        self.squad_members = set()
        self.member_names = {}
        self.current_squad_id = None
        self.current_chat_code = None
        self.seen_recreate_ts = 0
        self.seen_restart_ts = 0
        self.squad_created_at = 0
        self.last_recruit_at = 0
        self.last_bundle_at = 0
        self._recruit_lock = asyncio.Lock()
        self._bundle_lock = asyncio.Lock()
        # ✅ নতুন lock — একই সাথে দুইবার recreate আটকাতে
        self._recreate_lock = asyncio.Lock()
        update_bot_info(self.uid, status="🔄 Initializing...", squad_active=False)

    async def _send_bundle_on_join(self):
        if not self.online_writer or not self.bot_uid:
            return False

        async with self._bundle_lock:
            now = time.time()
            if now - self.last_bundle_at < _BUNDLE_COOLDOWN:
                return False

            with web_config_lock:
                enabled = web_config.get("auto_bundle_on_join", True)
                count = web_config.get("bundle_count_on_join", 2)

            if not enabled:
                return False

            count = max(1, min(5, int(count)))

            sent = 0
            for i in range(count):
                try:
                    bundle_id = random.choice(AUTO_BUNDLE_POOL)

                    if i == 0:
                        pkt = await Mahir_bundle_packet(bundle_id, self.key, self.iv, self.region or "bd")
                    else:
                        pkt = await Mahir_bundle_packet_2(bundle_id, self.key, self.iv, self.region or "bd")

                    if pkt:
                        self.online_writer.write(pkt)
                        await self.online_writer.drain()
                        sent += 1
                        await asyncio.sleep(0.5)
                except Exception as e:
                    console.print(f"[bold yellow]⚠ [{self.uid}] Bundle err: {e}[/bold yellow]")
                    break

            self.last_bundle_at = time.time()
            if sent:
                console.print(
                    f"[bold magenta]👗 [{self.uid}] Auto Bundle × {sent}[/bold magenta] "
                    f"[bold yellow](on join)[/bold yellow]"
                )
            return sent > 0

    async def _send_world_recruit(self, reason="manual", count=None):
        if not self.online_writer or not self.bot_uid:
            return False

        async with self._recruit_lock:
            with web_config_lock:
                delay = web_config.get("recruit_delay_sec", 1.5)
                default_count = web_config.get("world_recruit_count", 3)

            n = count if count is not None else default_count
            n = max(1, min(10, int(n)))

            now = time.time()
            if now - self.last_recruit_at < 2.0 and reason != "initial":
                return False

            sent = 0
            for i in range(n):
                try:
                    pkt = await MAHIR_World_Recruit(self.bot_uid, self.key, self.iv)
                    if pkt:
                        self.online_writer.write(pkt)
                        await self.online_writer.drain()
                        sent += 1
                        await asyncio.sleep(0.35)
                except Exception as e:
                    console.print(f"[bold yellow]⚠ [{self.uid}] Recruit err: {e}[/bold yellow]")
                    break

            self.last_recruit_at = time.time()
            if sent:
                icon = {"join": "🟢", "leave": "🔴", "initial": "🚀", "manual": "📢"}.get(reason, "📢")
                console.print(
                    f"[bold cyan]{icon} [{self.uid}] World Recruit × {sent}[/bold cyan] "
                    f"[bold yellow](reason: {reason})[/bold yellow]"
                )
            return sent > 0

    async def _build_and_send_squad(self):
        try:
            with web_config_lock:
                size_code = web_config.get("squad_size", 4)
                recruit_count = web_config.get("world_recruit_count", 3)

            open_pkt = await MAHIR_OPenSq(self.key, self.iv, self.region, version)
            if not open_pkt or not self.online_writer:
                return False
            self.online_writer.write(open_pkt)
            await self.online_writer.drain()
            await asyncio.sleep(0.4)
            console.print(f"[bold cyan]ℹ [{self.uid}] Squad Created ✅[/bold cyan]")

            try:
                open_pkt2 = await MAHIR_OPenSq(self.key, self.iv, self.region, version)
                self.online_writer.write(open_pkt2)
                await self.online_writer.drain()
                await asyncio.sleep(0.3)
            except Exception: pass

            try:
                size_pkt = await MAHIR_cHSq22(size_code, self.bot_uid, self.key, self.iv, self.region)
                self.online_writer.write(size_pkt)
                await self.online_writer.drain()
                console.print(f"[bold cyan]ℹ [{self.uid}] Squad Size Set ({size_code}) ✅[/bold cyan]")
                await asyncio.sleep(0.3)
            except Exception as e:
                console.print(f"[bold yellow]⚠ Squad size error: {e}[/bold yellow]")

            # ✅ Only World Recruit — no WRR
            await self._send_world_recruit(reason="initial", count=recruit_count)

            self.squad_created = True
            self.squad_created_at = time.time()
            self.squad_members.clear()
            self.member_names.clear()
            update_bot_info(self.uid, status="✅ Squad Active", squad_active=True)
            return True
        except Exception as e:
            console.print(f"[bold red]Squad create err [{self.uid}]: {e}[/bold red]")
            return False

    # ✅ NEW: Lock-protected recreate — ৫ সেকেন্ড পরপর exit → create → recruit
    async def _do_recreate(self):
        # একই সাথে দুইবার recreate আটকাতে
        if self._recreate_lock.locked():
            return False
        async with self._recreate_lock:
            try:
                console.print(f"[bold yellow]🔄 [{self.uid}] Recreating squad (5s cycle)...[/bold yellow]")

                # 1️⃣ Group Exit
                if self.online_writer and self.bot_uid:
                    try:
                        exit_pkt = await MAHIR_LeaveSquad(
                            self.key, self.iv, self.region, self.bot_uid
                        )
                        if exit_pkt:
                            self.online_writer.write(exit_pkt)
                            await self.online_writer.drain()
                            console.print(f"[bold red]🚪 [{self.uid}] Exited old group[/bold red]")
                    except Exception:
                        pass

                self.squad_members.clear()
                self.member_names.clear()
                self.current_squad_id = None
                self.current_chat_code = None
                self.squad_created = False
                update_active_account(self.uid, squad_id='Pending...', squad_members='0/0')

                await asyncio.sleep(0.5)

                # 2️⃣ Group Create + World Recruit Requests
                return await self._build_and_send_squad()

            except Exception as e:
                console.print(f"[bold red]Recreate err [{self.uid}]: {e}[/bold red]")
            return False

    async def Auto_Squad_Welcome(self, squad_id, chat_code, user_uid, user_name="Player"):
        try:
            tracking_key = f"{self.bot_uid}_{squad_id}_{user_uid}"
            if tracking_key in welcome_tracking:
                return
            welcome_tracking[tracking_key] = time.time()
            if not self.chat_writer: return

            open_pkt = await MAHIR_OpenSquadChat(squad_id, chat_code, self.key, self.iv)
            if open_pkt:
                self.chat_writer.write(open_pkt)
                await self.chat_writer.drain()
                await asyncio.sleep(0.4)

            with web_config_lock:
                welcome_template = web_config.get("welcome_msg", DEFAULT_WELCOME_MSG)
            welcome_msg = welcome_template.replace("{user_name}", str(user_name))

            msg_pkt = await MAHIR_SendSquadMsg(squad_id, welcome_msg, self.bot_uid, self.key, self.iv)
            if msg_pkt:
                self.chat_writer.write(msg_pkt)
                await self.chat_writer.drain()
                console.print(f"[bold green]✅ [{self.uid}] Welcome Sent → {user_name}[/bold green]")
            await asyncio.sleep(0.3)

            curr_time_str = datetime.now().strftime("%I:%M:%S %p")
            update_bot_info(self.uid, last_squad_id=str(squad_id), last_active=curr_time_str)
        except Exception as e:
            console.print(f"[bold red]Welcome err: {e}[/bold red]")

    async def send_team_msg(self, message: str, squad_id=None):
        try:
            if not self.chat_writer:
                return False
            sq_id = squad_id or self.current_squad_id
            if not sq_id:
                return False
            pkt = await MAHIR_SendSquadMsg(int(sq_id), message, self.bot_uid, self.key, self.iv)
            if pkt:
                self.chat_writer.write(pkt)
                await self.chat_writer.drain()
                return True
        except Exception as e:
            console.print(f"[bold red]send_team_msg err: {e}[/bold red]")
        return False

    async def handle_team_command(self, cmd_raw: str, sender_uid, sender_name="Player"):
        try:
            cmd = cmd_raw.strip()
            cmd_lower = cmd.lower()

            if cmd_lower in ("/help", "help"):
                pages = await build_help_menu(nickname=sender_name, bot_uid=str(sender_uid))
                for p in pages:
                    await self.send_team_msg(p)
                    await asyncio.sleep(0.5)
                return True

            if cmd_lower in ("/app", "app"):
                intro = (
                    "[B][C][00FFFF]MAHIR TCP OFFICIAL APP\n"
                    "[FFFFFF]অফিসিয়াল অ্যাপটি ডাউনলোড করতে নিচের লিংকে ক্লিক করে কপি করুন এবং "
                    "com এর মধ্যে past করে link থেকে emoji গুলো remove করে সার্চ দেন ধন্যবাদ"
                )
                link = "https://www.mediafire.com/file/lvykrek51q17hae/MAHIR_TCP.apk"
                await self.send_team_msg(intro)
                await asyncio.sleep(0.4)
                await self.send_team_msg(link)
                return True

            if cmd_lower in ("/store", "store"):
                store_msg = (
                    "[C][FFD700]❖━━━━━━━━━━━━━━━❖\n"
                    "[C][B][00FFFF]⚡ MAHIR BOT STORE ⚡\n"
                    "[C][FFD700]────────────────\n"
                    "[C][00FF00]🤖 TCP BOT Price : [FFFF00]500 BDT\n"
                    "[C][00FF00]🌐 Website       : [FFFF00]mahir.xo.je\n"
                    "[C][00FF00]👤 Owner Telegram : [FFFF00]@MAHIR0208\n"
                    "[C][FFD700]❖━━━━━━━━━━━━━━━❖"
                )
                await self.send_team_msg(store_msg)
                return True

            if cmd_lower == "hi":
                hi_msg = (
                    "[00FFFF][b][c]\n"
                    "[FFFFFF]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "[FFFF00]😊 হাই! আপনার দিনটি কেমন যাচ্ছে?\n"
                    "[FFFF00]আশা করি আপনি সুস্থ ও ভালো আছেন।\n\n"
                    "[00FFFF]📱 যোগাযোগ করুন:\n"
                    "[FFD700]টেলিগ্রাম: @MAHIR0208\n"
                    "[FFD700]টিকটক: @MAHIR__222\n"
                    "[00FF00]💡 বট ব্যবহার করতে চাইলে HELP টাইপ করুন!\n"
                    "[FFFFFF]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                await self.send_team_msg(hi_msg)
                return True

            if cmd_lower == ".time":
                bd_time = datetime.now().strftime('%I:%M %p')
                time_msg = (
                    f"[B][C][00FFFF]╔═══════════════╗\n"
                    f"[B][C][00FFFF]║  『 ⌚ SYSTEM STATUS 』  ║\n"
                    f"[B][C][00FFFF]╠═══════════════╣\n"
                    f"[B][C][FFFFFF]🕒 BD TIME : [00FF00]{bd_time}\n"
                    f"[B][C][FFFFFF]⏱️ UPTIME  : [FFFF00]ONLINE\n"
                    f"[B][C][00FFFF]╚═══════════════╝\n"
                    f"[B][C][0dffd0]MAHIR VIP SYSTEM ONLINE ✔"
                )
                await self.send_team_msg(time_msg)
                return True

            if cmd_lower == "mahir":
                mahir_logo = (
                    "[B][C][FF0000]███╗░░░███╗░█████╗░██╗░░██╗██╗██████╗\n"
                    "[B][C][FF4500]████╗░████║██╔══██╗██║░░██║██║██╔══██╗\n"
                    "[B][C][FFD700]██╔████╔██║███████║███████║██║██████╔╝\n"
                    "[B][C][00FF00]██║╚██╔╝██║██╔══██║██╔══██║██║██╔══██╗\n"
                    "[B][C][00FFFF]██║░╚═╝░██║██║░░██║██║░░██║██║██║░░██║\n"
                    "[B][C][FF1493]╚═╝░░░░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝╚═╝╚═╝░░╚═╝\n\n"
                    "[B][C][00FFFF]   🔥 WELCOME TO MAHIR BOT 🔥"
                )
                await self.send_team_msg(mahir_logo)
                return True

            if cmd_lower == "my id":
                id_msg = (
                    f"[B][C][00FFFF]╔═══════════════╗\n"
                    f"[B][C][00FFFF]║  👤 YOUR INFO  ║\n"
                    f"[B][C][00FFFF]╠═══════════════╣\n"
                    f"[B][C][FFFFFF]Name : [00FF00]{sender_name}\n"
                    f"[B][C][FFFFFF]UID  : [FFFF00]{sender_uid}\n"
                    f"[B][C][00FFFF]╚═══════════════╝"
                )
                await self.send_team_msg(id_msg)
                return True

            with web_config_lock:
                cmds = dict(web_config.get("commands", {}))

            for trigger, cfg in cmds.items():
                if not cfg.get("enabled", True):
                    continue
                match_mode = cfg.get("match", "contains")
                t = trigger.lower(); m = cmd_lower
                matched = False
                if match_mode == "exact" and m == t: matched = True
                elif match_mode == "startswith" and m.startswith(t): matched = True
                elif match_mode == "contains" and t in m: matched = True

                if matched:
                    ctype = cfg.get("type", "message")
                    if ctype == "message":
                        resp = cfg.get("response", "").replace("{user_name}", str(sender_name))
                        await self.send_team_msg(resp)
                        return True
                    elif ctype == "recruit_squad":
                        await self._send_world_recruit(reason="manual")
                        return True

            return False
        except Exception as e:
            console.print(f"[bold red]handle_team_command err: {e}[/bold red]")
            return False

    async def _handle_member_change(self, new_members_dict, reason_hint="auto"):
        try:
            joined = {u: n for u, n in new_members_dict.items() if u not in self.squad_members}
            left = {u: self.member_names.get(u, "Unknown")
                    for u in self.squad_members if u not in new_members_dict}

            self.squad_members = set(new_members_dict.keys())
            self.member_names.update(new_members_dict)

            with web_config_lock:
                recruit_on_join = web_config.get("auto_recruit_on_join", True)
                recruit_on_leave = web_config.get("auto_recruit_on_leave", True)
                sz = web_config.get("squad_size", 4)

            if joined and recruit_on_join:
                names_str = ", ".join(f"{n}" for n in joined.values())
                console.print(
                    f"[bold cyan]🟢 [{self.uid}] Member JOIN:[/bold cyan] "
                    f"[bold yellow]{names_str}[/bold yellow] → auto recruit"
                )
                asyncio.create_task(self._send_world_recruit(reason="join"))

            if left and recruit_on_leave:
                names_str = ", ".join(f"{n}" for n in left.values())
                console.print(
                    f"[bold cyan]🔴 [{self.uid}] Member LEFT:[/bold cyan] "
                    f"[bold yellow]{names_str}[/bold yellow] → auto recruit"
                )
                asyncio.create_task(self._send_world_recruit(reason="leave"))

            update_active_account(self.uid, **{
                'squad_members': f"{len(self.squad_members)}/{sz+1}"
            })
        except Exception as e:
            console.print(f"[bold red]Member-change err: {e}[/bold red]")

    async def tcp_online(self, ip, port, auth_token):
        self.current_squad_id = None
        self.squad_members = set()
        self.member_names = {}
        self.seen_recreate_ts = get_recreate_timestamp()
        while self.is_running:
            try:
                reader, writer = await asyncio.open_connection(ip, int(port))
                writer.write(bytes.fromhex(auth_token)); await writer.drain()
                self.reader, self.online_writer = reader, writer
                self.is_online = True
                update_bot_info(self.uid, status="✅ Online")
                console.print(f"[bold cyan]ℹ [{self.uid}] ONLINE Connected ✅[/bold cyan]")

                if not await self._build_and_send_squad():
                    self.is_online = False; await asyncio.sleep(10); continue

                while self.is_running and self.is_online:
                    cur_ts = get_recreate_timestamp()
                    if cur_ts > self.seen_recreate_ts:
                        self.seen_recreate_ts = cur_ts
                        await self._do_recreate()
                        continue

                    with web_config_lock:
                        auto_recreate = web_config.get("auto_recreate", True)
                        lifetime = web_config.get("squad_lifetime_sec", 10)
                    # ✅ ৫ সেকেন্ড পরপর Auto Recreate
                    if auto_recreate and self.squad_created and (time.time() - self.squad_created_at > lifetime):
                        console.print(f"[bold yellow]⏰ [{self.uid}] Squad lifetime ({lifetime}s) ended → recreate[/bold yellow]")
                        await self._do_recreate()
                        continue

                    try:
                        # ✅ timeout 5.0 → 1.0 (lifetime check আরও responsive)
                        data = await asyncio.wait_for(self.reader.read(65536), timeout=1.0)
                        if not data: break
                        data_hex = data.hex()

                        if data_hex.startswith("0e00") or data_hex.startswith("0500"):
                            decoded = DeCode_PackEt(data_hex[10:])
                            if decoded:
                                try:
                                    packet_json = json.loads(decoded)

                                    f5 = packet_json.get('5')
                                    if not isinstance(f5, dict):
                                        continue
                                    f5_data = f5.get('data')
                                    if not isinstance(f5_data, dict):
                                        continue

                                    squad_owner_int = safe_get_int(f5_data.get('1'))
                                    squad_owner = str(squad_owner_int) if squad_owner_int is not None else None
                                    if squad_owner and squad_owner != str(self.bot_uid):
                                        self.current_squad_id = squad_owner

                                    c_code = (
                                        safe_get_str(f5_data.get('14')) or
                                        safe_get_str(f5_data.get('17')) or
                                        safe_get_str(f5_data.get('31')) or
                                        safe_get_str(f5_data.get('33'))
                                    )

                                    current_members = {}
                                    for pf_key in ('6', '2', '3', '5', '7'):
                                        candidate = safe_dict(f5_data.get(pf_key))
                                        if not candidate:
                                            continue
                                        cand_uid = safe_get_int(candidate.get('1'))
                                        cand_name = safe_get_str(candidate.get('2'))
                                        if (cand_uid
                                            and str(cand_uid) != str(self.bot_uid)
                                            and len(str(cand_uid)) > 8
                                            and cand_name):
                                            uid_str = str(cand_uid)
                                            p_name = cand_name
                                            current_members[uid_str] = p_name

                                            if uid_str not in self.squad_members:
                                                sq_id = squad_owner_int or (int(self.current_squad_id) if self.current_squad_id else None)
                                                if sq_id and c_code:
                                                    asyncio.create_task(self.Auto_Squad_Welcome(
                                                        int(sq_id), c_code, uid_str, user_name=p_name))
                                                console.print(
                                                    f"[bold cyan][{self.uid}][/bold cyan] "
                                                    f"[bold green]➜ Member Joined:[/bold green] "
                                                    f"[bold yellow]{p_name}[/bold yellow] ({uid_str})")

                                                asyncio.create_task(self._send_bundle_on_join())
                                            break

                                    if current_members:
                                        joined_now = {u: n for u, n in current_members.items()
                                                      if u not in self.squad_members}
                                        if joined_now:
                                            for u, n in joined_now.items():
                                                self.squad_members.add(u)
                                                self.member_names[u] = n
                                            with web_config_lock:
                                                recruit_on_join = web_config.get("auto_recruit_on_join", True)
                                                sz = web_config.get('squad_size', 4)
                                            if recruit_on_join:
                                                asyncio.create_task(self._send_world_recruit(reason="join"))
                                            update_active_account(self.uid, **{
                                                'squad_members': f"{len(self.squad_members)}/{sz+1}"
                                            })

                                    new_sq_id_int = safe_get_int(f5_data.get('1'))
                                    if new_sq_id_int and 10000000 < new_sq_id_int < 999999999:
                                        if str(new_sq_id_int) != str(self.current_squad_id):
                                            self.current_squad_id = str(new_sq_id_int)
                                            console.print(Panel(
                                                f"[bold green]🆔 Squad ID :[/bold green] [bold yellow]{self.current_squad_id}[/bold yellow]\n"
                                                f"[bold cyan]👤 Bot Name :[/bold cyan] [white]{self.Nm}[/white]\n"
                                                f"[bold cyan]🆔 Bot UID  :[/bold cyan] [white]{self.bot_uid}[/white]",
                                                title=f"[bold magenta]✨ SQUAD ESTABLISHED ({self.uid})[/bold magenta]",
                                                border_style="cyan"))
                                            update_bot_info(self.uid, last_squad_id=str(new_sq_id_int), squad_active=True)
                                            with web_config_lock:
                                                sz = web_config.get('squad_size', 4)
                                            update_active_account(self.uid, **{
                                                'squad_id': self.current_squad_id,
                                                'squad_members': f"0/{sz+1}"
                                            })

                                    full_squad_list = safe_dict(f5_data.get('4'))
                                    if full_squad_list:
                                        new_snapshot = {}
                                        for k, v in full_squad_list.items():
                                            v_dict = safe_dict(v)
                                            if not v_dict:
                                                continue
                                            m_uid_int = safe_get_int(v_dict.get('1'))
                                            m_name = safe_get_str(v_dict.get('2'))
                                            if m_uid_int and str(m_uid_int) != str(self.bot_uid) and m_name:
                                                new_snapshot[str(m_uid_int)] = m_name
                                        if new_snapshot:
                                            await self._handle_member_change(new_snapshot)

                                except Exception:
                                    pass
                    except asyncio.TimeoutError: continue
                    except Exception: break
            except Exception as e:
                console.print(f"[bold red][{self.uid}] tcp_online err: {e}[/bold red]")
                self.is_online = False
            await asyncio.sleep(8)

    async def tcp_chat(self, ip, port, auth_token, key, iv, ready_event):
        while self.is_running:
            try:
                reader, writer = await asyncio.open_connection(ip, int(port))
                writer.write(bytes.fromhex(auth_token)); await writer.drain()
                self.chat_reader = reader; self.chat_writer = writer
                ready_event.set()
                console.print(f"[bold cyan]ℹ [{self.uid}] CHAT Connected ✅[/bold cyan]")

                while self.is_running:
                    try:
                        data = await asyncio.wait_for(self.chat_reader.read(4096), timeout=5.0)
                        if not data: break
                        data_hex = data.hex()

                        if data_hex.startswith("1200"):
                            decoded = DeCode_PackEt(data_hex[10:])
                            if decoded:
                                try:
                                    pj = json.loads(decoded)

                                    f5 = pj.get('5')
                                    if not isinstance(f5, dict):
                                        continue
                                    f5_data = f5.get('data')
                                    if not isinstance(f5_data, dict):
                                        continue

                                    msg_text = safe_get_str(f5_data.get('4')).strip()
                                    chat_id = safe_get_int(f5_data.get('2'))
                                    sender_uid = safe_get_int(f5_data.get('1'))

                                    f9 = safe_dict(f5_data.get('9'))
                                    sender_name = safe_get_str(f9.get('1'), "Player") if f9 else "Player"

                                    if not msg_text or not sender_uid:
                                        continue

                                    if str(sender_uid) == str(self.bot_uid):
                                        continue

                                    console.print(
                                        f"[bold cyan][{self.uid}][/bold cyan] "
                                        f"[white]{sender_name}[/white] [dim]({sender_uid})[/dim]: "
                                        f"[yellow]{msg_text}[/yellow]"
                                    )

                                    handled = await self.handle_team_command(
                                        msg_text, sender_uid, sender_name
                                    )
                                    if handled:
                                        console.print(
                                            f"[bold green]✅ [{self.uid}] Command handled:[/bold green] "
                                            f"[yellow]{msg_text[:30]}[/yellow]"
                                        )
                                except Exception:
                                    pass
                    except asyncio.TimeoutError:
                        continue
                    except Exception:
                        break
            except Exception:
                pass
            await asyncio.sleep(8)

    async def keep_online_forever(self):
        global online_count
        while self.is_running:
            try:
                self.seen_restart_ts = get_restart_timestamp()
                self.tasks = []

                open_id, access_token = await GeNeRaTeAccAccess(self.uid, self.password)
                if not open_id:
                    update_bot_info(self.uid, status="❌ Auth Failed")
                    await asyncio.sleep(10); continue

                payload = await EncRypTMajoRLoGin(open_id, access_token, version)
                response = await MajorLogin(payload)
                if not response:
                    update_bot_info(self.uid, status="❌ Login Failed")
                    await asyncio.sleep(10); continue

                try: auth_data = await DecRypTMajoRLoGin(response)
                except:
                    update_bot_info(self.uid, status="❌ Decrypt Failed")
                    await asyncio.sleep(10); continue

                if not getattr(auth_data, 'token', None) or not getattr(auth_data, 'url', None):
                    update_bot_info(self.uid, status="❌ Empty Auth")
                    await asyncio.sleep(10); continue

                login_data = await GetLoginData(auth_data.url, payload, auth_data.token)
                if not login_data:
                    update_bot_info(self.uid, status="❌ Data Failed")
                    await asyncio.sleep(10); continue

                from Pb2 import PorTs_pb2
                port_data = PorTs_pb2.GetLoginData()
                port_data.ParseFromString(login_data)
                self.key = auth_data.key; self.iv = auth_data.iv
                self.region = auth_data.region; self.bot_uid = auth_data.account_uid

                extracted_name = extract_player_name(login_data)
                if extracted_name and len(extracted_name) < 60:
                    self.Nm = extracted_name
                else:
                    try:
                        dec_jwt = jwt.decode(auth_data.token, options={"verify_signature": False})
                        fb = dec_jwt.get('nickname')
                        self.Nm = str(fb) if fb and len(str(fb)) < 30 else f"Player_{str(auth_data.account_uid)[-4:]}"
                    except: self.Nm = f"Player_{str(auth_data.account_uid)[-4:]}"

                update_bot_info(self.uid, account_uid=str(auth_data.account_uid))

                online_ip, online_port = port_data.Online_IP_Port.split(":")
                chat_ip, chat_port = port_data.AccountIP_Port.split(":")

                online_auth = create_auth_token_online(auth_data.account_uid, auth_data.token, auth_data.timestamp, auth_data.key, auth_data.iv)
                chat_auth = create_auth_token_chat(auth_data.account_uid, auth_data.token, auth_data.timestamp, auth_data.key, auth_data.iv)

                if not online_auth or not chat_auth:
                    update_bot_info(self.uid, status="❌ Token Failed")
                    await asyncio.sleep(10); continue

                console.print(f"[bold green]✔ BoT OnLiNe: {self.Nm} | Squad Mode | Region: {self.region}[/bold green]")

                with active_lock:
                    if not any(a['uid'] == self.uid for a in active_accounts):
                        online_count += 1
                        active_accounts.append({
                            'uid': self.uid, 'bot_uid': str(auth_data.account_uid), 'name': self.Nm,
                            'region': self.region or 'BD', 'time': datetime.now().strftime('%H:%M:%S'),
                            'squad_id': 'Pending...', 'squad_members': '0/0'})

                update_bot_info(self.uid, status="✅ Online", account_uid=str(auth_data.account_uid), squad_active=True)

                ready = asyncio.Event()
                t1 = asyncio.create_task(self.tcp_chat(chat_ip, chat_port, chat_auth, auth_data.key, auth_data.iv, ready))
                self.tasks.append(t1)
                await ready.wait()
                t2 = asyncio.create_task(self.tcp_online(online_ip, online_port, online_auth))
                self.tasks.append(t2)

                monitor = asyncio.create_task(self._monitor_restart())
                try:
                    await asyncio.gather(t1, t2, return_exceptions=True)
                finally:
                    if not monitor.done(): monitor.cancel()
            except Exception as e:
                console.print(f"[bold red]❌ UID {self.uid} Err: {e}[/bold red]")
                update_bot_info(self.uid, status="❌ Error", squad_active=False)
            remove_active_account(self.uid)

            if get_restart_timestamp() > self.seen_restart_ts:
                console.print(f"[bold green]♻️ [{self.uid}] Reconnecting...[/bold green]")
                continue
            await asyncio.sleep(10)

    async def _monitor_restart(self):
        while self.is_running:
            await asyncio.sleep(2)
            cur_ts = get_restart_timestamp()
            if cur_ts > self.seen_restart_ts:
                self.seen_restart_ts = cur_ts
                console.print(f"[bold yellow]♻️ [{self.uid}] Restart signal[/bold yellow]")
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
        except Exception:
            return ""

    def _html_escape(self, s):
        return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with active_lock:
                cur_online = online_count; cur_total = total_accounts; cur_threads = len(active_accounts)
            with web_config_lock:
                cur_size = web_config.get("squad_size", 4)
                cur_recruit = web_config.get("world_recruit_count", 3)
                cur_lifetime = web_config.get("squad_lifetime_sec", 5)
                cur_auto = web_config.get("auto_recreate", True)
                rc_welcome = web_config.get("welcome_msg", DEFAULT_WELCOME_MSG)
                rc_join = web_config.get("auto_recruit_on_join", True)
                rc_leave = web_config.get("auto_recruit_on_leave", True)
                rc_delay = web_config.get("recruit_delay_sec", 1.5)
                rc_bundle = web_config.get("auto_bundle_on_join", True)
                rc_bundle_count = web_config.get("bundle_count_on_join", 2)
            welcome_esc = self._html_escape(rc_welcome)

            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MAHIR SQUAD BOT</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; font-family:'Rajdhani',sans-serif; }}
body {{ background:#030712; color:#f3f4f6; min-height:100vh; padding:20px; background-image: radial-gradient(at 0% 0%, rgba(239,68,68,0.15) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(59,130,246,0.15) 0px, transparent 50%); background-attachment:fixed; }}
.container {{ max-width:1500px; margin:0 auto; }}
.header {{ text-align:center; padding:30px; background:rgba(17,24,39,0.7); backdrop-filter:blur(16px); border:1px solid rgba(255,255,255,0.1); border-radius:20px; margin-bottom:25px; }}
.header h1 {{ font-family:'Orbitron',sans-serif; font-size:2.8em; font-weight:900; background:linear-gradient(135deg,#fff,#ff4b4b 50%,#ff8533); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.header p {{ margin-top:8px; font-size:1.1em; color:#9ca3af; letter-spacing:2px; font-weight:600; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:20px; margin-bottom:25px; }}
.stat-card {{ background:rgba(17,24,39,0.6); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:20px; text-align:center; }}
.stat-card h2 {{ font-family:'Orbitron',sans-serif; font-size:2.5em; color:#10b981; }}
.stat-card p {{ margin-top:5px; font-size:1em; color:#9ca3af; font-weight:700; letter-spacing:1px; }}
.section {{ background:rgba(17,24,39,0.6); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:25px; margin-bottom:25px; }}
.section-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; flex-wrap:wrap; gap:10px; }}
.section h2 {{ font-family:'Orbitron',sans-serif; color:#38bdf8; font-size:1.3em; letter-spacing:1.5px; }}
.live-indicator {{ display:inline-flex; align-items:center; gap:6px; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); padding:4px 12px; border-radius:20px; font-size:0.85em; color:#10b981; font-weight:700; }}
.pulse-dot {{ width:8px; height:8px; background:#10b981; border-radius:50%; box-shadow:0 0 8px #10b981; animation:pulse 1.5s infinite; }}
@keyframes pulse {{ 0%{{transform:scale(0.95)}} 70%{{transform:scale(1)}} 100%{{transform:scale(0.95)}} }}
.table-wrapper {{ overflow-x:auto; max-height:500px; overflow-y:auto; border-radius:10px; border:1px solid rgba(255,255,255,0.05); }}
table {{ width:100%; border-collapse:collapse; text-align:left; }}
th,td {{ padding:14px 16px; border-bottom:1px solid rgba(255,255,255,0.05); font-size:1.05em; white-space:nowrap; }}
th {{ background:rgba(31,41,55,0.9); color:#f3f4f6; position:sticky; top:0; }}
.badge-online {{ background:rgba(16,185,129,0.15); color:#10b981; padding:4px 10px; border-radius:6px; font-weight:700; border:1px solid rgba(16,185,129,0.3); }}
textarea {{ width:100%; background:rgba(15,23,42,0.8); color:#38bdf8; border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:15px; font-family:'Courier New',monospace; font-size:14px; resize:vertical; outline:none; }}
textarea:focus {{ border-color:#38bdf8; }}
.btn {{ padding:14px 32px; background:linear-gradient(135deg,#ef4444,#dc2626); color:#fff; border:none; border-radius:10px; font-size:1.05em; font-weight:700; cursor:pointer; margin-top:15px; letter-spacing:1px; }}
.btn-green {{ background:linear-gradient(135deg,#10b981,#059669); }}
.btn-orange {{ background:linear-gradient(135deg,#f97316,#ea580c); }}
.btn-pink {{ background:linear-gradient(135deg,#ec4899,#be185d); }}
.footer {{ text-align:center; padding:20px; color:#6b7280; font-weight:600; }}
#toast {{ visibility:hidden; min-width:250px; background:#10b981; color:#fff; text-align:center; border-radius:8px; padding:14px; position:fixed; z-index:99; right:30px; bottom:30px; font-weight:bold; opacity:0; transition:opacity 0.3s,bottom 0.3s; }}
#toast.show {{ visibility:visible; opacity:1; bottom:40px; }}
.config-grid {{ display:grid; gap:20px; }}
.config-label {{ color:#9ca3af; font-weight:700; letter-spacing:1px; margin-bottom:8px; }}
.input-text {{ width:100%; padding:12px 16px; background:rgba(15,23,42,0.8); color:#38bdf8; border:1px solid rgba(255,255,255,0.1); border-radius:10px; font-family:'Courier New',monospace; font-size:15px; outline:none; }}
.input-text:focus {{ border-color:#38bdf8; }}
.help-text {{ color:#6b7280; font-size:0.85em; margin-top:6px; }}
.live-log {{ height:400px; overflow-y:auto; background:#0a0a0a; border-radius:10px; padding:15px; font-family:'Courier New',monospace; font-size:13px; color:#10b981; line-height:1.6; }}
.action-bar {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:20px; padding:18px; background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.08); border-radius:14px; align-items:center; }}
.action-bar .btn {{ margin-top:0; padding:12px 24px; }}
.radio-row {{ display:flex; gap:20px; flex-wrap:wrap; }}
.radio-chip {{ display:inline-flex; align-items:center; gap:8px; background:rgba(56,189,248,0.08); border:1px solid rgba(56,189,248,0.3); padding:10px 20px; border-radius:10px; cursor:pointer; }}
.radio-chip input {{ width:16px; height:16px; accent-color:#38bdf8; }}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>🔥 MAHIR SQUAD BOT 🔥</h1><p>⚡ AUTO RECREATE 5s · WORLD RECRUIT · TEAM CHAT · AUTO BUNDLE ⚡</p></div>

<div class="stats">
<div class="stat-card"><h2 id="stat-online">{cur_online}</h2><p>🟢 ONLINE</p></div>
<div class="stat-card"><h2 id="stat-total">{cur_total}</h2><p>📊 TOTAL</p></div>
<div class="stat-card"><h2 id="stat-threads">{cur_threads}</h2><p>⚙️ ACTIVE</p></div>
<div class="stat-card"><h2 id="stat-version" style="font-size:1.8em;color:#38bdf8;">{version}</h2><p>📦 VERSION ({ob})</p></div>
</div>

<div class="section">
<div class="section-header"><h2>⚡ Quick Actions</h2><div class="live-indicator"><div class="pulse-dot"></div> LIVE</div></div>
<div class="action-bar">
<button class="btn btn-orange" onclick="doAccountRestart()">♻️ ACCOUNT RESTART</button>
<button class="btn btn-pink" onclick="doSquadRecreate()">🔄 SQUAD RECREATE</button>
</div>
</div>

<div class="section">
<div class="section-header"><h2>⚙️ Squad Configuration</h2></div>
<form id="squad-form" onsubmit="saveSquadConfig(event)">
<div class="config-grid">
<div>
<div class="config-label">👥 Squad Size</div>
<div class="radio-row">
<label class="radio-chip"><input type="radio" name="squad_size" value="3" {"checked" if cur_size==3 else ""}><span>4 Players</span></label>
<label class="radio-chip"><input type="radio" name="squad_size" value="4" {"checked" if cur_size==4 else ""}><span>5 Players</span></label>
<label class="radio-chip"><input type="radio" name="squad_size" value="5" {"checked" if cur_size==5 else ""}><span>6 Players</span></label>
</div>
</div>
<div>
<div class="config-label">📢 World Recruit Count (Initial)</div>
<input type="number" min="1" max="10" class="input-text" id="world_recruit_count" value="{cur_recruit}">
</div>
<div>
<div class="config-label">⏱️ Squad Lifetime (sec) — Auto Recreate Cycle</div>
<input type="number" min="5" max="3600" class="input-text" id="squad_lifetime_sec" value="{cur_lifetime}">
<div class="help-text">Default: <b>5</b> sec — প্রতি ৫ সেকেন্ড পরপর exit → create → recruit</div>
</div>
<div>
<label class="radio-chip" style="padding:10px 16px;">
<input type="checkbox" id="auto_recreate_chk" {"checked" if cur_auto else ""}>
<span>🔁 Auto Recreate</span>
</label>
</div>
<div>
<label class="radio-chip" style="padding:10px 16px;">
<input type="checkbox" id="auto_recruit_on_join_chk" {"checked" if rc_join else ""}>
<span>🟢 Auto Recruit on JOIN</span>
</label>
</div>
<div>
<label class="radio-chip" style="padding:10px 16px;">
<input type="checkbox" id="auto_recruit_on_leave_chk" {"checked" if rc_leave else ""}>
<span>🔴 Auto Recruit on LEAVE</span>
</label>
</div>
<div>
<label class="radio-chip" style="padding:10px 16px;">
<input type="checkbox" id="auto_bundle_on_join_chk" {"checked" if rc_bundle else ""}>
<span>👗 Auto Bundle on JOIN</span>
</label>
</div>
<div>
<div class="config-label">👗 Bundle Count (on join)</div>
<input type="number" min="1" max="5" class="input-text" id="bundle_count_on_join" value="{rc_bundle_count}">
</div>
<div>
<div class="config-label">⏱️ Recruit Delay (sec)</div>
<input type="number" min="0.5" max="30" step="0.5" class="input-text" id="recruit_delay_sec" value="{rc_delay}">
</div>
<div>
<div class="config-label">💬 Welcome Message</div>
<textarea id="welcome_msg_ta" style="height:200px; color:#facc15;" spellcheck="false">{welcome_esc}</textarea>
<div class="help-text">Placeholder: <b>{{user_name}}</b></div>
</div>
<button type="submit" class="btn btn-green" id="squad-save-btn">💾 SAVE SQUAD CONFIG</button>
</div>
</form>
</div>

<div class="section">
<div class="section-header">
<h2>📋 Active Bots</h2>
<div class="live-indicator"><div class="pulse-dot"></div> LIVE</div>
</div>
<div class="table-wrapper">
<table>
<thead><tr>
<th>BOT UID</th><th>UID</th><th>NAME</th><th>REGION</th>
<th>SQUAD ID</th><th>MEMBERS</th><th>TIME</th><th>STATUS</th>
</tr></thead>
<tbody id="accounts-tbody"><tr><td colspan="8">🔄 Loading...</td></tr></tbody>
</table>
</div>
</div>

<div class="section">
<div class="section-header">
<h2>📜 Live Log</h2>
<button class="btn" onclick="clearLogView()" style="margin-top:0;padding:8px 16px;background:linear-gradient(135deg,#ef4444,#dc2626);">🗑️ CLEAR</button>
<div class="live-indicator"><div class="pulse-dot"></div> AUTO-SYNC</div>
</div>
<div id="live-log" class="live-log">📡 Waiting for logs...</div>
</div>

<div class="footer"><p>© 2026 MAHIR SQUAD BOT | Auto Recreate Every 5s</p></div>
</div>
<div id="toast"></div>

<script>
function showToast(msg, color) {{
const t = document.getElementById('toast');
t.innerText = msg; t.style.background = color || '#10b981';
t.className = 'show';
setTimeout(() => {{ t.className = t.className.replace('show',''); }}, 3000);
}}

async function doAccountRestart() {{
if (!confirm('Restart ALL accounts?')) return;
try {{ const r = await fetch('/restart_accounts', {{method:'POST'}});
if (r.ok) showToast('♻️ Account Restart Triggered!'); }} catch(e) {{ showToast('❌ Error','#ef4444'); }}
}}

async function doSquadRecreate() {{
if (!confirm('Recreate ALL squads?')) return;
try {{ const r = await fetch('/recreate_squads', {{method:'POST'}});
if (r.ok) showToast('🔄 Squad Recreate Triggered!'); }} catch(e) {{ showToast('❌ Error','#ef4444'); }}
}}

async function saveSquadConfig(e) {{
e.preventDefault();
const btn = document.getElementById('squad-save-btn');
btn.innerText = '⏳...'; btn.disabled = true;
const form = document.getElementById('squad-form');
const size = form.querySelector('input[name="squad_size"]:checked').value;
const body = new URLSearchParams();
body.append('squad_size', size);
body.append('world_recruit_count', document.getElementById('world_recruit_count').value);
body.append('squad_lifetime_sec', document.getElementById('squad_lifetime_sec').value);
body.append('auto_recreate', document.getElementById('auto_recreate_chk').checked ? '1' : '0');
body.append('auto_recruit_on_join', document.getElementById('auto_recruit_on_join_chk').checked ? '1' : '0');
body.append('auto_recruit_on_leave', document.getElementById('auto_recruit_on_leave_chk').checked ? '1' : '0');
body.append('auto_bundle_on_join', document.getElementById('auto_bundle_on_join_chk').checked ? '1' : '0');
body.append('bundle_count_on_join', document.getElementById('bundle_count_on_join').value);
body.append('recruit_delay_sec', document.getElementById('recruit_delay_sec').value);
body.append('welcome_msg', document.getElementById('welcome_msg_ta').value);
const r = await fetch('/save_squad_config', {{method:'POST', headers:{{'Content-Type':'application/x-www-form-urlencoded'}}, body: body.toString()}});
if (r.ok) showToast('⚙️ Saved!');
btn.innerText = '💾 SAVE SQUAD CONFIG'; btn.disabled = false;
}}

async function fetchStats() {{
try {{
const r = await fetch('/api/stats'); if (!r.ok) return;
const d = await r.json();
document.getElementById('stat-online').innerText = d.online;
document.getElementById('stat-total').innerText = d.total;
document.getElementById('stat-threads').innerText = d.threads;
document.getElementById('stat-version').innerText = d.version;
const tb = document.getElementById('accounts-tbody');
if (d.accounts && d.accounts.length) {{
tb.innerHTML = d.accounts.map(a => `<tr>
<td>${{a.bot_uid}}</td><td>${{a.uid}}</td>
<td style="color:#38bdf8;font-weight:bold;">${{a.name}}</td>
<td style="color:#f59e0b;font-weight:bold;">${{a.region}}</td>
<td style="color:#facc15;font-weight:bold;">${{a.squad_id||'Pending...'}}</td>
<td style="color:#a78bfa;font-weight:bold;">${{a.squad_members||'0/0'}}</td>
<td>${{a.time}}</td>
<td><span class="badge-online">● ONLINE</span></td></tr>`).join('');
}} else tb.innerHTML = '<tr><td colspan="8">⚠️ No active bots.</td></tr>';
}} catch(e) {{}}
}}

async function fetchLogs() {{
try {{
const r = await fetch('/api/logs'); if (!r.ok) return;
const d = await r.json();
const el = document.getElementById('live-log');
const logs = d.logs || [];
if (!logs.length) {{ el.innerHTML = '📡 Waiting for logs...'; return; }}
const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 30;
el.innerHTML = logs.map(l => `<div>${{l.replace(/&/g,'&amp;').replace(/</g,'&lt;')}}</div>`).join('');
if (atBottom) el.scrollTop = el.scrollHeight;
}} catch(e) {{}}
}}
function clearLogView() {{ document.getElementById('live-log').innerHTML = '📡 Cleared.'; }}

fetchStats(); setInterval(fetchStats, 2000);
fetchLogs(); setInterval(fetchLogs, 2500);
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
                'version': version or "loading...", 'release': ob or "loading...", 'accounts': accs})
            return

        if self.path == '/api/logs':
            with log_lock:
                logs = list(log_buffer)
            self._json_response({'logs': logs})
            return

        self.send_response(404); self.end_headers()

    def do_POST(self):
        raw = self._read_body()

        if self.path == '/restart_accounts':
            trigger_restart_all()
            console.print("[bold yellow]♻️ Account restart triggered[/bold yellow]")
            self._text_response('OK'); return

        if self.path == '/recreate_squads':
            trigger_recreate_all()
            console.print("[bold yellow]🔄 Squad recreate triggered[/bold yellow]")
            self._text_response('OK'); return

        if self.path == '/save_squad_config':
            params = parse_qs(raw)
            try:
                size = int(params.get('squad_size', ['4'])[0])
                if size not in (3, 4, 5): size = 4
                rc = int(params.get('world_recruit_count', ['3'])[0])
                if rc < 1 or rc > 10: rc = 3
                # ✅ ৫ সেকেন্ড minimum
                lt = int(params.get('squad_lifetime_sec', ['5'])[0])
                if lt < 5 or lt > 3600: lt = 5
                ar = params.get('auto_recreate', ['0'])[0] == '1'
                ajo = params.get('auto_recruit_on_join', ['0'])[0] == '1'
                alv = params.get('auto_recruit_on_leave', ['0'])[0] == '1'
                abj = params.get('auto_bundle_on_join', ['0'])[0] == '1'
                bcj = int(params.get('bundle_count_on_join', ['2'])[0])
                if bcj < 1 or bcj > 5: bcj = 2
                rds = float(params.get('recruit_delay_sec', ['1.5'])[0])
                if rds < 0.5 or rds > 30: rds = 1.5
                wm = params.get('welcome_msg', [''])[0] or DEFAULT_WELCOME_MSG
                with web_config_lock:
                    web_config['squad_size'] = size
                    web_config['world_recruit_count'] = rc
                    web_config['squad_lifetime_sec'] = lt
                    web_config['auto_recreate'] = ar
                    web_config['auto_recruit_on_join'] = ajo
                    web_config['auto_recruit_on_leave'] = alv
                    web_config['auto_bundle_on_join'] = abj
                    web_config['bundle_count_on_join'] = bcj
                    web_config['recruit_delay_sec'] = rds
                    web_config['welcome_msg'] = wm
                save_web_config()
                console.print(f"[bold green]⚙️ Squad Config Updated (Lifetime: {lt}s)[/bold green]")
                self._text_response('OK')
            except Exception as e:
                self._text_response(f"Error: {e}", 400)
            return

        self.send_response(404); self.end_headers()

    def log_message(self, format, *args): pass

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
        "[magenta]👥 Squad Create: OpEnSq + cHSq22[/magenta]\n"
        "[yellow]📢 World Recruit: Initial + Auto on Join/Leave[/yellow]\n"
        "[blue]💬 Team Chat: ENABLED ✅[/blue]\n"
        "[bold red]🚫 WRR Packet: REMOVED[/bold red]\n"
        "[bold magenta]👗 AUTO BUNDLE ON JOIN: ENABLED ✅[/bold magenta]\n"
        "[bold yellow]⏰ AUTO RECREATE CYCLE: 5 SECONDS (EXIT → CREATE → RECRUIT)[/bold yellow]\n"
        "[bold cyan]📢 TEAM CHAT CMDS: /help /app /store HI .time MAHIR my id[/bold cyan]",
        title="[bold red]🔥 MAHIR SQUAD BOT 🔥[/bold red]",
        border_style="bright_red", expand=False))
    while True: await asyncio.sleep(3600)

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try: loop.run_until_complete(main_async())
    except KeyboardInterrupt: console.print("\n[bold red]Shutdown.[/bold red]")

if __name__ == "__main__":
    main()