# -*- coding: utf-8 -*-
"""
update_library.py — Verificación y reemplazo seguro de MyVideos

Flujo (reinicio justo después, sin Clean/Scan):
  5..80  descarga MyVideos
  80..93 copia MyVideos a .tmp (progreso real por bytes)
  93..99 borrar Textures/Thumbnails (progreso suave)
  99     swap atómico
  100    OK final (solo después de borrar caché)
"""

import os
import re
import time
import sqlite3
import traceback
import shutil
import json
import urllib.request

import xbmc
import xbmcvfs
import xbmcgui

from lib import utils
from lib import log_utils
from lib import jsonrpc_utils
from lib import fix_guisettings


# ---------- Config ----------
MASTER_DB_BASE_URL = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/userdata/database.master"
CLIENT_DB_BASE_URL = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/userdata/database.client"


def _get_db_base_url() -> str:
    try:
        return MASTER_DB_BASE_URL if utils.is_master_device() else CLIENT_DB_BASE_URL
    except Exception:
        return CLIENT_DB_BASE_URL


MASTER_REQUIRED_CONDITIONS = [
    ("/storage/.mnt/videos/1/",  "movies",  "metadata.themoviedb.org.python"),
    ("/storage/.mnt/videos/2/",  "movies",  "metadata.themoviedb.org.python"),
    ("/storage/.mnt/tvshows/1/", "tvshows", "metadata.tvshows.themoviedb.org.python"),
    ("/storage/.mnt/tvshows/2/", "tvshows", "metadata.tvshows.themoviedb.org.python"),
]

CLIENT_REQUIRED_CONDITIONS = [
    ("/storage/videos/",  "movies",  "metadata.themoviedb.org.python"),
    ("/storage/tvshows/", "tvshows", "metadata.tvshows.themoviedb.org.python"),
]


def _get_required_conditions():
    try:
        return MASTER_REQUIRED_CONDITIONS if utils.is_master_device() else CLIENT_REQUIRED_CONDITIONS
    except Exception:
        return CLIENT_REQUIRED_CONDITIONS


# ---------- JSON-RPC helpers ----------
def _jsonrpc_call_soft(method: str, params: dict | None = None):
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params is not None:
            payload["params"] = params
        raw = xbmc.executeJSONRPC(json.dumps(payload))
        if not raw:
            return False, None, {"message": "empty response"}
        data = json.loads(raw)
        if "error" in data and data["error"]:
            return False, None, data["error"]
        return True, data.get("result"), None
    except Exception as e:
        return False, None, {"message": str(e)}


def _get_addon_details(addon_id: str) -> dict | None:
    ok, res, _ = _jsonrpc_call_soft(
        "Addons.GetAddonDetails",
        {"addonid": addon_id, "properties": ["enabled", "name"]}
    )
    if ok and isinstance(res, dict) and res.get("addon"):
        return res["addon"]

    ok, res, _ = _jsonrpc_call_soft(
        "Addons.GetAddons",
        {"properties": ["enabled", "name"], "enabled": "all"}
    )
    if ok and isinstance(res, dict):
        for a in res.get("addons", []):
            if a.get("addonid") == addon_id:
                return a

    ok, res, _ = _jsonrpc_call_soft("Addons.GetAddons", {"enabled": "all"})
    if ok and isinstance(res, dict):
        for a in res.get("addons", []):
            if a.get("addonid") == addon_id:
                return a
    return None


def _get_addon_enabled_state(addon_id: str) -> bool | None:
    det = _get_addon_details(addon_id)
    return None if det is None else bool(det.get("enabled"))


def _set_addon_enabled(addon_id: str, enabled: bool) -> bool:
    ok, _, _ = _jsonrpc_call_soft("Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": enabled})
    if ok:
        state = _get_addon_enabled_state(addon_id)
        if state is not None and state == enabled:
            return True

    try:
        xbmc.executebuiltin(f'{"EnableAddon" if enabled else "DisableAddon"}("{addon_id}")')
        xbmc.sleep(900)
        state = _get_addon_enabled_state(addon_id)
        return state is not None and state == enabled
    except Exception:
        return False


def _disable_libraryautoupdate_if_enabled():
    addon_id = "service.libraryautoupdate"
    state = _get_addon_enabled_state(addon_id)
    if state is True:
        log_utils.write_log(f"Deshabilitando '{addon_id}' para evitar conflictos de biblioteca…")
        if _set_addon_enabled(addon_id, False):
            log_utils.write_log(f"'{addon_id}' deshabilitado correctamente.")
        else:
            log_utils.write_log(f"No se pudo deshabilitar '{addon_id}'.", level="WARNING")


