# -*- coding: utf-8 -*-
"""
service.py — Flujo por fases + control de hilos (Kodi 20/21 Omega compatible)

Fase 1 (bloqueante y SIEMPRE): start_cloud_storage()
Fase 2 (secuencial): auto_update, update_library, update_pvr (uno tras otro)
Tareas periódicas (ajustables por settings):
  - UpdateLibrary (silencioso) cada X horas si inactivo, con red y montajes OK.
  - CleanLibrary  (silencioso) cada Y horas si inactivo, con red y montajes OK.

Parada limpia: xbmc.Monitor.waitForAbort()
"""
import os
import sys
import threading
import traceback
import json
import time

import xbmc
import xbmcgui

from lib import log_utils
from lib import jsonrpc_utils
from lib import rclone_utils
from lib.cloud_storage import start_cloud_storage
from lib.updater import update_system
from lib.update_library import update_library
from lib.update_pvr import update_pvr, update_playlist
from lib import utils

# ---- Config constante ----
SLEEP_INTERVAL_SECS = 10
RETRY_BACKOFF_SECS = 30
CHECK_TICK_SECS    = 60  # cada cuánto evaluar condiciones

REQUIRED_MOUNTS = [
    "/storage/videos/1",
    "/storage/videos/2",
    "/storage/tvshows/1",
    "/storage/tvshows/2",
]

LOG_FILE = log_utils.LOG_FILE

# ---- Estado global de planificación ----
_last_update_ts   = 0.0
_last_clean_ts    = 0.0
_last_pvrcheck_ts = None

_LIBRARY_LOCK = threading.Lock()
_PVR_LOCK     = threading.Lock()

class StoppableWorker(threading.Thread):
    """Hilo que ejecuta una función y respeta abortRequested()."""
    def __init__(self, name, target, monitor, interval=0, run_once=False):
        super().__init__(name=name, daemon=True)
        self._target_fn = target
        self._monitor   = monitor
        self._interval  = max(0, int(interval))
        self._run_once  = bool(run_once)

    def run(self):
        log(f"Worker '{self.name}' start (run_once={self._run_once}, interval={self._interval}s)")
        try:
            while not self._monitor.abortRequested():
                try:
                    self._target_fn()
                except Exception:
                    log(f"Worker '{self.name}' error:\n{traceback.format_exc()}", "ERROR")
                    if self._monitor.waitForAbort(RETRY_BACKOFF_SECS):
                        break

                if self._run_once:
                    break

                if self._interval > 0 and self._monitor.waitForAbort(self._interval):
                    break
        finally:
            log(f"Worker '{self.name}' exit")

def log(msg, level="INFO"):
    log_utils.write_log(msg, level)

def view_log():
    """Abre el log en un cuadro de texto."""
    if not os.path.exists(LOG_FILE):
        xbmcgui.Dialog().ok(utils.ADDON_NAME, "No hay log disponible")
        return
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            contenido = f.read()[-4000:]
        xbmcgui.Dialog().textviewer(utils.addon.getLocalizedString(30007), contenido)
    except Exception as e:
        xbmcgui.Dialog().ok(utils.ADDON_NAME, f"Error al abrir log: {e}")

# ---------- Lectura segura de ajustes ----------
def _get_bool_setting(key: str, default: bool) -> bool:
    fn = getattr(utils, "get_bool", None)
    if callable(fn):
        try:
            return bool(fn(key, default))
        except Exception:
            pass
    try:
        import xbmcaddon
        addon = xbmcaddon.Addon()
        return addon.getSettingBool(key)
    except Exception:
        return default

def _get_int_setting(key: str, default: int) -> int:
    fn = getattr(utils, "get_int", None)
    if callable(fn):
        try:
            return int(fn(key, default))
        except Exception:
            pass
    try:
        import xbmcaddon
        addon = xbmcaddon.Addon()
        val = addon.getSetting(key)
        return int(val) if str(val).isdigit() else default
    except Exception:
        return default

def _hours_to_secs(h: int) -> int:
    try:
        h = max(0, int(h))
    except Exception:
        h = 0
    return h * 3600

def _load_pvr_prefs() -> dict:
    return {
        "update_enabled":      _get_bool_setting("pvr_update_enabled", True),
        "update_period_hours": max(0, _get_int_setting("pvr_update_period_hours", 12)),
    }

