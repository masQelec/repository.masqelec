# -*- coding: utf-8 -*-

import os
import glob
import base64
import hashlib
import uuid
import io
import re
import subprocess
import gzip
import time
import shutil
import zipfile
import datetime
import traceback
import json
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

from lib import log_utils

DEFAULT_MASTER_ETH0_MACS = "066230512670"
AUTH_KEYS_FILE = "/storage/.ssh/authorized_keys"

# ==========================
# CONFIG GITHUB
# ==========================
OWNER  = "masQelec"
REPO   = "cloud.masQelec".lower().replace("masqelec", "cloud.masqelec")  # no-op defensivo, respeta tu valor final
REPO   = "cloud.masqelec"
BRANCH = "master"

SRC_DIR = "/storage/.catalog"
ZIP_NAME = "catalog.zip"
VER_NAME = "catalog.version"

FILES = [
    (ZIP_NAME, f"catalog/{ZIP_NAME}"),
    (VER_NAME, f"catalog/{VER_NAME}"),
]

API_BASE = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"

# User-Agents
UA_HTTP = "KodiELEC-HTTP/1.0"

GITHUB_TOKEN_B64 = "WVYvGj1NOE1ERGdjNg00T0wwM2hnaHBfOFQ0OWlsT0tMWEtDQTRvYQ=="
GITHUB_FEISTEL_ROUNDS = 8

# =========================================================
# Telegram: credenciales CIFRADAS (base64) para GitHub
# =========================================================
TG_TOKEN_B64  = "Ki4GdzwnKWgcRCxVTwdpbClTGVVBPGs4NTk5NzIxOTMxOkFBR2R0eENrZEZsbw=="
TG_CHATID = "952051424"   # <-- quitado "=" (era muy probable bug)
TG_FEISTEL_ROUNDS = 8

# ---- Config red (ajusta si quieres) ----
NET_TIMEOUT = 30           # segundos
NET_RETRIES = 2            # reintentos adicionales en error de red
RETRY_BACKOFF = 2          # segundos entre reintentos

# Identidad del addon centralizada (usada por otros módulos)
ADDON_ID = "service.cloud.masqelec"

try:
    addon = xbmcaddon.Addon(id=ADDON_ID)
except Exception:
    addon = xbmcaddon.Addon()

try:
    ADDON_NAME = addon.getAddonInfo("name")
except Exception:
    ADDON_NAME = ADDON_ID

# UA_HTTP final (incluye nombre real si existe)
UA_HTTP = f"{ADDON_NAME}/1.0 (+Kodi)"

# ==========================
# CATÁLOGO REMOTO (RAW): SOLO version y comparación por UTC
# ==========================
RAW_CATALOG_BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/catalog"

_UTC_RE = re.compile(r"\butc=([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)\b")
_HASH64_RE = re.compile(r"\b([0-9a-fA-F]{64})\b")

def _parse_utc_epoch(ver_text: str):
    """
    Extrae utc=...Z y devuelve epoch en UTC real.
    IMPORTANTE: NO usar time.mktime() (interpreta hora local).
    """
    if not ver_text:
        return None
    m = _UTC_RE.search(ver_text)
    if not m:
        return None
    try:
        dt = datetime.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None

def _version_hash64(ver_text: str) -> str:
    if not ver_text:
        return ""
    tok = ver_text.split()[0].strip()
    if re.fullmatch(r"[0-9a-fA-F]{64}", tok):
        return tok.lower()
    m = _HASH64_RE.search(ver_text)
    return (m.group(1).lower() if m else "")

