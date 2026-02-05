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

import urllib.request
import urllib.parse

from lib import log_utils
from lib import jsonrpc_utils
from lib import rclone_utils
from lib.cloud_storage import start_cloud_storage
from lib.updater import update_system
from lib.update_library import update_library
from lib.update_pvr import update_pvr, update_playlist
from lib.jsonrpc_utils import get_library_stats, get_installed_addons_filtered, format_addons_for_log
from lib.fix_settings import fix_skin_home_menu_visibility_and_reload
from lib import utils
from lib import core_catalog

# ---- Config constante ----
SLEEP_INTERVAL_SECS = 10
RETRY_BACKOFF_SECS = 30
CHECK_TICK_SECS    = 60  # cada cuánto evaluar condiciones

REQUIRED_RCLONE_MOUNTS = [
    ("users_library_1:tvshows", "/storage/.mnt/tvshows/1"),
    ("users_library_1:movies",  "/storage/.mnt/videos/1"),
    ("users_library_2:tvshows", "/storage/.mnt/tvshows/2"),
    ("users_library_2:movies",  "/storage/.mnt/videos/2"),
]

LIST_TIMEOUT = 2.0  # segundos

LOG_FILE = log_utils.LOG_FILE

# ---- Estado global de planificación ----
_last_update_ts   = 0.0
_last_clean_ts    = 0.0
_last_pvrcheck_ts = None

_LIBRARY_LOCK = threading.Lock()
_PVR_LOCK     = threading.Lock()

# ---------- Circuit breaker / cooldown por tarea ----------
_TASK_FAILS = {"pvr": 0, "update": 0, "clean": 0}
_TASK_COOLDOWN_UNTIL = {"pvr": 0.0, "update": 0.0, "clean": 0.0}

_TASK_FAIL_THRESHOLD = 3          # fallos consecutivos antes de enfriar
_TASK_COOLDOWN_SECS  = 60 * 60    # 60 min de enfriamiento

def _task_is_in_cooldown(name: str) -> bool:
    until = float(_TASK_COOLDOWN_UNTIL.get(name, 0.0) or 0.0)
    return time.time() < until

def _task_mark_success(name: str):
    _TASK_FAILS[name] = 0
    _TASK_COOLDOWN_UNTIL[name] = 0.0

def _task_mark_failure(name: str, where: str, exc_text: str):
    _TASK_FAILS[name] = int(_TASK_FAILS.get(name, 0) or 0) + 1
    fails = _TASK_FAILS[name]
    log(f"{where}: fallo #{fails} en tarea '{name}'.\n{exc_text}", "ERROR")

    if fails >= _TASK_FAIL_THRESHOLD:
        _TASK_COOLDOWN_UNTIL[name] = time.time() + _TASK_COOLDOWN_SECS
        log(
            f"Tarea '{name}' entra en cooldown {int(_TASK_COOLDOWN_SECS/60)} min tras {fails} fallos consecutivos.",
            "WARNING"
        )

def _log_metrics_snapshot() -> None:
    """Vuelca un resumen corto de métricas (sin spam)."""
    try:
        tasks = ["cloud_storage", "updater", "catalog", "library", "pvr", "clean"]
        parts = []
        for t in tasks:
            m = utils.metrics_get(t)
            if not m:
                continue
            lr = m.get("last_result")
            dt = m.get("last_duration_sec")
            ts = m.get("last_run_ts")
            if ts:
                ago = int(time.time() - int(ts))
                parts.append(f"{t}={lr} ({ago}s, {dt:.1f}s)" if isinstance(dt,(int,float)) else f"{t}={lr} ({ago}s)")
            else:
                parts.append(f"{t}={lr}")
        if parts:
            log_utils.write_log("Estado tareas: " + " | ".join(parts), "INFO")
    except Exception:
        return

