# -*- coding: utf-8 -*-
"""
update.py — Comprobación y aplicación de actualización de sistema
- Lee versión local y remota (VERSION/VERSION_ID) y compara correctamente
- Usa rclone_utils para sincronizar artefactos de forma robusta (sync selectivo a staging en RAM)
- Descarga temporal en RAM (/dev/shm) y movimiento a /storage/.update
- Manejo de cuota de Google Drive (no bloquea lsjson por rate limit)
- Diálogo al usuario y reinicio seguro
"""

import os
import re
import time
import urllib.request
import urllib.error
import shutil
import xbmc
import xbmcgui
import traceback

from lib import log_utils
from lib import utils
from lib import rclone_utils as rc

# ------------------------------
# CONFIG RED (para control remoto de versión)
# ------------------------------

NET_TIMEOUT = 20
NET_RETRIES = 2
UA = "masQelec/1.0 (+Kodi)"

REMOTE_UPDATE_REMOTE = "masqelec"
REMOTE_UPDATE_DIR    = "masqelec/update"   # carpeta remota donde están los paquetes

def _net_open(url: str, timeout: int = NET_TIMEOUT):
    """Abre una URL con UA y reintentos básicos."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last_err = None
    for attempt in range(NET_RETRIES + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            last_err = e
            log_utils.write_log(f"[net] intento {attempt+1}/{NET_RETRIES+1} falló para {url}: {getattr(e, 'reason', e)}", "ERROR")
            time.sleep(2)
    raise last_err

def get_text_from_url(url: str):
    """Descarga el contenido de texto desde una URL, con timeout y reintentos."""
    try:
        with _net_open(url) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log(f"Error al obtener datos de la URL: {e}", "ERROR")
        return None

# ------------------------------
# PARSEO DE VERSIONES
# ------------------------------

def parse_version(v: str):
    """
    Convierte '1.2.3' en tupla comparable (1,2,3).
    Soporta '1.2', '1.2.3-beta' (ignora sufijos no numéricos).
    """
    if not v:
        return (0,)
    parts = []
    for p in re.split(r"[.\-+]", v.strip()):
        m = re.match(r"\d+", p)
        if m:
            parts.append(int(m.group(0)))
        else:
            break
    return tuple(parts) if parts else (0,)

def get_version_from_file(filename: str, identifier: str):
    """Obtiene la versión desde un archivo local buscando un identificador."""
    try:
        with open(filename, 'r', encoding="utf-8", errors="ignore") as f:
            for line in f:
                if identifier in line:
                    m = re.search(r'"([^"]+)"', line)
                    return m.group(1) if m else None
    except FileNotFoundError:
        log_utils.write_log(f"No se encontró el archivo {filename}", "ERROR")
    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log(f"Error leyendo {filename}: {e}", "ERROR")
    return None

def get_version_from_text(text: str, identifier: str):
    """Obtiene la versión desde un texto en memoria."""
    if not text:
        return None
    for line in text.splitlines():
        if identifier in line:
            m = re.search(r'"([^"]+)"', line)
            return m.group(1) if m else None
    return None

def _cleanup_dir(path: str):
    """Elimina un directorio recursivamente sin romper el flujo."""
    try:
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
            log_utils.write_log(f"[cleanup] Eliminado staging temporal: {path}")
    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log(f"[cleanup] Error al eliminar {path}: {e}", "ERROR")

def _sync_update_to_staging(version_file_base: str) -> tuple[str | None, str | None]:
    """
    Sincroniza desde el remoto SOLO el/los artefacto(s) que matcheen version_file_base.*
    a un staging temporal en RAM. Devuelve (staging_dir, local_pkg_path) o (None,None) en error.

    Se admiten extensiones habituales: .tar, .tar.gz, .tar.xz, .zip
    """
    base_tmp = "/tmp"
    staging  = os.path.join(base_tmp, "staging_update")
    try:
        if os.path.exists(staging):
            shutil.rmtree(staging, ignore_errors=True)
        os.makedirs(staging, exist_ok=True)
    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log(f"[staging] No se pudo preparar {staging}: {e}", "ERROR")
        return None, None

    # includes cerrando todo lo demás (staging minimal)
    # NOTA: usamos patrones para cubrir distintas extensiones
    includes = [
        f"/{version_file_base}.tar",
        f"/{version_file_base}.tar.*",
        f"/{version_file_base}.zip",
    ]
    log_utils.write_log(f"[sync] rclone sync selectivo {REMOTE_UPDATE_REMOTE}:{REMOTE_UPDATE_DIR} -> {staging} (includes={includes})")

    ok = rc.sync_remote_dir(
        remote=REMOTE_UPDATE_REMOTE,
        remote_dir=REMOTE_UPDATE_DIR,
        local_dir=staging,
        includes=includes,
        excludes=["**"],
        delete_excluded=True,
        dry_run=False
    )
    if not ok:
        log_utils.write_log("[sync] rclone sync selectivo de update falló", "ERROR")
        _cleanup_dir(staging)
        return None, None

    # Elegir el artefacto descargado (prioridad: .tar, .tar.gz/.tar.xz, .zip, otros)
    try:
        entries = [f for f in os.listdir(staging) if os.path.isfile(os.path.join(staging, f))]
        # Filtra por prefijo version_file_base + '.'
        candidates = [f for f in entries if f == f"{version_file_base}.tar" or f.startswith(f"{version_file_base}.")]
        if not candidates:
            log_utils.write_log(f"[sync] No se encontró artefacto para {version_file_base} en staging.", "ERROR")
            _cleanup_dir(staging)
            return None, None

        # Orden de preferencia
        pref_order = []
        if f"{version_file_base}.tar" in candidates:
            pref_order.append(f"{version_file_base}.tar")
        pref_order += sorted([c for c in candidates if c.endswith(".tar.gz") or c.endswith(".tar.xz")])
        if f"{version_file_base}.zip" in candidates:
            pref_order.append(f"{version_file_base}.zip")
        # completa con el resto (por si acaso)
        pref_order += [c for c in candidates if c not in pref_order]

        chosen = pref_order[0]
        pkg_path = os.path.join(staging, chosen)
        if not (os.path.exists(pkg_path) and os.path.getsize(pkg_path) > 0):
            log_utils.write_log(f"[sync] Artefacto no válido: {pkg_path}", "ERROR")
            _cleanup_dir(staging)
            return None, None

        log_utils.write_log(f"[sync] Artefacto listo en staging: {pkg_path}")
        return staging, pkg_path

    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log(f"[sync] Error inspeccionando staging: {e}", "ERROR")
        _cleanup_dir(staging)
        return None, None

def _place_update_package(pkg_local_path: str, target_dir: str = "/storage/.update") -> str | None:
    """
    Copia el paquete desde staging al directorio de actualización.
    Devuelve la ruta final o None si falla.
    """
    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception:
        pass

    try:
        final_path = os.path.join(target_dir, os.path.basename(pkg_local_path))
        shutil.copy2(pkg_local_path, final_path)
        if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
            log_utils.write_log(f"[update] Artefacto colocado en {final_path}")
            return final_path
        log_utils.write_log(f"[update] Copia inválida a {final_path}", "ERROR")
        return None
    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log(f"[update] Error copiando paquete a {target_dir}: {e}", "ERROR")
        return None

# ------------------------------
# ACTUALIZACIÓN DEL SISTEMA
# ------------------------------

def update_system():
    """Verifica si hay una actualización disponible e inicia el proceso."""
    monitor = xbmc.Monitor()

    # Circuit breaker (persistente): evita bucles si el remoto falla continuamente
    if not utils.cb_should_run("updater"):
        msg = "updater en cooldown por fallos repetidos; se omite este ciclo."
        if utils.cb_should_log_cooldown("updater"):
            log_utils.write_log(msg, "INFO")
        else:
            log_utils.write_log(msg, "DEBUG")
        return

    try:
        log_utils.write_log("Iniciando verificación de sistema para actualización.")

        # 1) Versión local
        local_version = get_version_from_file('/etc/os-release', 'VERSION_ID')
        if not local_version:
            log_utils.write_log("No se pudo obtener la versión local.", "WARNING")
            utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
            return

        # 2) Versión remota (fichero de control)
        url_content = get_text_from_url(
            'https://docs.google.com/uc?export=download&id=1jYfAGe_peaZJvhhTgXhDWBrQIX8yeAPv'
        )
        if not url_content:
            log_utils.write_log("No se pudo obtener la versión remota.", "WARNING")
            utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
            return

        remote_version = get_version_from_text(url_content, 'VERSION_ID')
        if not remote_version:
            log_utils.write_log("No se encontró VERSION_ID en el archivo remoto.", "WARNING")
            return

        version_file = get_version_from_text(url_content, 'VERSION')  # nombre base del paquete sin extensión
        log_utils.write_log(f"Local: {local_version} | Remota: {remote_version} | Archivo base: {version_file or 'N/D'}")

        # 3) Comparar versiones correctamente
        local_t  = parse_version(local_version)
        remote_t = parse_version(remote_version)
        log_utils.write_log(f"Comparación de versión: local={local_version} -> {local_t} | remoto={remote_version} -> {remote_t}")

        if local_t < remote_t:
            log_utils.write_log(f"Nueva actualización disponible: {remote_version} > {local_version}")

            if not version_file:
                log_utils.write_log("El archivo remoto no especifica VERSION (nombre base del paquete).", "ERROR")
                return

            # 4) Sincronizar artefacto de actualización a STAGING (selectivo) y colocarlo en /storage/.update
            staging = None
            try:
                staging, pkg_path = _sync_update_to_staging(version_file)
                if not pkg_path:
                    log_utils.write_log("No se pudo preparar el artefacto en staging.", "ERROR")
                    return

                final_pkg = _place_update_package(pkg_path, "/storage/.update")
                if not final_pkg:
                    log_utils.write_log("La colocación del archivo de actualización falló. No se mostrará el diálogo.", "ERROR")
                    return

                if monitor.abortRequested():
                    return

                dialog = xbmcgui.Dialog()
                ret = dialog.yesno(
                    "Actualización disponible",
                    f"Se encontró la versión {remote_version}.\n¿Deseas actualizar ahora o en el próximo reinicio?",
                    nolabel="Posponer",
                    yeslabel="Actualizar"
                )

                if ret:
                    try:
                        log_utils.notify("Iniciando proceso de actualización…", xbmcgui.NOTIFICATION_INFO)
                    except Exception:
                        pass
                    log_utils.write_log(f"Reiniciando para actualizar (paquete: {final_pkg})")
                    time.sleep(2)
                    try:
                        xbmc.executebuiltin("Reboot")
                    except Exception:
                        os.system('reboot')
                else:
                    try:
                        log_utils.notify("Se actualizará en el próximo reinicio.", xbmcgui.NOTIFICATION_INFO)
                    except Exception:
                        pass

            finally:
                # 🧹 Limpieza de staging en cualquier caso
                if staging:
                    _cleanup_dir(staging)

        else:
            if local_t == remote_t:
                log_utils.write_log("La versión remota es IGUAL a la local. No hay actualización.")
            else:
                log_utils.write_log("La versión remota es MENOR que la local. No hay actualización.")

    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log(f"Error en update_system: {e}\n{traceback.format_exc()}", "ERROR")
        try:
            log_utils.notify("Error en el proceso de actualización", xbmcgui.NOTIFICATION_ERROR)
        except Exception:
            pass
