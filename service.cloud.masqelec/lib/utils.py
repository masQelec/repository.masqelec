# -*- coding: utf-8 -*-

import os
import io
import re
import subprocess
import gzip
import time
import shutil
import zipfile
import datetime
import traceback
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcvfs

from lib import log_utils

# ---- Config red (ajusta si quieres) ----
NET_TIMEOUT = 30           # segundos
NET_RETRIES = 2            # reintentos adicionales en error de red
RETRY_BACKOFF = 2          # segundos entre reintentos

# Identidad del addon centralizada (usada por otros módulos)
ADDON_ID = "service.cloud.masqelec"

try:
    addon = xbmcaddon.Addon(id=ADDON_ID)
except Exception:
    # Fallback por si se importa fuera de Kodi
    addon = xbmcaddon.Addon()

try:
    ADDON_NAME = addon.getAddonInfo("name")
except Exception:
    ADDON_NAME = ADDON_ID


UA = f"{ADDON_NAME}/1.0 (+Kodi)"

# ----------------- Helpers internos -----------------

def _net_open(url: str, timeout: int = NET_TIMEOUT):
    """Abre URL con User-Agent y timeout, con reintentos simples."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    last_err = None
    for attempt in range(NET_RETRIES + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            last_err = e
            log_utils.write_log(f"Intento {attempt+1}/{NET_RETRIES+1} falló para {url}: {getattr(e, 'reason', e)}", "ERROR")
            time.sleep(RETRY_BACKOFF)
    raise last_err

def _read_maybe_gzip(response) -> bytes:
    """Lee bytes desde response y descomprime si viene gz."""
    data = response.read()
    enc = response.headers.get("Content-Encoding", "")
    if "gzip" in enc.lower() or response.geturl().endswith(".gz"):
        try:
            return gzip.decompress(data)
        except Exception:
            # Si falla, devolvemos original
            return data
    return data

def _find_extracted_addon_dir(temp_dir_os: str, expected_id: str) -> str:
    """
    Encuentra en el directorio temporal la carpeta que contiene el addon con id=expected_id.
    Considera casos donde el ZIP viene como addon_id/ o addon_id-version/.
    """
    # 1) Coincidencia directa
    direct = os.path.join(temp_dir_os, expected_id)
    if os.path.isdir(direct):
        return direct

    # 2) Buscar carpeta con addon.xml y id correcto
    for entry in os.listdir(temp_dir_os):
        path = os.path.join(temp_dir_os, entry)
        if os.path.isdir(path):
            addon_xml = os.path.join(path, "addon.xml")
            if os.path.isfile(addon_xml):
                try:
                    tree = ET.parse(addon_xml)
                    root = tree.getroot()
                    if root.tag == "addon" and root.get("id") == expected_id:
                        return path
                except Exception:
                    continue

    return ""

def _safe_rmtree(path: str):
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass

# ----------------- API pública -----------------

def get_addon_download_url(addon_id: str, addons_xml_url: str):
    """
    Obtiene la URL de descarga de un addon a partir de un addons.xml (o addons.xml.gz) remoto.
    Asume estructura estándar: base/{addon_id}/{addon_id}-{version}.zip
    """
    log_utils.write_log(f"Buscando URL de descarga para '{addon_id}' en '{addons_xml_url}'")
    try:
        resp = _net_open(addons_xml_url)
        xml_content = _read_maybe_gzip(resp)
        root = ET.fromstring(xml_content)

        addon_elem = root.find(f"./addon[@id='{addon_id}']")
        if addon_elem is None:
            log_utils.write_log(f"Addon '{addon_id}' no encontrado en addons.xml", "ERROR")
            return None

        version = addon_elem.get("version")
        if not version:
            log_utils.write_log(f"No se detectó versión para '{addon_id}'", "ERROR")
            return None

        base_url = addons_xml_url.rsplit("/", 1)[0]
        download_url = f"{base_url}/{addon_id}/{addon_id}-{version}.zip"
        log_utils.write_log(f"URL de descarga construida: {download_url}")
        return download_url

    except urllib.error.URLError as e:
        log_utils.write_log(f"Error de red accediendo a {addons_xml_url}: {getattr(e, 'reason', e)}", "ERROR")
        return None
    except ET.ParseError as e:
        log_utils.write_log(f"Error parseando addons.xml: {e}", "ERROR")
        return None
    except Exception as e:
        log_utils.write_log(f"Error inesperado en get_addon_download_url: {e}", "ERROR")
        return None

def install_addon_silent(addon_id: str, addon_url: str) -> bool:
    """
    Descarga un addon en memoria, lo extrae a temp y lo mueve a la carpeta de addons.
    Respeta cancelación con xbmc.Monitor(); asegura limpieza de temp.
    """
    monitor = xbmc.Monitor()
    log_utils.write_log(f"Instalación silenciosa de {addon_id} desde {addon_url}")

    temp_dir_kodi = "special://temp/addons_temp/"
    temp_dir_os = xbmcvfs.translatePath(temp_dir_kodi)
    dest_dir_os = xbmcvfs.translatePath("special://home/addons/")

    try:
        if not os.path.exists(temp_dir_os):
            os.makedirs(temp_dir_os, exist_ok=True)

        # Cancelación temprana
        if monitor.abortRequested():
            log_utils.write_log("Abort solicitado antes de descargar.")
            return False

        # 1) Descargar ZIP → memoria (con timeout y UA)
        with _net_open(addon_url) as response:
            data = response.read()
            if not data or len(data) < 100:  # umbral básico contra respuestas vacías
                log_utils.write_log("Descarga vacía o demasiado pequeña; abortando.", "ERROR")
                return False
            zip_content = io.BytesIO(data)

        if monitor.abortRequested():
            log_utils.write_log("Abort solicitado tras descarga.")
            return False

        # 2) Descomprimir en temp
        with zipfile.ZipFile(zip_content, "r") as zf:
            zf.extractall(temp_dir_os)
        log_utils.write_log(f"ZIP extraído en: {temp_dir_os}")

        # 3) Detectar carpeta del addon extraído
        addon_extracted_path = _find_extracted_addon_dir(temp_dir_os, addon_id)
        if not addon_extracted_path:
            log_utils.write_log("No se encontró carpeta del addon extraído con addon.xml válido.", "ERROR")
            return False

        addon_final_path = os.path.join(dest_dir_os, addon_id)

        # 4) Eliminar versión anterior (si existe)
        if os.path.exists(addon_final_path):
            log_utils.write_log(f"Eliminando versión previa en: {addon_final_path}")
            _safe_rmtree(addon_final_path)

        if monitor.abortRequested():
            log_utils.write_log("Abort solicitado antes de mover.")
            return False

        # 5) Mover a destino
        shutil.move(addon_extracted_path, addon_final_path)
        log_utils.write_log(f"{addon_id} instalado en {addon_final_path}")

        # 6) Avisar a Kodi para que refresque add-ons locales
        try:
            xbmc.executebuiltin("UpdateLocalAddons")
            xbmc.executebuiltin("UpdateAddonRepos")
        except Exception:
            pass

        return True

    except urllib.error.URLError as e:
        log_utils.write_log(f"Error de red al descargar {addon_id}: {getattr(e, 'reason', e)}", "ERROR")
        return False
    except zipfile.BadZipFile:
        log_utils.write_log("El archivo descargado no es un ZIP válido.", "ERROR")
        return False
    except Exception:
        log_utils.write_log(f"Error inesperado instalando {addon_id}.\n{traceback.format_exc()}", "ERROR")
        return False
    finally:
        # 7) Limpiar temp
        _safe_rmtree(temp_dir_os)
        log_utils.write_log(f"Temporal limpiado: {temp_dir_os}")

def install_addon_from_repo(addon_id: str, addons_xml_url: str) -> bool:
    """
    Alta de addon: resuelve URL de descarga desde addons.xml(.gz) y procede a instalar.
    """
    addon_url = get_addon_download_url(addon_id, addons_xml_url)
    if not addon_url:
        log_utils.write_log(f"No se pudo resolver la URL de {addon_id}.", "ERROR")
        return False
    return install_addon_silent(addon_id, addon_url)

# ----------------- Zerotier -----------------

def get_zerotier_ids(zerotier_cli_path="/storage/.opt/bin/zerotier-cli") -> dict:
    """
    Devuelve (nwid, address) usando:
      - nwid: de `zerotier-cli listnetworks -j` -> campo 'nwid' (o 'id' si no está 'nwid')
      - address:  de `zerotier-cli info -j`         -> campo 'address'

    En caso de no pertenecer a ninguna red, nwid = "no_networks".
    En error, devuelve ("unknown_network", "unknown_member").
    """
    if not os.path.exists(zerotier_cli_path):
        log_utils.write_log(f"[zerotier] No existe: {zerotier_cli_path}", level="WARNING")
        return "unknown_network", "unknown_member"

    nwid = "unknown_network"
    address  = "unknown_member"

    # --- Member (address) ---
    try:
        p = subprocess.run([zerotier_cli_path, "info", "-j"],
                           capture_output=True, text=True, check=True)
        info = json.loads(p.stdout)
        if isinstance(info, dict) and isinstance(info.get("address"), str):
            address = info["address"]
        else:
            log_utils.write_log(f"[zerotier] info -j JSON inesperado: {str(info)[:200]}", level="WARNING")
    except Exception as e:
        log_utils.write_log(f"[zerotier] info -j error: {e}", level="ERROR")

    # --- Network (nwid/id) ---
    try:
        p = subprocess.run([zerotier_cli_path, "listnetworks", "-j"],
                           capture_output=True, text=True, check=True)
        nets = json.loads(p.stdout)

        # `listnetworks -j` normalmente devuelve una lista de redes
        if isinstance(nets, list):
            if nets:
                # Tomamos la primera (da igual el status, se quiere el ID)
                n = nets[0]
                nwid = n.get("nwid") or n.get("id") or "unknown_network"
            else:
                nwid = "no_networks"
        elif isinstance(nets, dict):
            # Algunas versiones podrían envolver en {'networks': [...]}
            arr = nets.get("networks") or []
            if arr:
                n = arr[0]
                nwid = n.get("nwid") or n.get("id") or "unknown_network"
            else:
                nwid = "no_networks"
        else:
            log_utils.write_log(f"[zerotier] listnetworks -j JSON inesperado: {str(nets)[:200]}", level="WARNING")
    except Exception as e:
        log_utils.write_log(f"[zerotier] listnetworks -j error: {e}", level="ERROR")
        
    return {
        "nwid": nwid,
        "address": address,
    }

import os
from lib import log_utils

def get_net_info() -> dict:
    """
    Devuelve un diccionario con las direcciones MAC de eth0 y wlan0.
    Ejemplo:
        {
            "eth0": "00163e7ab45f",
            "wlan0": "unknown_mac"
        }
    """
    def _read_mac(interface: str) -> str:
        mac_path = f"/sys/class/net/{interface}/address"
        if not os.path.exists(mac_path):
            log_utils.write_log(f"[net] La interfaz '{interface}' no existe.", level="WARNING")
            return "unknown_mac"
        try:
            with open(mac_path, "r") as f:
                mac = f.read().strip().lower().replace(":", "")
                if len(mac) == 12 and all(c in "0123456789abcdef" for c in mac):
                    return mac
                else:
                    log_utils.write_log(f"[net] MAC inválida en {interface}: {mac}", level="WARNING")
                    return "unknown_mac"
        except Exception as e:
            log_utils.write_log(f"[net] Error leyendo MAC de {interface}: {e}", level="WARNING")
            return "unknown_mac"

    return {
        "eth0": _read_mac("eth0"),
        "wlan0": _read_mac("wlan0"),
    }