class StoppableWorker(threading.Thread):
    """Hilo que ejecuta una función y respeta abortRequested()."""
    def __init__(self, name, target, monitor, interval=0, run_once=False):
        super().__init__(name=name, daemon=True)
        self._target_fn = target
        self._monitor   = monitor
        self._interval  = max(0, int(interval))
        self._run_once  = bool(run_once)

    def run(self):
        log(
            f"Hilo '{self.name}' iniciado "
            f"(run_once={self._run_once}, intervalo={self._interval}s)"
        )
        try:
            while not self._monitor.abortRequested():
                try:
                    self._target_fn()
                except Exception:
                    log(
                        f"Error en hilo '{self.name}':\n{traceback.format_exc()}",
                        "ERROR"
                    )
                    if self._monitor.waitForAbort(RETRY_BACKOFF_SECS):
                        break

                if self._run_once:
                    break

                if self._interval > 0 and self._monitor.waitForAbort(self._interval):
                    break
        finally:
            log(f"Hilo '{self.name}' finalizado")

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
        except Exception as e:
            log_utils.write_log(f"Excepción ignorada en service.py: {e}", "DEBUG")
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
        except Exception as e:
            log_utils.write_log(f"Excepción ignorada en service.py: {e}", "DEBUG")
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

def _safe_listdir(path: str, timeout: float = LIST_TIMEOUT):
    """
    Ejecuta os.listdir(path) en un hilo para evitar bloqueos.
    Si pasa del timeout, devuelve None.
    """
    result = {"items": None}

    def runner():
        try:
            result["items"] = os.listdir(path)
        except Exception:
            result["items"] = None

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    t.join(timeout)

    return result["items"]

def _unescape_mount(s: str) -> str:
    """
    /proc/mounts escapa algunos caracteres (espacio, tab, newline, backslash).
    """
    if not isinstance(s, str):
        return s
    return (
        s.replace("\\040", " ")
         .replace("\\011", "\t")
         .replace("\\012", "\n")
         .replace("\\134", "\\")
    )

def _mounts_ready() -> bool:
    """
    Verifica que los montajes rclone están:
      ✔ en /proc/mounts como fuse.rclone
      ✔ accesibles
      ✔ NO vacíos
      ✔ sin bloquear por FUSE colgado
    """
    try:
        try:
            with open("/proc/mounts", "r") as f:
                lines = f.readlines()
        except Exception as e:
            log(f"_mounts_ready: no se pudo leer /proc/mounts: {e}", "ERROR")
            return False

        rclone_mounts = []
        for line in lines:
            if "fuse.rclone" not in line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue

            src = _unescape_mount(parts[0])
            target = _unescape_mount(parts[1])
            fstype = parts[2]

            if fstype == "fuse.rclone":
                rclone_mounts.append((src, target))

        if not rclone_mounts:
            log("_mounts_ready: no hay montajes fuse.rclone en /proc/mounts", "WARNING")
            return False

        required_targets = {t for _, t in REQUIRED_RCLONE_MOUNTS}
        mounted_targets  = {t for _, t in rclone_mounts}

        missing = required_targets - mounted_targets
        if missing:
            log(f"_mounts_ready: faltan targets montados: {sorted(missing)}", "WARNING")
            return False

        for _, target in REQUIRED_RCLONE_MOUNTS:
            if not os.path.isdir(target):
                log(f"_mounts_ready: directorio no existe: {target}", "WARNING")
                return False

            items = _safe_listdir(target, timeout=LIST_TIMEOUT)
            if items is None:
                log(f"_mounts_ready: TIMEOUT listando {target} (posible rclone colgado)", "WARNING")
                return False
            if not items:
                log(f"_mounts_ready: carpeta vacía (montaje incompleto): {target}", "WARNING")
                return False

        return True

    except Exception as e:
        log(f"_mounts_ready: excepción inesperada: {e}", "ERROR")
        return False