def _load_library_prefs() -> dict:
    """
    Ajustes relevantes (con defaults):
      - update_library (bool maestro)
      - lib_update_on_start (bool)
      - lib_update_period_hours (0–24)
      - lib_clean_enabled (bool)
      - lib_clean_period_hours (0–24)
    """
    return {
        "update_enabled":       _get_bool_setting("update_library", True),
        "update_on_start":      _get_bool_setting("lib_update_on_start", True),
        "update_period_hours":  max(0, _get_int_setting("lib_update_period_hours", 6)),
        "clean_enabled":        _get_bool_setting("lib_clean_enabled", True),
        "clean_period_hours":   max(0, _get_int_setting("lib_clean_period_hours", 12)),
    }

# ---------- Utilidades de estado/condiciones ----------
def _has_network() -> bool:
    try:
        return xbmc.getCondVisibility("System.HasNetwork")
    except Exception:
        return True

def _is_idle() -> bool:
    """Inactivo = no limpiando, no escaneando, no reproduciendo."""
    try:
        cleaning = xbmc.getCondVisibility("Library.IsCleaningVideo")
        scanning = xbmc.getCondVisibility("Library.IsScanningVideo")
        playing  = xbmc.getCondVisibility("Player.HasMedia")
        return not (cleaning or scanning or playing)
    except Exception:
        return True

def _mounts_ready() -> bool:
    """Comprobación ligera de montajes rclone: directorios existen y son accesibles."""
    try:
        for p in REQUIRED_MOUNTS:
            if not os.path.isdir(p):
                log(f"Mount no disponible (no existe): {p}", "WARNING")
                return False
            try:
                os.listdir(p)
            except Exception:
                log(f"Mount no accesible: {p}", "WARNING")
                return False
        return True
    except Exception:
        return False

# ------------- Tareas silenciosas JSON-RPC -------------
def clean_library_silent():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "VideoLibrary.Clean",
        "params": {"showdialogs": False}
    }
    xbmc.executeJSONRPC(json.dumps(payload))
    mon = xbmc.Monitor()
    while xbmc.getCondVisibility("Library.IsCleaningVideo") and not mon.abortRequested():
        mon.waitForAbort(1)

def update_library_silent():
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "VideoLibrary.Scan",
        "params": {"showdialogs": False}
    }
    xbmc.executeJSONRPC(json.dumps(payload))
    mon = xbmc.Monitor()
    while xbmc.getCondVisibility("Library.IsScanningVideo") and not mon.abortRequested():
        mon.waitForAbort(1)

# ---------- Subida de log post-workers ----------
def _upload_log(nwid: str, address: str, eth0: str, wlan0: str):
    """
    Sube el LOG vía rclone a log:masqelec/log/<nwid>_<address>_<eth0>_<wlan0>_service.log
    Solo si se detectan errores o advertencias en el log.
    """
    try:
        error_or_warning_found = False
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if '[ERROR]' in line or '[WARNING]' in line:
                        error_or_warning_found = True
                        break

        if not error_or_warning_found:
            log("No errors/warnings found in log. Skipping log upload.")
            #return

        destination_filename = f"{nwid}_{address}_{eth0}_{wlan0}_service.log"
        log(f"Uploading log to remote: log:masqelec/log/{destination_filename}")
        ok = rclone_utils.copy_to_tmp_then_move_remote(
            LOG_FILE, "log", f"masqelec/log/{destination_filename}"
        )
        if ok:
            log("Log uploaded successfully via rclone.")
        else:
            log("Failed to upload log via rclone.", "ERROR")

    except Exception:
        log(f"upload_log failed:\n{traceback.format_exc()}", "ERROR")

# ------------- FASES -------------
def _phase1_cloud_storage_blocking(monitor: xbmc.Monitor):
    """Fase 1: Cloud storage SIEMPRE y BLOQUEANTE."""
    log("Phase 1: cloud_storage (start_cloud_storage) -> start")
    try:
        start_cloud_storage()
    except Exception:
        log(f"cloud_storage failed:\n{traceback.format_exc()}", "ERROR")
    log("Phase 1: cloud_storage -> done")
    if monitor.abortRequested():
        raise SystemExit

# ---------- WRAPPERS ONE-SHOT (FASE 2) ----------
def _update_system_wrapper():
    try:
        enabled = _get_bool_setting("auto_update", True)
        if enabled:
            log("Auto update enabled -> update_system()")
            update_system()
        else:
            log("Auto update disabled")
    except Exception:
        log(f"update_system failed:\n{traceback.format_exc()}", "ERROR")

def _update_library_wrapper():
    """One-shot al arranque (usa flujo avanzado de update_library.py) controlado por ajustes."""
    global _last_update_ts
    try:
        prefs = _load_library_prefs()
        if prefs["update_enabled"] and prefs["update_on_start"]:
            log("Updating library at startup via update_library()")
            with _LIBRARY_LOCK:
                update_library()
                _last_update_ts = time.time()
        else:
            log("Startup library update is disabled by settings")
    except Exception:
        log(f"update_library failed:\n{traceback.format_exc()}", "ERROR")

