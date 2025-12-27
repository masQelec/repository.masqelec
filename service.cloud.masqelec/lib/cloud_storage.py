# -*- coding: utf-8 -*-
"""
cloud_storage.py — Descarga/descifrado atómico de rclone.conf + verificación de servicios
"""

import os
import urllib.request
import urllib.error
import urllib.parse
import subprocess
import traceback
import time
import stat
import shutil
import socket
import re
import hashlib

from lib import log_utils
from lib import utils

# ==============================
# Config red
# ==============================
NET_TIMEOUT = 30
NET_RETRIES = 2
UA = "masQelec/1.0 (+Kodi)"

tmp_dir = "/tmp"

# ==============================
# Hash helpers
# ==============================
def _sha256(b: bytes) -> str:
    return hashlib.sha256(b or b"").hexdigest()

# ==============================
# Normalización rclone.conf
# ==============================
_RE_DROP_VOLATILE = re.compile(r"^\s*token\s*=", re.IGNORECASE)

def _normalize_rclone_conf_bytes(data: bytes) -> bytes:
    """
    Normaliza rclone.conf para comparación estable:
      - Normaliza EOLs (\n, \r\n, \r)
      - Elimina BOM UTF-8
      - Elimina líneas volátiles (token=...)
      - Quita espacios finales
      - Ignora diferencia SOLO por newline final
    """
    if data is None:
        return b""

    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]

    lines = data.splitlines()
    out = []

    for raw in lines:
        line = raw.decode("utf-8", "replace")
        if _RE_DROP_VOLATILE.match(line):
            continue
        out.append(line.rstrip())

    norm = "\n".join(out).rstrip("\n")
    return norm.encode("utf-8")

# ==============================
# Red
# ==============================
def _net_open(url: str, timeout: int = NET_TIMEOUT):
    try:
        host = urllib.parse.urlparse(url).hostname or ""
    except Exception:
        host = ""

    if host:
        if not utils.wait_for_dns(host, timeout=15, interval=1.0):
            log_utils.write_log(f"[net] DNS no listo para {host}. Omito descarga.", "WARNING")
            raise urllib.error.URLError("DNS not ready")

    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last_err = None

    for attempt in range(NET_RETRIES + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)

        except urllib.error.URLError as e:
            last_err = e
            reason = getattr(e, "reason", None)

            if isinstance(reason, socket.gaierror):
                log_utils.write_log(
                    f"[net] DNS fallo para {host or url}: {reason}. Se reintentará más tarde.",
                    "WARNING",
                )
                raise

            log_utils.write_log(
                f"[net] intento {attempt+1}/{NET_RETRIES+1} falló para {url}: {reason or e}",
                "ERROR",
            )

            if attempt < NET_RETRIES:
                time.sleep(2)

    raise last_err

# ==============================
# FS helpers
# ==============================
def _cleanup_path(p: str):
    try:
        if not p:
            return
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        elif os.path.exists(p):
            os.remove(p)
    except Exception as e:
        log_utils.write_log(f"Excepción ignorada en cloud_storage: {e}", "DEBUG")

def _atomic_write_bytes(dst_path: str, data: bytes, mode: int = None):
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
# Descarga
# ==============================
def download_to_file(url: str, dst_path: str) -> bool:
    try:
        log_utils.write_log(f"Descargando: {url} -> {dst_path}")
        with _net_open(url) as resp, open(dst_path, "wb") as f:
            shutil.copyfileobj(resp, f, length=256 * 1024)
            f.flush()
            os.fsync(f.fileno())
        return os.path.exists(dst_path) and os.path.getsize(dst_path) > 0

    except urllib.error.URLError as e:
        msg = str(e)
        reason = getattr(e, "reason", None)

        if "DNS not ready" in msg or isinstance(reason, socket.gaierror):
            log_utils.write_log(f"Descarga omitida por DNS: {url}", "WARNING")
            return False

        log_utils.write_log(f"URLError descargando '{url}': {e}", "ERROR")
        return False

    except Exception as e:
        log_utils.write_log(f"Error descargando '{url}': {e}\n{traceback.format_exc()}", "ERROR")
        return False