# ------------- Tareas silenciosas JSON-RPC -------------
def clean_library_silent(timeout_start=5, timeout_total=30*30):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "VideoLibrary.Clean",
        "params": {"showdialogs": False}
    }

    try:
        raw = xbmc.executeJSONRPC(json.dumps(payload))
        resp = json.loads(raw) if raw else {}
    except Exception as e:
        log(f"JSON-RPC inválido/exception: {e}",  "ERROR")
        return False

    if isinstance(resp, dict) and resp.get("error"):
        log(f"JSON-RPC error: {resp['error']}",  "ERROR")
        return False

    mon = xbmc.Monitor()

    waited = 0.0
    while not mon.abortRequested() and waited < timeout_start:
        if xbmc.getCondVisibility("Library.IsCleaningVideo"):
            break
        mon.waitForAbort(0.25)
        waited += 0.25

    if not xbmc.getCondVisibility("Library.IsCleaningVideo"):
        log(f"Clean NO arrancó en {timeout_start}s (posible: ya estaba en curso, o no hay nada que limpiar).",  "INFO")
        return False

    waited = 0
    while xbmc.getCondVisibility("Library.IsCleaningVideo") and not mon.abortRequested() and waited < timeout_total:
        mon.waitForAbort(1)
        waited += 1

    if mon.abortRequested():
        log("AbortRequested mientras limpiaba.",  "INFO")
        return False

    if xbmc.getCondVisibility("Library.IsCleaningVideo"):
        log(f"Timeout total esperando fin del clean ({timeout_total}s).",  "INFO")
        return False

    return True

def update_library_silent(timeout_start=5, timeout_total=30*30):
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "VideoLibrary.Scan",
        "params": {"showdialogs": True}
    }

    try:
        raw = xbmc.executeJSONRPC(json.dumps(payload))
        resp = json.loads(raw) if raw else {}
    except Exception as e:
        log(f"JSON-RPC inválido/exception: {e}", "ERROR")
        return False

    if isinstance(resp, dict) and resp.get("error"):
        log(f"JSON-RPC error: {resp['error']}", "ERROR")
        return False

    mon = xbmc.Monitor()

    waited = 0
    while not mon.abortRequested() and waited < timeout_start:
        if xbmc.getCondVisibility("Library.IsScanningVideo"):
            break
        mon.waitForAbort(0.25)
        waited += 0.25

    if not xbmc.getCondVisibility("Library.IsScanningVideo"):
        log(f"Scan NO arrancó en {timeout_start}s (posible: ya estaba escaneando, colgado, o no hay fuentes).",  "INFO")
        return False

    waited = 0
    while xbmc.getCondVisibility("Library.IsScanningVideo") and not mon.abortRequested() and waited < timeout_total:
        mon.waitForAbort(1)
        waited += 1

    if mon.abortRequested():
        log("AbortRequested mientras escaneaba.",  "INFO")
        return False

    if xbmc.getCondVisibility("Library.IsScanningVideo"):
        log(f"Timeout total esperando fin del scan ({timeout_total}s).",  "INFO")
        return False

    return True

# --- NUEVO: Verificación DB vs FS (solo clientes) ---
def _client_verify_db_vs_fs() -> dict:
    try:
        res = core_catalog.verify_catalog_db_vs_fs()
        tot = (res or {}).get("total") or {}
        missing = int(tot.get("missing", 0) or 0)
        extra   = int(tot.get("extra", 0) or 0)
        log(f"Cliente: DB↔FS catálogo => Missing={missing} Extra={extra}", "INFO")
        return res
    except Exception:
        log(f"Cliente: fallo verificación DB↔FS:\n{traceback.format_exc()}", "ERROR")
        return {"total": {"missing": 0, "extra": 0}}

