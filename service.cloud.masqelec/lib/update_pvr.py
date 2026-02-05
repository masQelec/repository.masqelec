# -*- coding: utf-8 -*-
"""
update_pvr.py — Gestión de PVR (limpio)
- Playlist con USER_CODE/PASS_CODE (instalación SOLO si cambia hash final)
- Sync tv_grab_file desde nube
- Ajuste http_user_agent en Tvheadend
- Reconciliación selectiva en Kodi (TVxx.db)
- Soft reset robusto si:
    a) cambia playlist, o
    b) DB no coincide con playlist aunque el hash sea igual
- Prune TVH: deshabilita canales fuera de playlist (channel/grid) por bouquet
- Rescate: toggle pvr.hts y reinicio Kodi (solo idle) opcional
"""

import os
import re
import unicodedata
import time
import json
import gzip
import zlib
import socket
import sqlite3
import subprocess
import traceback
import uuid
import urllib.request
import urllib.parse

from lib import log_utils
from lib import rclone_utils
from lib import utils
from lib import jsonrpc_utils

try:
    import xbmc
    import xbmcgui
except Exception:
    xbmc = None
    xbmcgui = None

# ------------------------------
# Constantes
# ------------------------------
PVR_ADDON_ID = "pvr.hts"
TVH_TAGDIR = "/storage/.kodi/userdata/addon_data/service.tvheadend43/channel/tag"
TVH_SERVICE = "service.tvheadend43"

TVH_HTTP_PORT = 9981
TVH_HTSP_PORT = 9982

TVH_AUTH_FILE = "/storage/.kodi/userdata/addon_data/service.cloud.masqelec/tvh_auth.json"

UA = "KodiELEC/1.0"
ENABLE_KODI_RESTART_FALLBACK = True

# Último diagnóstico de mismatch (canales en DB pero no en playlist)
_LAST_DB_MISMATCH: list[str] = []


