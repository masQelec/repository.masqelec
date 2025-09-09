# -*- coding: utf-8 -*-
"""
update_library.py — Verificación y reemplazo seguro de MyVideos con CleanLibrary
y sincronización coordinada de Textures y Thumbnails cuando MyVideos cambia, usando
descarga selectiva a un directorio temporal (RAM si es posible) con progreso
optimizado para Google Drive.

- Ajusta 'videolibrary.moviesetsfolder' (JSON-RPC).
- Verifica MyVideos*.db (SQLite RO).
- Si falta o está mal:
  * Descarga masqelec:masqelec/userdata -> TMP (solo MyVideosNN, TexturesNN y Thumbnails.zip) con progreso.
  * Valida e instala MyVideos adecuado (sin backup).
  * Instala también Textures correspondiente a la versión de Kodi (best-effort).
  * Aplica Thumbnails.zip al directorio de thumbnails (reemplaza y elimina sobrantes).
  * Lanza CleanLibrary y UpdateLibrary (JSON-RPC) tras cerrar el diálogo.
  * 🧹 Limpia staging en todos los casos (finally) para liberar RAM.

Además:
- Deshabilita 'service.libraryautoupdate' si está habilitado (evita conflictos).
- Notificación previa si se realizará actualización/reparación.
- Diálogo con barra de progreso y opción de cancelar (cancelable entre fases).
- Progreso estable por “pesos” de ficheros (Google Drive-friendly).
- Notificación final tanto si se completa como si se cancela.
"""

import os
import re
import time
import sqlite3
import traceback
import zipfile
import shutil
import json

import xbmc
import xbmcvfs
import xbmcgui

from lib import log_utils
from lib import utils
from lib import jsonrpc_utils
from lib import rclone_utils
from lib import fix_guisettings

# ---------- Config ----------
RCLONE_REMOTE = "masqelec"
REMOTE_USERDATA = "masqelec/userdata"   # carpeta a sincronizar (origen)

# Pesos relativos por fichero para una barra estable (evita saltos con Drive)
# Se reparten 100 puntos internos en fase de “staging”; luego se mapearán a 5..55 de la UI.
WEIGHTS = {
    "myvideos": 15.0,   # MyVideosNN.db
    "textures": 5.0,   # TexturesNN.db
    "thumbs":   80.0,   # Thumbnails.zip
}

REQUIRED_CONDITIONS = [
    ("/storage/videos/1/",  "movies",  "metadata.themoviedb.org.python"),
    ("/storage/videos/2/",  "movies",  "metadata.themoviedb.org.python"),
    ("/storage/tvshows/1/", "tvshows", "metadata.tvshows.themoviedb.org.python"),
    ("/storage/tvshows/2/", "tvshows", "metadata.tvshows.themoviedb.org.python"),
]

# ---------- JSON-RPC helpers (compatibles) ----------
def _jsonrpc_call_soft(method: str, params: dict | None = None):
    """
    Llamada JSON-RPC sin excepciones:
      -> (ok: bool, result: Any | None, error: dict | None)
    """
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
    """Detalles mínimos del add-on (enabled, name si está soportado)."""
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
    """Intenta Addons.SetAddonEnabled; si falla, usa builtins y verifica."""
    ok, _, _ = _jsonrpc_call_soft("Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": enabled})
    if ok:
        state = _get_addon_enabled_state(addon_id)
        if state is not None and state == enabled:
            return True

    # Fallback builtins
    try:
        xbmc.executebuiltin(f'{"EnableAddon" if enabled else "DisableAddon"}("{addon_id}")')
        xbmc.sleep(900)
        state = _get_addon_enabled_state(addon_id)
        return state is not None and state == enabled
    except Exception:
        return False

def _disable_libraryautoupdate_if_enabled():
    """Deshabilita 'service.libraryautoupdate' si está habilitado para evitar conflictos."""
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

def _wait_for_scan_idle(max_wait_s=30):
    """Espera a que NO haya escaneo activo (hasta max_wait_s)."""
    start = time.time()
    mon = xbmc.Monitor()
    while time.time() - start < max_wait_s and not mon.abortRequested():
        try:
            if not xbmc.getCondVisibility('Library.IsScanningVideo'):
                return True
        except Exception:
            pass
        mon.waitForAbort(0.25)
    return not xbmc.getCondVisibility('Library.IsScanningVideo')