# ---------- Subida de log post-workers ----------
def _upload_log(n: str, nwid: str, id_device: str, eth0: str, wlan0: str):
    try:
        error_or_warning_found = False
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if '[ERROR]' in line or '[WARNING]' in line:
                        error_or_warning_found = True
                        break

        destination_filename = f"{n}_{nwid}_{id_device}_{eth0}_{wlan0}_service.log"
        log("Subiendo log al remoto: " f"log:masqelec/log/{destination_filename}")
        ok = rclone_utils.copy_to_tmp_then_move_remote(
            LOG_FILE, "log", f"masqelec/log/{destination_filename}"
        )
        if ok:
            log("Log subido correctamente vía rclone.")
        else:
            log("No se pudo subir el log a través de rclone.", "ERROR")

        if error_or_warning_found:
            network_info = f"Dispositivo: {n}_{nwid}_{id_device}_{eth0}_{wlan0}"
            ok = utils.telegram_send_log_with_summary_if_problem(
                LOG_FILE, destination_filename, network_info
            )
            if ok:
                log("Telegram: log enviado.", "INFO")
            else:
                log("Telegram: no se pudo enviar.", "WARNING")
        else:
            log("No se han encontrado errores ni advertencias en el log.", "INFO")

    except Exception:
        log(f"upload_log fallido:\n{traceback.format_exc()}", "ERROR")

# ------------- FASES -------------
def _phase1_cloud_storage_blocking(monitor: xbmc.Monitor):
    log("Fase 1: cloud_storage (start_cloud_storage) -> inicio")
    try:
        start_cloud_storage()
    except Exception:
        log(f"Fallo en cloud_storage:\n{traceback.format_exc()}", "ERROR")
    log("Fase 1: cloud_storage -> finalizado")
    if monitor.abortRequested():
        raise SystemExit

# ---------- WRAPPERS ONE-SHOT (FASE 2) ----------
def _fix_settings_wrapper():
    try:
        fix_skin_home_menu_visibility_and_reload(log_summary=True)
    except Exception:
        log(f"Fallo en fix_settings:\n{traceback.format_exc()}", "WARNING")

def _update_system_wrapper():
    try:
        enabled = _get_bool_setting("auto_update", True)
        if enabled:
            if not utils.kodi_is_idle(min_idle_secs=300):
                log(
                    "Omitiendo actualización automática: "
                    "Kodi no está inactivo el tiempo suficiente.",
                    "INFO",
                )
                return
            log("Actualización automática habilitada y Kodi inactivo -> update_system()")
            update_system()
        else:
            log("Actualización automática desactivada")
    except Exception:
        log(f"Fallo en update_system:\n{traceback.format_exc()}", "ERROR")

def _update_library_wrapper():
    global _last_update_ts
    try:
        prefs = _load_library_prefs()
        if prefs["update_enabled"] and prefs["update_on_start"]:
            log("Actualizando biblioteca al inicio mediante update_library()")
            if _LIBRARY_LOCK.acquire(blocking=False):
                try:
                    update_library()
                    _last_update_ts = time.time()
                finally:
                    _LIBRARY_LOCK.release()
            else:
                log("Omitiendo update_library al inicio: ya hay una operación de biblioteca en curso.", "DEBUG")
        else:
            log("Actualización de biblioteca al inicio desactivada por ajustes")
    except Exception:
        log(f"Fallo en update_library:\n{traceback.format_exc()}", "ERROR")

def _update_pvr_wrapper():
    try:
        enabled = _get_bool_setting("update_pvr", True)
        if enabled:
            log("Actualizando PVR mediante update_pvr()")
            update_pvr()
        else:
            log("Actualización de PVR desactivada")
    except Exception:
        log(f"Fallo en update_pvr:\n{traceback.format_exc()}", "ERROR")

