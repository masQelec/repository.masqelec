# -*- coding: utf-8 -*-
"""device_utils.py — rol MASTER/CLIENT + info de red/ZeroTier"""

import os
import re
import socket
import subprocess
import hashlib
import traceback

import xbmcvfs

from lib import log_utils
from lib import system_utils

#cache de rol (None = no calculado aún)
_DEVICE_ROLE = None

# Compat: valor por defecto (puedes sobreescribirlo desde settings si ya lo haces)
DEFAULT_MASTER_ETH0_MACS = "066230512670"

AUTH_KEYS_FILE = "/storage/.ssh/authorized_keys"

def _normalize_mac12(s):
    if not s:
        return ""
    s = s.strip().lower().replace(":", "").replace("-", "")
    return s if re.fullmatch(r"[0-9a-f]{12}", s) else ""

def get_device_eth0_mac():
    """Devuelve MAC de eth0 en formato 12 hex (sin ':')."""
    try:
        info = get_net_info()
        mac = (info.get("eth0") or "").strip().lower()
        return mac if mac and mac != "unknown_mac" else ""
    except Exception:
        return ""

def _parse_master_macs(macs_cfg):
    parts = re.split(r"[,\s]+", (macs_cfg or "").strip())
    out = set()
    for p in parts:
        m = _normalize_mac12(p)
        if m:
            out.add(m)
    return out

def is_master_device():
    eth0 = _normalize_mac12(get_device_eth0_mac())
    if not eth0:
        return False

    master_set = _parse_master_macs(DEFAULT_MASTER_ETH0_MACS)
    if not master_set:
        log_utils.write_log("[role] DEFAULT_MASTER_ETH0_MACS vacío o inválido", "WARNING")
        return False

    return eth0 in master_set

def get_device_role():
    """
    Devuelve 'MASTER' o 'CLIENT'.
    Cacheado tras la primera evaluación.
    """
    global _DEVICE_ROLE

    if _DEVICE_ROLE is not None:
        return _DEVICE_ROLE

    try:
        is_master = bool(is_master_device())
    except Exception:
        is_master = False

    _DEVICE_ROLE = "MASTER" if is_master else "CLIENT"

    try:
        log_utils.write_log(
            "Rol dispositivo detectado: {}".format(_DEVICE_ROLE),
            "INFO"
        )
    except Exception as e:
        # FIX: antes referenciaba 'path' que no existe
        try:
            log_utils.write_log("[role] Log falló: {}".format(e), "DEBUG")
        except Exception:
            pass

    return _DEVICE_ROLE

def is_client():
    return get_device_role() == "CLIENT"

def get_key_from_authorized_keys(filename=AUTH_KEYS_FILE):
    """
    Devuelve una clave binaria estable derivada del primer key válido
    encontrado en authorized_keys (sha256).
    """
    try:
        if not filename or not os.path.exists(filename):
            return None

        with open(filename, "rb") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(b"#"):
                    continue
                # primera clave válida → hash estable
                return hashlib.sha256(line).digest()

    except Exception:
        log_utils.log(
            "[device] error leyendo authorized_keys:\n{}".format(traceback.format_exc()),
            level="WARNING",
        )

    return None

def get_net_info():
    def _read_mac(interface):
        mac_path = "/sys/class/net/{}/address".format(interface)
        if not os.path.exists(mac_path):
            log_utils.write_log("[net] La interfaz '{}' no existe.".format(interface), level="WARNING")
            return "unknown_mac"
        try:
            with open(mac_path, "r") as f:
                mac = f.read().strip().lower().replace(":", "").replace("-", "")
                if len(mac) == 12 and all(c in "0123456789abcdef" for c in mac):
                    return mac
                else:
                    log_utils.write_log("[net] MAC inválida en {}: {}".format(interface, mac), level="WARNING")
                    return "unknown_mac"
        except Exception as e:
            log_utils.write_log("[net] Error leyendo MAC de {}: {}".format(interface, e), level="WARNING")
            return "unknown_mac"

    return {"eth0": _read_mac("eth0"), "wlan0": _read_mac("wlan0")}

def get_zerotier_ids(ZT_DIRS=None):
    """
    Lee datos de ZeroTier desde ficheros locales (*.conf).
    Devuelve: {"n": node_name, "nwid": network_id, "id": device_id}
    """
    import os, glob, traceback

    if ZT_DIRS is None:
        # Probables ubicaciones (NO invento “la correcta”, solo pruebo varias)
        ZT_DIRS = [
            "/opt/var/lib/zerotier-one/networks.d",   # Entware típico
            "/var/lib/zerotier-one/networks.d",       # Linux estándar
            "/storage/.cache/zerotier-one/networks.d" # algunos layouts embebidos
        ]

    try:
        base = None
        for d in ZT_DIRS:
            if os.path.isdir(d):
                base = d
                break

        if not base:
            log_utils.write_log("[zerotier] networks.d no existe en: {}".format(", ".join(ZT_DIRS)), "WARNING")
            return {}

        confs = sorted(glob.glob(os.path.join(base, "*.conf")))
        confs = [p for p in confs if not p.endswith(".local.conf")]

        if not confs:
            log_utils.write_log("[zerotier] no hay .conf en {}".format(base), "WARNING")
            return {}

        best = max(confs, key=lambda p: os.path.getmtime(p))

        node_name = None
        nwid = None
        id_device = None

        with open(best, "rb") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                # tu código original cortaba cuando ve C=/COO=; lo mantengo
                if raw.startswith(b"C=") or raw.startswith(b"COO="):
                    break

                line = raw.decode("utf-8", errors="ignore").strip()
                if line.startswith("n="):
                    node_name = line.split("=", 1)[1].strip()
                elif line.startswith("nwid="):
                    nwid = line.split("=", 1)[1].strip()
                elif line.startswith("id="):
                    id_device = line.split("=", 1)[1].strip()

        if not nwid:
            nwid_from_name = os.path.basename(best).split(".")[0]
            if len(nwid_from_name) >= 16:
                nwid = nwid_from_name

        out = {"n": node_name, "nwid": nwid, "id": id_device}

        # LOG útil si algo falta (para que no vuelvas a “no_name” a ciegas)
        if not out.get("nwid"):
            log_utils.write_log("[zerotier] no se pudo extraer nwid desde {}".format(best), "WARNING")

        return out

    except Exception:
        log_utils.write_log("[zerotier] fallo leyendo conf:\n{}".format(traceback.format_exc()), "WARNING")
        return {}

