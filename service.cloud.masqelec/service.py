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
import threading

import xbmc
import xbmcgui

import urllib.request

from lib import log_utils
from lib import jsonrpc_utils
from lib import rclone_utils
from lib.cloud_storage import start_cloud_storage
from lib.updater import update_system
from lib.update_library import update_library
from lib.update_pvr import update_pvr, update_playlist
from lib.jsonrpc_utils import get_library_stats, get_installed_addons
from lib import utils

# ---- Config constante ----
SLEEP_INTERVAL_SECS = 10
RETRY_BACKOFF_SECS = 30
CHECK_TICK_SECS    = 60  # cada cuánto evaluar condiciones

REQUIRED_RCLONE_MOUNTS = [
    ("users_library_1:movies",  "/storage/videos/1"),
    ("users_library_2:movies",  "/storage/videos/2"),
    ("users_library_1:tvshows", "/storage/tvshows/1"),
    ("users_library_2:tvshows", "/storage/tvshows/2"),
]

LIST_TIMEOUT = 2.0  # segundos

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

    # Si el hilo siguió bloqueado, devolvemos None
    return result["items"]


def _mounts_ready() -> bool:
    """
    Verifica que los montajes rclone están:
      ✔ en /proc/mounts como fuse.rclone
      ✔ accesibles
      ✔ NO vacíos
      ✔ sin bloquear por FUSE colgado
    """

    try:
        # 1) Leer /proc/mounts
        try:
            with open("/proc/mounts", "r") as f:
                lines = f.readlines()
        except Exception as e:
            log(f"_mounts_ready: no se pudo leer /proc/mounts: {e}", "ERROR")
            return False

        # Extraer montajes fuse.rclone
        rclone_mounts = []
        for line in lines:
            if "fuse.rclone" not in line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            src, target, fstype = parts[0], parts[1], parts[2]
            if fstype == "fuse.rclone":
                rclone_mounts.append((src, target))

        if not rclone_mounts:
            log("_mounts_ready: no hay montajes fuse.rclone en /proc/mounts", "WARNING")
            return False

        # 2) Verificación de los 4 montajes requeridos
        for required_src, required_target in REQUIRED_RCLONE_MOUNTS:
            found = any(
                (src == required_src and target == required_target)
                for src, target in rclone_mounts
            )
            if not found:
                log(f"_mounts_ready: falta montaje {required_src} → {required_target}", "WARNING")
                return False

        # 3) Accesibilidad + contenido + timeout
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
    Sube el LOG vía rclone a log:masqelec/log/<nwid>_<address>_<eth0>_<wlan0>_service.log.
    Si no hay errores/avisos, simplemente se anota y se sube igual.
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
            log("No se han encontrado errores ni advertencias en el log.")

        destination_filename = f"{nwid}_{address}_{eth0}_{wlan0}_service.log"
        log(
            "Subiendo log al remoto: "
            f"log:masqelec/log/{destination_filename}"
        )
        ok = rclone_utils.copy_to_tmp_then_move_remote(
            LOG_FILE, "log", f"masqelec/log/{destination_filename}"
        )
        if ok:
            log("Log subido correctamente vía rclone.")
        else:
            log("No se pudo subir el log a través de rclone.", "ERROR")

    except Exception:
        log(f"upload_log fallido:\n{traceback.format_exc()}", "ERROR")


# ------------- FASES -------------
def _phase1_cloud_storage_blocking(monitor: xbmc.Monitor):
    """Fase 1: Cloud storage SIEMPRE y BLOQUEANTE."""
    log("Fase 1: cloud_storage (start_cloud_storage) -> inicio")
    try:
        start_cloud_storage()
    except Exception:
        log(f"Fallo en cloud_storage:\n{traceback.format_exc()}", "ERROR")
    log("Fase 1: cloud_storage -> finalizado")
    if monitor.abortRequested():
        raise SystemExit


# ---------- WRAPPERS ONE-SHOT (FASE 2) ----------
def _update_system_wrapper():
    try:
        enabled = _get_bool_setting("auto_update", True)
        if enabled:
            # Para auto-update de sistema somos más conservadores: exigimos más inactividad
            if not utils.kodi_is_idle(min_idle_secs=300):
                log(
                    "Omitiendo actualización automática: "
                    "Kodi no está inactivo el tiempo suficiente.",
                    "INFO",
                )
                return
            log(
                "Actualización automática habilitada y Kodi inactivo "
                "-> update_system()"
            )
            update_system()
        else:
            log("Actualización automática desactivada")
    except Exception:
        log(f"Fallo en update_system:\n{traceback.format_exc()}", "ERROR")