def _startup_maintenance_wrapper():
    global _last_clean_ts, _last_update_ts

    try:
        if not utils.is_online():
            log("Mantenimiento de arranque: sin red, se omite.", "WARNING")
            return
        if not _mounts_ready():
            log("Mantenimiento de arranque: montajes rclone no listos, se omite.", "WARNING")
            return

        # 1) PVR playlist
        try:
            update_pvr_enabled = _get_bool_setting("update_pvr", True)
        except Exception:
            update_pvr_enabled = True

        if update_pvr_enabled:
            log("Mantenimiento de arranque: actualización de lista PVR -> inicio")
            update_playlist()
            log("Mantenimiento de arranque: actualización de lista PVR -> finalizado")
        else:
            log("Mantenimiento de arranque: actualización de lista PVR desactivada por ajustes")

        prefs = _load_library_prefs()

        sync_applied = False
        verify = None

        if utils.is_client():
            log("Cliente: comprobando/sincronizando catálogo remoto…")
            try:
                sync_applied = bool(core_catalog.sync_catalog_https())
            except Exception:
                log(f"Cliente: fallo sincronizando catálogo:\n{traceback.format_exc()}", "ERROR")
                sync_applied = False

            if not sync_applied:
                verify = _client_verify_db_vs_fs()

        # 2) CleanLibrary
        if prefs.get("clean_enabled", True):
            if utils.is_client():
                do_clean = False
                if sync_applied:
                    do_clean = True
                else:
                    tot = (verify or {}).get("total") or {}
                    do_clean = int(tot.get("extra", 0) or 0) > 0

                if do_clean:
                    log("Mantenimiento de arranque: CleanLibrary (silencioso) -> inicio")
                    clean_library_silent()
                    log("Mantenimiento de arranque: CleanLibrary (silencioso) -> finalizado")
                    _last_clean_ts = time.time()
            else:
                log("Mantenimiento de arranque: CleanLibrary (silencioso) -> inicio")
                clean_library_silent()
                log("Mantenimiento de arranque: CleanLibrary (silencioso) -> finalizado")
                _last_clean_ts = time.time()
        else:
            log("Mantenimiento de arranque: CleanLibrary desactivado por ajustes")

        # 3) UpdateLibrary
        if prefs.get("update_enabled", True) and prefs.get("update_on_start", True):
            if utils.is_client():
                do_scan = False
                if sync_applied:
                    do_scan = True
                else:
                    tot = (verify or {}).get("total") or {}
                    missing = int(tot.get("missing", 0) or 0)
                    extra   = int(tot.get("extra", 0) or 0)
                    do_scan = (missing > 0) or (extra > 0)

                if do_scan:
                    log("Mantenimiento de arranque: UpdateLibrary (silencioso) -> inicio")
                    update_library_silent()
                    log("Mantenimiento de arranque: UpdateLibrary (silencioso) -> finalizado")
                    _last_update_ts = time.time()
            else:
                log("Mantenimiento de arranque: UpdateLibrary (silencioso) -> inicio")
                update_library_silent()
                _last_update_ts = time.time()
                log("Mantenimiento de arranque: UpdateLibrary (silencioso) -> finalizado")
                log("Iniciando carga del catalogo")
                core_catalog.generate_catalog()
                utils.load_catalog_github()
        else:
            log("Mantenimiento de arranque: UpdateLibrary al inicio desactivado por ajustes")

    except Exception:
        log(
            "Fallo en mantenimiento de arranque (PVR + Clean + Update):\n"
            f"{traceback.format_exc()}",
            "ERROR",
        )

# ---------- Workers periódicos ----------
def _periodic_pvr_worker():
    global _last_pvrcheck_ts
    prefs = _load_pvr_prefs()
    if not prefs["update_enabled"]:
        return

    period_secs = _hours_to_secs(prefs["update_period_hours"])
    if period_secs <= 0:
        return

    now = time.time()

    if _last_pvrcheck_ts is None:
        _last_pvrcheck_ts = now
        return

    if (now - _last_pvrcheck_ts) < period_secs:
        return

    if not utils.is_online():
        log("Omitiendo revisión PVR: sin red.", "WARNING")
        return
    if not utils.kodi_is_idle():
        log("Omitiendo revisión PVR: Kodi no está inactivo.", "INFO")
        return

    if _task_is_in_cooldown("pvr"):
        log("Omitiendo revisión PVR: en cooldown por fallos recientes.", "WARNING")
        return

    if _PVR_LOCK.acquire(blocking=False):
        try:
            log("Revisión periódica de canales PVR -> inicio")
            update_playlist()
            _task_mark_success("pvr")
            _last_pvrcheck_ts = time.time()
            log("Revisión periódica de canales PVR -> finalizado")
        except Exception:
            _task_mark_failure("pvr", "Error en revisión periódica de canales PVR", traceback.format_exc())
        finally:
            _PVR_LOCK.release()
    else:
        log("Omitiendo revisión de canales PVR: ya hay una operación PVR en curso.", "INFO")