# ---------- Estado Kodi ----------
def _is_scanning() -> bool:
    try:
        return xbmc.getCondVisibility('Library.IsScanningVideo')
    except Exception:
        return False


def _has_network() -> bool:
    try:
        return xbmc.getCondVisibility("System.HasNetwork")
    except Exception:
        return True


def _wait_until_ready(max_wait=60):
    mon = xbmc.Monitor()
    start = time.time()
    while time.time() - start < max_wait and not mon.abortRequested():
        if _has_network() and not _is_scanning():
            return True
        mon.waitForAbort(0.5)
    return True


# ---------- Helpers rutas locales ----------
def _database_dir_os(default_dir="/storage/.kodi/userdata/Database/") -> str:
    try:
        return xbmcvfs.translatePath("special://database")
    except Exception:
        return default_dir


def _thumbnails_dir_os(default_dir="/storage/.kodi/userdata/Thumbnails/") -> str:
    try:
        p = xbmcvfs.translatePath("special://thumbnails")
        return p if p.endswith(os.sep) else p + os.sep
    except Exception:
        return default_dir


def _cleanup_dir(path: str):
    try:
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
            log_utils.write_log(f"[cleanup] Eliminado staging temporal: {path}")
    except Exception as e:
        log_utils.write_log(f"[cleanup] Error al eliminar {path}: {e}", "ERROR")


def _remove_textures_dbs(local_db_dir: str):
    try:
        if not os.path.isdir(local_db_dir):
            return
        for f in os.listdir(local_db_dir):
            if f.startswith("Textures") and f.endswith(".db"):
                p = os.path.join(local_db_dir, f)
                try:
                    os.remove(p)
                    log_utils.write_log(f"[textures-db] Eliminado {f}")
                except Exception as e:
                    log_utils.write_log(f"[textures-db] No se pudo eliminar {f}: {e}", "WARNING")
    except Exception as e:
        log_utils.write_log(f"[textures-db] Error listando Textures*.db: {e}", "WARNING")


def _remove_thumbnails_dir():
    thumbs_dir = _thumbnails_dir_os()
    try:
        if os.path.exists(thumbs_dir):
            shutil.rmtree(thumbs_dir, ignore_errors=True)
            log_utils.write_log(f"[thumbs] Eliminada carpeta de thumbnails: {thumbs_dir}")
    except Exception as e:
        log_utils.write_log(f"[thumbs] No se pudo eliminar {thumbs_dir}: {e}", "WARNING")


# ---------- Progreso “pro” ----------
def _dp_update_safe(dp: xbmcgui.DialogProgress, pct: int, line1: str, line2: str = ""):
    try:
        if line2:
            dp.update(int(pct), f"{line1}\n{line2}")
        else:
            dp.update(int(pct), str(line1))
    except Exception:
        pass


def _copy_file_with_progress(src: str, dst: str, dp: xbmcgui.DialogProgress, pct_from: int, pct_to: int, label: str) -> bool:
    """
    Copia real por bytes: progreso estable y sin saltos.
    Respeta Cancelar (dp.iscanceled()).
    """
    try:
        total = os.path.getsize(src)
    except Exception:
        total = 0

    read_bytes = 0
    chunk = 256 * 1024

    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
    except Exception:
        pass

    try:
        with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
            while True:
                if dp.iscanceled():
                    return False
                b = fsrc.read(chunk)
                if not b:
                    break
                fdst.write(b)
                read_bytes += len(b)

                if total > 0:
                    frac = min(1.0, read_bytes / float(total))
                    pct = pct_from + int(frac * (pct_to - pct_from))
                else:
                    # sin tamaño -> avance suave
                    pct = min(pct_to - 1, pct_from + int(read_bytes / (2 * 1024 * 1024)))

                _dp_update_safe(dp, max(pct_from, min(pct, pct_to - 1)), label, os.path.basename(dst))

        try:
            fdst.flush()
        except Exception:
            pass

        _dp_update_safe(dp, pct_to, label, "OK")
        return True
    except Exception as e:
        log_utils.write_log(f"[copy] Error copiando {src} -> {dst}: {e}", "ERROR")
        return False


