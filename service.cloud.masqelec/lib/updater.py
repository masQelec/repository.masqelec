# -*- coding: utf-8 -*-
"""
update.py — Comprobación y aplicación de actualización de sistema
- Lee versión local y remota (VERSION/VERSION_ID) y compara correctamente
- Control remoto (os-release) vía rclone: masqelec/update/<DEVICE>/os-release
- Selecciona carpeta remota SEGÚN COREELEC_DEVICE (Amlogic-ng / Amlogic-ce)
- Usa rclone_utils para sync selectivo a staging + movimiento a /storage/.update
- Diálogo al usuario y reinicio seguro
"""

import os
import re
import time
import shutil
import xbmc
import xbmcgui
import traceback

from lib import log_utils
from lib import utils
from lib import rclone_utils as rc

# ------------------------------
# CONFIG
# ------------------------------

REMOTE_UPDATE_REMOTE = "masqelec"
REMOTE_UPDATE_BASEDIR = "masqelec/update"   # dentro hay subcarpetas por DEVICE: Amlogic-ng, Amlogic-ce, ...
REMOTE_CONTROL_NAME = "os-release"          # fichero remoto por device: .../<DEVICE>/os-release


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

# ------------------------------
# LECTURA KV (os-release style)
# ------------------------------

def get_kv_from_file(filename: str, key: str):
    """
    Lee un KEY=VALUE desde un archivo tipo os-release.
    Admite VALUE con o sin comillas.
    """
    try:
        with open(filename, 'r', encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if not line.startswith(key + "="):
                    continue
                v = line.split("=", 1)[1].strip()
                if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
                    return v[1:-1]
                return v
    except Exception as e:
        log_utils.write_log("[kv] Error leyendo {}: {}".format(filename, e), "ERROR")
        return None

def get_kv_from_text(text: str, key: str):
    """
    Lee un KEY=VALUE desde texto en memoria.
    Admite VALUE con o sin comillas.
    """
    if not text:
        return None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith(key + "="):
            continue
        v = line.split("=", 1)[1].strip()
        if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
            return v[1:-1]
        return v
    return None

# ------------------------------
# CONTROL REMOTO VÍA RCLONE
# ------------------------------

def get_text_from_rclone(remote: str, remote_path: str):
    """
    Descarga un fichero pequeño vía rclone a /tmp y lo lee como texto.
    Requiere rc.copy_remote_to_tmp_then_move(remote, remote_path, final_dir).
    """
    tmp_dir = "/tmp/update_control"
    try:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
        os.makedirs(tmp_dir, exist_ok=True)
    except Exception:
        pass

    try:
        ok = rc.copy_remote_to_tmp_then_move(remote=remote, remote_path=remote_path, final_dir=tmp_dir)
        if not ok:
            log_utils.write_log("[control] No se pudo copiar control remoto via rclone: {}:{}".format(remote, remote_path), "ERROR")
            utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
            return None

        local_file = os.path.join(tmp_dir, os.path.basename(remote_path))
        if not os.path.exists(local_file) or os.path.getsize(local_file) <= 0:
            log_utils.write_log("[control] Control copiado pero no válido: {}".format(local_file), "ERROR")
            utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
            return None

        with open(local_file, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log("[control] Error leyendo control remoto: {}".format(e), "ERROR")
        return None
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

# ------------------------------
# HELPERS UPDATE
# ------------------------------

def _cleanup_dir(path: str):
    try:
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
            log_utils.write_log("[cleanup] Eliminado staging temporal: {}".format(path))
    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log("[cleanup] Error al eliminar {}: {}".format(path, e), "ERROR")

def _sync_update_to_staging(version_file_base: str, remote_update_dir: str):
    """
    Sincroniza desde remote_update_dir SOLO el/los artefacto(s) que matcheen version_file_base.*
    a un staging temporal. Devuelve (staging_dir, local_pkg_path) o (None,None) en error.
    """
    staging = "/tmp/staging_update"
    try:
        if os.path.exists(staging):
            shutil.rmtree(staging, ignore_errors=True)
        os.makedirs(staging, exist_ok=True)
    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log("[staging] No se pudo preparar {}: {}".format(staging, e), "ERROR")
        return None, None

    includes = [
        "/{}.tar".format(version_file_base),
        "/{}.tar.*".format(version_file_base),
        "/{}.zip".format(version_file_base),
    ]

    log_utils.write_log("[sync] rclone sync selectivo {}:{} -> {} (includes={})".format(
        REMOTE_UPDATE_REMOTE, remote_update_dir, staging, includes
    ))

    ok = rc.sync_remote_dir(
        remote=REMOTE_UPDATE_REMOTE,
        remote_dir=remote_update_dir,
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

    try:
        entries = [f for f in os.listdir(staging) if os.path.isfile(os.path.join(staging, f))]
        candidates = [f for f in entries if f == "{}.tar".format(version_file_base) or f.startswith(version_file_base + ".")]
        if not candidates:
            log_utils.write_log("[sync] No se encontró artefacto para {} en staging.".format(version_file_base), "ERROR")
            _cleanup_dir(staging)
            return None, None

        pref_order = []
        t_plain = "{}.tar".format(version_file_base)
        if t_plain in candidates:
            pref_order.append(t_plain)
        pref_order += sorted([c for c in candidates if c.endswith(".tar.gz") or c.endswith(".tar.xz")])
        z_plain = "{}.zip".format(version_file_base)
        if z_plain in candidates:
            pref_order.append(z_plain)
        pref_order += [c for c in candidates if c not in pref_order]

        chosen = pref_order[0]
        pkg_path = os.path.join(staging, chosen)
        if not (os.path.exists(pkg_path) and os.path.getsize(pkg_path) > 0):
            log_utils.write_log("[sync] Artefacto no válido: {}".format(pkg_path), "ERROR")
            _cleanup_dir(staging)
            return None, None

        log_utils.write_log("[sync] Artefacto listo en staging: {}".format(pkg_path))
        return staging, pkg_path

    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log("[sync] Error inspeccionando staging: {}".format(e), "ERROR")
        _cleanup_dir(staging)
        return None, None

def _place_update_package(pkg_local_path: str, target_dir: str = "/storage/.update"):
    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception:
        pass

    try:
        final_path = os.path.join(target_dir, os.path.basename(pkg_local_path))
        shutil.copy2(pkg_local_path, final_path)
        if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
            log_utils.write_log("[update] Artefacto colocado en {}".format(final_path))
            return final_path
        log_utils.write_log("[update] Copia inválida a {}".format(final_path), "ERROR")
        return None
    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log("[update] Error copiando paquete a {}: {}".format(target_dir, e), "ERROR")
        return None

# ------------------------------
# ACTUALIZACIÓN DEL SISTEMA
# ------------------------------

def update_system():
    monitor = xbmc.Monitor()

    # Circuit breaker
    if not utils.cb_should_run("updater"):
        msg = "updater en cooldown por fallos repetidos; se omite este ciclo."
        if utils.cb_should_log_cooldown("updater"):
            log_utils.write_log(msg, "INFO")
        else:
            log_utils.write_log(msg, "DEBUG")
        return

    try:
        log_utils.write_log("Iniciando verificación de sistema para actualización.")

        # 1) Versión local y DEVICE local
        local_osr = "/etc/os-release"
        local_version = get_kv_from_file(local_osr, "VERSION_ID")
        if not local_version:
            log_utils.write_log("No se pudo obtener la versión local.", "WARNING")
            utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
            return

        device = get_kv_from_file(local_osr, "COREELEC_DEVICE")
        if not device:
            log_utils.write_log("[update] No se pudo determinar COREELEC_DEVICE. Abort por seguridad.", "ERROR")
            return

        # 2) Control remoto por DEVICE: masqelec/update/<DEVICE>/os-release
        remote_update_dir = "{}/{}".format(REMOTE_UPDATE_BASEDIR, device)
        remote_control_path = "{}/{}".format(remote_update_dir, REMOTE_CONTROL_NAME)

        log_utils.write_log("[update] DEVICE local: {} | Control remoto: {}:{}".format(
            device, REMOTE_UPDATE_REMOTE, remote_control_path
        ))

        remote_text = get_text_from_rclone(REMOTE_UPDATE_REMOTE, remote_control_path)
        if not remote_text:
            log_utils.write_log("No se pudo obtener el control remoto (os-release) vía rclone.", "WARNING")
            utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
            return

        remote_version = get_kv_from_text(remote_text, "VERSION_ID")
        if not remote_version:
            log_utils.write_log("No se encontró VERSION_ID en el os-release remoto.", "WARNING")
            return

        version_file = get_kv_from_text(remote_text, "VERSION")  # nombre base del paquete sin extensión
        log_utils.write_log("Local: {} | Remota: {} | Archivo base: {}".format(
            local_version, remote_version, version_file or "N/D"
        ))

        # 3) Comparar versiones
        local_t  = parse_version(local_version)
        remote_t = parse_version(remote_version)
        log_utils.write_log("Comparación de versión: local={} -> {} | remoto={} -> {}".format(
            local_version, local_t, remote_version, remote_t
        ))

        if local_t < remote_t:
            log_utils.write_log("Nueva actualización disponible: {} > {}".format(remote_version, local_version))

            if not version_file:
                log_utils.write_log("El os-release remoto no especifica VERSION (nombre base del paquete).", "ERROR")
                return

            staging = None
            try:
                staging, pkg_path = _sync_update_to_staging(version_file, remote_update_dir)
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
                    "Se encontró la versión {}.\n¿Deseas actualizar ahora o en el próximo reinicio?".format(remote_version),
                    nolabel="Posponer",
                    yeslabel="Actualizar"
                )

                if ret:
                    try:
                        log_utils.notify("Iniciando proceso de actualización…", xbmcgui.NOTIFICATION_INFO)
                    except Exception:
                        pass
                    log_utils.write_log("Reiniciando para actualizar (paquete: {})".format(final_pkg))
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
                if staging:
                    _cleanup_dir(staging)

        else:
            if local_t == remote_t:
                log_utils.write_log("La versión remota es IGUAL a la local. No hay actualización.")
            else:
                log_utils.write_log("La versión remota es MENOR que la local. No hay actualización.")

    except Exception as e:
        utils.cb_note_failure("updater", fail_threshold=3, cooldown_sec=3600)
        log_utils.write_log("Error en update_system: {}\n{}".format(e, traceback.format_exc()), "ERROR")
        try:
            log_utils.notify("Error en el proceso de actualización", xbmcgui.NOTIFICATION_ERROR)
        except Exception:
            pass