def _periodic_update_worker():
    global _last_update_ts
    prefs = _load_library_prefs()
    if not prefs["update_enabled"]:
        return

    period_secs = _hours_to_secs(prefs["update_period_hours"])
    if period_secs <= 0:
        return

    now = time.time()
    if (now - _last_update_ts) < period_secs:
        return

    if not utils.is_online():
        log("Omitiendo UpdateLibrary: sin red.", "WARNING")
        return
    if not utils.kodi_is_idle():
        log("Omitiendo UpdateLibrary: Kodi no está inactivo.", "INFO")
        return
    if not _mounts_ready():
        log("Omitiendo UpdateLibrary: montajes rclone no listos.", "WARNING")
        return

    if _task_is_in_cooldown("update"):
        log("Omitiendo UpdateLibrary: en cooldown por fallos recientes.", "WARNING")
        return

    if _LIBRARY_LOCK.acquire(blocking=False):
        success = True
        try:
            if utils.is_client():
                log("Cliente: comprobando/sincronizando catálogo remoto…")
                applied = False
                try:
                    applied = bool(core_catalog.sync_catalog_https())
                except Exception:
                    log(f"Cliente: fallo sincronizando catálogo:\n{traceback.format_exc()}", "ERROR")
                    applied = False

                if not applied:
                    verify = _client_verify_db_vs_fs()
                    tot = (verify or {}).get("total") or {}
                    missing = int(tot.get("missing", 0) or 0)
                    extra   = int(tot.get("extra", 0) or 0)

                    if (missing > 0) or (extra > 0):
                        log_utils.write_log("Cliente: DB↔FS desfasado (sin cambios remotos) → Scan", "INFO")
                        log("UpdateLibrary periódico (silencioso) -> inicio")
                        update_library_silent()
                        _last_update_ts = time.time()
                        log("UpdateLibrary periódico (silencioso) -> finalizado")
                    else:
                        log_utils.write_log("Cliente: catálogo al día y DB↔FS OK → se omite Scan", "INFO")
                    return

                log_utils.write_log("Cliente: catálogo actualizado → se ejecuta Scan", "INFO")
                log("UpdateLibrary periódico (silencioso) -> inicio")
                update_library_silent()
                _last_update_ts = time.time()
                log("UpdateLibrary periódico (silencioso) -> finalizado")

            else:
                log("UpdateLibrary periódico (silencioso) -> inicio")
                update_library_silent()
                _last_update_ts = time.time()
                log("UpdateLibrary periódico (silencioso) -> finalizado")
                log("Iniciando carga del catalogo")
                core_catalog.generate_catalog()
                utils.load_catalog_github()

        except Exception:
            success = False
            _task_mark_failure("update", "Error en UpdateLibrary periódico", traceback.format_exc())
        finally:
            if success:
                _task_mark_success("update")
            _LIBRARY_LOCK.release()
    else:
        log("Omitiendo UpdateLibrary: ya hay una operación de biblioteca en curso.", "INFO")