def _smooth_progress_block(dp: xbmcgui.DialogProgress, pct_from: int, pct_to: int, label: str, seconds: float = 1.2) -> bool:
    """
    Avance suave durante tareas sin “progreso real” (rmtree/textures).
    Si la tarea acaba antes, este bloque puede ser muy corto (seconds pequeño).
    """
    start = time.time()
    last = pct_from
    while True:
        if dp.iscanceled():
            return False
        elapsed = time.time() - start
        if elapsed >= seconds:
            break
        frac = elapsed / max(0.001, seconds)
        pct = pct_from + int(frac * (pct_to - pct_from))
        pct = max(last, min(pct, pct_to))
        last = pct
        _dp_update_safe(dp, pct, label)
        xbmc.sleep(120)
    _dp_update_safe(dp, pct_to, label)
    return True


# ---------- Pickers MyVideos ----------
def _pick_latest_myvideos(db_dir: str):
    try:
        files = [f for f in os.listdir(db_dir) if f.startswith("MyVideos") and f.endswith(".db")]
    except Exception as e:
        log_utils.write_log(f"[videos-db] Error listando {db_dir}: {e}", "ERROR")
        return None, None
    if not files:
        return None, None

    def vernum(name: str) -> int:
        m = re.search(r"(\d+)\.db$", name)
        return int(m.group(1)) if m else -1

    latest = max(files, key=vernum)
    return latest, os.path.join(db_dir, latest)


# ---------- Validaciones DB ----------
def _validate_db_ro(db_path: str) -> bool:
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        return False
    try:
        uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(path)")
        cols = [c[1] for c in cur.fetchall()]
        cur.close()
        conn.close()
        return all(c in cols for c in ("strPath", "strContent", "strScraper"))
    except Exception:
        return False


def _db_ok_ro(db_path: str) -> bool:
    REQUIRED_CONDITIONS = _get_required_conditions()

    try:
        uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2)
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(path)")
        cols = [row[1] for row in cur.fetchall()]
        for col in ("strPath", "strContent", "strScraper"):
            if col not in cols:
                log_utils.write_log(f"[videos-db] Falta columna '{col}' en 'path'", "ERROR")
                cur.close()
                conn.close()
                return False

        all_ok = True
        for strPath, strContent, strScraper in REQUIRED_CONDITIONS:
            cur.execute(
                "SELECT 1 FROM path WHERE strPath=? AND strContent=? AND strScraper=? LIMIT 1",
                (strPath, strContent, strScraper)
            )
            if not cur.fetchone():
                log_utils.write_log(
                    f"[videos-db] FALTA: {strPath} content='{strContent}' scraper='{strScraper}'",
                    "WARNING"
                )
                all_ok = False

        cur.close()
        conn.close()
        return all_ok
    except Exception as e:
        log_utils.write_log(f"[videos-db] Error verificando DB: {e}\n{traceback.format_exc()}", "ERROR")
        return False


# ---------- Versión esperada ----------
def _expected_videos_num_for_kodi() -> int | None:
    info = jsonrpc_utils.get_kodi_version() or {}
    major = info.get("major")
    if major is None:
        return None

    mapping = {19: 119, 20: 121, 21: 131}
    if major in mapping:
        return mapping[major]

    lower = [v for k, v in mapping.items() if k <= major]
    if lower:
        return max(lower)
    return max(mapping.values())


