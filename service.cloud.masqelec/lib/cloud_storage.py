# -*- coding: utf-8 -*-
"""
cloud_storage.py — Descarga/descifrado atómico de rclone.conf + verificación de servicios

Cambios:
- NO se comparan contenidos: siempre se descarga y reemplaza rclone.conf (atómico, 0600).
- No se detienen/arrancan servicios sólo por reemplazar el conf.
- Tras escribir, se verifica estado de servicios y se activan si hiciera falta.
- Unidades .service se actualizan desde remoto; daemon-reload sólo si cambian.
- Si una unidad cambió, se aplica con try-restart (solo esas unidades).
- Escritura ATÓMICA también para los .service + permisos 0644.
- systemctl siempre con nombre completo del unit (sin recortar .service).
- Limpieza de temporales.
"""

import os
import urllib.request
import urllib.error
import subprocess
import traceback
import time
import stat
import shutil

from lib import log_utils
from lib import utils

# ==============================
# Config red
# ==============================
NET_TIMEOUT = 30
NET_RETRIES = 2
UA = "masQelec/1.0 (+Kodi)"

tmp_dir = "/tmp"


def _net_open(url: str, timeout: int = NET_TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last_err = None
    for attempt in range(NET_RETRIES + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            last_err = e
            log_utils.write_log(
                f"[net] intento {attempt+1}/{NET_RETRIES+1} falló para {url}: {getattr(e, 'reason', e)}",
                "ERROR",
            )
            # no dormir si ya es el último intento
            if attempt < NET_RETRIES:
                time.sleep(2)
    raise last_err


def _cleanup_path(p: str):
    try:
        if not p:
            return
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        elif os.path.exists(p):
            os.remove(p)
    except Exception:
        pass


def _atomic_write_bytes(dst_path: str, data: bytes, mode: int = None):
    """
    Escritura atómica: escribe a .tmp, fsync, replace.
    Si mode se pasa, chmod tras el replace.
    """
    tmp_out = dst_path + ".tmp"
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    with open(tmp_out, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

    try:
        os.replace(tmp_out, dst_path)
    finally:
        try:
            if os.path.exists(tmp_out):
                os.remove(tmp_out)
        except Exception:
            pass

    if mode is not None:
        try:
            os.chmod(dst_path, mode)
        except Exception:
            pass


# ==============================
# DESCARGA
# ==============================
def download_to_file(url: str, dst_path: str) -> bool:
    """Descarga un recurso a un fichero local (dst_path)."""
    try:
        log_utils.write_log(f"Descargando: {url} -> {dst_path}")
        with _net_open(url) as resp, open(dst_path, "wb") as f:
            shutil.copyfileobj(resp, f, length=256 * 1024)
            f.flush()
            os.fsync(f.fileno())
        return os.path.exists(dst_path) and os.path.getsize(dst_path) > 0
    except Exception as e:
        log_utils.write_log(f"Error descargando '{url}': {e}\n{traceback.format_exc()}", "ERROR")
        return False


def decrypt_file_to_file(src_path: str, key: bytes, dst_path: str, rounds: int = 8) -> bool:
    """Lee texto base64, descifra (como tu script) y escribe binario en dst_path."""
    try:
        # Mejor fallar duro si el texto no es válido, para no “corromper” base64 con �
        with open(src_path, "r", encoding="utf-8", errors="strict") as f:
            encrypted_text = f.read()

        decrypted = utils.decrypt(encrypted_text, key, rounds=rounds)
        if decrypted is None:
            return False

        with open(dst_path, "wb") as out:
            out.write(decrypted)
            out.flush()
            os.fsync(out.fileno())
        return True
    except Exception as e:
        log_utils.write_log(f"Error desencriptando {src_path}: {e}\n{traceback.format_exc()}", "ERROR")
        return False


# ==============================
# SYSTEMD HELPERS
# ==============================
def _has_systemctl() -> bool:
    from shutil import which
    return which("systemctl") is not None


def _unit_name(unit: str) -> str:
    # Siempre trabajar con el unit completo, para evitar ambigüedades
    return unit if unit.endswith(".service") else (unit + ".service")


def _systemctl_is_active(unit: str) -> bool:
    if not _has_systemctl():
        return False
    try:
        subprocess.run(
            ["systemctl", "is-active", _unit_name(unit)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _systemctl_enable_now(unit: str):
    if not _has_systemctl():
        return
    subprocess.call(["systemctl", "enable", "--now", _unit_name(unit)])


def _systemctl_try_restart(unit: str):
    if not _has_systemctl():
        return
    subprocess.call(["systemctl", "try-restart", _unit_name(unit)])


def handle_service_file(service_name: str, base_url: str, systemd_dir: str) -> bool:
    """
    Descarga y compara un archivo de servicio.
    Devuelve True si el fichero CAMBIÓ (requiere daemon-reload y aplicar con try-restart).
    """
    service_unit = _unit_name(service_name)
    dest = os.path.join(systemd_dir, service_unit)
    url = f"{base_url}{service_unit}"

    tmp_path = os.path.join(tmp_dir, f".{service_unit}.tmp")
    changed = False

    try:
        ok = download_to_file(url, tmp_path)
        if not ok:
            log_utils.write_log(f"No se pudo descargar '{service_unit}'. Saltando.", "WARNING")
            return False

        with open(tmp_path, "rb") as tf:
            remote_content = tf.read().replace(b"\r\n", b"\n")

        if os.path.exists(dest):
            with open(dest, "rb") as lf:
                local_content = lf.read().replace(b"\r\n", b"\n")

            if local_content != remote_content:
                log_utils.write_log(f"El archivo '{service_unit}' local difiere. Reemplazando (atómico).")
                _atomic_write_bytes(dest, remote_content, mode=0o644)
                changed = True
            else:
                log_utils.write_log(f"'{service_unit}' coincide con la versión remota. Verificando estado service…")
                if _has_systemctl():
                    if _systemctl_is_active(service_unit):
                        log_utils.write_log(f"El servicio '{service_unit}' está activo.")
                    else:
                        log_utils.write_log(f"El servicio '{service_unit}' no está activo. Habilitando e iniciando…")
                        _systemctl_enable_now(service_unit)
                else:
                    log_utils.write_log("systemctl no disponible; no se puede verificar/iniciar servicios.", "WARNING")
        else:
            log_utils.write_log(f"Archivo '{service_unit}' no encontrado. Creándolo con la versión remota (atómico).")
            os.makedirs(systemd_dir, exist_ok=True)
            _atomic_write_bytes(dest, remote_content, mode=0o644)
            changed = True

    finally:
        _cleanup_path(tmp_path)

    return changed


def _ensure_services_active(services):
    """Verifica y activa servicios si no están activos; no los detiene."""
    if not _has_systemctl():
        log_utils.write_log("systemctl no disponible; no puedo verificar/activar servicios.", "WARNING")
        return

    for unit in services:
        unit = _unit_name(unit)
        if _systemctl_is_active(unit):
            log_utils.write_log(f"Servicio '{unit}' activo.")
        else:
            log_utils.write_log(f"Servicio '{unit}' inactivo. Habilitando e iniciando…")
            _systemctl_enable_now(unit)


# ==============================
# CLOUD STORAGE (fase bloqueante)
# ==============================
def start_cloud_storage():
    """
    Flujo:
      1) Descargar rclone.conf.enc a tmp.
      2) Desencriptar a tmp exactamente como el script de cifrado.
      3) Normalizar EOL y reemplazar SIEMPRE /storage/.config/rclone/rclone.conf (atómico, 0600).
      4) Actualizar unidades .service desde remoto; systemctl daemon-reload sólo si cambiaron.
      5) Si una unidad cambió, aplicar con try-restart (solo esas unidades).
      6) Verificar servicios rclone/zerotier y activarlos si no están activos.
    """
    enc_tmp = os.path.join(tmp_dir, ".rclone.conf.enc.tmp")
    dec_tmp = os.path.join(tmp_dir, ".rclone.conf.dec.tmp")

    try:
        key = utils.get_key_from_authorized_keys()

        rclone_conf_path = "/storage/.config/rclone/rclone.conf"
        rclone_dir = os.path.dirname(rclone_conf_path)
        enc_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone/rclone.conf.enc"

        # 1) Descargar cifrado -> tmp
        if not download_to_file(enc_url, enc_tmp):
            log_utils.write_log("No se pudo descargar rclone.conf.enc.", "ERROR")
            return

        # 2) Desencriptar -> tmp
        if not decrypt_file_to_file(enc_tmp, key, dec_tmp, rounds=8):
            log_utils.write_log("Falló el desencriptado de rclone.conf.", "ERROR")
            return

        # 3) Normalizar EOL y reemplazar SIEMPRE (atómico, 0600)
        with open(dec_tmp, "rb") as f:
            remote_raw = f.read()
        remote_norm = remote_raw.replace(b"\r\n", b"\n")

        os.makedirs(rclone_dir, exist_ok=True)
        _atomic_write_bytes(rclone_conf_path, remote_norm, mode=(stat.S_IRUSR | stat.S_IWUSR))  # 0600

        log_utils.write_log("rclone.conf actualizado (reemplazo directo) correctamente.")

        # 4) Unidades de systemd
        services = [
            "rclone_tvshows_1.service",
            "rclone_tvshows_2.service",
            "rclone_videos_1.service",
            "rclone_videos_2.service",
            "zerotier.service",
        ]
        systemd_dir = "/storage/.config/system.d/"
        os.makedirs(systemd_dir, exist_ok=True)

        changed_units = []
        for service in services:
            if handle_service_file(service, "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/system.d/", systemd_dir):
                changed_units.append(_unit_name(service))

        if changed_units and _has_systemctl():
            log_utils.write_log("Cambios en unidades detectados. Recargando daemon de systemd…")
            subprocess.call(["systemctl", "daemon-reload"])

            # 5) Aplicar cambios: si el servicio está activo, try-restart (solo los que cambiaron)
            for unit in changed_units:
                if _systemctl_is_active(unit):
                    log_utils.write_log(f"Unidad '{unit}' cambió y está activa: aplicando try-restart…")
                    _systemctl_try_restart(unit)
                else:
                    # si no está activo, que la parte de ensure lo habilite y arranque
                    log_utils.write_log(f"Unidad '{unit}' cambió pero no está activa: se arrancará si procede.")

        # 6) Asegurar que los servicios estén activos
        _ensure_services_active(services)

        log_utils.write_log("Almacenamiento en la nube configurado/verificado exitosamente.")

    except FileNotFoundError as e:
        log_utils.write_log(f"Error: {e}. Asegúrese de que la clave de cifrado existe.", "ERROR")
    except Exception as e:
        log_utils.write_log(f"Error en start_cloud_storage: {e}\n{traceback.format_exc()}", "ERROR")
    finally:
        # 🧹 Limpieza de temporales
        _cleanup_path(enc_tmp)
        _cleanup_path(dec_tmp)