def decrypt_file_to_file(src_path: str, key: bytes, dst_path: str, rounds: int = 8) -> bool:
    try:
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
# SYSTEMD helpers (SIN CAMBIOS)
# ==============================
def _has_systemctl() -> bool:
    from shutil import which
    return which("systemctl") is not None

def _unit_name(unit: str) -> str:
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
    rc, out, err = utils.run_cmd(["systemctl", "enable", "--now", _unit_name(unit)], timeout=10)
    if rc != 0:
        log_utils.write_log(f"systemctl enable --now falló para {unit}: {err or out}", "WARNING")

def _systemctl_try_restart(unit: str):
    if not _has_systemctl():
        return
    rc, out, err = utils.run_cmd(["systemctl", "try-restart", _unit_name(unit)], timeout=10)
    if rc != 0:
        log_utils.write_log(f"systemctl try-restart falló para {unit}: {err or out}", "WARNING")

# ==============================
# CLOUD STORAGE
# ==============================
def start_cloud_storage():
    if not utils.cb_should_run("cloud_storage"):
        if utils.cb_should_log_cooldown("cloud_storage"):
            log_utils.write_log("cloud_storage en cooldown; se omite.", "INFO")
        return

    enc_tmp = os.path.join(tmp_dir, ".rclone.conf.crypt.tmp")
    dec_tmp = os.path.join(tmp_dir, ".rclone.conf.plain.tmp")

    try:
        key = utils.get_key_from_authorized_keys()

        rclone_conf_path = "/storage/.config/rclone/rclone.conf"
        rclone_dir = os.path.dirname(rclone_conf_path)
        enc_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone/rclone.conf.crypt"

        if not download_to_file(enc_url, enc_tmp):
            log_utils.write_log("No se pudo descargar rclone.conf.crypt.", "WARNING")
            return

        if not decrypt_file_to_file(enc_tmp, key, dec_tmp, rounds=8):
            log_utils.write_log("Falló el desencriptado de rclone.conf.", "ERROR")
            return

        with open(dec_tmp, "rb") as f:
            remote_raw = f.read()

        remote_norm = _normalize_rclone_conf_bytes(remote_raw)

        os.makedirs(rclone_dir, exist_ok=True)

        local_norm = None
        if os.path.exists(rclone_conf_path):
            try:
                with open(rclone_conf_path, "rb") as lf:
                    local_raw = lf.read()
                local_norm = _normalize_rclone_conf_bytes(local_raw)
            except Exception:
                local_norm = None

        if local_norm is not None and local_norm == remote_norm:
            log_utils.write_log("rclone.conf sin cambios (idéntico tras normalizar).")
        else:
            if local_norm is not None:
                log_utils.write_log(
                    f"rclone.conf difiere: sha_local={_sha256(local_norm)} sha_remote={_sha256(remote_norm)}",
                    "DEBUG",
                )

            stable = b"\n".join(remote_raw.splitlines()).rstrip(b"\n") + b"\n"
            _atomic_write_bytes(
                rclone_conf_path,
                stable,
                mode=(stat.S_IRUSR | stat.S_IWUSR),
            )
            log_utils.write_log("rclone.conf actualizado (cambios detectados).")

        # Servicios
        services = [
            "rclone_tvshows_1.service",
            "rclone_tvshows_2.service",
            "rclone_videos_1.service",
            "rclone_videos_2.service",
            "zerotier.service",
        ]

        for unit in services:
            if not _systemctl_is_active(unit):
                _systemctl_enable_now(unit)

        utils.cb_note_success("cloud_storage")

    except Exception as e:
        utils.cb_note_failure("cloud_storage", threshold=3, cooldown_sec=3600)
        log_utils.write_log(f"Error en cloud_storage: {e}\n{traceback.format_exc()}", "ERROR")
    finally:
        _cleanup_path(enc_tmp)
        _cleanup_path(dec_tmp)