def _wait_for_scan_complete(max_wait_s=3600):
    """Espera a que cualquier escaneo que se dispare termine (hasta max_wait_s)."""
    start = time.time()
    mon = xbmc.Monitor()
    was_scanning = False
    while time.time() - start < max_wait_s and not mon.abortRequested():
        try:
            scanning = xbmc.getCondVisibility('Library.IsScanningVideo')
            if scanning:
                was_scanning = True
            elif was_scanning:
                # Se activó y ya terminó
                return True
        except Exception:
            pass
        mon.waitForAbort(0.5)
    # Si nunca se activó, igualmente consideramos OK para no bloquear
    return True

def _run_clean_update_safely():
    """
    Ejecuta Clean y Update vía JSON-RPC, sin diálogos, esperando a que terminen
    (si es que se activan) y dando un pequeño respiro a la UI antes de arrancar.
    """
    try:
        xbmc.sleep(500)  # respiro tras E/S pesada
        _wait_for_scan_idle(20)

        # Clean (sin diálogos)
        _jsonrpc_call_soft("VideoLibrary.Clean", {"showdialogs": True})

        # Update/Scan
        _jsonrpc_call_soft("VideoLibrary.Scan", {})
    except Exception as e:
        log_utils.write_log(f"Error en _run_clean_update_safely: {e}\n{traceback.format_exc()}", "ERROR")

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
    """Elimina un directorio de forma recursiva, sin romper el flujo."""
    try:
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
            log_utils.write_log(f"[cleanup] Eliminado staging temporal: {path}")
    except Exception as e:
        log_utils.write_log(f"[cleanup] Error al eliminar {path}: {e}", "ERROR")

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
def _db_ok_ro(db_path: str) -> bool:
    try:
        uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(path)")
        cols = [row[1] for row in cur.fetchall()]
        for col in ("strPath", "strContent", "strScraper"):
            if col not in cols:
                log_utils.write_log(f"[videos-db] Falta columna '{col}' en 'path'", "ERROR")
                cur.close(); conn.close()
                return False
        all_ok = True
        for strPath, strContent, strScraper in REQUIRED_CONDITIONS:
            cur.execute(
                "SELECT 1 FROM path WHERE strPath=? AND strContent=? AND strScraper=? LIMIT 1",
                (strPath, strContent, strScraper)
            )
            if not cur.fetchone():
                log_utils.write_log(f"[videos-db] FALTA: {strPath} content='{strContent}' scraper='{strScraper}'", "WARNING")
                all_ok = False
        cur.close(); conn.close()
        return all_ok
    except Exception as e:
        log_utils.write_log(f"[videos-db] Error verificando DB: {e}\n{traceback.format_exc()}", "ERROR")
        return False

def _validate_db_ro(db_path: str) -> bool:
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        return False
    try:
        uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(path)")
        cols = [c[1] for c in cur.fetchall()]
        cur.close(); conn.close()
        return all(c in cols for c in ("strPath", "strContent", "strScraper"))
    except Exception:
        return False

def _textures_db_ok_ro(db_path: str) -> bool:
    try:
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            return False
        uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(texture)")
        cols = [row[1] for row in cur.fetchall()]
        cur.close(); conn.close()
        return ("url" in cols) and ("cachedurl" in cols)
    except Exception:
        return False

# ---------- Versiones esperadas ----------
def _expected_videos_num_for_kodi() -> int | None:
    """
    v19 (Matrix) -> 119
    v20 (Nexus)  -> 121
    v21 (Omega)  -> 131
    """
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

def _expected_textures_num_for_kodi() -> int | None:
    info = jsonrpc_utils.get_kodi_version() or {}
    major = info.get("major")
    if major is None:
        return None
    mapping = {19: 13, 20: 13, 21: 13}
    if major in mapping:
        return mapping[major]
    lower = [v for k, v in mapping.items() if k <= major]
    if lower:
        return max(lower)
    return max(mapping.values())