# ------------------------------
# Regex playlist
# ------------------------------
_RE_TVG_NAME = re.compile(r"""tvg-name\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)
_RE_TVG_LOGO = re.compile(r"""tvg-logo\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)
_RE_GRP_TITLE = re.compile(r"""group-title\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)


# ------------------------------
# UI helper
# ------------------------------
def _popup(title: str, message: str, ms: int = 3500) -> None:
    title = title or "Kodi"
    message = message or ""
    try:
        if xbmcgui:
            xbmcgui.Dialog().notification(title, message, time=int(ms))
            return
    except Exception:
        pass
    try:
        if xbmc:
            xbmc.executebuiltin(
                "Notification({}, {}, {}, {})".format(
                    title.replace(",", " "),
                    message.replace(",", " "),
                    int(ms),
                    "",
                )
            )
    except Exception:
        pass


# ------------------------------
# System helpers
# ------------------------------
def _run(cmd, timeout=20) -> bool:
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=int(timeout),
            check=True,
        )
        return True
    except Exception:
        return False


def _is_service_active(unit: str) -> bool:
    try:
        r = subprocess.run(
            ["systemctl", "is-active", unit],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return (r.stdout or b"").decode("utf-8", "ignore").strip() == "active"
    except Exception:
        return False


def _is_service_inactive(unit: str) -> bool:
    try:
        r = subprocess.run(
            ["systemctl", "is-active", unit],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        s = (r.stdout or b"").decode("utf-8", "ignore").strip()
        return s in ("inactive", "failed", "deactivating", "unknown", "")
    except Exception:
        return False


def _wait_service_state(unit: str, want_active: bool, timeout_s: int = 25) -> bool:
    deadline = time.time() + max(1, int(timeout_s))
    while time.time() < deadline:
        if want_active and _is_service_active(unit):
            return True
        if (not want_active) and _is_service_inactive(unit):
            return True
        time.sleep(0.5)
    return False


def _stop_tvheadend() -> bool:
    ok = _run(["systemctl", "stop", TVH_SERVICE], timeout=25)
    _wait_service_state(TVH_SERVICE, want_active=False, timeout_s=25)
    log_utils.write_log("[pvr] Tvheadend parado." if ok else "[pvr] No pude parar Tvheadend.", level="INFO" if ok else "WARNING")
    return ok


def _start_tvheadend() -> bool:
    ok = _run(["systemctl", "start", TVH_SERVICE], timeout=25)
    _wait_service_state(TVH_SERVICE, want_active=True, timeout_s=25)
    log_utils.write_log("[pvr] Tvheadend iniciado." if ok else "[pvr] No pude iniciar Tvheadend.", level="INFO" if ok else "WARNING")
    return ok


# ------------------------------
# Tvheadend Digest HTTP layer
# ------------------------------
_TVH_DIGEST_OPENER = None
_TVH_DIGEST_USERPASS = None  # (user, pass)


def _tvh_read_http_auth() -> tuple[str, str]:
    """Lee credenciales de TVH desde TVH_AUTH_FILE.

    Soporta:
      - user+pass (Basic Auth)
      - user sin pass (TVH con auth "usuario sin contraseña")
    """
    try:
        if not os.path.exists(TVH_AUTH_FILE):
            return "", ""
        with open(TVH_AUTH_FILE, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return "", ""
        u = (data.get("username") or data.get("user") or "").strip()
        p = (data.get("password") or data.get("pass") or "")
        p = (p if isinstance(p, str) else "").strip()
        return (u, p) if u else ("", "")
    except Exception:
        return "", ""


_TVH_HTTP_AUTH_CACHE: tuple[str, str] | None = None
_TVH_BASIC_OPENER = None
_TVH_BASIC_USERPASS: tuple[str, str] | None = None


def _tvh_get_http_auth() -> tuple[str, str]:
    """Credenciales cacheadas (evita leer JSON en cada request)."""
    global _TVH_HTTP_AUTH_CACHE
    if _TVH_HTTP_AUTH_CACHE is None:
        _TVH_HTTP_AUTH_CACHE = _tvh_read_http_auth()
    return _TVH_HTTP_AUTH_CACHE


def _tvh_urlopen(req: urllib.request.Request, timeout_s: float):
    """Abre request a TVH.

    - Sin credenciales: directo.
    - user+pass: Basic Auth via opener.
    - user sin pass: NO fuerza Authorization; se usará `username=` inyectado en GET/POST.
    """
    u, p = _tvh_get_http_auth()
    if not u:
        return urllib.request.urlopen(req, timeout=float(timeout_s))

    if not p:
        # Importante: NO enviar Authorization: Basic user:
        return urllib.request.urlopen(req, timeout=float(timeout_s))

    global _TVH_BASIC_OPENER, _TVH_BASIC_USERPASS
    if _TVH_BASIC_OPENER is None or _TVH_BASIC_USERPASS != (u, p):
        pm = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        base = f"http://127.0.0.1:{int(TVH_HTTP_PORT)}/"
        pm.add_password(None, base, u, p)
        handler = urllib.request.HTTPBasicAuthHandler(pm)
        _TVH_BASIC_OPENER = urllib.request.build_opener(handler)
        _TVH_BASIC_USERPASS = (u, p)

    return _TVH_BASIC_OPENER.open(req, timeout=float(timeout_s))


def _tvh_api_get(api_path: str, query: dict | None = None, timeout_s: float = 10.0) -> tuple[bool, int, str]:
    host = "127.0.0.1"

    q = dict(query or {})
    # auth: user sin pass -> TVH suele aceptar ?username=USER
    u, p = _tvh_get_http_auth()
    if u and not p and "username" not in q:
        q["username"] = u

    qs = urllib.parse.urlencode(q)
    url = f"http://{host}:{int(TVH_HTTP_PORT)}/api/{api_path.lstrip('/')}{('?' + qs) if qs else ''}"

    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "*/*")
    req.add_header("Connection", "close")

    try:
        with _tvh_urlopen(req, timeout_s) as r:
            code = int(getattr(r, "status", 200) or 200)
            body = (r.read() or b"").decode("utf-8", "replace")
            return True, code, body
    except Exception as e:
        try:
            code = int(getattr(e, "code", 0) or 0)
            body = (e.read() or b"").decode("utf-8", "replace") if hasattr(e, "read") else str(e)
            return False, code, body
        except Exception:
            return False, 0, str(e)


def _tvh_api_get_json(api_path: str, query: dict | None = None, timeout_s: float = 10.0) -> tuple[bool, int, dict | None, str]:
    ok, code, body = _tvh_api_get(api_path, query=query, timeout_s=timeout_s)
    if not ok:
        return False, code, None, body or ""
    try:
        j = json.loads(body or "{}")
        return True, code, (j if isinstance(j, dict) else None), body or ""
    except Exception:
        return True, code, None, body or ""


def _tvh_api_post_form(api_path: str, form: dict, timeout_s: float = 15.0) -> tuple[bool, int, str]:
    host = "127.0.0.1"
    url = f"http://{host}:{int(TVH_HTTP_PORT)}/api/{api_path.lstrip('/')}"

    f = dict(form or {})
    # auth: user sin pass -> TVH suele aceptar username=USER también en POST form
    u, p = _tvh_get_http_auth()
    if u and not p and "username" not in f:
        f["username"] = u

    data = urllib.parse.urlencode(f).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("User-Agent", UA)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "*/*")
    req.add_header("Connection", "close")

    try:
        with _tvh_urlopen(req, timeout_s) as r:
            code = int(getattr(r, "status", 200) or 200)
            body = (r.read() or b"").decode("utf-8", "replace")
            return True, code, body
    except Exception as e:
        try:
            code = int(getattr(e, "code", 0) or 0)
            body = (e.read() or b"").decode("utf-8", "replace") if hasattr(e, "read") else str(e)
            return False, code, body
        except Exception:
            return False, 0, str(e)

def _tvh_channel_set_epggrab(channel_uuid: str, epggrab_uuid: str) -> tuple[bool, int, str]:
    """
    Intenta asignar EPG Source a un channel UUID.
    En tu grid.json, channel.epggrab es LISTA, así que aquí forzamos lista siempre.

    Prueba varios formatos porque TVH cambia entre builds:
      - POST form idnode/save con node={...} (JSON object)
      - POST form idnode/save con node=[{...}] (JSON array)
      - POST json idnode/save con node={...}
      - POST json idnode/save con node=[{...}]
    """
    ch = (channel_uuid or "").strip()
    epg = (epggrab_uuid or "").strip()
    if not ch or not epg:
        return False, 0, "missing uuid"

    node_obj = {"uuid": ch, "epggrab": [epg]}

    variants_form = [
        ("v1_form_node_obj", {"node": json.dumps(node_obj, separators=(",", ":"))}),
        ("v2_form_node_arr", {"node": json.dumps([node_obj], separators=(",", ":"))}),
    ]

    for tag, fields in variants_form:
        log_utils.write_log(f"[pvr][epgsrc] TRY {tag}: fields={fields}", level="WARNING")
        ok, code, body = _tvh_api_post_form("idnode/save", fields, timeout_s=18.0)
        if ok and 200 <= int(code or 0) < 300:
            return True, int(code or 0), body
        log_utils.write_log(
            f"[pvr][epgsrc] SAVE FAIL {tag} (HTTP {code}): {(body or '')[:200]}",
            level="WARNING",
        )

    variants_json = [
        ("v3_json_node_obj", {"node": node_obj}),
        ("v4_json_node_arr", {"node": [node_obj]}),
    ]

    for tag, payload in variants_json:
        log_utils.write_log(f"[pvr][epgsrc] TRY {tag}: payload={payload}", level="WARNING")
        ok, code, body = _tvh_api_post_json("idnode/save", payload, timeout_s=18.0)
        if ok and 200 <= int(code or 0) < 300:
            return True, int(code or 0), body
        log_utils.write_log(
            f"[pvr][epgsrc] SAVE FAIL {tag} (HTTP {code}): {(body or '')[:200]}",
            level="WARNING",
        )

    return False, 0, "all variants failed"

def _addon_set_enabled(addon_id: str, enabled: bool) -> bool:
    try:
        return bool(jsonrpc_utils.set_addon_enabled(addon_id, enabled))
    except Exception as e:
        log_utils.write_log(f"[pvr] JSON-RPC set_addon_enabled({addon_id},{enabled}): {e}", level="WARNING")
        return False


def _get_addon_enabled(addon_id: str):
    try:
        res = jsonrpc_utils.jsonrpc_call(
            "Addons.GetAddonDetails",
            {"addonid": addon_id, "properties": ["enabled"]},
        )
        if isinstance(res, dict):
            det = res.get("addon") or {}
            if "enabled" in det:
                return bool(det["enabled"])
        return None
    except Exception:
        return None


def _wait_addon_enabled(addon_id: str, want_enabled: bool, timeout_s: int = 12) -> bool:
    deadline = time.time() + max(1, int(timeout_s))
    while time.time() < deadline:
        v = _get_addon_enabled(addon_id)
        if v is not None and bool(v) == bool(want_enabled):
            return True
        time.sleep(0.5)
    return False


def _pvr_get_properties():
    ok, res, _ = jsonrpc_utils.jsonrpc_try(
        "PVR.GetProperties",
        params={"properties": ["available", "scanning", "recording"]},
        retries=0,
        quiet_codes={-32100, -32602},
        log_level="DEBUG",
    )
    return res if (ok and isinstance(res, dict)) else None


def _pvr_has_any_channels_via_conditions() -> bool:
    try:
        if xbmc:
            return bool(xbmc.getCondVisibility("Pvr.HasTVChannels") or xbmc.getCondVisibility("Pvr.HasRadioChannels"))
    except Exception:
        pass
    return False


# ------------------------------
# DB helpers
# ------------------------------
def _pick_tv_db_path() -> str:
    db_dir = "/storage/.kodi/userdata/Database"
    if not os.path.isdir(db_dir):
        return ""
    cands = []
    try:
        for fn in os.listdir(db_dir):
            low = fn.lower()
            if low.startswith("tv") and low.endswith(".db") and not low.endswith(".db-wal") and not low.endswith(".db-shm"):
                cands.append(os.path.join(db_dir, fn))
    except Exception:
        return ""
    if not cands:
        return ""
    cands.sort(key=lambda p: (os.path.basename(p).lower(), os.path.getmtime(p)))
    return cands[-1]


def _db_count_channels_groups(tv_db_path: str) -> tuple[int, int]:
    if not tv_db_path or not os.path.exists(tv_db_path):
        return 0, 0
    if os.path.exists(tv_db_path + "-wal") or os.path.exists(tv_db_path + "-shm"):
        return 0, 0

    con = None
    try:
        con = sqlite3.connect(tv_db_path, timeout=2.0)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}

        n_channels = 0
        n_groups = 0

        if "channels" in tables:
            cur.execute("SELECT COUNT(1) FROM channels")
            n_channels = int(cur.fetchone()[0] or 0)

        if "channelgroups" in tables:
            cur.execute(
                """
                SELECT COUNT(1)
                FROM channelgroups
                WHERE idGroup <> 1 AND TRIM(IFNULL(sName,'')) <> ''
                """
            )
            n_groups = int(cur.fetchone()[0] or 0)

        return n_channels, n_groups
    except Exception:
        return 0, 0
    finally:
        try:
            if con:
                con.close()
        except Exception:
            pass


def _pvr_has_any_channels_via_db() -> bool:
    try:
        tvdb = _pick_tv_db_path()
        if not tvdb:
            return False
        n_ch, _ = _db_count_channels_groups(tvdb)
        return n_ch > 0
    except Exception:
        return False


def _log_pvr_db_stats(prefix: str = "[pvr]") -> None:
    try:
        tvdb = _pick_tv_db_path()
        if not tvdb:
            log_utils.write_log(f"{prefix} DB stats: TVxx.db no encontrada", level="INFO")
            return

        n_ch, n_gr = _db_count_channels_groups(tvdb)
        if n_ch == 0 and n_gr == 0:
            if os.path.exists(tvdb + "-wal") or os.path.exists(tvdb + "-shm"):
                log_utils.write_log(f"{prefix} DB stats: DB en uso (wal/shm), omito conteo", level="INFO")
            else:
                log_utils.write_log(f"{prefix} DB stats: no pude leer conteo (0/0)", level="INFO")
            return

        log_utils.write_log(f"{prefix} DB stats: canales={n_ch} grupos={n_gr}", level="INFO")
    except Exception:
        pass


# ------------------------------
# Playlist parse + normalización
# ------------------------------
def _norm_key(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.casefold()


def _norm_url(s: str) -> str:
    return (s or "").strip()


def _parse_m3u_name_logo_group(m3u_path: str):
    wanted_names = set()
    logos_by_name = {}
    wanted_groups = set()

    def _add_name(name_raw: str) -> str:
        nk = _norm_key(name_raw)
        if nk:
            wanted_names.add(nk)
        return nk

    def _add_logo(nkey: str, logo: str):
        if not nkey:
            return
        logos_by_name.setdefault(nkey, set()).add(logo)

    try:
        with open(m3u_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.startswith("#EXTINF"):
                    continue

                nkey_tvg = ""
                m = _RE_TVG_NAME.search(line)
                if m:
                    name_raw = (m.group(2) or "").strip()
                    if name_raw:
                        nkey_tvg = _add_name(name_raw)

                nkey_disp = ""
                if "," in line:
                    disp = line.split(",", 1)[1].strip()
                    if disp:
                        nkey_disp = _add_name(disp)

                if not (nkey_tvg or nkey_disp):
                    continue

                m = _RE_TVG_LOGO.search(line)
                logo = (m.group(2) if m else "") or ""
                logo = _norm_url(logo)
                if logo:
                    _add_logo(nkey_tvg or nkey_disp, logo)

                m = _RE_GRP_TITLE.search(line)
                grp = (m.group(2) if m else "") or ""
                grp = (grp or "").strip()
                if grp:
                    wanted_groups.add(_norm_key(grp))
    except Exception:
        pass

    return wanted_names, logos_by_name, wanted_groups


# ------------------------------
# Grupos protegidos (Kodi DB)
# ------------------------------
_PROTECTED_GROUP_NAMES_RAW = {
    "all channels", "all radio",
    "todos los canales", "todos los radios", "todas las radios",
    "tots els canals", "tota la ràdio",
    "tous les canaux", "toutes les chaînes", "toutes les radios",
}
_PROTECTED_GROUP_NAMES_NORM = {_norm_key(x) for x in _PROTECTED_GROUP_NAMES_RAW if _norm_key(x)}


def _is_internal_or_protected_group(gid: int, gname: str, iClientId, sClientName: str) -> bool:
    try:
        gid = int(gid)
    except Exception:
        gid = -1

    if gid == 1:
        return True

    try:
        if iClientId is not None and int(iClientId) < 0:
            return True
    except Exception:
        return True

    if not (sClientName or "").strip():
        return True

    nk = _norm_key(gname)
    return bool(nk and nk in _PROTECTED_GROUP_NAMES_NORM)


# ------------------------------
# Plan reconcile (solo calcula)
# ------------------------------
def _plan_reconcile(tv_db_path: str, playlist_m3u_path: str, update_icons: bool) -> tuple[bool, int, int, int]:
    global _LAST_DB_MISMATCH

    if not tv_db_path or not os.path.exists(tv_db_path):
        return False, 0, 0, 0
    if os.path.exists(tv_db_path + "-wal") or os.path.exists(tv_db_path + "-shm"):
        return False, 0, 0, 0

    wanted_names, logos_by_name, wanted_groups = _parse_m3u_name_logo_group(playlist_m3u_path)
    if not wanted_names:
        return False, 0, 0, 0

    con = None
    try:
        con = sqlite3.connect(tv_db_path, timeout=2.0)
        cur = con.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        if "channels" not in tables:
            return False, 0, 0, 0

        cur.execute("SELECT idChannel, sChannelName, sIconPath FROM channels")
        rows = cur.fetchall()

        del_channels = 0
        upd_icons = 0
        missing = []

        for _, ch_name, ch_icon in rows:
            name_key = _norm_key(ch_name)
            icon = _norm_url(ch_icon)
            if not name_key:
                continue
            if name_key not in wanted_names:
                del_channels += 1
                if len(missing) < 5:
                    missing.append(ch_name)
                continue
            if update_icons:
                logos = logos_by_name.get(name_key) or set()
                if len(logos) == 1:
                    pl_icon = next(iter(logos))
                    if pl_icon and pl_icon != icon:
                        upd_icons += 1

        _LAST_DB_MISMATCH = list(missing)

        if del_channels:
            log_utils.write_log(f"[pvr] DB mismatch: ejemplos canales en DB pero no en playlist: {missing}", level="INFO")

        del_groups = 0
        if "channelgroups" in tables:
            cur.execute("SELECT idGroup, sName, iClientId, sClientName FROM channelgroups")
            grows = cur.fetchall()
            wanted_groups_norm = set(wanted_groups)

            for gid, gname, iClientId, sClientName in grows:
                try:
                    gid_int = int(gid)
                except Exception:
                    continue

                if _is_internal_or_protected_group(gid_int, gname, iClientId, sClientName):
                    continue

                gname_key = _norm_key(gname)
                if gname_key and (gname_key not in wanted_groups_norm):
                    del_groups += 1

        return True, del_channels, upd_icons, del_groups

    except Exception:
        return False, 0, 0, 0
    finally:
        try:
            if con:
                con.close()
        except Exception:
            pass


# ------------------------------
# Reconcile real (borra canales/grupos en TVxx.db)
# ------------------------------
def reconcile_kodi_channels_and_groups_with_playlist(
    tv_db_path: str,
    playlist_m3u_path: str = "/storage/.user/playlist.m3u",
    update_icons: bool = False,
) -> tuple[bool, int, int, int]:
    if not tv_db_path or not os.path.exists(tv_db_path):
        log_utils.write_log("[pvr] TVxx.db no encontrada; abortando reconcile.", level="WARNING")
        return False, 0, 0, 0

    if os.path.exists(tv_db_path + "-wal") or os.path.exists(tv_db_path + "-shm"):
        log_utils.write_log("[pvr] TV DB en uso (wal/shm presentes); abortando reconcile.", level="INFO")
        return False, 0, 0, 0

    wanted_names, logos_by_name, wanted_groups = _parse_m3u_name_logo_group(playlist_m3u_path)
    if not wanted_names:
        log_utils.write_log("[pvr] Playlist vacía/no parseable; NO se reconcilia.", level="WARNING")
        return False, 0, 0, 0

    con = None
    try:
        con = sqlite3.connect(tv_db_path, timeout=2.0)
        cur = con.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        if "channels" not in tables:
            log_utils.write_log("[pvr] No existe tabla 'channels'; abortando.", level="WARNING")
            return False, 0, 0, 0

        cur.execute("SELECT idChannel, sChannelName, sIconPath FROM channels")
        rows = cur.fetchall()

        to_delete_channels = []
        to_update_icons = []

        for cid, ch_name, ch_icon in rows:
            name_key = _norm_key(ch_name)
            icon = _norm_url(ch_icon)
            if not name_key:
                continue
            if name_key not in wanted_names:
                to_delete_channels.append(int(cid))
                continue
            if update_icons:
                logos = logos_by_name.get(name_key) or set()
                if len(logos) == 1:
                    pl_icon = next(iter(logos))
                    if pl_icon and pl_icon != icon:
                        to_update_icons.append((pl_icon, int(cid)))

        to_delete_groups = []
        if "channelgroups" in tables:
            cur.execute("SELECT idGroup, sName, iClientId, sClientName FROM channelgroups")
            grows = cur.fetchall()
            wanted_groups_norm = set(wanted_groups)

            for gid, gname, iClientId, sClientName in grows:
                try:
                    gid_int = int(gid)
                except Exception:
                    continue

                if _is_internal_or_protected_group(gid_int, gname, iClientId, sClientName):
                    continue

                gname_key = _norm_key(gname)
                if gname_key and (gname_key not in wanted_groups_norm):
                    to_delete_groups.append(gid_int)

        if not to_delete_channels and not to_update_icons and not to_delete_groups:
            log_utils.write_log("[pvr] Reconcile: no hay cambios.", level="INFO")
            return True, 0, 0, 0

        con.execute("BEGIN IMMEDIATE")

        if "map_channelgroups_channels" in tables and to_delete_channels:
            cur.execute(
                "DELETE FROM map_channelgroups_channels WHERE idChannel IN ({})".format(",".join("?" for _ in to_delete_channels)),
                to_delete_channels,
            )

        if "map_channelgroups_channels" in tables and to_delete_groups:
            cur.execute(
                "DELETE FROM map_channelgroups_channels WHERE idGroup IN ({})".format(",".join("?" for _ in to_delete_groups)),
                to_delete_groups,
            )

        if to_delete_channels:
            cur.execute(
                "DELETE FROM channels WHERE idChannel IN ({})".format(",".join("?" for _ in to_delete_channels)),
                to_delete_channels,
            )

        if to_update_icons:
            cur.executemany("UPDATE channels SET sIconPath=? WHERE idChannel=?", to_update_icons)

        if "channelgroups" in tables and to_delete_groups:
            cur.execute(
                "DELETE FROM channelgroups WHERE idGroup IN ({})".format(",".join("?" for _ in to_delete_groups)),
                to_delete_groups,
            )

        con.commit()

        log_utils.write_log(
            "[pvr] Reconciliación OK: canales_borrados={} iconos_actualizados={} grupos_borrados={}".format(
                len(to_delete_channels), len(to_update_icons), len(to_delete_groups)
            ),
            level="INFO",
        )
        return True, len(to_delete_channels), len(to_update_icons), len(to_delete_groups)

    except Exception as e:
        try:
            if con:
                con.rollback()
        except Exception:
            pass
        log_utils.write_log("[pvr] Error reconcile: {}\n{}".format(e, traceback.format_exc()), level="ERROR")
        return False, 0, 0, 0
    finally:
        try:
            if con:
                con.close()
        except Exception:
            pass


# ------------------------------
# Tags TVH (ficheros)
# ------------------------------
def _tvh_tag_norm(s):
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.casefold()


def _tvh_parse_groups_from_m3u(m3u_path):
    groups = set()
    try:
        with open(m3u_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.lstrip().startswith("#EXTINF"):
                    continue
                m = _RE_GRP_TITLE.search(line)
                if not m:
                    continue
                g = (m.group(2) or "").strip()
                if g:
                    groups.add(g)
    except Exception:
        return set()
    return groups

def _tvh_api_post_json(api_path: str, payload: dict, timeout_s: float = 15.0) -> tuple[bool, int, str]:
    host = "127.0.0.1"
    url = f"http://{host}:{int(TVH_HTTP_PORT)}/api/{api_path.lstrip('/')}"

    p = dict(payload or {})

    # auth: user sin pass -> también lo metemos en payload si aplica
    u, pw = _tvh_get_http_auth()
    if u and not pw and "username" not in p:
        p["username"] = u

    data = json.dumps(p, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("User-Agent", UA)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "*/*")
    req.add_header("Connection", "close")

    try:
        with _tvh_urlopen(req, timeout_s) as r:
            code = int(getattr(r, "status", 200) or 200)
            body = (r.read() or b"").decode("utf-8", "replace")
            return True, code, body
    except Exception as e:
        try:
            code = int(getattr(e, "code", 0) or 0)
            body = (e.read() or b"").decode("utf-8", "replace") if hasattr(e, "read") else str(e)
            return False, code, body
        except Exception:
            return False, 0, str(e)

def _tvh_load_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception:
        return None


def _tvh_save_json_atomic(path, data):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return True
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False


def sync_tvh_channel_tags_from_playlist(playlist_m3u_path):
    tagdir = TVH_TAGDIR

    if not os.path.isdir(tagdir):
        log_utils.write_log(f"[pvr][tags] tagdir no existe: {tagdir}", level="WARNING")
        return False, 0, 0

    desired_raw = _tvh_parse_groups_from_m3u(playlist_m3u_path)
    if not desired_raw:
        log_utils.write_log("[pvr][tags] playlist sin group-title; no sincronizo tags.", level="WARNING")
        return False, 0, 0

    desired_norm = set(_tvh_tag_norm(g) for g in desired_raw)

    entries = []
    max_index = -1

    try:
        for fn in os.listdir(tagdir):
            if fn.startswith("."):
                continue
            path = os.path.join(tagdir, fn)
            if not os.path.isfile(path):
                continue

            d = _tvh_load_json(path)
            if not isinstance(d, dict):
                continue

            name = (d.get("name") or "").strip()
            if not name:
                continue

            internal = bool(d.get("internal"))
            idx = d.get("index")
            if isinstance(idx, int):
                max_index = max(max_index, idx)

            entries.append({"file": path, "norm": _tvh_tag_norm(name), "internal": internal})
    except Exception as e:
        log_utils.write_log(f"[pvr][tags] error leyendo tagdir: {e}", level="ERROR")
        return False, 0, 0

    existing_norm = set(e["norm"] for e in entries if not e["internal"])
    to_create = [g for g in sorted(desired_raw) if _tvh_tag_norm(g) not in existing_norm]
    to_delete = [e for e in entries if (not e["internal"]) and (e["norm"] not in desired_norm)]

    created = 0
    deleted = 0

    for e in to_delete:
        try:
            os.remove(e["file"])
            deleted += 1
        except Exception:
            pass

    next_index = max_index + 1
    for g in to_create:
        try:
            tag_id = uuid.uuid4().hex
            path = os.path.join(tagdir, tag_id)
            data = {
                "enabled": True,
                "index": int(next_index),
                "name": g,
                "internal": False,
                "private": False,
                "icon": "",
                "titled_icon": False,
                "comment": "",
            }
            if _tvh_save_json_atomic(path, data):
                created += 1
                next_index += 1
        except Exception:
            pass

    log_utils.write_log(f"[pvr][tags] sync OK: created={created} deleted={deleted} (groups={len(desired_raw)})", level="INFO")
    return True, created, deleted


# ------------------------------
# Ports / READY
# ------------------------------
def _check_port_connection(host: str, port: int) -> bool:
    try:
        infos = socket.getaddrinfo(host, int(port), socket.AF_UNSPEC, socket.SOCK_STREAM)
    except Exception:
        return False

    for fam, socktype, proto, _, addr in infos:
        try:
            s = socket.socket(fam, socktype, proto)
            s.settimeout(1.0)
            try:
                if s.connect_ex(addr) == 0:
                    return True
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        except Exception:
            pass
    return False


def _wait_tvheadend_ready(timeout_s: int = 70) -> bool:
    log_utils.write_log("[pvr] Esperando Tvheadend: servicio + puertos 9981/9982...", level="INFO")
    deadline = time.time() + max(5, int(timeout_s))

    while time.time() < deadline:
        if _is_service_active(TVH_SERVICE):
            http_ok = _check_port_connection("localhost", TVH_HTTP_PORT)
            htsp_ok = _check_port_connection("localhost", TVH_HTSP_PORT)
            if http_ok and htsp_ok:
                time.sleep(2.0)
                log_utils.write_log("[pvr] Tvheadend READY (9981/9982 OK).", level="INFO")
                return True
        time.sleep(2.0)

    log_utils.write_log("[pvr] TIMEOUT: Tvheadend no abrió 9981/9982 a tiempo.", level="ERROR")
    return False


def _wait_pvr_ready(timeout_s=120, poll_s=1.5, grace_s=20) -> bool:
    t0 = time.time()
    warned = False

    while (time.time() - t0) < float(timeout_s):
        props = _pvr_get_properties()
        if props and bool(props.get("available")):
            if _pvr_has_any_channels_via_conditions() or _pvr_has_any_channels_via_db():
                return True
            if (time.time() - t0) >= float(grace_s) and not warned:
                log_utils.write_log("[pvr] PVR available=True pero aún sin canales; espero…", level="INFO")
                warned = True
        else:
            if (time.time() - t0) >= float(grace_s) and not warned:
                log_utils.write_log("[pvr] PVR aún no disponible (available=False); espero…", level="INFO")
                warned = True
        time.sleep(float(poll_s))

    log_utils.write_log("[pvr] TIMEOUT esperando PVR READY.", level="WARNING")
    return False


def _toggle_pvr_addon_rescue(addon_id: str) -> None:
    _addon_set_enabled(addon_id, False)
    time.sleep(2.5)
    _addon_set_enabled(addon_id, True)
    time.sleep(2.5)


def _restart_kodi_if_idle(timeout_s=20) -> bool:
    try:
        if not utils.kodi_is_idle():
            log_utils.write_log("[pvr] Kodi no está idle; NO reinicio (rescate).", level="INFO")
            return False
    except Exception as e:
        log_utils.write_log(f"[pvr] No pude comprobar idle; NO reinicio Kodi: {e}", level="WARNING")
        return False

    for cmd in (["systemctl", "restart", "kodi"], ["systemctl", "restart", "kodi.service"]):
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=int(timeout_s), check=True)
            log_utils.write_log("[pvr] Kodi reiniciado (rescate PVR).", level="WARNING")
            return True
        except Exception:
            pass

    try:
        subprocess.run(["killall", "-TERM", "kodi.bin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=True)
        log_utils.write_log("[pvr] Kodi TERM enviado (rescate PVR).", level="WARNING")
        return True
    except Exception as e:
        log_utils.write_log(f"[pvr] No pude reiniciar Kodi: {e}", level="ERROR")
        return False


# ------------------------------
# Tvheadend grid helpers (channel + bouquet)
# ------------------------------
def _tvh_find_target_bouquet_uuid() -> str:
    ok, code, data, raw = _tvh_api_get_json("bouquet/grid", query={"start": 0, "limit": 200}, timeout_s=10)
    if not ok or not isinstance(data, dict):
        log_utils.write_log(f"[pvr] bouquet/grid FAIL (HTTP {code}): {(raw or '')[:200]}", level="WARNING")
        return ""

    entries = data.get("entries") or []
    if not isinstance(entries, list) or not entries:
        log_utils.write_log("[pvr] bouquet/grid OK pero sin entries.", level="WARNING")
        return ""

    iptv_bouquets = []
    for b in entries:
        if not isinstance(b, dict):
            continue
        uuid_ = (b.get("uuid") or "").strip()
        source = ((b.get("source") or b.get("type") or "")).strip().lower()
        name = (b.get("name") or "").strip()
        if not uuid_:
            continue
        if "iptv" in source:
            iptv_bouquets.append((uuid_, name))
            lname = name.lower()
            if "iptv" in lname or "local" in lname:
                log_utils.write_log(f"[pvr] bouquet IPTV seleccionado por nombre: {name} ({uuid_})", level="INFO")
                return uuid_

    if len(iptv_bouquets) == 1:
        uuid_, name = iptv_bouquets[0]
        log_utils.write_log(f"[pvr] bouquet IPTV único seleccionado: {name} ({uuid_})", level="INFO")
        return uuid_

    if iptv_bouquets:
        log_utils.write_log(f"[pvr] bouquets IPTV encontrados pero ambiguos: {iptv_bouquets}", level="WARNING")
        return iptv_bouquets[0][0]

    log_utils.write_log("[pvr] No se encontró ningún bouquet IPTV.", level="WARNING")
    return ""


def _tvh_channel_grid_fetch(limit: int = 7000) -> tuple[bool, list[dict], int, str]:
    ok, code, data, raw = _tvh_api_get_json("channel/grid", query={"start": 0, "limit": int(limit)}, timeout_s=12)
    if not ok or not isinstance(data, dict):
        return False, [], int(code or 0), (raw or "")
    entries = data.get("entries") or []
    if not isinstance(entries, list):
        entries = []
    entries = [e for e in entries if isinstance(e, dict)]
    return True, entries, int(code or 0), (raw or "")


def _tvh_idnode_delete_uuids(uuids: list[str], retries: int = 2, timeout_s: float = 15.0) -> tuple[bool, int]:
    """
    Borra nodos por UUID usando /api/idnode/delete.
    Soporta dos formatos (A y B) porque TVH depende del build:
      A) form: node=[{"uuid":"..."},...]
      B) form: uuid=<u>&uuid=<u2>...
    Devuelve (ok, deleted_count_aproximado)
    """
    if not uuids:
        return True, 0

    uuids = [u.strip() for u in uuids if (u or "").strip()]
    if not uuids:
        return True, 0

    def _is_auth(body: str, code: int) -> bool:
        b = (body or "")
        return int(code or 0) == 401 or ("401 Unauthorized" in b) or ("Default login" in b) or ("/login" in b)

    last_code = 0
    last_body = ""

    for attempt in range(retries + 1):
        if attempt > 0:
            time.sleep(0.6 + attempt * 0.8)

        # Formato A (node JSON dentro de form-urlencoded)
        node = [{"uuid": u} for u in uuids]
        formA = {"node": json.dumps(node, separators=(",", ":"))}
        ok, code, body = _tvh_api_post_form("idnode/delete", formA, timeout_s=float(timeout_s))
        code_i = int(code or 0)
        last_code, last_body = code_i, (body or "")

        if ok and 200 <= code_i < 300:
            return True, len(uuids)

        if _is_auth(last_body, last_code):
            log_utils.write_log(
                "[pvr][tvh_delete] idnode/delete AUTH FAIL (HTTP {}): {}".format(code_i, (last_body or "")[:200]),
                level="ERROR",
            )
            return False, 0

        # Si 400, probamos formato B: uuid repetido
        if code_i == 400:
            try:
                formB = [("uuid", u) for u in uuids]
                data = urllib.parse.urlencode(formB).encode("utf-8")

                url = "http://127.0.0.1:{}/api/idnode/delete".format(int(TVH_HTTP_PORT))
                req = urllib.request.Request(url, data=data, method="POST")
                req.add_header("User-Agent", UA)
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
                req.add_header("Accept", "*/*")
                req.add_header("Connection", "close")

                with _tvh_urlopen(req, timeout_s) as r:
                    code2 = int(getattr(r, "status", 200) or 200)
                    body2 = (r.read() or b"").decode("utf-8", "replace")

                if 200 <= code2 < 300:
                    return True, len(uuids)

                last_code, last_body = code2, body2
            except Exception as e:
                last_code, last_body = 0, str(e)

        log_utils.write_log(
            "[pvr][tvh_delete] idnode/delete FAIL (HTTP {} attempt={}/{}): {}".format(
                last_code, attempt + 1, retries + 1, (last_body or "")[:200].replace("\n", " ")
            ),
            level="WARNING",
        )

    log_utils.write_log(
        "[pvr][tvh_delete] idnode/delete FINAL FAIL (HTTP {}): {}".format(
            last_code, (last_body or "")[:200].replace("\n", " ")
        ),
        level="ERROR",
    )
    return False, 0

def _tvh_list_bad_channels_in_bouquet(bouquet_uuid: str) -> tuple[bool, list[str], list[dict]]:
    bq = (bouquet_uuid or "").strip()
    if not bq:
        return False, [], []

    ok, entries, code, raw = _tvh_channel_grid_fetch(limit=8000)
    if not ok:
        log_utils.write_log("[pvr][tvh_cleanup] channel/grid FAIL (HTTP {}): {}".format(code, (raw or "")[:200]), level="WARNING")
        return False, [], []

    bad_names = {"{name-not-set}", "service01", ""}

    uuids: list[str] = []
    samples: list[dict] = []

    for ch in entries:
        if (ch.get("bouquet") or "").strip() != bq:
            continue
        if bool(ch.get("internal")):
            continue

        uuid_ = (ch.get("uuid") or ch.get("key") or ch.get("id") or "").strip()
        if not uuid_:
            continue

        name = (ch.get("name") or "").strip()
        if name.casefold() in bad_names:
            uuids.append(uuid_)
            if len(samples) < 10:
                samples.append({
                    "uuid": uuid_,
                    "name": name,
                    "enabled": ch.get("enabled"),
                    "number": ch.get("number"),
                    "services": ch.get("services"),
                })

    return True, uuids, samples

def tvh_delete_name_not_set_channels(
    bouquet_uuid: str,
    dry_run: bool = False,
    batch: int = 40,
) -> tuple[bool, int]:
    """
    Borra canales basura del bouquet ({name-not-set}, Service01, vacío),
    con verificación real y reintento individual si queda alguno.

    Devuelve (ok, deleted_real).
    """
    bq = (bouquet_uuid or "").strip()
    if not bq:
        log_utils.write_log("[pvr][tvh_cleanup] bouquet_uuid vacío; no limpio.", level="WARNING")
        return False, 0

    ok, to_delete, samples = _tvh_list_bad_channels_in_bouquet(bq)
    if not ok:
        return False, 0

    if not to_delete:
        log_utils.write_log("[pvr][tvh_cleanup] OK: no hay {name-not-set}/Service01 en ese bouquet.", level="INFO")
        return True, 0

    log_utils.write_log(
        "[pvr][tvh_cleanup] Detectados canales basura: {} (bouquet={}). Ejemplos: {}".format(len(to_delete), bq, samples),
        level="WARNING",
    )

    if dry_run:
        log_utils.write_log("[pvr][tvh_cleanup] DRY_RUN activo: no borro.", level="WARNING")
        return True, 0

    before_set = set(to_delete)

    # 1) intento por batches
    for i in range(0, len(to_delete), max(1, int(batch))):
        chunk = to_delete[i:i + int(batch)]
        ok2, _ = _tvh_idnode_delete_uuids(chunk, retries=2, timeout_s=18.0)
        if not ok2:
            log_utils.write_log("[pvr][tvh_cleanup] ABORT: fallo borrando batch {}..{}".format(i, i + len(chunk) - 1), level="ERROR")
            return False, 0
        time.sleep(0.4)  # deja respirar a TVH

    # 2) verificar qué queda
    okv, remaining, _samples2 = _tvh_list_bad_channels_in_bouquet(bq)
    if not okv:
        # no puedo verificar => no te vendo humo: considero fallo parcial
        log_utils.write_log("[pvr][tvh_cleanup] No pude verificar tras borrado (channel/grid).", level="WARNING")
        return False, 0

    remaining_set = set(remaining)
    deleted_real = len(before_set - remaining_set)

    # 3) reintento individual para los que queden (esto suele arreglar el “borra 1 de 2”)
    if remaining:
        log_utils.write_log("[pvr][tvh_cleanup] Quedan {} basura tras batch; reintento 1-by-1...".format(len(remaining)), level="WARNING")
        for u in list(remaining):
            ok3, _ = _tvh_idnode_delete_uuids([u], retries=3, timeout_s=18.0)
            time.sleep(0.35)
            # recheck rápido del mismo uuid
            okx, rem2, _ = _tvh_list_bad_channels_in_bouquet(bq)
            if not okx:
                continue
            if u not in set(rem2):
                deleted_real += 1

        # verificación final
        okf, final_rem, _ = _tvh_list_bad_channels_in_bouquet(bq)
        if okf and final_rem:
            log_utils.write_log("[pvr][tvh_cleanup] WARNING: aún quedan basura tras retries: {}".format(final_rem[:10]), level="WARNING")

    log_utils.write_log("[pvr][tvh_cleanup] OK: deleted_real={}".format(deleted_real), level="INFO")
    return True, deleted_real

def _tvh_collect_channels_to_delete(
    playlist_m3u_path: str,
    bouquet_uuid: str,
) -> tuple[bool, list[str], list[dict]]:
    """
    Devuelve uuids a borrar y samples (debug).
    Criterios:
      - En el bouquet dado
      - No internal
      - (a) name NOT IN playlist  OR
      - (b) name in {name-not-set, Service01, vacío}
    """
    bq = (bouquet_uuid or "").strip()
    if not bq:
        return False, [], []

    wanted_names, _, _ = _parse_m3u_name_logo_group(playlist_m3u_path)
    if not wanted_names:
        log_utils.write_log("[pvr][tvh_prune_ch] playlist sin nombres parseables; abort.", level="WARNING")
        return False, [], []

    ok, entries, code, raw = _tvh_channel_grid_fetch(limit=8000)
    if not ok:
        log_utils.write_log("[pvr][tvh_prune_ch] channel/grid FAIL (HTTP {}): {}".format(code, (raw or "")[:200]), level="WARNING")
        return False, [], []

    bad_names = {"{name-not-set}", "service01", ""}

    uuids: list[str] = []
    samples: list[dict] = []

    for ch in entries:
        if (ch.get("bouquet") or "").strip() != bq:
            continue
        if bool(ch.get("internal")):
            continue

        uuid_ = (ch.get("uuid") or ch.get("key") or ch.get("id") or "").strip()
        if not uuid_:
            continue

        name = (ch.get("name") or "").strip()
        ncf = name.casefold()

        # (b) basura explícita
        is_bad = (ncf in bad_names)

        # (a) fuera de playlist
        in_playlist = False
        if name:
            in_playlist = (_norm_key(name) in wanted_names)

        if is_bad or (not in_playlist):
            uuids.append(uuid_)
            if len(samples) < 12:
                samples.append({
                    "uuid": uuid_,
                    "name": name,
                    "enabled": ch.get("enabled"),
                    "number": ch.get("number"),
                    "services": ch.get("services"),
                    "reason": ("bad-name" if is_bad else "name-not-in-playlist"),
                })

    return True, uuids, samples

def tvh_delete_channels_not_in_playlist_or_bad(
    playlist_m3u_path: str,
    bouquet_uuid: str,
    dry_run: bool = False,
    batch: int = 60,
    max_rounds: int = 4,
    settle_s: float = 0.6,
) -> tuple[bool, int]:
    """
    BORRA (idnode/delete) canales del bouquet:
      - fuera de playlist
      - y/o {name-not-set}/Service01/vacío
    Con verificación REAL y rondas por si TVH tarda o regenera.

    Devuelve (ok, deleted_real_acumulado).
    """
    bq = (bouquet_uuid or "").strip()
    if not bq:
        log_utils.write_log("[pvr][tvh_prune_ch] bouquet_uuid vacío; no borro.", level="WARNING")
        return False, 0

    deleted_real_total = 0

    for round_i in range(1, max_rounds + 1):
        ok, to_del, samples = _tvh_collect_channels_to_delete(playlist_m3u_path, bq)
        if not ok:
            return False, deleted_real_total

        if not to_del:
            if round_i == 1:
                log_utils.write_log("[pvr][tvh_prune_ch] OK: no hay canales fuera/basura en ese bouquet.", level="INFO")
            else:
                log_utils.write_log("[pvr][tvh_prune_ch] OK: limpio tras {} rondas.".format(round_i - 1), level="INFO")
            return True, deleted_real_total

        log_utils.write_log(
            "[pvr][tvh_prune_ch] Ronda {}/{}: a borrar={} (bouquet={}). Ejemplos: {}".format(
                round_i, max_rounds, len(to_del), bq, samples
            ),
            level="WARNING",
        )

        if dry_run:
            log_utils.write_log("[pvr][tvh_prune_ch] DRY_RUN activo: no borro.", level="WARNING")
            return True, 0

        before_set = set(to_del)

        # 1) Borrado por batches
        for i in range(0, len(to_del), max(1, int(batch))):
            chunk = to_del[i:i + int(batch)]
            ok2, _ = _tvh_idnode_delete_uuids(chunk, retries=3, timeout_s=18.0)
            if not ok2:
                log_utils.write_log("[pvr][tvh_prune_ch] ABORT: fallo borrando batch {}..{}".format(i, i + len(chunk) - 1), level="ERROR")
                return False, deleted_real_total
            time.sleep(settle_s)

        # 2) Verificación
        okv, after_list, _ = _tvh_collect_channels_to_delete(playlist_m3u_path, bq)
        if not okv:
            log_utils.write_log("[pvr][tvh_prune_ch] No pude verificar tras borrado.", level="WARNING")
            return False, deleted_real_total

        after_set = set(after_list)
        deleted_this_round = len(before_set - after_set)
        deleted_real_total += deleted_this_round

        log_utils.write_log(
            "[pvr][tvh_prune_ch] Ronda {}: deleted_real={} quedan={}".format(round_i, deleted_this_round, len(after_set)),
            level="INFO",
        )

        # 3) Si quedan, reintento 1-by-1 (muy importante para tu caso de “borra 1 de 2”)
        if after_set:
            for u in list(after_set):
                ok3, _ = _tvh_idnode_delete_uuids([u], retries=4, timeout_s=18.0)
                time.sleep(settle_s)
                if not ok3:
                    continue

            # mini-verificación extra
            okf, final_list, _ = _tvh_collect_channels_to_delete(playlist_m3u_path, bq)
            if okf and not final_list:
                log_utils.write_log("[pvr][tvh_prune_ch] Limpieza completa tras reintento 1-by-1.", level="INFO")
                return True, deleted_real_total

        # Si sigue habiendo, volvemos a empezar otra ronda (posible regen)
        time.sleep(1.0)

    # Si llegamos aquí, tras max_rounds sigue apareciendo: esto es casi seguro REGENERACIÓN
    ok_last, remain, samples_last = _tvh_collect_channels_to_delete(playlist_m3u_path, bq)
    if ok_last and remain:
        log_utils.write_log(
            "[pvr][tvh_prune_ch] WARNING: tras {} rondas siguen reapareciendo {} canales. Esto huele a regeneración automática. Ejemplos: {}".format(
                max_rounds, len(remain), samples_last[:6]
            ),
            level="WARNING",
        )
    return True, deleted_real_total


# ------------------------------
# tv_grab_file
# ------------------------------
def update_tv_grab_file() -> bool:
    local_path = "/storage/.kodi/addons/service.tvheadend43/bin/tv_grab_file"
    remote_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/pvr/tv_grab_file"
    remote_tmp = local_path + ".remote"

    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if not utils.download_atomic(remote_tmp, remote_url, retries=2, timeout=20):
            log_utils.write_log("[tv_grab_file] Descarga fallida.", level="ERROR")
            return False

        remote_data = utils._read_bytes(remote_tmp)
        local_data = utils._read_bytes(local_path) if os.path.exists(local_path) else None

        if local_data == remote_data:
            log_utils.write_log("[tv_grab_file] Sin cambios.")
            return True

        tmp_local = local_path + ".part"
        with open(tmp_local, "wb") as f:
            f.write(remote_data)
            f.flush()
            os.fsync(f.fileno())

        os.chmod(tmp_local, 0o755)
        os.replace(tmp_local, local_path)

        log_utils.write_log("[tv_grab_file] Actualizado.")
        return True

    except Exception as e:
        log_utils.write_log("[tv_grab_file] Error: {}\n{}".format(e, traceback.format_exc()), level="ERROR")
        return False
    finally:
        try:
            if os.path.exists(remote_tmp):
                os.remove(remote_tmp)
        except Exception:
            pass

# ------------------------------
# http_user_agent tvheadend
# ------------------------------
def ensure_tvh_http_user_agent() -> bool:
    cfg_path = "/storage/.kodi/userdata/addon_data/service.tvheadend43/config"
    desired_agent = "samsung-agent/1.1"

    if not os.path.exists(cfg_path):
        log_utils.write_log("[tvh_config] Config no encontrado.", level="ERROR")
        return False

    try:
        with open(cfg_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read().strip()

        if raw.endswith(";"):
            raw = raw[:-1].rstrip()

        data = json.loads(raw)

        if data.get("http_user_agent") == desired_agent:
            return True

        data["http_user_agent"] = desired_agent

        tmp = cfg_path + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp, cfg_path)
        log_utils.write_log("[tvh_config] http_user_agent ajustado.")
        return True

    except Exception as e:
        log_utils.write_log("[tvh_config] Error: {}\n{}".format(e, traceback.format_exc()), level="ERROR")
        return False

# ------------------------------
# EPG
# ------------------------------
def force_tvh_epg_reload(internal: bool = True) -> bool:
    if not internal:
        return False
    ok, code, body = _tvh_api_get("epggrab/internal/rerun", {"rerun": 1}, timeout_s=10)
    if ok:
        log_utils.write_log(f"[pvr] EPG: internal rerun OK (HTTP {code}).", level="INFO")
        return True
    log_utils.write_log(f"[pvr] EPG: internal rerun FAIL (HTTP {code}): {(body or '')[:200]}", level="WARNING")
    return False

def _tvh_service_set_svcname(service_uuid: str, svc_name: str):
    """
    CoreELEC / tvheadend43
    El nombre editable del SERVICE es 'svcname', NO 'channelname'.
    """
    fields = {
        "op": "save",
        "conf": 1,
        "class": "service",
        "node": (service_uuid or "").strip(),
        "svcname": (svc_name or "").strip(),
    }
    return _tvh_api_post_form("idnode/save", fields)

def _pick_best_epg_hit(ch_name_raw: str, want_raw: str, hits: list[dict]) -> dict | None:
    """
    Desempata hits que colisionan en la misma key normalizada.
    Devuelve 1 dict o None si no puede decidir con seguridad.
    """
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]

    ch = (ch_name_raw or "").strip()
    want = (want_raw or ch).strip()

    # Variante "display" sin prefijo |ES|/[ES]/(ES)
    want_noprefix = re.sub(r'^\s*\|[^|]{1,16}\|\s*', '', want)
    want_noprefix = re.sub(r'^\s*\[[^\]]{1,16}\]\s*', '', want_noprefix)
    want_noprefix = re.sub(r'^\s*\([^\)]{1,16}\)\s*', '', want_noprefix).strip()

    def _epg_name(e: dict) -> str:
        for k in ("name", "channelname", "displayname", "id"):
            v = e.get(k)
            if v:
                return str(v).strip()
        return ""

    hit_names = [(_epg_name(h), h) for h in hits]

    # 1) match exacto (con y sin prefijo)
    for nm, h in hit_names:
        if nm == want or nm == want_noprefix:
            return h

    # 2) match por token de calidad (si el canal lo trae)
    qual = None
    for q in ("UHD", "4K", "FHD", "HD", "SD"):
        if q in want.upper():
            qual = q
            break

    if qual:
        qual_hits = [(nm, h) for nm, h in hit_names if qual in nm.upper()]
        if len(qual_hits) == 1:
            return qual_hits[0][1]

    # 3) si hay uno "sin calidad" y el canal tampoco trae calidad, preferir ese
    def _has_quality(s: str) -> bool:
        up = s.upper()
        return any(t in up for t in ("UHD", "4K", "FHD", "HD", "SD"))

    want_has_q = _has_quality(want)
    noqual_hits = [(nm, h) for nm, h in hit_names if not _has_quality(nm)]
    if (not want_has_q) and len(noqual_hits) == 1:
        return noqual_hits[0][1]

    return None

def tvh_autofix_missing_epg_sources(
    dry_run: bool = False,
    max_examples: int = 12,   # ya no se usa para log de missing; lo dejo para compatibilidad
    max_changes: int = 60,
    skip_adult: bool = True,
) -> tuple[bool, int, int, int]:
    """
    Asigna EPG Source a canales que lo han perdido (epggrab vacío).
    Matching por nombre normalizado.

    Devuelve: (ok, fixed, not_found, ambiguous)
    """

    QUALITY_TOKENS = {
        "SD", "HD", "FHD", "UHD", "4K",
        "HEVC", "H265", "H.265", "H264", "H.264",
        "HDR", "DV", "DOLBY", "VISION",
    }

    OVERRIDE = {
        # "|ES| SOMOS FHD": "SOMOS",
        # "|ES| SOMOS": "SOMOS",
    }

    def _norm_epg_name(s: str) -> str:
        s = (s or "").strip()
        if not s:
            return ""

        # prefijos IPTV
        s = re.sub(r'^\s*\|[^|]{1,16}\|\s*', '', s)      # |ES|
        s = re.sub(r'^\s*\[[^\]]{1,16}\]\s*', '', s)     # [ES]
        s = re.sub(r'^\s*\([^\)]{1,16}\)\s*', '', s)     # (ES)

        # acentos fuera
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))

        s = s.upper()

        parts = re.split(r"\s+", s)
        parts = [p for p in parts if p and p not in QUALITY_TOKENS]
        s = " ".join(parts)

        s = re.sub(r"[^A-Z0-9 ]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    # 1) EPG grabber channels
    ok, code, data, raw = _tvh_api_get_json("epggrab/channel/grid", query={"start": 0, "limit": 9000}, timeout_s=12)
    if not ok or not isinstance(data, dict):
        log_utils.write_log(
            f"[pvr][epgsrc] epggrab/channel/grid FAIL (HTTP {code}): {(raw or '')[:200]}",
            level="WARNING",
        )
        return False, 0, 0, 0

    epg_entries = data.get("entries") or []
    if not isinstance(epg_entries, list):
        epg_entries = []

    epg_by_norm: dict[str, list[dict]] = {}
    for e in epg_entries:
        if not isinstance(e, dict):
            continue
        candidates = set()

        for k in ("name", "id", "channelname", "displayname"):
            v = e.get(k)
            if v:
                nn = _norm_epg_name(str(v))
                if nn:
                    candidates.add(nn)

        names = e.get("names")
        if isinstance(names, list):
            for a in names:
                if a:
                    nn = _norm_epg_name(str(a))
                    if nn:
                        candidates.add(nn)

        for nn in candidates:
            epg_by_norm.setdefault(nn, []).append(e)

    # 2) Channels
    okc, channels, code2, raw2 = _tvh_channel_grid_fetch(limit=12000)
    if not okc:
        log_utils.write_log(
            f"[pvr][epgsrc] channel/grid FAIL (HTTP {code2}): {(raw2 or '')[:200]}",
            level="WARNING",
        )
        return False, 0, 0, 0

    # Missing = epggrab vacío (None / "" / [])
    missing = []
    for ch in channels:
        if not isinstance(ch, dict):
            continue
        eg = ch.get("epggrab")
        if not eg:
            missing.append(ch)

    if not missing:
        log_utils.write_log("[pvr][epgsrc] OK: no hay canales sin EPG Source.", level="INFO")
        return True, 0, 0, 0

    fixed = 0
    not_found = 0
    ambiguous = 0
    save_fail = 0
    skipped_adult = 0
    skipped_no_uuid_or_name = 0

    for ch in missing:
        if fixed >= int(max_changes):
            log_utils.write_log(f"[pvr][epgsrc] STOP: alcanzado max_changes={max_changes}", level="WARNING")
            break

        ch_name = (ch.get("name") or "").strip()
        ch_uuid = (ch.get("uuid") or ch.get("key") or ch.get("id") or "").strip()
        if not ch_uuid or not ch_name:
            skipped_no_uuid_or_name += 1
            continue

        if skip_adult and ch_name.startswith("|ADULTOS|"):
            skipped_adult += 1
            continue

        want = OVERRIDE.get(ch_name)
        key = _norm_epg_name(want if want else ch_name)

        hits = epg_by_norm.get(key, [])
        if len(hits) == 0:
            not_found += 1
            continue

        if len(hits) > 1:
            picked = _pick_best_epg_hit(ch_name, want if want else ch_name, hits)
            if not picked:
                ambiguous += 1
                cand = [(h.get("name") or h.get("id") or "<?>") for h in hits[:4] if isinstance(h, dict)]
                log_utils.write_log(
                    f"[pvr][epgsrc] AMBIGUO: '{ch_name}' -> '{key}' hits={len(hits)} cand={cand}",
                    level="INFO",
                )
                continue
            hits = [picked]

        epg = hits[0]
        epg_uuid = (epg.get("uuid") or epg.get("key") or epg.get("id") or "").strip()
        if not epg_uuid:
            ambiguous += 1
            log_utils.write_log(f"[pvr][epgsrc] HIT sin uuid/id: '{ch_name}' -> '{key}'", level="WARNING")
            continue

        if dry_run:
            fixed += 1
            log_utils.write_log(f"[pvr][epgsrc] DRY_RUN OK: '{ch_name}' -> '{key}' ({epg_uuid})", level="INFO")
            continue

        oks, c3, b3 = _tvh_channel_set_epggrab(ch_uuid, epg_uuid)

        if oks and 200 <= int(c3 or 0) < 300:
            fixed += 1
            log_utils.write_log(f"[pvr][epgsrc] OK: '{ch_name}' -> '{key}'", level="INFO")
        else:
            save_fail += 1
            log_utils.write_log(
                f"[pvr][epgsrc] SAVE FAIL (HTTP {c3}): ch='{ch_name}' key='{key}' body='{(b3 or '')[:160]}'",
                level="WARNING",
            )

    # Resumen compacto (sin inflar logs)
    log_utils.write_log(
        "[pvr][epgsrc] Fin autofix: fixed={} not_found={} ambiguous={} save_fail={} skipped_adult={} skipped_invalid={}".format(
            fixed, not_found, ambiguous, save_fail, skipped_adult, skipped_no_uuid_or_name
        ),
        level="INFO",
    )
    return True, fixed, not_found, ambiguous


# ------------------------------
# Playlist updater principal
# ------------------------------
def update_playlist() -> tuple[bool, bool]:
    """
    Devuelve: (ok, did_something)
    did_something=True si hubo soft reset (playlist nueva o DB mismatch).
    """
    user_dir = "/storage/.user"
    playlist_file = os.path.join(user_dir, "playlist.m3u")
    user_file = os.path.join(user_dir, "user")

    BASE_URLS = [
        "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/pvr/playlist.m3u",
    ]

    def _read_text(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _norm_newlines(s: str) -> str:
        return (s or "").replace("\r\n", "\n").replace("\r", "\n")

    def _sha256_text(s: str) -> str:
        return utils._sha256_bytes(_norm_newlines(s).encode("utf-8", errors="replace"))

    def _has_valid_creds(txt: str) -> bool:
        m_user = re.search(r'USER_CODE="([^"]+)"', txt)
        m_pass = re.search(r'PASS_CODE="([^"]+)"', txt)
        return bool(m_user and m_pass and m_user.group(1).strip() and m_pass.group(1).strip())

    def _extract_creds(txt: str) -> tuple[str, str]:
        m_user = re.search(r'USER_CODE="([^"]+)"', txt)
        m_pass = re.search(r'PASS_CODE="([^"]+)"', txt)
        if not (m_user and m_pass):
            return "", ""
        return m_user.group(1).strip(), m_pass.group(1).strip()

    def _try_fetch_user_from_remote() -> bool:
        try:
            eth0 = "nomac"
            try:
                ni = utils.get_net_info() or {}
                eth0 = (ni.get("eth0") or "").strip().replace(":", "").lower() or eth0
            except Exception as e:
                log_utils.write_log(f"Excepción ignorada en update_pvr: {e}", "DEBUG")

            remote = "masqelec"
            remote_path = f"masqelec/user/{eth0}"
            tmp_dir = "/tmp"
            tmp_file = os.path.join(tmp_dir, eth0)

            ok = rclone_utils.copy_remote_to_tmp_then_move(remote, remote_path, tmp_dir)
            if not ok or not os.path.exists(tmp_file):
                log_utils.write_log(f"[update_playlist] user remoto no encontrado: {remote}:{remote_path}", level="INFO")
                return False

            txt = _read_text(tmp_file)
            if not _has_valid_creds(txt):
                log_utils.write_log("[update_playlist] user remoto inválido (faltan USER_CODE/PASS_CODE)", level="WARNING")
                try:
                    os.remove(tmp_file)
                except Exception:
                    pass
                return False

            os.makedirs(user_dir, exist_ok=True)
            tmp_install = user_file + ".part"
            with open(tmp_install, "w", encoding="utf-8") as f:
                f.write(_norm_newlines(txt))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_install, user_file)

            try:
                os.remove(tmp_file)
            except Exception:
                pass

            log_utils.write_log(f"[update_playlist] user recuperado del remoto ({eth0})")
            return True

        except Exception as e:
            log_utils.write_log(f"[update_playlist] Error recuperando user remoto: {e}\n{traceback.format_exc()}", level="ERROR")
            return False

    try:
        os.makedirs(user_dir, exist_ok=True)

        if not os.path.exists(user_file):
            if not _try_fetch_user_from_remote():
                log_utils.write_log("Archivo /storage/.user/user no disponible.", level="ERROR")
                _log_pvr_db_stats(prefix="[pvr]")
                return False, False

        # descargar plantilla playlist (con soporte gzip/deflate)
        remote_tpl = None
        last_bytes = 0
        last_firstline = ""

        for url in BASE_URLS:
            try:
                with utils._net_open(url, timeout=20) as r:
                    data = r.read()
                last_bytes = len(data or b"")

                enc = ""
                try:
                    enc = (getattr(r, "headers", None).get("Content-Encoding") or "").lower()
                except Exception:
                    enc = ""

                try:
                    if ("gzip" in enc) or (data[:3] == b"\x1f\x8b\x08"):
                        data = gzip.decompress(data)
                    elif "deflate" in enc:
                        data = zlib.decompress(data)
                except Exception:
                    pass

                txt = (data or b"").decode("utf-8", "replace")
            except Exception:
                continue

            candidate_norm = _norm_newlines(txt)
            try:
                last_firstline = (candidate_norm.strip().splitlines()[0] if candidate_norm.strip() else "")[:200]
            except Exception:
                last_firstline = ""

            low = (candidate_norm.lstrip()[:160] or "").lower()
            if last_bytes < 64 or low.startswith("<!doctype html") or low.startswith("<html"):
                continue

            if "USER_CODE" in candidate_norm and "PASS_CODE" in candidate_norm:
                remote_tpl = candidate_norm
                break

        if not remote_tpl:
            log_utils.write_log(
                f"Plantilla playlist remota inválida. URLs probadas={len(BASE_URLS)}; última bytes={last_bytes}; primera='{last_firstline}'",
                level="ERROR",
            )
            _log_pvr_db_stats(prefix="[pvr]")
            return False, False

        content = _read_text(user_file)
        if not _has_valid_creds(content):
            log_utils.write_log("USER_CODE o PASS_CODE inválidos en /storage/.user/user", level="ERROR")
            _log_pvr_db_stats(prefix="[pvr]")
            return False, False

        user_code, pass_code = _extract_creds(content)
        new_playlist = _norm_newlines(remote_tpl).replace("USER_CODE", user_code).replace("PASS_CODE", pass_code)
        new_hash = _sha256_text(new_playlist)

        local_hash = None
        if os.path.exists(playlist_file):
            try:
                local_hash = _sha256_text(_read_text(playlist_file))
            except Exception:
                local_hash = None

        playlist_changed = (local_hash is None) or (local_hash != new_hash)

        tvdb = _pick_tv_db_path()
        db_mismatch = False
        plan = (False, 0, 0, 0)
        if tvdb and os.path.exists(playlist_file):
            plan = _plan_reconcile(tvdb, playlist_file, update_icons=False)
            if plan[0]:
                _, del_ch, upd_ic, del_gr = plan
                db_mismatch = (del_ch > 0) or (upd_ic > 0) or (del_gr > 0)

        needs_soft_reset = bool(playlist_changed or db_mismatch)
        if not needs_soft_reset:
            log_utils.write_log("[pvr] Sin cambios y DB consistente con playlist.", level="INFO")
            _log_pvr_db_stats(prefix="[pvr]")
            return True, False

        _popup("PVR", "Actualizando PVR…", ms=3000)
        log_utils.write_log(
            "[pvr] Playlist CAMBIA." if playlist_changed else f"[pvr] Playlist igual, pero DB NO coincide (soft reset). plan={plan}",
            level="INFO",
        )

        # 1) disable pvr.hts
        _addon_set_enabled(PVR_ADDON_ID, False)
        _wait_addon_enabled(PVR_ADDON_ID, want_enabled=False, timeout_s=12)
        time.sleep(2.0)

        # 2) asegurar TVH ready
        if not _is_service_active(TVH_SERVICE):
            _start_tvheadend()
        tvh_ready = _wait_tvheadend_ready(timeout_s=70)

        # 2.5) prune TVH channels fuera de playlist (por bouquet)
        if tvh_ready and os.path.exists(playlist_file):
            try:
                bq_uuid = _tvh_find_target_bouquet_uuid()
                tvh_delete_channels_not_in_playlist_or_bad(
                    playlist_m3u_path=playlist_file,
                    bouquet_uuid=bq_uuid,
                    dry_run=False,
                    batch=60,
                    max_rounds=4,
            )

            except Exception as e:
                log_utils.write_log(f"[pvr][tvh_prune_ch] EXCEPTION: {e}", level="WARNING")

        # 2.6) LIMPIEZA FINAL: eliminar basura {name-not-set}
        try:
            tvh_delete_name_not_set_channels(
                bouquet_uuid=bq_uuid,
                dry_run=False,
                batch=40,
            )
        except Exception as e:
            log_utils.write_log(
                "[pvr][tvh_cleanup] EXCEPTION limpiando {name-not-set}: {}".format(e),
                level="WARNING",
            )

        # 3) stop tvh
        _stop_tvheadend()
        time.sleep(1.0)

        # 4) instalar playlist si cambia
        if playlist_changed:
            tmp = playlist_file + ".part"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(new_playlist)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, playlist_file)
            log_utils.write_log("[pvr] Playlist instalada/actualizada.", level="INFO")

        # 5) reconcile DB con TVH parado
        tvdb = _pick_tv_db_path()
        if tvdb:
            reconcile_kodi_channels_and_groups_with_playlist(tv_db_path=tvdb, playlist_m3u_path=playlist_file, update_icons=False)
        else:
            log_utils.write_log("[pvr] No se encontró TVxx.db para reconciliar.", level="WARNING")

        # 6) tags TVH (ficheros) con TVH parado
        try:
            ok_tags, n_created, n_deleted = sync_tvh_channel_tags_from_playlist(playlist_file)
            if ok_tags:
                log_utils.write_log(f"[pvr][tags] sincronizados: +{n_created} -{n_deleted}", level="INFO")
        except Exception as e:
            log_utils.write_log(f"[pvr][tags] sync error: {e}", level="WARNING")

        # 7) start tvh + wait
        _start_tvheadend()
        if not _wait_tvheadend_ready(timeout_s=70):
            log_utils.write_log("[pvr] Tvheadend no listo; NO habilito pvr.hts (evito 0%).", level="WARNING")
            _log_pvr_db_stats(prefix="[pvr]")
            return True, True
        
        # 7.1) TVH a veces regenera basura al arrancar -> limpieza 2ª pasada
        try:
            bq_uuid = _tvh_find_target_bouquet_uuid()
            tvh_delete_name_not_set_channels(
                bouquet_uuid=bq_uuid,
                dry_run=False,
                batch=40,
            )
        except Exception as e:
            log_utils.write_log("[pvr][tvh_cleanup] EXCEPTION post-start: {}".format(e), level="WARNING")

        # 7.2) Reasignar EPG Source a canales que lo pierdan al reiniciar TVH
        try:
            tvh_autofix_missing_epg_sources(dry_run=False)
        except Exception as e:
            log_utils.write_log(f"[pvr][epgsrc] EXCEPTION autofix: {e}", level="WARNING")

        force_tvh_epg_reload(internal=True)
        time.sleep(1.0)

        # 8) enable pvr.hts + wait ready
        _addon_set_enabled(PVR_ADDON_ID, True)
        pvr_ok = _wait_pvr_ready(timeout_s=120, poll_s=1.5, grace_s=20)

        if not pvr_ok:
            log_utils.write_log("[pvr] PVR no quedó READY tras enable. Aplico toggle rescate.", level="WARNING")
            _toggle_pvr_addon_rescue(PVR_ADDON_ID)

            if not _wait_pvr_ready(timeout_s=70, poll_s=1.5, grace_s=15):
                log_utils.write_log("[pvr] PVR sigue sin READY tras rescate. Intento restart tvheadend + toggle.", level="WARNING")
                _run(["systemctl", "restart", TVH_SERVICE], timeout=25)
                if _wait_tvheadend_ready(timeout_s=70):
                    _toggle_pvr_addon_rescue(PVR_ADDON_ID)
                    _wait_pvr_ready(timeout_s=90, poll_s=1.5, grace_s=20)

        if not _wait_pvr_ready(timeout_s=25, poll_s=1.5, grace_s=8):
            log_utils.write_log("[pvr] PVR sigue sin ready. Último rescate: toggle + (opcional) reinicio Kodi idle.", level="ERROR")
            _toggle_pvr_addon_rescue(PVR_ADDON_ID)
            if not _wait_pvr_ready(timeout_s=45, poll_s=1.5, grace_s=10) and ENABLE_KODI_RESTART_FALLBACK:
                _restart_kodi_if_idle(timeout_s=25)

        _log_pvr_db_stats(prefix="[pvr]")

        return True, True

    except Exception as e:
        log_utils.write_log(f"Error en update_playlist: {e}\n{traceback.format_exc()}", level="ERROR")
        _log_pvr_db_stats(prefix="[pvr]")
        return False, False


# ------------------------------
# Final checks (lo mínimo)
# ------------------------------
def tvh_auth_smoketest() -> bool:
    ok, code, body = _tvh_api_get("serverinfo", timeout_s=8)
    if ok and (200 <= code < 300):
        log_utils.write_log(f"[pvr] TVH auth OK (serverinfo HTTP {code}).", level="INFO")
        return True
    log_utils.write_log(f"[pvr] TVH auth FAIL (serverinfo HTTP {code}): {(body or '')[:200]}", level="ERROR")
    return False


def ensure_pvr_stack_active_final() -> None:
    try:
        # TVH
        if not (_is_service_active(TVH_SERVICE) and _check_port_connection("localhost", TVH_HTTP_PORT) and _check_port_connection("localhost", TVH_HTSP_PORT)):
            log_utils.write_log("[pvr][final] Tvheadend NO OK; intento arrancar...", level="WARNING")
            _start_tvheadend()
            if not _wait_tvheadend_ready(timeout_s=70):
                log_utils.write_log("[pvr][final] Tvheadend sigue NO listo.", level="ERROR")
                return
        else:
            log_utils.write_log("[pvr][final] Tvheadend OK (servicio+puertos).", level="INFO")

        # pvr.hts
        en = _get_addon_enabled(PVR_ADDON_ID)
        if en is True:
            if _wait_pvr_ready(timeout_s=25, poll_s=1.5, grace_s=8):
                log_utils.write_log(f"[pvr][final] {PVR_ADDON_ID} enabled y PVR READY.", level="INFO")
            else:
                log_utils.write_log(f"[pvr][final] {PVR_ADDON_ID} enabled pero PVR NO READY.", level="WARNING")
            return

        if en is False:
            log_utils.write_log(f"[pvr][final] {PVR_ADDON_ID} estaba DESHABILITADO; habilitando...", level="WARNING")
            _addon_set_enabled(PVR_ADDON_ID, True)
            _wait_addon_enabled(PVR_ADDON_ID, want_enabled=True, timeout_s=12)
            time.sleep(1.5)
            if _wait_pvr_ready(timeout_s=60, poll_s=1.5, grace_s=15):
                log_utils.write_log(f"[pvr][final] {PVR_ADDON_ID} habilitado y PVR READY.", level="INFO")
            else:
                log_utils.write_log(f"[pvr][final] {PVR_ADDON_ID} habilitado pero PVR no llegó a READY.", level="WARNING")
            return

        log_utils.write_log(f"[pvr][final] No pude leer estado de {PVR_ADDON_ID}.", level="WARNING")
    except Exception as e:
        log_utils.write_log(f"[pvr][final] Error en ensure_pvr_stack_active_final: {e}", level="WARNING")


def update_pvr():
    start_ts = time.time()

    try:
        tvh_auth_smoketest()
    except Exception:
        pass

    try:
        update_tv_grab_file()
    except Exception as e:
        log_utils.write_log(f"[pvr] update_tv_grab_file error: {e}", level="WARNING")

    try:
        ensure_tvh_http_user_agent()
    except Exception as e:
        log_utils.write_log(f"[pvr] ensure_tvh_http_user_agent error: {e}", level="WARNING")

    if _is_service_active(TVH_SERVICE) and _check_port_connection("localhost", TVH_HTTP_PORT):
        tvh_autofix_missing_epg_sources(dry_run=False)
        force_tvh_epg_reload(internal=True)   # para que haga matching y rellene EPG cuanto antes


    try:
        ensure_pvr_stack_active_final()
    except Exception as e:
        log_utils.write_log(f"[pvr] ensure_pvr_stack_active_final error: {e}", level="WARNING")

    try:
        dt = time.time() - start_ts
        log_utils.write_log(f"[pvr] update_pvr terminado en {dt:.1f}s", level="INFO")
    except Exception:
        pass

