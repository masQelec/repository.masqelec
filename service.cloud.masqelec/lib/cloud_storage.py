# -*- coding: utf-8 -*-
"""
cloud_storage.py — Descarga/descifrado atómico de rclone.conf + verificación de servicios

Cambios:
- NO se comparan contenidos: siempre se descarga y reemplaza rclone.conf (atómico, 0600).
- No se detienen/arrancan servicios sólo por reemplazar el conf.
- Tras escribir, se verifica estado de servicios y se activan si hiciera falta.
- Unidades .service se actualizan desde remoto; daemon-reload sólo si cambian.
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
            log_utils.write_log(f"[net] intento {attempt+1}/{NET_RETRIES+1} falló para {url}: {getattr(e, 'reason', e)}", "ERROR")
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

# ==============================
# DESCARGA
# ==============================
def download_to_file(url: str, dst_path: str) -> bool:
    """Descarga un recurso a un fichero local (dst_path)."""
    try:
        log_utils.write_log(f"Descargando: {url} -> {dst_path}")
        with _net_open(url) as resp, open(dst_path, "wb") as f:
            shutil.copyfileobj(resp, f, length=256*1024)
        return os.path.exists(dst_path) and os.path.getsize(dst_path) > 0
    except Exception as e:
        log_utils.write_log(f"Error descargando '{url}': {e}\n{traceback.format_exc()}", "ERROR")
        return False

def decrypt_file_to_file(src_path: str, key: bytes, dst_path: str, rounds: int = 8) -> bool:
    """Lee texto base64, descifra (como tu script) y escribe binario en dst_path."""
    try:
        with open(src_path, "r", encoding="utf-8", errors="replace") as f:
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

def _service_name(unit: str) -> str:
    return unit[:-8] if unit.endswith(".service") else unit

def handle_service_file(service_name: str, base_url: str, systemd_dir: str):
    """
    Maneja la descarga, comparación, y estado de un archivo de servicio.
    Devuelve True si se realizaron cambios que requieren 'daemon-reload'.
    """
    dest = os.path.join(systemd_dir, service_name)
    url = f"{base_url}{service_name}"

    # Descargar a tmp y comparar normalizando EOL
    tmp_path = os.path.join(tmp_dir, f".{service_name}.tmp")
    changed = False
    try:
        ok = download_to_file(url, tmp_path)
        if not ok:
            log_utils.write_log(f"No se pudo descargar '{service_name}'. Saltando.", "WARNING")
            return False

        with open(tmp_path, "rb") as tf:
            remote_content = tf.read().replace(b"\r\n", b"\n")

        if os.path.exists(dest):
            with open(dest, "rb") as lf:
                local_content = lf.read().replace(b"\r\n", b"\n")
            if local_content != remote_content:
                log_utils.write_log(f"El archivo '{service_name}' local difiere. Reemplazando.")
                with open(dest, "wb") as f:
                    f.write(remote_content)
                    f.flush()
                    os.fsync(f.fileno())
                changed = True
            else:
                log_utils.write_log(f"'{service_name}' coincide con la versión remota. Verificando estado service…")
                if _has_systemctl():
                    name = _service_name(service_name)
                    try:
                        subprocess.run(['systemctl', 'is-active', name], check=True,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        log_utils.write_log(f"El servicio '{name}' está activo.")
                    except subprocess.CalledProcessError:
                        log_utils.write_log(f"El servicio '{name}' no está activo. Habilitando e iniciando…")
                        subprocess.call(["systemctl", "enable", "--now", name])
                else:
                    log_utils.write_log("systemctl no disponible; no se puede verificar/iniciar servicios.", "WARNING")
        else:
            log_utils.write_log(f"Archivo '{service_name}' no encontrado. Creándolo con la versión remota.")
            os.makedirs(systemd_dir, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(remote_content)
                f.flush()
                os.fsync(f.fileno())
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
        name = _service_name(unit)
        try:
            subprocess.run(['systemctl', 'is-active', name], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log_utils.write_log(f"Servicio '{name}' activo.")
        except subprocess.CalledProcessError:
            log_utils.write_log(f"Servicio '{name}' inactivo. Habilitando e iniciando…")
            subprocess.call(["systemctl", "enable", "--now", name])

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
      5) Verificar servicios rclone/zerotier y activarlos si no están activos.
    """
    enc_tmp = os.path.join(tmp_dir, ".rclone.conf.enc.tmp")
    dec_tmp = os.path.join(tmp_dir, ".rclone.conf.dec.tmp")

    try:
        key = utils.get_key_from_authorized_keys()

        rclone_conf_path = "/storage/.config/rclone/rclone.conf"
        rclone_dir = os.path.dirname(rclone_conf_path)
        enc_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone.conf.enc"

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
        tmp_out = rclone_conf_path + ".tmp"
        with open(tmp_out, "wb") as f:
            f.write(remote_norm)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.replace(tmp_out, rclone_conf_path)
        finally:
            try:
                if os.path.exists(tmp_out):
                    os.remove(tmp_out)
            except Exception:
                pass
        try:
            os.chmod(rclone_conf_path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
        except Exception:
            pass

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

        daemon_needs_reload = False
        for service in services:
            if handle_service_file(service, "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/", systemd_dir):
                daemon_needs_reload = True

        if daemon_needs_reload and _has_systemctl():
            log_utils.write_log("Cambios en unidades detectados. Recargando daemon de systemd…")
            subprocess.call(["systemctl", "daemon-reload"])

        # 5) Asegurar que los servicios estén activos
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