# ---------- Instalación desde staging ----------
def _install_myvideos_and_textures_from_staging(staging_dir: str, local_db_dir: str) -> bool:
    """
    Copia desde staging los ficheros MyVideosNN.db (obligatorio) y TexturesNN.db (best-effort).
    Valida que las DB sean “RO OK” antes de dejarlas instaladas.
    """
    os.makedirs(local_db_dir, exist_ok=True)
    db_src_dir = os.path.join(staging_dir, "Database")

    # MyVideos
    expected_v = _expected_videos_num_for_kodi()
    if expected_v is None:
        log_utils.write_log("[videos-db] No se pudo determinar MyVideos esperado para esta versión de Kodi.", "ERROR")
        return False
    mv_name = f"MyVideos{expected_v}.db"
    mv_src = os.path.join(db_src_dir, mv_name)
    mv_dst = os.path.join(local_db_dir, mv_name)

    if not os.path.exists(mv_src) or os.path.getsize(mv_src) <= 0:
        log_utils.write_log(f"[videos-db] No existe en staging: {mv_src}", "ERROR")
        return False

    try:
        shutil.copy2(mv_src, mv_dst)
    except Exception as e:
        log_utils.write_log(f"[videos-db] Error copiando {mv_src} -> {mv_dst}: {e}", "ERROR")
        return False

    if not _validate_db_ro(mv_dst):
        log_utils.write_log("[videos-db] DB copiada pero inválida; eliminando.", "ERROR")
        try: os.remove(mv_dst)
        except Exception: pass
        return False

    # (opcional) pequeño respiro + flush para sistemas embebidos
    try:
        xbmc.sleep(200)
        if hasattr(os, "sync"):
            os.sync()
    except Exception:
        pass

    # Textures (best-effort)
    expected_t = _expected_textures_num_for_kodi()
    if expected_t is not None:
        tx_name = f"Textures{expected_t}.db"
        tx_src = os.path.join(db_src_dir, tx_name)
        tx_dst = os.path.join(local_db_dir, tx_name)
        if os.path.exists(tx_src) and os.path.getsize(tx_src) > 0:
            try:
                shutil.copy2(tx_src, tx_dst)
                if not _textures_db_ok_ro(tx_dst):
                    log_utils.write_log("[textures-db] DB de Textures copiada pero inválida; eliminando.", "ERROR")
                    try: os.remove(tx_dst)
                    except Exception: pass
                else:
                    log_utils.write_log(f"[textures-db] Instalado {tx_name}")
            except Exception as e:
                log_utils.write_log(f"[textures-db] Error copiando {tx_src} -> {tx_dst}: {e}", "ERROR")
        else:
            log_utils.write_log(f"[textures-db] No se encontró {tx_name} en staging (continuando)")

    return True

# ---------- Progreso con opción de cancelar ----------
def _apply_thumbnails_zip_from_staging(staging_dir: str, progress_cb=None, canceled_cb=None):
    """
    Extrae Thumbnails.zip con progreso granular y limpia sobrantes también con progreso.
    - progress_cb(pct: 0..100, msg: str)
    - canceled_cb() -> bool
    """
    if progress_cb is None:
        progress_cb = lambda pct, msg="": None
    if canceled_cb is None:
        canceled_cb = lambda: False

    thumbs_dir = _thumbnails_dir_os()
    os.makedirs(thumbs_dir, exist_ok=True)

    zip_path = os.path.join(staging_dir, "Thumbnails.zip")
    if not (os.path.exists(zip_path) and os.path.getsize(zip_path) > 0):
        log_utils.write_log("[thumbs] No hay Thumbnails.zip en staging (saltando)")
        return

    # 1) Leer y extraer ZIP con progreso
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = [m for m in zf.namelist() if not m.endswith("/")]
            total = max(len(members), 1)
            zip_set = set(os.path.normpath(m) for m in members)

            progress_cb(0, "Extrayendo Thumbnails…")
            for i, m in enumerate(members, start=1):
                if canceled_cb():
                    log_utils.write_log("[thumbs] Cancelado durante la extracción.")
                    return
                try:
                    zf.extract(m, thumbs_dir)
                except Exception:
                    log_utils.write_log(f"[thumbs] Error extrayendo {m}", "WARNING")
                if i % 50 == 0 or i == total:
                    pct = int((i / float(total)) * 60)  # 0..60% de esta fase
                    progress_cb(pct, f"Extrayendo Thumbnails… ({i}/{total})")
    except Exception as e:
        log_utils.write_log(f"[thumbs] Error leyendo/descomprimiendo ZIP: {e}", "ERROR")
        return
    finally:
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass

    # 2) Eliminar lo que no esté en el ZIP con progreso
    try:
        # Construir set actual
        current_set = set()
        for root, _, files in os.walk(thumbs_dir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), thumbs_dir)
                current_set.add(os.path.normpath(rel))

        to_delete = list(current_set - zip_set)
        total_del = len(to_delete)
        progress_cb(70, "Limpiando archivos no incluidos en Thumbnails.zip…")
        if total_del > 0:
            for j, rel in enumerate(to_delete, start=1):
                if canceled_cb():
                    log_utils.write_log("[thumbs] Cancelado durante limpieza de sobrantes.")
                    return
                try:
                    os.remove(os.path.join(thumbs_dir, rel))
                except Exception:
                    pass
                if j % 100 == 0 or j == total_del:
                    pct = 70 + int((j / float(total_del)) * 25)  # 70..95
                    progress_cb(pct, f"Limpieza… ({j}/{total_del})")

        # 3) Limpiar dirs vacíos (sin progreso fino)
        for root, dirs, files in os.walk(thumbs_dir, topdown=False):
            if not dirs and not files:
                try:
                    os.rmdir(root)
                except Exception:
                    pass

        progress_cb(100, "Thumbnails aplicados.")
        log_utils.write_log("[thumbs] Sincronización de thumbnails completada.")
    except Exception as e:
        log_utils.write_log(f"[thumbs] Error durante limpieza de sobrantes: {e}", "ERROR")