def _periodic_clean_worker():
    global _last_clean_ts, _last_update_ts
    prefs = _load_library_prefs()
    if not prefs["clean_enabled"]:
        return

    period_secs = _hours_to_secs(prefs["clean_period_hours"])
    if period_secs <= 0:
        return

    now = time.time()

    if _last_clean_ts == 0.0:
        _last_clean_ts = now
        return

    if (now - _last_clean_ts) < period_secs:
        return

    if not utils.is_online():
        log("Omitiendo CleanLibrary: sin red.", "WARNING")
        return
    if not utils.kodi_is_idle():
        log("Omitiendo CleanLibrary: Kodi no está inactivo.", "INFO")
        return
    if not _mounts_ready():
        log("Omitiendo CleanLibrary: montajes rclone no listos.", "WARNING")
        return

    if _task_is_in_cooldown("clean"):
        log("Omitiendo CleanLibrary: en cooldown por fallos recientes.", "WARNING")
        return

    if _LIBRARY_LOCK.acquire(blocking=False):
        success = True
        try:
            if utils.is_client():
                log("Cliente: comprobando/sincronizando catálogo remoto…")
                applied = False
                try:
                    applied = bool(core_catalog.sync_catalog_https())
                except Exception:
                    log(f"Cliente: fallo sincronizando catálogo:\n{traceback.format_exc()}", "ERROR")
                    applied = False

                if not applied:
                    verify = _client_verify_db_vs_fs()
                    tot = (verify or {}).get("total") or {}
                    extra = int(tot.get("extra", 0) or 0)

                    if extra > 0:
                        log_utils.write_log("Cliente: DB tiene extras (sin cambios remotos) → Clean + Scan", "INFO")

                        log("CleanLibrary periódica (silenciosa) -> inicio")
                        clean_library_silent()
                        log("CleanLibrary periódica (silenciosa) -> finalizado")

                        log("UpdateLibrary post-clean (silencioso) -> inicio")
                        update_library_silent()
                        log("UpdateLibrary post-clean (silencioso) -> finalizado")

                        _last_clean_ts = time.time()
                        _last_update_ts = time.time()
                    else:
                        log_utils.write_log("Cliente: catálogo al día y sin extras → se omite Clean", "INFO")
                    return

                log_utils.write_log("Cliente: catálogo actualizado → se ejecuta Clean", "INFO")
                log("CleanLibrary periódica (silenciosa) -> inicio")
                clean_library_silent()
                _last_clean_ts = time.time()
                log("CleanLibrary periódica (silenciosa) -> finalizado")

            else:
                log("CleanLibrary periódica (silenciosa) -> inicio")
                clean_library_silent()
                _last_clean_ts = time.time()
                log("CleanLibrary periódica (silenciosa) -> finalizado")
        except Exception:
            success = False
            _task_mark_failure("clean", "Error en CleanLibrary periódica", traceback.format_exc())
        finally:
            if success:
                _task_mark_success("clean")
            _LIBRARY_LOCK.release()
    else:
        log("Omitiendo CleanLibrary: ya hay una operación de biblioteca en curso.", "INFO")