def _update_pvr_wrapper():
    try:
        enabled = _get_bool_setting("update_pvr", True)
        if enabled:
            log("Updating PVR via update_pvr()")
            update_pvr()
        else:
            log("PVR update disabled")
    except Exception:
        log(f"update_pvr failed:\n{traceback.format_exc()}", "ERROR")

# ---------- Workers periódicos ----------
def _periodic_pvr_worker():
    """Refresca la playlist periódicamente si Kodi está inactivo, hay red y montajes OK."""
    global _last_pvrcheck_ts
    prefs = _load_pvr_prefs()
    if not prefs["update_enabled"]:
        return

    period_secs = _hours_to_secs(prefs["update_period_hours"])
    if period_secs <= 0:
        return  # 0 = nunca

    now = time.time()

    # Inicializa al primer tick para retrasar la 1ª ejecución
    if _last_pvrcheck_ts is None:
        _last_pvrcheck_ts = now
        return

    if (now - _last_pvrcheck_ts) < period_secs:
        return

    if not _has_network():
        log("Skip PVR check: sin red.", "WARNING"); return
    if not _is_idle():
        log("Skip PVR check: Kodi no está inactivo.", "INFO"); return
    if not _mounts_ready():
        log("Skip PVR check: montajes rclone no listos.", "WARNING"); return

    if _PVR_LOCK.acquire(blocking=False):
        try:
            log("Periodic channel PVR check -> start")
            # Sólo refrescamos la lista de canales
            update_playlist()
            _last_pvrcheck_ts = time.time()
            log("Periodic channel PVR check -> done")
        except Exception:
            log(f"Periodic channel PVR check error:\n{traceback.format_exc()}", "ERROR")
        finally:
            _PVR_LOCK.release()
    else:
        log("Skip channel PVR check: ya hay una operación PVR en curso.", "INFO")

def _periodic_update_worker():
    """Lanza UpdateLibrary silencioso si toca y se cumplen condiciones."""
    global _last_update_ts
    prefs = _load_library_prefs()
    if not prefs["update_enabled"]:
        return

    period_secs = _hours_to_secs(prefs["update_period_hours"])
    if period_secs <= 0:
        return  # 0 = nunca

    now = time.time()
    if (now - _last_update_ts) < period_secs:
        return

    if not _has_network():
        log("Skip UpdateLibrary: sin red.", "WARNING"); return
    if not _is_idle():
        log("Skip UpdateLibrary: Kodi no está inactivo (escaneando/limpiando/reproduciendo).", "INFO"); return
    if not _mounts_ready():
        log("Skip UpdateLibrary: montajes rclone no listos.", "WARNING"); return

    if _LIBRARY_LOCK.acquire(blocking=False):
        try:
            log("Periodic UpdateLibrary (silencioso) -> start")
            update_library_silent()
            _last_update_ts = time.time()
            log("Periodic UpdateLibrary -> done")
        except Exception:
            log(f"Periodic UpdateLibrary error:\n{traceback.format_exc()}", "ERROR")
        finally:
            _LIBRARY_LOCK.release()
    else:
        log("Skip UpdateLibrary: ya hay una operación de biblioteca en curso.", "INFO")

def _periodic_clean_worker():
    """Lanza CleanLibrary silencioso si toca y se cumplen condiciones."""
    global _last_clean_ts
    prefs = _load_library_prefs()
    if not prefs["clean_enabled"]:
        return

    period_secs = _hours_to_secs(prefs["clean_period_hours"])
    if period_secs <= 0:
        return  # 0 = nunca

    now = time.time()
    if (now - _last_clean_ts) < period_secs:
        return

    if not _has_network():
        log("Skip CleanLibrary: sin red.", "WARNING"); return
    if not _is_idle():
        log("Skip CleanLibrary: Kodi no está inactivo (escaneando/limpiando/reproduciendo).", "INFO"); return
    if not _mounts_ready():
        log("Skip CleanLibrary: montajes rclone no listos.", "WARNING"); return

    if _LIBRARY_LOCK.acquire(blocking=False):
        try:
            log("Periodic CleanLibrary (silencioso) -> start")
            clean_library_silent()
            _last_clean_ts = time.time()
            log("Periodic CleanLibrary -> done")
        except Exception:
            log(f"Periodic CleanLibrary error:\n{traceback.format_exc()}", "ERROR")
        finally:
            _LIBRARY_LOCK.release()
    else:
        log("Skip CleanLibrary: ya hay una operación de biblioteca en curso.", "INFO")