# ---------- Instalación desde staging (solo MyVideos, swap atómico) ----------
def _install_myvideos_from_staging(
    staging_dir: str,
    local_db_dir: str,
    dp: xbmcgui.DialogProgress,
    pct_copy_from: int = 80,
    pct_copy_to: int = 93,
    pct_clean_from: int = 93,
    pct_clean_to: int = 99,
) -> bool:
    os.makedirs(local_db_dir, exist_ok=True)
    db_src_dir = os.path.join(staging_dir, "Database")

    expected_v = _expected_videos_num_for_kodi()
    if expected_v is None:
        log_utils.write_log("[videos-db] No se pudo determinar MyVideos esperado para esta versión de Kodi.", "ERROR")
        return False

    mv_name = f"MyVideos{expected_v}.db"
    mv_src = os.path.join(db_src_dir, mv_name)
    mv_dst = os.path.join(local_db_dir, mv_name)
    tmp_dst = mv_dst + ".tmp"

    if not os.path.exists(mv_src) or os.path.getsize(mv_src) <= 0:
        log_utils.write_log(f"[videos-db] No existe en staging: {mv_src}", "ERROR")
        return False

    # 1) Validar staging ANTES de tocar nada local
    if not _validate_db_ro(mv_src):
        log_utils.write_log("[videos-db] MyVideos en staging es inválida; no se tocan cachés locales.", "ERROR")
        return False

    # 2) Copiar a .tmp con progreso real
    try:
        if os.path.exists(tmp_dst):
            os.remove(tmp_dst)
    except Exception:
        pass

    _dp_update_safe(dp, pct_copy_from, "Copiando MyVideos a destino temporal…", mv_name)
    ok_copy = _copy_file_with_progress(mv_src, tmp_dst, dp, pct_copy_from, pct_copy_to, "Copiando MyVideos…")
    if not ok_copy:
        try:
            if os.path.exists(tmp_dst):
                os.remove(tmp_dst)
        except Exception:
            pass
        return False

    if not _validate_db_ro(tmp_dst):
        log_utils.write_log("[videos-db] DB tmp inválida; no se hace swap.", "ERROR")
        try:
            os.remove(tmp_dst)
        except Exception:
            pass
        return False

    # 3) Borrar caches locales con progreso “suave”
    _dp_update_safe(dp, pct_clean_from, "Eliminando cachés (Textures/Thumbnails)…")
    # Textures suele ser rápido
    _smooth_progress_block(dp, pct_clean_from, min(pct_clean_from + 2, pct_clean_to), "Eliminando Textures*.db…", seconds=0.6)
    _remove_textures_dbs(local_db_dir)

    # Thumbnails puede ser largo: damos más recorrido de progreso “visual”
    _smooth_progress_block(dp, min(pct_clean_from + 2, pct_clean_to), pct_clean_to, "Eliminando Thumbnails…", seconds=1.8)
    _remove_thumbnails_dir()

    # 4) Swap atómico al final (muy rápido)
    _dp_update_safe(dp, 99, "Aplicando swap atómico de la base de datos…")
    try:
        os.replace(tmp_dst, mv_dst)
    except Exception as e:
        log_utils.write_log(f"[videos-db] Error en swap atómico {tmp_dst} -> {mv_dst}: {e}", "ERROR")
        try:
            if os.path.exists(tmp_dst):
                os.remove(tmp_dst)
        except Exception:
            pass
        return False

    # 5) Validación final
    if not _validate_db_ro(mv_dst):
        log_utils.write_log("[videos-db] DB tras swap inválida (muy raro).", "ERROR")
        return False

    try:
        xbmc.sleep(200)
        if hasattr(os, "sync"):
            os.sync()
    except Exception:
        pass

    return True


# ---------- Descarga a staging con progreso ----------
def _download_url_to_file(
    url: str,
    dst_path: str,
    dp: xbmcgui.DialogProgress,
    pct_from: int,
    pct_to: int,
    label: str
) -> bool:
    try:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    except Exception:
        pass

    tmp_path = dst_path + ".part"
    try:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    except Exception:
        pass

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KodiELEC/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            total = r.headers.get("Content-Length")
            total = int(total) if total and total.isdigit() else None

            read_bytes = 0
            chunk = 256 * 1024

            with open(tmp_path, "wb") as f:
                while True:
                    if dp.iscanceled():
                        return False
                    data = r.read(chunk)
                    if not data:
                        break
                    f.write(data)
                    read_bytes += len(data)

                    if total:
                        frac = min(1.0, read_bytes / float(total))
                        pct = pct_from + int(frac * (pct_to - pct_from))
                    else:
                        pct = min(pct_to - 1, pct_from + int(read_bytes / (2 * 1024 * 1024)))

                    _dp_update_safe(dp, max(pct_from, min(pct_to, pct)), label, os.path.basename(dst_path))

        os.replace(tmp_path, dst_path)
        return True

    except Exception as e:
        log_utils.write_log(f"[sync-url] Error descargando {url} -> {dst_path}: {e}", "ERROR")
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False