def _nz(x, idx=None, key=None):
    """Devuelve x[key] si dict, x[idx] si secuencia, o None."""
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

    log("Servicio iniciando")

    role = utils.get_device_role()

    name  = "0"
    major = "0"
    minor = "0"
    kodi_version = jsonrpc_utils.get_kodi_version()
    if isinstance(kodi_version, dict):
        name  = kodi_version.get("name",  name)
        major = kodi_version.get("major", major)
        minor = kodi_version.get("minor", minor)
        log(f"Versión detectada: {name} {major}.{minor}")

    n         = "no_name"
    nwid      = "no_networks"
    id_device = "no_device_id"
    eth0      = "unknown_mac"
    wlan0     = "unknown_mac"

    zerotier_ids = utils.get_zerotier_ids()
    if isinstance(zerotier_ids, dict):
        n          = zerotier_ids.get("n", n)
        nwid       = zerotier_ids.get("nwid", nwid)
        id_device  = zerotier_ids.get("id", id_device)
        log(f"Red Zerotier detectada: Name: {n} NetworkID: {nwid} ID: {id_device}")

    net_info = utils.get_net_info()
    if net_info:
        eth0_candidate  = _nz(net_info, idx=0, key="eth0")
        wlan0_candidate = _nz(net_info, idx=1, key="wlan0")
        if eth0_candidate:
            eth0 = eth0_candidate
        if wlan0_candidate:
            wlan0 = wlan0_candidate
        log(f"Direcciones MAC: Eth: {eth0}  Wlan: {wlan0}")

    _phase1_cloud_storage_blocking(monitor)

    oneshot_sequence = [
        ("fix_settings_once",   _fix_settings_wrapper),
        ("auto_update_once",    _update_system_wrapper),
        ("library_update_once", _update_library_wrapper),
        ("pvr_update_once",     _update_pvr_wrapper),
        ("startup_maintenance", _startup_maintenance_wrapper),
    ]

    log("Iniciando operaciones de arranque (one-shots secuenciales)")

    for name, fn in oneshot_sequence:
        if monitor.abortRequested():
            log(f"Abort solicitado antes de ejecutar '{name}'")
            break
        try:
            log(f"Iniciando one-shot: {name}")
            t = StoppableWorker(name, fn, monitor, run_once=True)
            t.start()
            while t.is_alive() and not monitor.abortRequested():
                monitor.waitForAbort(0.25)
            log(f"Finalizado one-shot: {name}")
        except Exception:
            log(f"No se pudo ejecutar one-shot '{name}':\n{traceback.format_exc()}", "ERROR")

    log("Operaciones de arranque completadas (one-shots secuenciales)")

    try:
        stats = get_library_stats()

        total_movies   = int(stats.get("total_movies", 0))
        total_tvshows  = int(stats.get("total_tvshows", 0))
        total_sets     = int(stats.get("total_movie_sets", 0))
        total_episodes = int(stats.get("total_episodes", 0))

        if total_movies == 0 or total_tvshows == 0:
            log(
                "Stats biblioteca ANÓMALAS: "
                f"Películas={total_movies}, "
                f"Sagas={total_sets}, "
                f"Series={total_tvshows}, "
                f"Episodios={total_episodes}",
                "ERROR"
            )
        else:
            log(
                "Stats biblioteca: "
                f"Películas={total_movies}, "
                f"Sagas={total_sets}, "
                f"Series={total_tvshows}, "
                f"Episodios={total_episodes}",
                "INFO"
            )

    except Exception as e:
        log(f"No se pudieron obtener las estadísticas de biblioteca para añadir al log: {e}", "ERROR")

    try:
        ALLOW = [
            "service.tvheadend43",
            "pvr.hts",
            "service.cloud.masqelec",
        ]

        addons = get_installed_addons_filtered(ALLOW, include_missing=True)
        for line in format_addons_for_log(addons):
            log(line, "INFO")

    except Exception:
        log("No se pudo obtener el listado de addons para añadir al log", "ERROR")

    try:
        _upload_log(
            n or         "no_name",
            nwid or      "no_networks",
            id_device or "no_device_id",
            eth0 or      "unknown_mac",
            wlan0 or     "unknown_mac",
        )
    except Exception:
        log("upload_log (post-one-shots) falló:\n" f"{traceback.format_exc()}", "ERROR")

    workers_periodic = [
        StoppableWorker("periodic_pvr_tick", _periodic_pvr_worker, monitor, interval=CHECK_TICK_SECS),
        StoppableWorker("periodic_clean_tick", _periodic_clean_worker, monitor, interval=CHECK_TICK_SECS),
        StoppableWorker("periodic_update_tick", _periodic_update_worker, monitor, interval=CHECK_TICK_SECS),
    ]
    for w in workers_periodic:
        try:
            w.start()
        except Exception:
            log(f"No se pudo iniciar el worker '{w.name}':\n{traceback.format_exc()}", "ERROR")

    while not monitor.abortRequested():
        if monitor.waitForAbort(SLEEP_INTERVAL_SECS):
            break

    log("Servicio deteniéndose: abort solicitado")
    for w in workers_periodic:
        try:
            w.join(timeout=10)
        except Exception as e:
            log_utils.write_log(f"Excepción ignorada en service.py: {e}", "DEBUG")
    log("Servicio detenido correctamente")

if __name__ == "__main__":
    run_service()

