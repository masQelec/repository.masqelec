# -*- coding: utf-8 -*-
"""
update_pvr.py — Gestión de PVR:
- Playlist con USER_CODE/PASS_CODE (instalación SOLO si cambia el hash final)
- Sincronización de tv_grab_file desde la nube
- Ajuste http_user_agent en Tvheadend
- Reconciliación selectiva en Kodi (TVxx.db)
- Soft reset robusto si:
    a) cambia playlist, o
    b) la DB no coincide con la playlist aunque el hash sea igual
- Reload agresivo (rescate):
    - enable pvr.hts -> esperar "PVR ready" (PVR.GetProperties + condiciones PVR)
    - si falla -> toggle rescate
    - si sigue fallando -> reinicio Kodi (solo idle) [activado]
"""

import os
import re
import time
import json
import gzip
import zlib
import socket
import sqlite3
import subprocess
import traceback
import base64
import uuid
import urllib.request
import urllib.parse
import urllib.error

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
TVH_SERVICE  = "service.tvheadend43"

TVH_HTTP_PORT = 9981
TVH_HTSP_PORT = 9982

# Rescate
ENABLE_KODI_RESTART_FALLBACK = True


# ------------------------------
# Regex playlist
# ------------------------------
_RE_TVG_NAME  = re.compile(r"""tvg-name\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)
_RE_TVG_LOGO  = re.compile(r"""tvg-logo\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)
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
            xbmc.executebuiltin('Notification({}, {}, {}, {})'.format(
                title.replace(",", " "),
                message.replace(",", " "),
                int(ms),
                ""
            ))
    except Exception:
        pass


# ------------------------------
# System helpers
# ------------------------------
def _run(cmd, timeout=20) -> bool:
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=int(timeout), check=True)
        return True
    except Exception:
        return False