# ---------- Sincronización a TMP con progreso ----------
def _sync_selected_to_tmp_with_progress(dp: xbmcgui.DialogProgress) -> str | None:
    """
    Descarga explícitamente a STAGING (copyto) con progreso estable por “pesos”:
    - Database/MyVideosNN.db  (peso 20)
    - Database/TexturesNN.db  (peso 10, opcional)
    - Thumbnails.zip          (peso 70, opcional)
    """
    base_tmp = "/tmp"
    staging = os.path.join(base_tmp, "staging_userdata")
    try:
        if os.path.exists(staging):
            try: shutil.rmtree(staging)
            except Exception: pass
        os.makedirs(staging, exist_ok=True)
    except Exception as e:
        log_utils.write_log(f"[sync] No se pudo preparar staging {staging}: {e}", "ERROR")
        return None

    v = _expected_videos_num_for_kodi()
    t = _expected_textures_num_for_kodi()
    if v is None:
        log_utils.write_log("[sync] No se pudo determinar el MyVideos esperado para esta versión de Kodi.", "ERROR")
        return None

    rel_files = [f"Database/MyVideos{v}.db", "Thumbnails.zip"]
    if t is not None:
        rel_files.insert(1, f"Database/Textures{t}.db")  # MyVideos -> Textures -> Thumbnails

    # Construye plan de pesos por archivo
    def _file_weight(rel: str) -> float:
        r = rel.lower()
        if r.endswith("/thumbnails.zip") or r == "thumbnails.zip":
            return WEIGHTS["thumbs"]
        if "/textures" in r:
            return WEIGHTS["textures"]
        if "/myvideos" in r:
            return WEIGHTS["myvideos"]
        return 0.0

    plan = [(rp, _file_weight(rp)) for rp in rel_files]
    total_w = sum(w for _, w in plan) or 100.0

    # Estado de progreso acumulado por pesos
    acc_weight_done = 0.0

    def on_progress_file(rel: str, pct_file: float, msg: str = ""):
        # pct_file: 0..100 % dentro del fichero
        nonlocal acc_weight_done
        weight = _file_weight(rel)
        partial = (acc_weight_done + (weight * max(0.0, min(100.0, pct_file)) / 100.0))
        pct_staging = (partial * 100.0) / total_w  # 0..100
        pct_ui = 5 + int((pct_staging / 100.0) * 50)  # mapea a 5..55
        try:
            dp.update(min(55, max(5, pct_ui)), msg or f"Descargando {os.path.basename(rel)}…")
        except Exception:
            pass

    def on_file_done(rel: str):
        nonlocal acc_weight_done
        acc_weight_done += _file_weight(rel)

    def is_canceled() -> bool:
        try:
            return dp.iscanceled()
        except Exception:
            return False

    ok = rclone_utils.copy_selected_remote_files_with_progress(
        remote=RCLONE_REMOTE,
        remote_dir=REMOTE_USERDATA,
        rel_paths=rel_files,
        staging_dir=staging,
        on_progress_per_file=on_progress_file,
        on_file_done=on_file_done,
        is_canceled=is_canceled,
    )
    if not ok:
        return None
    return staging