def _http_get_text_simple(url: str, timeout: float = 10.0) -> str:
    """
    GET texto soportando gzip/deflate (algunos servidores contestan comprimido).
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA_HTTP,
            "Accept-Encoding": "gzip, deflate",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        enc = (r.headers.get("Content-Encoding") or "").lower()
        if "gzip" in enc:
            try:
                data = gzip.decompress(data)
            except Exception:
                pass
        return data.decode("utf-8", "replace").strip()

def _read_local_catalog_version_text() -> str:
    """
    Lee catalog.version local del addon_data (no del SRC_DIR).
    Esto es lo que tu cliente ya persistía.
    """
    local_path = os.path.join(
        xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}"),
        VER_NAME
    )
    try:
        with open(local_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except Exception:
        return ""

def _write_local_catalog_version_text_atomic(ver_text: str):
    """
    Guardado atómico de catalog.version en addon_data para el gate cliente.
    (Esto no sustituye al sync real, solo mantiene estado.)
    """
    local_dir = xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}")
    local_path = os.path.join(local_dir, VER_NAME)
    try:
        os.makedirs(local_dir, exist_ok=True)
        tmp = local_path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write((ver_text or "").rstrip("\n") + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, local_path)
    except Exception as e:
        log_utils.write_log(f"[catalog] No se pudo guardar catalog.version local (atómico): {e}", "WARNING")

def get_remote_catalog_version_text(timeout: float = 10.0) -> str:
    """
    Lee SOLO catalog.version remoto (RAW).
    """
    url = f"{RAW_CATALOG_BASE}/{VER_NAME}"
    try:
        return _http_get_text_simple(url, timeout=timeout)
    except Exception as e:
        log_utils.write_log(f"[catalog] Error leyendo remoto {VER_NAME}: {e}", "WARNING")
        return ""

def remote_catalog_is_newer(remote_ver: str, local_ver: str) -> bool:
    """
    Decide si remoto es más nuevo:
      1) comparar utc epoch (UTC real)
      2) fallback: hash64 distinto
      3) fallback final: texto distinto
    """
    r_utc = _parse_utc_epoch(remote_ver)
    l_utc = _parse_utc_epoch(local_ver)

    if r_utc is not None and l_utc is not None:
        return r_utc > l_utc
    if r_utc is not None and l_utc is None:
        return True
    if l_utc is not None and r_utc is None:
        return False

    rh = _version_hash64(remote_ver)
    lh = _version_hash64(local_ver)
    if rh and lh:
        return rh != lh

    return (remote_ver or "").strip() != (local_ver or "").strip()

# ---------- Utilidades de estado/condiciones ----------
def _has_network() -> bool:
    try:
        return xbmc.getCondVisibility("System.HasNetwork")
    except Exception:
        return True


def _has_internet(timeout: float = 3.0) -> bool:
    try:
        urllib.request.urlopen("https://www.google.com/generate_204", timeout=timeout)
        return True
    except Exception:
        return False


def is_online() -> bool:
    if not _has_network():
        return False
    return _has_internet()

# ==========================================================
# Rol del dispositivo (MASTER / CLIENTE)
# ==========================================================

_DEVICE_ROLE = None  # cache interno

def get_device_eth0_mac() -> str:
    """Devuelve MAC de eth0 en formato 12 hex (sin ':')."""
    try:
        info = get_net_info()
        mac = (info.get("eth0") or "").strip().lower()
        return mac if mac and mac != "unknown_mac" else ""
    except Exception:
        return ""

def _normalize_mac12(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower().replace(":", "").replace("-", "")
    return s if re.fullmatch(r"[0-9a-f]{12}", s) else ""

def _parse_master_macs(macs_cfg: str) -> set[str]:
    parts = re.split(r"[,\s]+", (macs_cfg or "").strip())
    out = set()
    for p in parts:
        m = _normalize_mac12(p)
        if m:
            out.add(m)
    return out

def is_master_device() -> bool:
    eth0 = _normalize_mac12(get_device_eth0_mac())
    if not eth0:
        return False

    master_set = _parse_master_macs(DEFAULT_MASTER_ETH0_MACS)
    if not master_set:
        log_utils.write_log("[role] DEFAULT_MASTER_ETH0_MACS vacío o inválido", "WARNING")
        return False

    return eth0 in master_set

def get_device_role():
    """
    Devuelve 'MASTER' o 'CLIENT'.
    Cacheado tras la primera evaluación.
    """
    global _DEVICE_ROLE

    if _DEVICE_ROLE is not None:
        return _DEVICE_ROLE

    try:
        is_master = bool(is_master_device())
    except Exception:
        is_master = False

    _DEVICE_ROLE = "MASTER" if is_master else "CLIENT"

    try:
        log_utils.write_log(
            f"Rol dispositivo detectado: {_DEVICE_ROLE}",
            "INFO"
        )
    except Exception as e:
        log_utils.write_log(f"safe_rmtree falló para {path}: {e}", "DEBUG")

    return _DEVICE_ROLE


def is_master():
    return get_device_role() == "MASTER"


def is_client():
    return get_device_role() == "CLIENT"

# ==============================
# CATÁLOGO: detectar cambios en clientes + gate con red
# ==============================
def get_addon_data_dir() -> str:
    return xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}")
# ---------------------------------------------------------
# Estado persistente (state.json) — NO sobreescribir claves
# ---------------------------------------------------------
def _state_path() -> str:
    return os.path.join(get_addon_data_dir(), "state.json")

def load_state() -> dict:
    """Carga state.json del addon_data. Si no existe o está corrupto, devuelve dict vacío."""
    path = _state_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def save_state(state: dict) -> bool:
    """Guarda state.json de forma atómica."""
    try:
        state_dir = get_addon_data_dir()
        os.makedirs(state_dir, exist_ok=True)
        tmp = os.path.join(state_dir, "state.json.tmp")
        final = os.path.join(state_dir, "state.json")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, final)
        return True
    except Exception:
        return False

def update_state(patch: dict) -> dict:
    """Merge superficial (dict.update) y guarda; devuelve el estado final."""
    st = load_state()
    try:
        if isinstance(patch, dict):
            st.update(patch)
    except Exception:
        pass
    save_state(st)
    return st

# ---------------------------------------------------------
# Circuit breaker simple por tarea (persistente)
# ---------------------------------------------------------
def cb_should_run(task: str) -> bool:
    st = load_state()
    cb = st.get("circuit_breaker") if isinstance(st.get("circuit_breaker"), dict) else {}
    t = cb.get(task) if isinstance(cb.get(task), dict) else {}
    next_ts = float(t.get("next_ts", 0) or 0)
    return time.time() >= next_ts

def cb_note_success(task: str) -> None:
    st = load_state()
    cb = st.get("circuit_breaker") if isinstance(st.get("circuit_breaker"), dict) else {}
    cb[task] = {"fails": 0, "next_ts": 0}
    st["circuit_breaker"] = cb
    save_state(st)

def cb_note_failure(task: str, fail_threshold: int = 3, cooldown_sec: int = 3600) -> dict:
    """Incrementa fallos y, si supera umbral, activa cooldown. Devuelve el bloque del task."""
    now = time.time()
    st = load_state()
    cb = st.get("circuit_breaker") if isinstance(st.get("circuit_breaker"), dict) else {}
    t = cb.get(task) if isinstance(cb.get(task), dict) else {}
    fails = int(t.get("fails", 0) or 0) + 1
    next_ts = float(t.get("next_ts", 0) or 0)

    if fails >= max(1, int(fail_threshold)):
        next_ts = max(next_ts, now + max(60, int(cooldown_sec)))
    cb[task] = {"fails": fails, "next_ts": next_ts}
    st["circuit_breaker"] = cb
    save_state(st)
    return cb[task]

def cb_should_log_cooldown(task: str, every_sec: int = 600) -> bool:
    """Evita spam: si está en cooldown, loguea como mucho cada X segundos."""
    now = time.time()
    st = load_state()
    meta = st.get("cb_meta") if isinstance(st.get("cb_meta"), dict) else {}
    last = float(meta.get(task, 0) or 0)
    if (now - last) >= max(60, int(every_sec)):
        meta[task] = now
        st["cb_meta"] = meta
        save_state(st)
        return True
    return False


def _read_bytes(path: str):
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def _get_catalog_fingerprint():
    """
    Fingerprint estable del catálogo local.
    - Preferente: hash del contenido de catalog.version
    - Fallback: mtime+tamaño de catalog.zip
    """
    ver_path = os.path.join(SRC_DIR, VER_NAME)
    zip_path = os.path.join(SRC_DIR, ZIP_NAME)

    b = _read_bytes(ver_path)
    if b:
        return "ver:" + _sha256_bytes(b)

    try:
        st = os.stat(zip_path)
        return f"zip:{int(st.st_mtime)}:{int(st.st_size)}"
    except Exception:
        return None

def catalog_changed_client() -> bool:
    """
    True si el catálogo LOCAL cambió desde la última vez en ESTE cliente.
    (Esto NO detecta remoto; lo dejo por si quieres usarlo como “anti spam” local.)
    """
    fp = _get_catalog_fingerprint()
    if not fp:
        return False

    state_dir = get_addon_data_dir()
    state_path = os.path.join(state_dir, "state.json")

    try:
        os.makedirs(state_dir, exist_ok=True)
    except Exception:
        return False

    last_fp = None
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
            last_fp = state.get("catalog_fp")
    except Exception:
        last_fp = None

    changed = (last_fp != fp)

    try:
        state = load_state()
        state["catalog_fp"] = fp
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception as e:
        log_utils.write_log(f"safe_rmtree falló para {path}: {e}", "DEBUG")

    return changed

def should_run_client_catalog_maintenance() -> bool:
    """
    Gate correcto para clientes (lo que te faltaba):

      - Solo en CLIENT
      - Solo si hay red/internet
      - Solo si catalog.version REMOTO es más nuevo (por utc=...Z en UTC real)

    Nota: NO depende del fingerprint local (eso te bloqueaba el update remoto).
    """
    if not is_client():
        return False
    if not is_online():
        return False

    remote_ver = get_remote_catalog_version_text(timeout=10.0)
    if not remote_ver:
        return False

    local_ver = _read_local_catalog_version_text()

    newer = remote_catalog_is_newer(remote_ver, local_ver)
    if newer:
        # Guardamos YA el remote_ver como “último visto” para que no repita el gate
        # si luego falla el sync por cualquier motivo (evita loops).
        _write_local_catalog_version_text_atomic(remote_ver)
    return newer

# ----------------- Estado de Kodi / inactividad -----------------

def kodi_is_idle(min_idle_secs: int = 0) -> bool:
    """
    Heurística PERMISIVA diseñada para:
      - CleanLibrary
      - UpdateLibrary / escaneos
      - Actualización de canales/EPG PVR
    """
    try:
        if any([
            xbmc.getCondVisibility("Library.IsCleaningVideo"),
            xbmc.getCondVisibility("Library.IsScanningVideo"),
            xbmc.getCondVisibility("Library.IsCleaningMusic"),
            xbmc.getCondVisibility("Library.IsScanningMusic"),
        ]):
            return False

        if any([
            xbmc.getCondVisibility("Player.Playing"),
            xbmc.getCondVisibility("Player.Paused"),
            xbmc.getCondVisibility("Player.HasGame"),
        ]):
            return False

        if any([
            xbmc.getCondVisibility("Pvr.IsRecording"),
            xbmc.getCondVisibility("Pvr.IsRecordingTV"),
            xbmc.getCondVisibility("Pvr.IsRecordingRadio"),
        ]):
            return False

        return True

    except Exception as e:
        try:
            log_utils.write_log(f"[idle] Error comprobando estado: {e}", level="WARNING")
        except Exception:
            pass
        return True

# ----------------- Helpers internos -----------------

def restart_kodi_with_popup(delay_ms: int = 5000):
    """
    Muestra popup INFO con sonido avisando del reinicio y reinicia Kodi tras delay_ms.
    Centralizado para que cualquier módulo lo use.

    Texto NO se cambia (pedido del usuario).
    """
    heading = "Información"
    message = "Kodi se va a reiniciar, espere unos momentos…"

    try:
        xbmcgui.Dialog().notification(
            heading,
            message,
            xbmcgui.NOTIFICATION_INFO,
            delay_ms,
            True,  # sound
        )
    except Exception:
        try:
            log_utils.notify(message, xbmcgui.NOTIFICATION_INFO)
        except Exception:
            pass

    try:
        xbmc.sleep(int(delay_ms))
    except Exception:
        xbmc.sleep(5000)

    try:
        log_utils.write_log("[kodi] Reiniciando Kodi: systemctl restart kodi", "INFO")
        subprocess.run(["systemctl", "restart", "kodi"], check=False)
    except Exception as e:
        log_utils.write_log(f"[kodi] No se pudo reiniciar Kodi: {e}", "ERROR")

def _net_open(url: str, timeout: int = NET_TIMEOUT):
    """Abre URL con User-Agent y timeout, con reintentos simples."""
    req = urllib.request.Request(url, headers={"User-Agent": UA_HTTP, "Accept-Encoding": "gzip, deflate"})
    last_err = None
    for attempt in range(NET_RETRIES + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            last_err = e
            log_utils.write_log(
                f"Intento {attempt+1}/{NET_RETRIES+1} falló para {url}: {getattr(e, 'reason', e)}",
                "ERROR"
            )
            time.sleep(RETRY_BACKOFF)
    raise last_err

def download_atomic(url: str, dst_path: str, retries: int = NET_RETRIES, timeout: int = NET_TIMEOUT,
                   tmp_suffix: str = ".part", chmod: int | None = None) -> bool:
    """
    Descarga una URL a dst_path de forma atómica:
    - descarga a dst_path + tmp_suffix
    - fsync
    - os.replace()
    - chmod opcional
    Devuelve True si se aplicó correctamente.
    """
    tmp_path = dst_path + tmp_suffix
    last_err = None

    # Reintentos con backoff (mismo estilo que _net_open)
    for attempt in range(retries + 1):
        try:
            with _net_open(url, timeout=timeout) as r, open(tmp_path, "wb") as f:
                shutil.copyfileobj(r, f, length=1024 * 1024)
                try:
                    f.flush()
                    os.fsync(f.fileno())
                except Exception:
                    # Si fsync falla, no abortamos: el replace sigue siendo atómico.
                    pass

            if chmod is not None:
                try:
                    os.chmod(tmp_path, chmod)
                except Exception as e:
                    log_utils.write_log(f"chmod({oct(chmod)}) falló para {tmp_path}: {e}", "WARNING")

            os.replace(tmp_path, dst_path)
            return True

        except Exception as e:
            last_err = e
            log_utils.write_log(
                f"Descarga atómica falló ({attempt+1}/{retries+1}) para {url} -> {dst_path}: {e}",
                "ERROR"
            )
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            time.sleep(RETRY_BACKOFF)

    log_utils.write_log(f"Descarga atómica agotó reintentos para {url}: {last_err}", "ERROR")
    return False


def run_cmd(cmd: list[str], timeout: int = 10) -> tuple[int, str, str]:
    """
    Ejecuta comando con timeout.
    Devuelve (returncode, stdout, stderr) como texto (utf-8 con replacement).
    """
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False
        )
        out = (p.stdout or b"").decode("utf-8", "replace")
        err = (p.stderr or b"").decode("utf-8", "replace")
        return p.returncode, out, err
    except subprocess.TimeoutExpired:
        return 124, "", f"Timeout expirado ({timeout}s)"
    except Exception as e:
        return 1, "", str(e)


def _read_maybe_gzip(response) -> bytes:
    """Lee bytes desde response y descomprime si viene gz."""
    data = response.read()
    enc = response.headers.get("Content-Encoding", "")
    if "gzip" in enc.lower() or response.geturl().endswith(".gz"):
        try:
            return gzip.decompress(data)
        except Exception:
            return data
    return data

def _find_extracted_addon_dir(temp_dir_os: str, expected_id: str) -> str:
    """
    Encuentra en el directorio temporal la carpeta que contiene el addon con id=expected_id.
    Considera casos donde el ZIP viene como addon_id/ o addon_id-version/.
    """
    direct = os.path.join(temp_dir_os, expected_id)
    if os.path.isdir(direct):
        return direct

    for entry in os.listdir(temp_dir_os):
        path = os.path.join(temp_dir_os, entry)
        if os.path.isdir(path):
            addon_xml = os.path.join(path, "addon.xml")
            if os.path.isfile(addon_xml):
                try:
                    tree = ET.parse(addon_xml)
                    root = tree.getroot()
                    if root.tag == "addon" and root.get("id") == expected_id:
                        return path
                except Exception:
                    continue

    return ""

def _safe_rmtree(path: str):
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        log_utils.write_log(f"safe_rmtree falló para {path}: {e}", "DEBUG")

# ----------------- API pública -----------------

def get_addon_download_url(addon_id: str, addons_xml_url: str):
    """
    Obtiene la URL de descarga de un addon a partir de un addons.xml (o addons.xml.gz) remoto.
    Asume estructura estándar: base/{addon_id}/{addon_id}-{version}.zip
    """
    log_utils.write_log(f"Buscando URL de descarga para '{addon_id}' en '{addons_xml_url}'")
    try:
        resp = _net_open(addons_xml_url)
        xml_content = _read_maybe_gzip(resp)
        root = ET.fromstring(xml_content)

        addon_elem = root.find(f"./addon[@id='{addon_id}']")
        if addon_elem is None:
            log_utils.write_log(f"Addon '{addon_id}' no encontrado en addons.xml", "ERROR")
            return None

        version = addon_elem.get("version")
        if not version:
            log_utils.write_log(f"No se detectó versión para '{addon_id}'", "ERROR")
            return None

        base_url = addons_xml_url.rsplit("/", 1)[0]
        download_url = f"{base_url}/{addon_id}/{addon_id}-{version}.zip"
        log_utils.write_log(f"URL de descarga construida: {download_url}")
        return download_url

    except urllib.error.URLError as e:
        log_utils.write_log(f"Error de red accediendo a {addons_xml_url}: {getattr(e, 'reason', e)}", "ERROR")
        return None
    except ET.ParseError as e:
        log_utils.write_log(f"Error parseando addons.xml: {e}", "ERROR")
        return None
    except Exception as e:
        log_utils.write_log(f"Error inesperado en get_addon_download_url: {e}", "ERROR")
        return None

def install_addon_silent(addon_id: str, addon_url: str) -> bool:
    """
    Descarga un addon en memoria, lo extrae a temp y lo mueve a la carpeta de addons.
    Respeta cancelación con xbmc.Monitor(); asegura limpieza de temp.
    """
    monitor = xbmc.Monitor()
    log_utils.write_log(f"Instalación silenciosa de {addon_id} desde {addon_url}")

    temp_dir_kodi = "special://temp/addons_temp/"
    temp_dir_os = xbmcvfs.translatePath(temp_dir_kodi)
    dest_dir_os = xbmcvfs.translatePath("special://home/addons/")

    try:
        if not os.path.exists(temp_dir_os):
            os.makedirs(temp_dir_os, exist_ok=True)

        if monitor.abortRequested():
            log_utils.write_log("Abort solicitado antes de descargar.")
            return False

        with _net_open(addon_url) as response:
            data = response.read()
            if not data or len(data) < 100:
                log_utils.write_log("Descarga vacía o demasiado pequeña; abortando.", "ERROR")
                return False
            zip_content = io.BytesIO(data)

        if monitor.abortRequested():
            log_utils.write_log("Abort solicitado tras descarga.")
            return False

        with zipfile.ZipFile(zip_content, "r") as zf:
            zf.extractall(temp_dir_os)
        log_utils.write_log(f"ZIP extraído en: {temp_dir_os}")

        addon_extracted_path = _find_extracted_addon_dir(temp_dir_os, addon_id)
        if not addon_extracted_path:
            log_utils.write_log("No se encontró carpeta del addon extraído con addon.xml válido.", "ERROR")
            return False

        addon_final_path = os.path.join(dest_dir_os, addon_id)

        if os.path.exists(addon_final_path):
            log_utils.write_log(f"Eliminando versión previa en: {addon_final_path}")
            _safe_rmtree(addon_final_path)

        if monitor.abortRequested():
            log_utils.write_log("Abort solicitado antes de mover.")
            return False

        shutil.move(addon_extracted_path, addon_final_path)
        log_utils.write_log(f"{addon_id} instalado en {addon_final_path}")

        try:
            xbmc.executebuiltin("UpdateLocalAddons")
            xbmc.executebuiltin("UpdateAddonRepos")
        except Exception:
            pass

        return True

    except urllib.error.URLError as e:
        log_utils.write_log(f"Error de red al descargar {addon_id}: {getattr(e, 'reason', e)}", "ERROR")
        return False
    except zipfile.BadZipFile:
        log_utils.write_log("El archivo descargado no es un ZIP válido.", "ERROR")
        return False
    except Exception:
        log_utils.write_log(f"Error inesperado instalando {addon_id}.\n{traceback.format_exc()}", "ERROR")
        return False
    finally:
        _safe_rmtree(temp_dir_os)
        log_utils.write_log(f"Temporal limpiado: {temp_dir_os}")

def install_addon_from_repo(addon_id: str, addons_xml_url: str) -> bool:
    addon_url = get_addon_download_url(addon_id, addons_xml_url)
    if not addon_url:
        log_utils.write_log(f"No se pudo resolver la URL de {addon_id}.", "ERROR")
        return False
    return install_addon_silent(addon_id, addon_url)

# ----------------- Zerotier -----------------

def get_zerotier_ids(ZT_NETWORKS_DIR="/opt/var/lib/zerotier-one/networks.d") -> dict:
    try:
        if not os.path.isdir(ZT_NETWORKS_DIR):
            return {}

        confs = sorted(glob.glob(os.path.join(ZT_NETWORKS_DIR, "*.conf")))
        confs = [p for p in confs if not p.endswith(".local.conf")]
        if not confs:
            return {}

        best = max(confs, key=lambda p: os.path.getmtime(p))

        node_name = None
        nwid = None
        id_device = None

        with open(best, "rb") as f:
            chunk = f.read(8192)

        for raw in chunk.splitlines():
            if b"=" not in raw:
                continue
            if raw.startswith(b"C=") or raw.startswith(b"COO="):
                break
            line = raw.decode("utf-8", errors="ignore").strip()

            if line.startswith("n="):
                node_name = line.split("=", 1)[1].strip()
            elif line.startswith("nwid="):
                nwid = line.split("=", 1)[1].strip()
            elif line.startswith("id="):
                id_device = line.split("=", 1)[1].strip()

        if not nwid:
            nwid_from_name = os.path.basename(best).split(".")[0]
            if len(nwid_from_name) >= 16:
                nwid = nwid_from_name

        return {"n": node_name, "nwid": nwid, "id": id_device}
    except Exception:
        return {}

def get_net_info() -> dict:
    def _read_mac(interface: str) -> str:
        mac_path = f"/sys/class/net/{interface}/address"
        if not os.path.exists(mac_path):
            log_utils.write_log(f"[net] La interfaz '{interface}' no existe.", level="WARNING")
            return "unknown_mac"
        try:
            with open(mac_path, "r") as f:
                mac = f.read().strip().lower().replace(":", "").replace("-", "")
                if len(mac) == 12 and all(c in "0123456789abcdef" for c in mac):
                    return mac
                else:
                    log_utils.write_log(f"[net] MAC inválida en {interface}: {mac}", level="WARNING")
                    return "unknown_mac"
        except Exception as e:
            log_utils.write_log(f"[net] Error leyendo MAC de {interface}: {e}", level="WARNING")
            return "unknown_mac"

    return {"eth0": _read_mac("eth0"), "wlan0": _read_mac("wlan0")}

# ==============================
# CIFRADO FEISTEL (idéntico a tu script)
# ==============================
def feistel_round(left: bytes, right: bytes, key: bytes):
    f_result = bytearray(b ^ key[i % len(key)] for i, b in enumerate(right))
    return right, bytearray(l ^ fr for l, fr in zip(left, f_result))

def decrypt(data_b64: str, key: bytes, rounds: int = 8):
    try:
        if not key:
            raise ValueError("La clave de descifrado está vacía")
        decoded_data = base64.b64decode(data_b64)

        left, right = decoded_data[:len(decoded_data)//2], decoded_data[len(decoded_data)//2:]
        for _ in range(rounds):
            right, left = feistel_round(right, left, key)

        return left + right
    except Exception as e:
        log_utils.write_log(f"Error al desencriptar los datos: {e}\n{traceback.format_exc()}", "ERROR")
        return None

def get_key_from_authorized_keys(filename="/storage/.ssh/authorized_keys"):
    if not os.path.exists(filename):
        log_utils.write_log(f"El archivo '{filename}' no existe. Abortando.", "ERROR")
        raise FileNotFoundError(f"El archivo '{filename}' no existe.")
    with open(filename, "rb") as file:
        key = file.read()
        if not key:
            raise ValueError("La clave leída está vacía")
        return key

# ==========================
# Telegram helpers
# ==========================

def _tg_get_plain_credentials() -> tuple[str, str]:
    key = get_key_from_authorized_keys(AUTH_KEYS_FILE)
    token_bytes = decrypt(TG_TOKEN_B64, key, rounds=TG_FEISTEL_ROUNDS)
    if not token_bytes:
        return "", ""

    token = token_bytes.decode("utf-8", errors="ignore").strip()
    chat_id = TG_CHATID
    return token, chat_id

def _multipart_formdata(fields: dict, files: dict):
    boundary = "----KodiELECFormBoundary" + uuid.uuid4().hex
    body = bytearray()

    def add_line(s: str):
        body.extend(s.encode("utf-8"))
        body.extend(b"\r\n")

    for k, v in (fields or {}).items():
        add_line(f"--{boundary}")
        add_line(f'Content-Disposition: form-data; name="{k}"')
        add_line("")
        add_line(str(v))

    for fieldname, fmeta in (files or {}).items():
        filename = fmeta.get("filename", "file.bin")
        content = fmeta.get("content", b"")
        ctype = fmeta.get("content_type", "application/octet-stream")

        add_line(f"--{boundary}")
        add_line(f'Content-Disposition: form-data; name="{fieldname}"; filename="{filename}"')
        add_line(f"Content-Type: {ctype}")
        add_line("")
        body.extend(content)
        body.extend(b"\r\n")

    add_line(f"--{boundary}--")
    return f"multipart/form-data; boundary={boundary}", bytes(body)

def telegram_send_message_encrypted(text: str, timeout: float = 10.0) -> bool:
    try:
        bot_token, chat_id = _tg_get_plain_credentials()
        if not bot_token or not chat_id:
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": "true",
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= getattr(r, "status", 0) < 300
    except Exception:
        return False

def telegram_send_document_encrypted(file_path: str, filename: str, caption: str = "", timeout: float = 25.0) -> bool:
    try:
        if not os.path.exists(file_path):
            return False

        bot_token, chat_id = _tg_get_plain_credentials()
        if not bot_token or not chat_id:
            return False

        with open(file_path, "rb") as f:
            data_bytes = f.read()

        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

        fields = {"chat_id": str(chat_id)}
        if caption:
            fields["caption"] = str(caption)[:900]

        files = {
            "document": {
                "filename": filename,
                "content": data_bytes,
                "content_type": "text/plain",
            }
        }

        ctype, body = _multipart_formdata(fields, files)
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", ctype)

        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= getattr(r, "status", 0) < 300

    except Exception as e:
        try:
            log_utils.write_log(f"Telegram: fallo enviando documento: {e}\n{traceback.format_exc()}", "ERROR")
        except Exception:
            pass
        return False

def _extract_warn_error_lines(log_path: str, max_lines: int = 30) -> list[str]:
    try:
        if not os.path.exists(log_path):
            return []
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        picked = []
        for line in reversed(lines):
            if "[ERROR]" in line or "[WARNING]" in line:
                picked.append(line.strip())
                if len(picked) >= max_lines:
                    break
        picked.reverse()
        return picked
    except Exception:
        return []

def telegram_send_log_with_summary_if_problem(
    log_path: str,
    filename: str,
    network_info_text: str,
    max_problem_lines: int = 30,
) -> bool:
    """Si el log contiene WARNING/ERROR, envía:
    1) Mensaje con resumen (red + métricas + cooldown + líneas problema)
    2) Log adjunto como documento
    """
    try:
        if not os.path.exists(log_path):
            return False

        problem_lines = _extract_warn_error_lines(log_path, max_lines=max_problem_lines)
        if not problem_lines:
            return False

        now = time.time()

        # -------- Resumen métricas / cooldown (útil para soporte) --------
        summary = ""
        try:
            tasks = ["cloud_storage", "updater", "catalog", "pvr", "library", "clean"]
            st = load_state() or {}
            cb = st.get("circuit_breaker") if isinstance(st.get("circuit_breaker"), dict) else {}

            metrics_parts = []
            for t in tasks:
                d = metrics_get(t) or {}
                if not d:
                    continue
                res = (d.get("last_result") or "?").upper()
                dur = d.get("duration_sec")
                ts = d.get("ts")
                part = f"{t}={res}"
                if isinstance(dur, (int, float)):
                    part += f" {dur:.1f}s"
                if isinstance(ts, (int, float)):
                    age = max(0, int(now - float(ts)))
                    part += f" ({age}s ago)"
                metrics_parts.append(part)

            cb_parts = []
            for t in tasks:
                tcb = cb.get(t) if isinstance(cb.get(t), dict) else {}
                fails = int(tcb.get("fails", 0) or 0)
                next_ts = float(tcb.get("next_ts", 0) or 0)
                if fails > 0 and next_ts > now:
                    mins = int((next_ts - now) / 60)
                    cb_parts.append(f"{t}:cooldown {mins}m (fails={fails})")

            lines = []
            if metrics_parts:
                lines.append("Tareas: " + " | ".join(metrics_parts))
            if cb_parts:
                lines.append("Cooldown: " + " | ".join(cb_parts))
            if lines:
                summary = "\n".join(lines).strip() + "\n\n"
        except Exception:
            summary = ""

        header = "KodiELEC: log con WARNING/ERROR\n\n"
        net = (network_info_text.strip() + "\n\n") if network_info_text else ""

        prefix = header + net + summary
        body = "\n".join(problem_lines)

        msg = prefix + body

        # Telegram suele limitar mensajes ~4096; dejamos margen para UTF-8.
        max_len = 3800
        if len(msg) > max_len:
            allowed = max_len - len(prefix)
            if allowed < 200:
                # Si el prefijo es demasiado grande, prioriza el contenido del problema.
                prefix2 = header + net
                allowed = max_len - len(prefix2)
                body2 = body[-max(0, allowed):]
                msg = prefix2 + body2
            else:
                body2 = body[-max(0, allowed):]
                msg = prefix + body2

        ok_msg = telegram_send_message_encrypted(msg)
        caption = "Log adjunto (WARNING/ERROR)"
        ok_doc = telegram_send_document_encrypted(log_path, filename, caption=caption)

        return bool(ok_msg and ok_doc)
    except Exception:
        return False


# ==========================
# GitHub API
# ==========================

def _gh_get_plain_token() -> str:
    """
    Devuelve el token de GitHub en claro, descifrando GITHUB_TOKEN_B64
    con la clave obtenida de authorized_keys (mismo modelo que Telegram).
    """
    try:
        if not GITHUB_TOKEN_B64:
            return ""

        key = get_key_from_authorized_keys(AUTH_KEYS_FILE)
        token_bytes = decrypt(GITHUB_TOKEN_B64, key, rounds=GITHUB_FEISTEL_ROUNDS)
        if not token_bytes:
            return ""
        return token_bytes.decode("utf-8", errors="ignore").strip()
    except Exception as e:
        try:
            log_utils.write_log(f"[github] Error descifrando token: {e}", "ERROR")
        except Exception:
            pass
        return ""

def _req(method, url, token, payload=None):
    headers = {
        "User-Agent": UA_HTTP,
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        log_utils.write_log(f"Error de red GitHub: {e}", "ERROR")
        return None, None

def _get_remote_sha(token, dst_path):
    path_enc = urllib.parse.quote(dst_path, safe="/")
    url = f"{API_BASE}/{path_enc}?ref={BRANCH}"

    status, body = _req("GET", url, token)
    if status is None:
        log_utils.write_log(f"GET sha sin respuesta (red) {dst_path}", "ERROR")
        return None

    if status == 200:
        try:
            return json.loads(body).get("sha")
        except ValueError:
            log_utils.write_log(f"JSON inválido obteniendo SHA de {dst_path}", "ERROR")
            return None

    if status == 404:
        return None

    log_utils.write_log(f"GET sha falló ({status}) {dst_path}: {body}", "ERROR")
    return None

def _upload_file(token, src_path, dst_path):
    if not os.path.exists(src_path):
        log_utils.write_log(f"No existe {src_path}", "ERROR")
        return False

    size = os.path.getsize(src_path)
    if size <= 0:
        log_utils.write_log(f"Archivo vacío: {src_path}", "ERROR")
        return False

    if size > 75 * 1024 * 1024:
        log_utils.write_log(f"Archivo demasiado grande: {src_path}", "ERROR")
        return False

    raw = open(src_path, "rb").read()
    b64 = base64.b64encode(raw).decode("ascii")

    if len(b64) > 100 * 1024 * 1024:
        log_utils.write_log(f"Payload base64 excesivo: {dst_path}", "ERROR")
        return False

    sha_local = hashlib.sha256(raw).hexdigest()[:12]
    msg = f"Update {dst_path} ({sha_local})"

    path_enc = urllib.parse.quote(dst_path, safe="/")
    url = f"{API_BASE}/{path_enc}"

    payload = {
        "message": msg,
        "content": b64,
        "branch": BRANCH,
    }

    sha_remote = _get_remote_sha(token, dst_path)
    if sha_remote:
        payload["sha"] = sha_remote

    status, body = _req("PUT", url, token, payload)
    if status is None:
        log_utils.write_log(f"PUT sin respuesta (red) {dst_path}", "ERROR")
        return False

    if status in (200, 201):
        return True

    if status in (409, 422):
        log_utils.write_log(f"Conflicto SHA en {dst_path}, reintentando", "WARNING")
        payload["sha"] = _get_remote_sha(token, dst_path)
        status, body = _req("PUT", url, token, payload)
        if status in (200, 201):
            return True

    log_utils.write_log(f"PUT falló {dst_path} ({status}): {body}", "ERROR")
    return False

def load_catalog_github():
    token = _gh_get_plain_token()
    if not token:
        log_utils.write_log("Token GitHub no disponible, abortando subida", "ERROR")
        return

    # Subir primero ZIP y luego VERSION (evita que clientes vean “version nueva” sin zip disponible)
    ordered = sorted(FILES, key=lambda x: 0 if x[0] == "catalog.zip" else 1)

    for fname, dst in ordered:
        src = os.path.join(SRC_DIR, fname)
        log_utils.write_log(f"Subiendo {src} -> {dst}", "INFO")
        if not _upload_file(token, src, dst):
            log_utils.write_log(f"Fallo subiendo {dst}", "ERROR")
        else:
            log_utils.write_log(f"{dst} subido correctamente", "INFO")



# ==============================
# MÉTRICAS (persistentes en state.json)
# ==============================
def metrics_note(task: str, ok: bool, duration_sec: float, extra: dict = None) -> None:
    """Guarda métricas simples por tarea en state.json sin hacer ruido."""
    try:
        now = int(time.time())
        data = {
            "last_run_ts": now,
            "last_duration_sec": float(duration_sec) if duration_sec is not None else None,
            "last_ok_ts": now if ok else None,
            "last_result": "OK" if ok else "FAIL",
        }
        if extra:
            data.update(extra)
        update_state({"metrics": {task: data}}, merge=True)
    except Exception:
        # nunca debe romper el flujo
        return

def metrics_get(task: str) -> dict:
    try:
        st = load_state() or {}
        return (st.get("metrics") or {}).get(task) or {}
    except Exception:
        return {}