def _nz(x, idx=None, key=None):
    """devuelve x[key] si dict, x[idx] si secuencia, o None."""
    if isinstance(x, dict):
        return x.get(key) if key else None
    if isinstance(x, (list, tuple)):
        if idx is not None and len(x) > idx:
            return x[idx]
    return None
    
# ------------- MAIN SERVICE -------------
def run_service():
    monitor = xbmc.Monitor()

    if len(sys.argv) > 1 and sys.argv[1] == "viewlog":
        view_log()
        sys.exit()

    log("Service starting")
    
    name  = "0"
    major = "0"
    minor = "0"
    kodi_version = jsonrpc_utils.get_kodi_version()
    if kodi_version:
        name_candidate  = _nz(kodi_version, idx=0, key="name")
        major_candidate = _nz(kodi_version, idx=1, key="major")
        minor_candidate = _nz(kodi_version, idx=1, key="minor")
        if name_candidate:  name  = name_candidate
        if major_candidate: major = major_candidate
        if minor_candidate: minor = minor_candidate
        log(f"Version detectada: {name} {major}.{minor}")


    # valores por defecto
    nwid   = "no_networks"
    address= "unknown_member"
    eth0   = "unknown_mac"
    wlan0  = "unknown_mac"

    zerotier_ids = utils.get_zerotier_ids()
    if zerotier_ids:
        nwid_candidate    = _nz(zerotier_ids, idx=0, key="nwid")
        address_candidate = _nz(zerotier_ids, idx=1, key="address")
        if nwid_candidate:    nwid    = nwid_candidate
        if address_candidate: address = address_candidate
        log(f"Red Zerotier detectada: NetworkID: {nwid} Member: {address}")

    net_info = utils.get_net_info()
    if net_info:
        # admite dict {"eth0": "...", "wlan0": "..."} o tupla/lista ("xx:xx:..", "yy:yy:..")
        eth0_candidate  = _nz(net_info, idx=0, key="eth0")
        wlan0_candidate = _nz(net_info, idx=1, key="wlan0")
        if eth0_candidate:  eth0  = eth0_candidate
        if wlan0_candidate: wlan0 = wlan0_candidate
        log(f"Mac Address: Eth: {eth0} Wlan: {wlan0}")

    # FASE 1: Cloud storage bloqueante
    _phase1_cloud_storage_blocking(monitor)

    # FASE 2: One-shots SECUECIALES (no empieza el siguiente hasta que termine el anterior)
    oneshot_sequence = [
        ("library_update_once", _update_library_wrapper),
        #("pvr_update_once",     _update_pvr_wrapper),
        ("auto_update_once",    _update_system_wrapper),
    ]

    log("Operaciones de arranque completadas (ejecución secuencial de one-shots)")

    for name, fn in oneshot_sequence:
        if monitor.abortRequested():
            log(f"Abort solicitado antes de ejecutar '{name}'")
            break
        try:
            log(f"Iniciando one-shot: {name}")
            t = StoppableWorker(name, fn, monitor, run_once=True)
            t.start()
            # Espera respetuosa con abort:
            while t.is_alive() and not monitor.abortRequested():
                monitor.waitForAbort(0.25)
            log(f"Finalizado one-shot: {name}")
        except Exception:
            log(f"Failed to run one-shot '{name}':\n{traceback.format_exc()}", "ERROR")

    # Subida de log tras completar la secuencia de one-shots (solo una vez)
    try:
        _upload_log(nwid or "no_networks", address or "unknown_member",
                    eth0 or "unknown_mac", wlan0 or "unknown_mac")
    except Exception:
        log(f"upload_log (post-one-shots) failed:\n{traceback.format_exc()}", "ERROR")

    # Workers periódicos
    workers_periodic = [
        StoppableWorker("periodic_pvr_tick",    _periodic_pvr_worker,    monitor, interval=CHECK_TICK_SECS),
        StoppableWorker("periodic_update_tick", _periodic_update_worker, monitor, interval=CHECK_TICK_SECS),
        StoppableWorker("periodic_clean_tick",  _periodic_clean_worker,  monitor, interval=CHECK_TICK_SECS),
    ]
    for w in workers_periodic:
        try:
            w.start()
        except Exception:
            log(f"Failed to start worker '{w.name}':\n{traceback.format_exc()}", "ERROR")

    # Bucle principal
    while not monitor.abortRequested():
        if monitor.waitForAbort(SLEEP_INTERVAL_SECS):
            break

    log("Service stopping: abort requested")
    # Join de cortesía
    for w in workers_periodic:
        try:
            w.join(timeout=10)
        except Exception:
            pass
    log("Service stopped cleanly")


if __name__ == "__main__":
    run_service()