# ---------- Flujo principal con barra de progreso ----------
def _do_update_with_progress(local_db_dir: str) -> bool:
    """
    1) staging (descarga selectiva) con progreso estable 5→55%
    2) instalación DBs (60%)
    3) thumbnails con progreso granular (85→95%)
    4) Clean/Update (tras cerrar el diálogo)
    Devuelve True si completó; False si se canceló o falló.
    """
    dp = xbmcgui.DialogProgress()
    dp.create("Actualizando biblioteca", "Preparando…")
    dp.update(0)

    canceled = False
    staging = None
    try:
        if dp.iscanceled():
            return False

        # Fase 1: staging con progreso por pesos
        dp.update(5, "Sincronizando datos al almacenamiento temporal…")
        staging = _sync_selected_to_tmp_with_progress(dp)
        if dp.iscanceled():
            canceled = True
            return False
        if not staging:
            dp.update(100, "Error en la sincronización.")
            return False

        # Fase 2: Instalar DBs
        dp.update(60, "Instalando bases de datos (MyVideos/Textures)…")
        ok_mv = _install_myvideos_and_textures_from_staging(staging, local_db_dir)
        if dp.iscanceled():
            canceled = True
            return False
        if not ok_mv:
            dp.update(100, "Error instalando bases de datos.")
            return False

        # Fase 3: Thumbnails (85 → 95 con progreso granular)
        def thumbs_progress(pct_step: float, msg: str = ""):
            pct = 85 + int((pct_step / 100.0) * 10)
            try:
                dp.update(min(max(pct, 85), 95), msg or "Aplicando Thumbnails…")
            except Exception:
                pass

        if dp.iscanceled():
            canceled = True
            return False
        _apply_thumbnails_zip_from_staging(staging, progress_cb=thumbs_progress, canceled_cb=dp.iscanceled)
        if dp.iscanceled():
            canceled = True
            return False

        # Fase 4: sólo marcar completado visualmente aquí (Clean/Update irá tras cerrar el diálogo)
        dp.update(100, "Preparando limpieza/actualización…")
        return True

    finally:
        try:
            dp.close()
        except Exception:
            pass

        # 🧹 Limpieza de staging SIEMPRE
        if staging:
            _cleanup_dir(staging)

        if canceled:
            try:
                log_utils.notify("Actualización cancelada", xbmcgui.NOTIFICATION_WARNING)
            except Exception:
                pass
            log_utils.write_log("Actualización de biblioteca CANCELADA por el usuario.")
        else:
            #Ejecutar Clean/Update con la UI libre (sin diálogo en primer plano)
            _run_clean_update_safely()
            try:
                log_utils.notify("Biblioteca limpiada y actualizada", xbmcgui.NOTIFICATION_INFO)
            except Exception:
                pass

# ---------- Flujo principal ----------
def update_library():
    """
    1) Espera entorno estable.
    2) Deshabilita 'service.libraryautoupdate' si está habilitado (evita conflictos).
    3) Corrige carpeta de sets.
    4) Verifica MyVideos; si falta o está mal:
        a) descarga selectiva con progreso a STAGING TMP
        b) Instalar MyVideos y Textures desde staging (validando).
        c) Aplicar Thumbnails.zip desde staging (extraer + limpiar sobrantes).
        d) CleanLibrary + UpdateLibrary (JSON-RPC) tras cerrar diálogo.
        e) 🧹 Borrar staging en cualquier caso (finally).
    """
    _wait_until_ready(10)

    # (2) evitar conflictos con auto-update de biblioteca
    try:
        _disable_libraryautoupdate_if_enabled()
    except Exception:
        log_utils.write_log("No se pudo deshabilitar 'service.libraryautoupdate'.", level="WARNING")

    # (3) corregir ajuste de sets
    fix_guisettings.fix_movieset_folder()
    fix_guisettings.fix_cache()
    
    local_db_dir = _database_dir_os()
    latest_name, latest_path = _pick_latest_myvideos(local_db_dir)

    # Caso: no hay DB local → actualización completa con progreso
    if not latest_name:
        log_utils.write_log("[videos-db] No hay MyVideos*.db local. Iniciando actualización con progreso…")
        try:
            log_utils.notify("Instalando base de datos de la biblioteca…", xbmcgui.NOTIFICATION_INFO)
        except Exception:
            pass

        completed = _do_update_with_progress(local_db_dir=local_db_dir)
        if completed:
            log_utils.write_log("Biblioteca instalada y actualizada correctamente.")
        return

    # Caso: hay DB local pero no cumple → actualización con progreso
    if not _db_ok_ro(latest_path):
        log_utils.write_log(f"[videos-db] {latest_name} no cumple. Iniciando actualización con progreso…")
        try:
            log_utils.notify("Reparando base de datos de la biblioteca…", xbmcgui.NOTIFICATION_INFO)
        except Exception:
            pass

        completed = _do_update_with_progress(local_db_dir=local_db_dir)
        if completed:
            log_utils.write_log("Biblioteca reparada y actualizada correctamente.")
        return

    # Caso: DB local válida
    log_utils.write_log(f"[videos-db] {latest_name} cumple las condiciones. No se hace nada.")