def _is_service_active(unit: str) -> bool:
    try:
        r = subprocess.run(["systemctl", "is-active", unit],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        return (r.stdout or b"").decode("utf-8", "ignore").strip() == "active"
    except Exception:
        return False


def _is_service_inactive(unit: str) -> bool:
    try:
        r = subprocess.run(["systemctl", "is-active", unit],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
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
    if ok:
        log_utils.write_log("[pvr] Tvheadend parado.", level="INFO")
    else:
        log_utils.write_log("[pvr] No pude parar Tvheadend.", level="WARNING")
    return ok


def _start_tvheadend() -> bool:
    ok = _run(["systemctl", "start", TVH_SERVICE], timeout=25)
    _wait_service_state(TVH_SERVICE, want_active=True, timeout_s=25)
    if ok:
        log_utils.write_log("[pvr] Tvheadend iniciado.", level="INFO")
    else:
        log_utils.write_log("[pvr] No pude iniciar Tvheadend.", level="WARNING")
    return ok


def _restart_tvheadend() -> bool:
    ok = _run(["systemctl", "restart", TVH_SERVICE], timeout=25)
    if ok:
        log_utils.write_log("[pvr] Tvheadend reiniciado.", level="INFO")
    else:
        log_utils.write_log("[pvr] No pude reiniciar Tvheadend.", level="WARNING")
    return ok


def _restart_kodi_if_idle(timeout_s=20) -> bool:
    """
    Reinicia Kodi SOLO si está idle.
    """
    try:
        if not utils.kodi_is_idle():
            log_utils.write_log("[pvr] Kodi no está idle; NO reinicio (rescate).", level="INFO")
            return False
    except Exception as e:
        log_utils.write_log("[pvr] No pude comprobar idle; NO reinicio Kodi: {}".format(e), level="WARNING")
        return False

    for cmd in (["systemctl", "restart", "kodi"], ["systemctl", "restart", "kodi.service"]):
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=int(timeout_s), check=True)
            log_utils.write_log("[pvr] Kodi reiniciado (rescate PVR).", level="WARNING")
            return True
        except Exception:
            pass

    try:
        subprocess.run(["killall", "-TERM", "kodi.bin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=5, check=True)
        log_utils.write_log("[pvr] Kodi TERM enviado (rescate PVR).", level="WARNING")
        return True
    except Exception as e:
        log_utils.write_log("[pvr] No pude reiniciar Kodi: {}".format(e), level="ERROR")
        return False


# ------------------------------
# JSON-RPC helpers
# ------------------------------
def _addon_set_enabled(addon_id: str, enabled: bool) -> bool:
    try:
        return bool(jsonrpc_utils.set_addon_enabled(addon_id, enabled))
    except Exception as e:
        log_utils.write_log("[pvr] JSON-RPC set_addon_enabled({},{}): {}".format(addon_id, enabled, e), level="WARNING")
        return False


def _get_addon_enabled(addon_id: str):
    try:
        res = jsonrpc_utils.jsonrpc_call("Addons.GetAddonDetails", {
            "addonid": addon_id,
            "properties": ["enabled"]
        })
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
        if v is None:
            time.sleep(0.5)
            continue
        if bool(v) == bool(want_enabled):
            return True
        time.sleep(0.5)
    return False


def _pvr_get_properties():
    """
    READY fiable: PVR.GetProperties.available.
    """
    ok, res, err = jsonrpc_utils.jsonrpc_try(
        "PVR.GetProperties",
        params={"properties": ["available", "scanning", "recording"]},
        retries=0,
        quiet_codes={-32100, -32602},
        log_level="DEBUG",
    )
    if ok and isinstance(res, dict):
        return res
    return None


def _pvr_has_any_channels_via_conditions() -> bool:
    """
    Segundo candado: condiciones internas (cuando xbmc está disponible).
    """
    try:
        if xbmc:
            return bool(
                xbmc.getCondVisibility("Pvr.HasTVChannels") or
                xbmc.getCondVisibility("Pvr.HasRadioChannels")
            )
    except Exception:
        pass
    return False


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
            cur.execute("""
                SELECT COUNT(1)
                FROM channelgroups
                WHERE
                    idGroup <> 1
                    AND TRIM(IFNULL(sName,'')) <> ''
            """)
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
    """
    Tercer candado (fallback): TVxx.db con canales.
    OJO: si wal/shm presentes, devuelve 0/0 => NO concluyas.
    """
    try:
        tvdb = _pick_tv_db_path()
        if not tvdb:
            return False
        n_ch, _ = _db_count_channels_groups(tvdb)
        return (n_ch > 0)
    except Exception:
        return False


def _wait_pvr_ready(timeout_s=120, poll_s=1.5, grace_s=20) -> bool:
    """
    READY robusto (sin PVR.GetChannelGroups):
      1) PVR.GetProperties.available=True
      2) y (Pvr.HasTVChannels or Pvr.HasRadioChannels) si xbmc disponible
      3) fallback: DB tiene canales
    """
    t0 = time.time()
    warned = False

    while (time.time() - t0) < float(timeout_s):
        props = _pvr_get_properties()

        if props and bool(props.get("available")):
            if _pvr_has_any_channels_via_conditions():
                return True
            if _pvr_has_any_channels_via_db():
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
    """
    Rescate: toggle con esperas grandes.
    """
    _addon_set_enabled(addon_id, False)
    time.sleep(2.5)
    _addon_set_enabled(addon_id, True)
    time.sleep(2.5)


# ------------------------------
# Port helpers
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

def _tvh_read_http_auth_from_config() -> tuple[str, str]:
    """
    Intenta sacar user/pass del config del addon tvheadend.
    Si no hay (típico en tu caso), devuelve ("","").
    """
    cfg_path = "/storage/.kodi/userdata/addon_data/service.tvheadend43/config"
    try:
        if not os.path.exists(cfg_path):
            return "", ""

        with open(cfg_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read().strip()

        if raw.endswith(";"):
            raw = raw[:-1].rstrip()

        data = json.loads(raw) if raw else {}
        if not isinstance(data, dict):
            return "", ""

        # Claves posibles (varían según builds/configs)
        for ukey, pkey in (
            ("http_username", "http_password"),
            ("http_user", "http_pass"),
            ("username", "password"),
            ("user", "pass"),
        ):
            u = (data.get(ukey) or "").strip()
            p = (data.get(pkey) or "").strip()
            if u:
                return u, p

        return "", ""
    except Exception:
        return "", ""

def _tvh_api_get(api_path: str, query: dict | None = None, timeout_s: int = 8) -> tuple[bool, int, str]:
    """
    GET a Tvheadend JSON API:
      - Primero sin auth
      - Si responde 401, reintenta con basic-auth si hay credenciales en config
    Devuelve: (ok, http_status, body_text)
    """
    host = "localhost"
    port = TVH_HTTP_PORT

    q = urllib.parse.urlencode(query or {})
    url = "http://{}:{}/api/{}{}".format(host, int(port), api_path.lstrip("/"), ("?" + q) if q else "")

    def _do_req(user="", pwd=""):
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "masQelec/1.0 (+Kodi)")
        if user:
            token = base64.b64encode(("{}:{}".format(user, pwd)).encode("utf-8")).decode("ascii")
            req.add_header("Authorization", "Basic {}".format(token))
        try:
            with urllib.request.urlopen(req, timeout=float(timeout_s)) as r:
                code = getattr(r, "status", 200) or 200
                body = (r.read() or b"").decode("utf-8", "replace")
                return True, int(code), body
        except urllib.error.HTTPError as e:
            try:
                body = (e.read() or b"").decode("utf-8", "replace")
            except Exception:
                body = ""
            return False, int(getattr(e, "code", 0) or 0), body
        except Exception as e:
            return False, 0, str(e)

    # 1) intento sin auth
    ok, code, body = _do_req("", "")
    if ok:
        return True, code, body

    # 2) si pide auth, reintento
    if code == 401:
        u, p = _tvh_read_http_auth_from_config()
        if u:
            ok2, code2, body2 = _do_req(u, p)
            return bool(ok2), int(code2), body2

    return False, code, body


def force_tvh_epg_reload(internal: bool = True, ota: bool = False) -> bool:
    """
    Fuerza recarga EPG en Tvheadend:
      - internal=True  => epggrab/internal/rerun
      - ota=True       => epggrab/ota/trigger
    """
    any_ok = False

    if internal:
        ok, code, body = _tvh_api_get("epggrab/internal/rerun", {"rerun": 1}, timeout_s=10)
        if ok:
            log_utils.write_log("[pvr] EPG: internal rerun OK (HTTP {}).".format(code), level="INFO")
            any_ok = True
        else:
            log_utils.write_log("[pvr] EPG: internal rerun FAIL (HTTP {}): {}".format(code, (body or "")[:200]), level="WARNING")

    if ota:
        ok, code, body = _tvh_api_get("epggrab/ota/trigger", {"trigger": 1}, timeout_s=10)
        if ok:
            log_utils.write_log("[pvr] EPG: OTA trigger OK (HTTP {}).".format(code), level="INFO")
            any_ok = True
        else:
            log_utils.write_log("[pvr] EPG: OTA trigger FAIL (HTTP {}): {}".format(code, (body or "")[:200]), level="WARNING")

    return any_ok

# ------------------------------
# Net helper
# ------------------------------
def _download_to(path_dst: str, url: str, retries: int = 2, timeout: int = 20) -> bool:
    return bool(utils.download_atomic(path_dst, url, retries=retries, timeout=timeout))


# ------------------------------
# DB logging
# ------------------------------
def _log_pvr_db_stats(prefix: str = "[pvr]") -> None:
    try:
        tvdb = _pick_tv_db_path()
        if not tvdb:
            log_utils.write_log("{} DB stats: TVxx.db no encontrada".format(prefix), level="INFO")
            return

        n_ch, n_gr = _db_count_channels_groups(tvdb)
        if n_ch == 0 and n_gr == 0:
            if os.path.exists(tvdb + "-wal") or os.path.exists(tvdb + "-shm"):
                log_utils.write_log("{} DB stats: DB en uso (wal/shm), omito conteo".format(prefix), level="INFO")
            else:
                log_utils.write_log("{} DB stats: no pude leer conteo (0/0)".format(prefix), level="INFO")
            return

        log_utils.write_log("{} DB stats: canales={} grupos={}".format(prefix, n_ch, n_gr), level="INFO")
    except Exception:
        pass


# ------------------------------
# Normalización / parse playlist
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

    def _add_logo(nkey, logo):
        logos_by_name.setdefault(nkey, set()).add(logo)

    try:
        with open(m3u_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.startswith("#EXTINF"):
                    continue

                m = _RE_TVG_NAME.search(line)
                if not m:
                    continue
                name_raw = (m.group(2) or "").strip()
                if not name_raw:
                    continue
                nkey = _norm_key(name_raw)
                if not nkey:
                    continue
                wanted_names.add(nkey)

                m = _RE_TVG_LOGO.search(line)
                logo = (m.group(2) if m else "") or ""
                logo = _norm_url(logo)
                if logo:
                    _add_logo(nkey, logo)

                m = _RE_GRP_TITLE.search(line)
                grp = (m.group(2) if m else "") or ""
                grp = (grp or "").strip()
                if grp:
                    wanted_groups.add(_norm_key(grp))
    except Exception:
        pass

    return wanted_names, logos_by_name, wanted_groups


# ------------------------------
# Protección de grupos internos / localizados (FIX)
# ------------------------------
_PROTECTED_GROUP_NAMES_RAW = {
    "all channels", "all radio",
    "todos los canales", "todos los radios", "todas las radios",
    "toda la radio", "todo radio",
    "tots els canals", "tots els canals de tv", "tota la ràdio",
    "tous les canaux", "toutes les chaînes", "toutes les radios",
}

# pre-normalizado para no recalcular en cada llamada
_PROTECTED_GROUP_NAMES_NORM = {_norm_key(x) for x in _PROTECTED_GROUP_NAMES_RAW if _norm_key(x)}

def _is_internal_or_protected_group(gid: int, gname: str, iClientId, sClientName: str) -> bool:
    """
    NO tocar si:
      - idGroup == 1
      - grupos internos Kodi: iClientId < 0 o sClientName vacío (tu caso real "Todos los canales")
      - nombres protegidos (varios idiomas)
    """
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
        # ante duda: protege
        return True

    if not (sClientName or "").strip():
        return True

    nk = _norm_key(gname)
    if nk and nk in _PROTECTED_GROUP_NAMES_NORM:
        return True

    return False


# ------------------------------
# Plan reconcile (FIX grupos internos)
# ------------------------------
def _plan_reconcile(tv_db_path: str, playlist_m3u_path: str, update_icons: bool) -> tuple[bool, int, int, int]:
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

        for _, ch_name, ch_icon in rows:
            name_key = _norm_key(ch_name)
            icon = _norm_url(ch_icon)
            if not name_key:
                continue
            if name_key not in wanted_names:
                del_channels += 1
                continue
            if update_icons:
                logos = logos_by_name.get(name_key) or set()
                if len(logos) == 1:
                    pl_icon = next(iter(logos))
                    if pl_icon and pl_icon != icon:
                        upd_icons += 1

        del_groups = 0
        if "channelgroups" in tables:
            # FIX: detectar y proteger grupos internos Kodi
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
                if not gname_key:
                    continue
                if gname_key not in wanted_groups_norm:
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
# Reconcile real (FIX grupos internos)
# ------------------------------
def reconcile_kodi_channels_and_groups_with_playlist(
    tv_db_path: str,
    playlist_m3u_path: str = "/storage/.user/playlist.m3u",
    update_icons: bool = True,
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
            # FIX: detectar y proteger grupos internos Kodi
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
                if not gname_key:
                    continue
                if gname_key not in wanted_groups_norm:
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
# tv_grab_file
# ------------------------------
def update_tv_grab_file() -> bool:
    local_path = "/storage/.kodi/addons/service.tvheadend43/bin/tv_grab_file"
    remote_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/pvr/tv_grab_file"
    remote_tmp = local_path + ".remote"

    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if not _download_to(remote_tmp, remote_url):
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
# Playlist updater
# ------------------------------
def _tvh_tag_norm(s):
    # comparación exacta (texto completo), case-insensitive y espacios normalizados
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
    """
    Sincroniza TVH_TAGDIR con los group-title del M3U (comparación exacta: casefold + espacios).
      - Crea tags que falten
      - Borra tags no-internal que no estén en la lista IPTV
    Recomendado ejecutarlo con Tvheadend parado (soft reset) para evitar lecturas concurrentes.
    Devuelve: (ok:bool, created:int, deleted:int)
    """
    tagdir = TVH_TAGDIR

    if not os.path.isdir(tagdir):
        log_utils.write_log("[pvr][tags] tagdir no existe: {}".format(tagdir), level="WARNING")
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

            entries.append({
                "file": path,
                "norm": _tvh_tag_norm(name),
                "internal": internal,
            })
    except Exception as e:
        log_utils.write_log("[pvr][tags] error leyendo tagdir: {}".format(e), level="ERROR")
        return False, 0, 0

    # Crear los que falten (nombre EXACTO del M3U)
    existing_norm = set(e["norm"] for e in entries if not e["internal"])
    to_create = [g for g in sorted(desired_raw) if _tvh_tag_norm(g) not in existing_norm]

    # Borrar los que sobran (solo no-internal)
    to_delete = [e for e in entries if (not e["internal"]) and (e["norm"] not in desired_norm)]

    created = 0
    deleted = 0

    # Borrado
    for e in to_delete:
        try:
            os.remove(e["file"])
            deleted += 1
        except Exception:
            pass

    # Creación
    for g in to_create:
        try:
            tag_id = uuid.uuid4().hex
            path = os.path.join(tagdir, tag_id)
            data = {
                "enabled": True,
                "index": 0,
                "name": g,  # EXACTO
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

    log_utils.write_log("[pvr][tags] sync OK: created={} deleted={} (groups={})".format(created, deleted, len(desired_raw)), level="INFO")
    return True, created, deleted
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
                log_utils.write_log("Excepción ignorada en update_pvr: {}".format(e), "DEBUG")

            remote = "masqelec"
            remote_path = "masqelec/user/{}".format(eth0)
            tmp_dir = "/tmp"
            tmp_file = os.path.join(tmp_dir, eth0)

            ok = False
            try:
                ok = rclone_utils.copy_remote_to_tmp_then_move(remote, remote_path, tmp_dir)
            except Exception as e:
                log_utils.write_log("[update_playlist] rclone copy failed: {}\n{}".format(e, traceback.format_exc()), level="ERROR")
                return False

            if not ok or not os.path.exists(tmp_file):
                log_utils.write_log("[update_playlist] user remoto no encontrado: {}:{}".format(remote, remote_path), level="INFO")
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

            log_utils.write_log("[update_playlist] user recuperado del remoto ({})".format(eth0))
            return True

        except Exception as e:
            log_utils.write_log("[update_playlist] Error recuperando user remoto: {}\n{}".format(e, traceback.format_exc()), level="ERROR")
            return False

    try:
        os.makedirs(user_dir, exist_ok=True)

        if not os.path.exists(user_file):
            if not _try_fetch_user_from_remote():
                log_utils.write_log("Archivo /storage/.user/user no disponible.", level="ERROR")
                _log_pvr_db_stats(prefix="[pvr]")
                return False, False

        # plantilla en memoria
        remote_tpl = None
        last_bytes = 0
        last_firstline = ""

        for url in BASE_URLS:
            try:
                with utils._net_open(url, timeout=20) as r:
                    data = r.read()
                last_bytes = len(data or b"")

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
            except Exception as e:
                log_utils.write_log("[update_playlist] Descarga plantilla falló para {}: {}".format(url, e), level="DEBUG")
                continue

            candidate_norm = _norm_newlines(txt)
            try:
                last_firstline = (candidate_norm.strip().splitlines()[0] if candidate_norm.strip() else "")[:200]
            except Exception:
                last_firstline = ""

            low = (candidate_norm.lstrip()[:160] or "").lower()
            if last_bytes < 64 or low.startswith("<!doctype html") or low.startswith("<html") or "rate limit" in low or "access denied" in low:
                continue

            if "USER_CODE" in candidate_norm and "PASS_CODE" in candidate_norm:
                remote_tpl = candidate_norm
                break

        if not remote_tpl:
            log_utils.write_log(
                "Plantilla playlist remota inválida. URLs probadas={}; última bytes={}; primera='{}'".format(
                    len(BASE_URLS), last_bytes, last_firstline
                ),
                level="ERROR",
            )
            _log_pvr_db_stats(prefix="[pvr]")
            return False, False

        # creds
        content = _read_text(user_file)
        if not _has_valid_creds(content):
            log_utils.write_log("USER_CODE o PASS_CODE inválidos en /storage/.user/user", level="ERROR")
            _log_pvr_db_stats(prefix="[pvr]")
            return False, False

        user_code, pass_code = _extract_creds(content)
        tpl = _norm_newlines(remote_tpl)
        new_playlist = tpl.replace("USER_CODE", user_code).replace("PASS_CODE", pass_code)
        new_hash = _sha256_text(new_playlist)

        local_hash = None
        if os.path.exists(playlist_file):
            try:
                local_hash = _sha256_text(_read_text(playlist_file))
            except Exception:
                local_hash = None

        playlist_changed = (local_hash is None) or (local_hash != new_hash)

        # DB mismatch aunque hash igual
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

        # --- SOFT RESET ---
        if playlist_changed:
            _popup("PVR", "Actualizando lista IPTV…", ms=3500)
            log_utils.write_log("[pvr] Playlist CAMBIA.", level="INFO")
        else:
            _popup("PVR", "Sincronizando PVR…", ms=3500)
            log_utils.write_log("[pvr] Playlist igual, pero DB NO coincide (soft reset). plan={}".format(plan), level="INFO")

        # 1) disable pvr.hts + wait real
        _addon_set_enabled(PVR_ADDON_ID, False)
        _wait_addon_enabled(PVR_ADDON_ID, want_enabled=False, timeout_s=12)
        time.sleep(1.5)

        # 2) stop tvheadend + wait real
        _stop_tvheadend()
        time.sleep(1.0)

        # 3) write playlist (solo si cambió)
        if playlist_changed:
            tmp = playlist_file + ".part"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(new_playlist)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, playlist_file)
            log_utils.write_log("[pvr] Playlist instalada/actualizada.", level="INFO")

        # 4) reconcile DB
        tvdb = _pick_tv_db_path()
        if tvdb:
            reconcile_kodi_channels_and_groups_with_playlist(
                tv_db_path=tvdb,
                playlist_m3u_path=playlist_file,
                update_icons=False,
            )
        else:
            log_utils.write_log("[pvr] No se encontró TVxx.db para reconciliar.", level="WARNING")

        
        # 4.5) Sync tags de Tvheadend (solo en soft reset / con tvheadend parado)
        try:
            ok_tags, n_created, n_deleted = sync_tvh_channel_tags_from_playlist(playlist_file)
            if ok_tags:
                log_utils.write_log("[pvr][tags] sincronizados: +{} -{}".format(n_created, n_deleted), level="INFO")
            else:
                log_utils.write_log("[pvr][tags] sync NO aplicada.", level="WARNING")
        except Exception as e:
            log_utils.write_log("[pvr][tags] sync error: {}".format(e), level="WARNING")

# 5) start tvheadend + wait ports
        _start_tvheadend()
        if not _wait_tvheadend_ready(timeout_s=70):
            log_utils.write_log("[pvr] Tvheadend no listo; NO habilito pvr.hts (evito 0%).", level="WARNING")
            _log_pvr_db_stats(prefix="[pvr]")
            return True, True
        # 5.5) Forzar recarga EPG en Tvheadend (antes de que Kodi reconecte al backend)
        force_tvh_epg_reload(internal=True, ota=False)
        time.sleep(1.0)

        # 6) enable pvr.hts (primera activación)
        _addon_set_enabled(PVR_ADDON_ID, True)

        # Espera READY robusta (sin channelgroupid)
        pvr_ok = _wait_pvr_ready(timeout_s=120, poll_s=1.5, grace_s=20)

        if not pvr_ok:
            try:
                _log_pvr_db_stats(prefix="[pvr]")
            except Exception:
                pass

            log_utils.write_log("[pvr] PVR no quedó READY tras enable. Aplico toggle rescate.", level="WARNING")
            _toggle_pvr_addon_rescue(PVR_ADDON_ID)

            if not _wait_pvr_ready(timeout_s=70, poll_s=1.5, grace_s=15):
                log_utils.write_log("[pvr] PVR sigue sin READY tras rescate 1. Aplico rescate fuerte (tvh restart + enable).", level="WARNING")
                _restart_tvheadend()
                if _wait_tvheadend_ready(timeout_s=70):
                    _addon_set_enabled(PVR_ADDON_ID, False)
                    time.sleep(2.0)
                    _addon_set_enabled(PVR_ADDON_ID, True)
                    _wait_pvr_ready(timeout_s=90, poll_s=1.5, grace_s=20)

        # 7) Toggle rescate adicional (si aún no está ready)
        if not _wait_pvr_ready(timeout_s=25, poll_s=1.5, grace_s=8):
            log_utils.write_log("[pvr] PVR no ready tras enable/rescates. Aplico rescate adicional (toggle)…", level="WARNING")

            _addon_set_enabled(PVR_ADDON_ID, False)
            _wait_addon_enabled(PVR_ADDON_ID, want_enabled=False, timeout_s=12)
            time.sleep(2.0)

            _addon_set_enabled(PVR_ADDON_ID, True)
            _wait_addon_enabled(PVR_ADDON_ID, want_enabled=True, timeout_s=12)
            time.sleep(2.0)

            if _wait_pvr_ready(timeout_s=45, poll_s=1.5, grace_s=10):
                log_utils.write_log("[pvr] PVR recuperado tras toggle rescate.", level="WARNING")
                _log_pvr_db_stats(prefix="[pvr]")
                return True, True

            # 8) Último recurso: reinicio Kodi (solo idle)
            if ENABLE_KODI_RESTART_FALLBACK:
                log_utils.write_log("[pvr] PVR sigue sin ready. Intento reinicio Kodi (idle).", level="ERROR")
                _restart_kodi_if_idle(timeout_s=25)

        _log_pvr_db_stats(prefix="[pvr]")
        return True, True

    except Exception as e:
        log_utils.write_log("Error en update_playlist: {}\n{}".format(e, traceback.format_exc()), level="ERROR")
        _log_pvr_db_stats(prefix="[pvr]")
        return False, False


# ------------------------------
# Punto de entrada general (mínimo)
# ------------------------------
def update_pvr():
    start_ts = time.time()

    try:
        update_tv_grab_file()
    except Exception as e:
        log_utils.write_log("[pvr] update_tv_grab_file error: {}".format(e), level="WARNING")

    try:
        ensure_tvh_http_user_agent()
    except Exception as e:
        log_utils.write_log("[pvr] ensure_tvh_http_user_agent error: {}".format(e), level="WARNING")
    try:
        dt = time.time() - start_ts
        log_utils.write_log("[pvr] update_pvr terminado en {:.1f}s".format(dt), level="INFO")
    except Exception:
        pass