def _sync_selected_to_tmp_with_progress(dp: xbmcgui.DialogProgress) -> str | None:
    base_tmp = "/tmp"
    staging = os.path.join(base_tmp, "staging_userdata")

    try:
        if os.path.exists(staging):
            shutil.rmtree(staging, ignore_errors=True)
        os.makedirs(staging, exist_ok=True)
    except Exception as e:
        log_utils.write_log(f"[sync] No se pudo preparar staging {staging}: {e}", "ERROR")
        return None

    v = _expected_videos_num_for_kodi()
    if v is None:
        log_utils.write_log("[sync] No se pudo determinar el MyVideos esperado para esta versión de Kodi.", "ERROR")
        return None

    base_url = _get_db_base_url().rstrip("/")
    mv_name = f"MyVideos{v}.db"
    url = f"{base_url}/{mv_name}"
    dst = os.path.join(staging, "Database", mv_name)

    if dp.iscanceled():
        return None

    ok = _download_url_to_file(
        url=url,
        dst_path=dst,
        dp=dp,
        pct_from=5,
        pct_to=80,
        label="Descargando MyVideos (GitHub RAW)…",
    )
    return staging if ok else None


# ---------- Flujo principal con barra de progreso ----------
def _do_update_with_progress(local_db_dir: str) -> bool:
    dp = xbmcgui.DialogProgress()
    dp.create("Actualizando biblioteca", "Preparando…")
    dp.update(0)

    canceled = False
    success = False
    staging = None

    try:
        if dp.iscanceled():
            canceled = True
            return False

        _dp_update_safe(dp, 5, "Descargando MyVideos al almacenamiento temporal…")
        staging = _sync_selected_to_tmp_with_progress(dp)
        if dp.iscanceled():
            canceled = True
            return False
        if not staging:
            _dp_update_safe(dp, 100, "Error en la sincronización.")
            return False

        _dp_update_safe(dp, 80, "Instalando MyVideos y limpiando cachés…")
        ok_mv = _install_myvideos_from_staging(
            staging_dir=staging,
            local_db_dir=local_db_dir,
            dp=dp,
            pct_copy_from=80,
            pct_copy_to=93,
            pct_clean_from=93,
            pct_clean_to=99,
        )
        if dp.iscanceled():
            canceled = True
            return False
        if not ok_mv:
            _dp_update_safe(dp, 100, "Error instalando MyVideos.")
            return False

        # 100% SOLO al final real
        _dp_update_safe(dp, 100, "Base de datos instalada y cachés eliminadas.")
        success = True
        return True

    finally:
        try:
            dp.close()
        except Exception:
            pass

        if staging:
            _cleanup_dir(staging)

        if canceled:
            try:
                log_utils.notify("Actualización cancelada", xbmcgui.NOTIFICATION_WARNING)
            except Exception:
                pass
            log_utils.write_log("Actualización de biblioteca CANCELADA por el usuario.")
        elif success:
            try:
                log_utils.notify("Biblioteca actualizada", xbmcgui.NOTIFICATION_INFO)
            except Exception:
                pass


# ---------- Flujo principal ----------
def update_library():
    start_ts = time.time()
    _wait_until_ready(10)

    try:
        _disable_libraryautoupdate_if_enabled()
    except Exception:
        log_utils.write_log("No se pudo deshabilitar 'service.libraryautoupdate'.", level="WARNING")

    try:
        fix_guisettings.fix_cache()
    except Exception:
        log_utils.write_log("fix_guisettings.fix_cache() falló (se continúa).", level="WARNING")

    local_db_dir = _database_dir_os()
    latest_name, latest_path = _pick_latest_myvideos(local_db_dir)

    if not latest_name:
        log_utils.write_log("[videos-db] No hay MyVideos*.db local. Iniciando instalación con progreso…")
        try:
            log_utils.notify("Instalando base de datos de la biblioteca…", xbmcgui.NOTIFICATION_INFO)
        except Exception:
            pass

        completed = _do_update_with_progress(local_db_dir=local_db_dir)
        if completed:
            log_utils.write_log("Biblioteca instalada/actualizada correctamente. Reiniciando Kodi…")
            try:
                utils.restart_kodi_with_popup(delay_ms=3000)
            except Exception:
                pass
        return

    if not _db_ok_ro(latest_path):
        log_utils.write_log(f"[videos-db] {latest_name} no cumple. Iniciando reparación con progreso…")
        try:
            log_utils.notify("Reparando base de datos de la biblioteca…", xbmcgui.NOTIFICATION_INFO)
        except Exception:
            pass

        completed = _do_update_with_progress(local_db_dir=local_db_dir)
        if completed:
            log_utils.write_log("Biblioteca reparada/actualizada correctamente. Reiniciando Kodi…")
            try:
                utils.restart_kodi_with_popup(delay_ms=3000)
            except Exception:
                pass
        return

    log_utils.write_log(f"[videos-db] {latest_name} cumple las condiciones. No se hace nada.")