def _update_library_wrapper():
    """One-shot al arranque (usa flujo avanzado de update_library.py) controlado por ajustes."""
    global _last_update_ts
    try:
        prefs = _load_library_prefs()
        if prefs["update_enabled"] and prefs["update_on_start"]:
            log("Actualizando biblioteca al inicio mediante update_library()")
            with _LIBRARY_LOCK:
                update_library()
                _last_update_ts = time.time()
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
    """
    Mantenimiento de arranque, en ESTE orden y de forma SECUENCIAL
    (no comienza uno hasta que termina el anterior):

      1) Actualizar lista PVR (update_playlist)
      2) CleanLibrary (silencioso)
      3) UpdateLibrary (silencioso)

    Se ejecuta una sola vez al inicio, independiente de los workers periódicos.
    Respeta los ajustes existentes donde tiene sentido.
    """
    try:
        # Primero, comprobaciones básicas
        if not is_online():
            log("Mantenimiento de arranque: sin red, se omite.", "WARNING")
            return
        if not _mounts_ready():
            log("Mantenimiento de arranque: montajes rclone no listos, se omite.", "WARNING")
            return

        # 1) Actualizar lista PVR (si está habilitado)
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

        # 2) CleanLibrary (según ajustes de biblioteca)
        prefs = _load_library_prefs()
        if prefs.get("clean_enabled", True):
            log("Mantenimiento de arranque: CleanLibrary (silencioso) -> inicio")
            clean_library_silent()
            log("Mantenimiento de arranque: CleanLibrary (silencioso) -> finalizado")
        else:
            log("Mantenimiento de arranque: CleanLibrary desactivado por ajustes")

        # 3) UpdateLibrary (según ajustes de biblioteca)
        if prefs.get("update_enabled", True) and prefs.get("update_on_start", True):
            log("Mantenimiento de arranque: UpdateLibrary (silencioso) -> inicio")
            update_library_silent()
            # actualizamos _last_update_ts para que el periódico respete el intervalo
            global _last_update_ts
            _last_update_ts = time.time()
            log("Mantenimiento de arranque: UpdateLibrary (silencioso) -> finalizado")
        else:
            log(
                "Mantenimiento de arranque: UpdateLibrary al inicio desactivado "
                "por ajustes"
            )

    except Exception:
        log(
            "Fallo en mantenimiento de arranque (PVR + Clean + Update):\n"
            f"{traceback.format_exc()}",
            "ERROR",
        )

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

    if not is_online():
        log("Omitiendo revisión PVR: sin red.", "WARNING")
        return
    if not utils.kodi_is_idle():
        log("Omitiendo revisión PVR: Kodi no está inactivo.", "INFO")
        return
    if not _mounts_ready():
        log("Omitiendo revisión PVR: montajes rclone no listos.", "WARNING")
        return

    if _PVR_LOCK.acquire(blocking=False):
        try:
            log("Revisión periódica de canales PVR -> inicio")
            # Sólo refrescamos la lista de canales
            update_playlist()
            _last_pvrcheck_ts = time.time()
            log("Revisión periódica de canales PVR -> finalizado")
        except Exception:
            log(
                "Error en revisión periódica de canales PVR:\n"
                f"{traceback.format_exc()}",
                "ERROR",
            )
        finally:
            _PVR_LOCK.release()
    else:
        log(
            "Omitiendo revisión de canales PVR: "
            "ya hay una operación PVR en curso.",
            "INFO",
        )


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

    if not is_online():
        log("Omitiendo UpdateLibrary: sin red.", "WARNING")
        return
    if not utils.kodi_is_idle():
        log("Omitiendo UpdateLibrary: Kodi no está inactivo.", "INFO")
        return
    if not _mounts_ready():
        log("Omitiendo UpdateLibrary: montajes rclone no listos.", "WARNING")
        return

    if _LIBRARY_LOCK.acquire(blocking=False):
        try:
            log("UpdateLibrary periódico (silencioso) -> inicio")
            update_library_silent()
            _last_update_ts = time.time()
            log("UpdateLibrary periódico -> finalizado")
        except Exception:
            log(
                f"Error en UpdateLibrary periódico:\n{traceback.format_exc()}",
                "ERROR",
            )
        finally:
            _LIBRARY_LOCK.release()
    else:
        log(
            "Omitiendo UpdateLibrary: ya hay una operación de biblioteca en curso.",
            "INFO",
        )


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

    # Retrasar primera ejecución para que no limpie nada más arrancar
    if _last_clean_ts == 0.0:
        _last_clean_ts = now
        return

    if (now - _last_clean_ts) < period_secs:
        return

    if not is_online():
        log("Omitiendo CleanLibrary: sin red.", "WARNING")
        return
    if not utils.kodi_is_idle():
        log("Omitiendo CleanLibrary: Kodi no está inactivo.", "INFO")
        return
    if not _mounts_ready():
        log("Omitiendo CleanLibrary: montajes rclone no listos.", "WARNING")
        return

    if _LIBRARY_LOCK.acquire(blocking=False):
        try:
            log("CleanLibrary periódica (silenciosa) -> inicio")
            clean_library_silent()
            _last_clean_ts = time.time()
            log("CleanLibrary periódica -> finalizado")
        except Exception:
            log(
                f"Error en CleanLibrary periódica:\n{traceback.format_exc()}",
                "ERROR",
            )
        finally:
            _LIBRARY_LOCK.release()
    else:
        log(
            "Omitiendo CleanLibrary: ya hay una operación de biblioteca en curso.",
            "INFO",
        )


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
    
    name  = "0"
    major = "0"
    minor = "0"
    kodi_version = jsonrpc_utils.get_kodi_version()
    if isinstance(kodi_version, dict):
        name  = kodi_version.get("name",  name)
        major = kodi_version.get("major", major)
        minor = kodi_version.get("minor", minor)
        log(f"Versión detectada: {name} {major}.{minor}")

    # valores por defecto para log de red
    nwid   = "no_networks"
    address = "unknown_member"
    eth0   = "unknown_mac"
    wlan0  = "unknown_mac"

    zerotier_ids = utils.get_zerotier_ids()
    if isinstance(zerotier_ids, dict):
        nwid    = zerotier_ids.get("nwid",   nwid)
        address = zerotier_ids.get("address", address)
        log(f"Red Zerotier detectada: NetworkID: {nwid} Miembro: {address}")

    net_info = utils.get_net_info()
    if net_info:
        # admite dict {"eth0": "...", "wlan0": "..."} o tupla/lista ("xx:xx:..", "yy:yy:..")
        eth0_candidate  = _nz(net_info, idx=0, key="eth0")
        wlan0_candidate = _nz(net_info, idx=1, key="wlan0")
        if eth0_candidate:
            eth0 = eth0_candidate
        if wlan0_candidate:
            wlan0 = wlan0_candidate
        log(f"Direcciones MAC: Eth: {eth0}  Wlan: {wlan0}")

    # FASE 1: Cloud storage bloqueante
    _phase1_cloud_storage_blocking(monitor)

    # FASE 2: One-shots SECUENCIALES (no empieza el siguiente hasta que termine el anterior)
    oneshot_sequence = [
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
            log(
                f"No se pudo ejecutar one-shot '{name}':\n{traceback.format_exc()}",
                "ERROR",
            )

    log("Operaciones de arranque completadas (one-shots secuenciales)")
   
    # Añadimos snapshot de stats de biblioteca al log antes de subirlo
    try:
        stats = get_library_stats()
        log(
            "Stats biblioteca: "
            f"Películas={stats['total_movies']}, "
            f"Sagas={stats['total_movie_sets']}, "
            f"Series={stats['total_tvshows']}, "
            f"Episodios={stats['total_episodes']}",
            "INFO"
        )
    except Exception:
        log(
            "No se pudieron obtener las estadísticas de biblioteca para añadir al log",
            "ERROR",
        )
    
    # Añadimos listado de addons al log antes de subirlo
    try:
        addons = get_installed_addons()
        for a in addons:
            log(
                f"{a['id']} | {a['name']} | v{a['version']} | enabled={a['enabled']}",
                "INFO"
            )
    except Exception:
        log(
            "No se pudo obtener el listado de addons para añadir al log",
            "ERROR",
        )

    try:
        _upload_log(
            nwid or "no_networks",
            address or "unknown_member",
            eth0 or "unknown_mac",
            wlan0 or "unknown_mac",
        )
    except Exception:
        log(
            "upload_log (post-one-shots) falló:\n"
            f"{traceback.format_exc()}",
            "ERROR",
        )

    # Workers periódicos
    workers_periodic = [
        StoppableWorker(
            "periodic_pvr_tick",
            _periodic_pvr_worker,
            monitor,
            interval=CHECK_TICK_SECS,
        ),
        StoppableWorker(
            "periodic_clean_tick",
            _periodic_clean_worker,
            monitor,
            interval=CHECK_TICK_SECS,
        ),
        StoppableWorker(
            "periodic_update_tick",
            _periodic_update_worker,
            monitor,
            interval=CHECK_TICK_SECS,
        ),
    ]
    for w in workers_periodic:
        try:
            w.start()
        except Exception:
            log(
                f"No se pudo iniciar el worker '{w.name}':\n{traceback.format_exc()}",
                "ERROR",
            )

    # Bucle principal
    while not monitor.abortRequested():
        if monitor.waitForAbort(SLEEP_INTERVAL_SECS):
            break

    log("Servicio deteniéndose: abort solicitado")
    # Join de cortesía
    for w in workers_periodic:
        try:
            w.join(timeout=10)
        except Exception:
            pass
    log("Servicio detenido correctamente")


if __name__ == "__main__":
    run_service()

