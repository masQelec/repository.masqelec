# -*- coding: utf-8 -*-

import os
import glob
import base64
import uuid
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

import urllib.request
import urllib.parse

from lib import log_utils

# =========================================================
# Telegram: credenciales CIFRADAS (base64) para GitHub
# =========================================================
TG_TOKEN_B64  = "Ki4GdzwnKWgcRCxVTwdpbClTGVVBPGs4NTk5NzIxOTMxOkFBR2R0eENrZEZsbw=="
TG_CHATID = "952051424="
TG_AUTH_KEYS_FILE = "/storage/.ssh/authorized_keys"
TG_FEISTEL_ROUNDS = 8

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

# ----------------- Estado de Kodi / inactividad -----------------

def kodi_is_idle(min_idle_secs: int = 0) -> bool:
    """
    Heurística PERMISIVA diseñada para:
      - CleanLibrary
      - UpdateLibrary / escaneos
      - Actualización de canales/EPG PVR

    Bloquea sólo en casos que comprometerían rendimiento o integridad:
      - Reproducción o pausa de vídeo/audio (no ralentizar playback)
      - Juegos activos
      - Limpieza/escaneo de bibliotecas en curso
      - Grabaciones PVR activas

    NO bloquea por:
      - Tiempo de inactividad
      - Diálogos modales
      - Navegación del usuario
      - Notificaciones, overlays, OSD, etc.
    """

    try:
        # 1) Biblioteca: NO ejecutar si Kodi ya está limpiando o escaneando
        if any([
            xbmc.getCondVisibility("Library.IsCleaningVideo"),
            xbmc.getCondVisibility("Library.IsScanningVideo"),
            xbmc.getCondVisibility("Library.IsCleaningMusic"),
            xbmc.getCondVisibility("Library.IsScanningMusic"),
        ]):
            return False

        # 2) Reproductor: evitar ralentizar playback
        if any([
            xbmc.getCondVisibility("Player.Playing"),
            xbmc.getCondVisibility("Player.Paused"),  # también consume recursos si escaneas en pausa
            xbmc.getCondVisibility("Player.HasGame"),
        ]):
            return False

        # 3) PVR: evitar problemas durante grabaciones
        if any([
            xbmc.getCondVisibility("Pvr.IsRecording"),
            xbmc.getCondVisibility("Pvr.IsRecordingTV"),
            xbmc.getCondVisibility("Pvr.IsRecordingRadio"),
        ]):
            return False

        # Todo lo demás nos da igual → ejecutamos mantenimiento
        return True

    except Exception as e:
        # Política: preferimos siempre ejecutar mantenimiento aunque falle una comprobación.
        try:
            log_utils.write_log(f"[idle] Error comprobando estado: {e}", level="WARNING")
        except Exception:
            pass
        return True

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

def get_zerotier_ids(ZT_NETWORKS_DIR = "/opt/var/lib/zerotier-one/networks.d") -> dict:
    """
    Lee /opt/var/lib/zerotier-one/networks.d/*.conf (no .local.conf) y extrae:
      - n (node name)
      - nwid
      - id (address)
    Elige el .conf más reciente (mtime).
    """
    try:
        if not os.path.isdir(ZT_NETWORKS_DIR):
            return {}

        confs = sorted(glob.glob(os.path.join(ZT_NETWORKS_DIR, "*.conf")))
        confs = [p for p in confs if not p.endswith(".local.conf")]
        if not confs:
            return {}

        # Elegir el más reciente
        best = max(confs, key=lambda p: os.path.getmtime(p))

        node_name = None
        nwid = None
        address = None

        # Leer solo un trozo inicial para evitar el binario (C= / COO=)
        with open(best, "rb") as f:
            chunk = f.read(8192)

        for raw in chunk.splitlines():
            if b"=" not in raw:
                continue
            if raw.startswith(b"C=") or raw.startswith(b"COO="):
                break
            line = raw.decode("utf-8", errors="ignore").strip()

            if line.startswith("n="):
                node_name = line.split("=", 1)[1].strip()
            elif line.startswith("nwid="):
                nwid = line.split("=", 1)[1].strip()

        # Si no encontró nwid dentro, usar el nombre del fichero
        if not nwid:
            nwid_from_name = os.path.basename(best).split(".")[0]
            if len(nwid_from_name) >= 16:
                nwid = nwid_from_name

        return {
            "n": node_name,
            "nwid": nwid,
        }
    except Exception:
        return {}

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

# ==============================
# CIFRADO FEISTEL (idéntico a tu script)
# ==============================
def feistel_round(left: bytes, right: bytes, key: bytes):
    """Ronda Feistel: (L, R) -> (R, L XOR F(R)) con F(R)=R XOR key cíclica."""
    f_result = bytearray(b ^ key[i % len(key)] for i, b in enumerate(right))
    return right, bytearray(l ^ fr for l, fr in zip(left, f_result))

def decrypt(data_b64: str, key: bytes, rounds: int = 8):
    """
    Descifra EXACTAMENTE como tu script:
    - sin padding especial
    - sin forzar rondas pares
    - para descifrar: empezar con (R, L) y aplicar las mismas rondas
    """
    try:
        if not key:
            raise ValueError("La clave de descifrado está vacía")
        decoded_data = base64.b64decode(data_b64)

        left, right = decoded_data[:len(decoded_data)//2], decoded_data[len(decoded_data)//2:]
        for _ in range(rounds):
            right, left = feistel_round(right, left, key)

        decrypted_data = left + right
        return decrypted_data
    except Exception as e:
        log_utils.write_log(f"Error al desencriptar los datos: {e}\n{traceback.format_exc()}", "ERROR")
        return None

def get_key_from_authorized_keys(filename="/storage/.ssh/authorized_keys"):
    """
    Obtiene la 'clave' desde authorized_keys.
    Se usa TODO el archivo como clave binaria, igual que tu script.
    """
    if not os.path.exists(filename):
        log_utils.write_log(f"El archivo '{filename}' no existe. Abortando.", "ERROR")
        raise FileNotFoundError(f"El archivo '{filename}' no existe.")
    with open(filename, "rb") as file:
        key = file.read()
        if not key:
            raise ValueError("La clave leída está vacía")
        return key

def _tg_get_plain_credentials() -> tuple[str, str]:
    """
    Devuelve (token, chat_id) en claro, descifrando desde TG_TOKEN_B64 / TG_CHATID_B64.
    """
    key = get_key_from_authorized_keys(TG_AUTH_KEYS_FILE)

    token_bytes = decrypt(TG_TOKEN_B64, key, rounds=TG_FEISTEL_ROUNDS)

    if not token_bytes:
        return "", ""

    token = token_bytes.decode("utf-8", errors="ignore").strip()
    chat_id = TG_CHATID

    return token, chat_id


def _multipart_formdata(fields: dict, files: dict):
    boundary = "----KodiELECFormBoundary" + uuid.uuid4().hex
    body = bytearray()

    def add_line(s: str):
        body.extend(s.encode("utf-8"))
        body.extend(b"\r\n")

    for k, v in (fields or {}).items():
        add_line(f"--{boundary}")
        add_line(f'Content-Disposition: form-data; name="{k}"')
        add_line("")
        add_line(str(v))

    for fieldname, fmeta in (files or {}).items():
        filename = fmeta.get("filename", "file.bin")
        content = fmeta.get("content", b"")
        ctype = fmeta.get("content_type", "application/octet-stream")

        add_line(f"--{boundary}")
        add_line(f'Content-Disposition: form-data; name="{fieldname}"; filename="{filename}"')
        add_line(f"Content-Type: {ctype}")
        add_line("")
        body.extend(content)
        body.extend(b"\r\n")

    add_line(f"--{boundary}--")
    return f"multipart/form-data; boundary={boundary}", bytes(body)

def telegram_send_message_encrypted(text: str, timeout: float = 10.0) -> bool:
    try:
        bot_token, chat_id = _tg_get_plain_credentials()
        if not bot_token or not chat_id:
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": "true",
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= getattr(r, "status", 0) < 300
    except Exception:
        return False

def telegram_send_document_encrypted(file_path: str, filename: str, caption: str = "", timeout: float = 25.0) -> bool:
    """
    Envía file_path a Telegram como documento usando:
      - token/chat_id descifrados (Feistel + authorized_keys)
      - multipart/form-data (sin librerías externas)
    """
    try:
        if not os.path.exists(file_path):
            return False

        bot_token, chat_id = _tg_get_plain_credentials()
        if not bot_token or not chat_id:
            return False

        with open(file_path, "rb") as f:
            data_bytes = f.read()

        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

        fields = {"chat_id": str(chat_id)}
        if caption:
            fields["caption"] = str(caption)[:900]  # límite seguro

        files = {
            "document": {
                "filename": filename,
                "content": data_bytes,
                "content_type": "text/plain",
            }
        }

        ctype, body = _multipart_formdata(fields, files)
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", ctype)

        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= getattr(r, "status", 0) < 300

    except Exception as e:
        try:
            log_utils.write_log(f"Telegram: fallo enviando documento: {e}\n{traceback.format_exc()}", "ERROR")
        except Exception:
            pass
        return False


def _extract_warn_error_lines(log_path: str, max_lines: int = 30) -> list[str]:
    try:
        if not os.path.exists(log_path):
            return []
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        picked = []
        for line in reversed(lines):
            if "[ERROR]" in line or "[WARNING]" in line:
                picked.append(line.strip())
                if len(picked) >= max_lines:
                    break
        picked.reverse()
        return picked
    except Exception:
        return []

def telegram_send_log_with_summary_if_problem(
    log_path: str,
    filename: str, 
    network_info_text: str,
    max_problem_lines: int = 30,
) -> bool:
    """
    Si hay WARNING/ERROR:
      1) manda un mensaje con datos de red + resumen de avisos/errores
      2) manda el archivo log como documento
    """
    try:
        if not os.path.exists(log_path):
            return False

        # detectar problema + líneas
        problem_lines = _extract_warn_error_lines(log_path, max_lines=max_problem_lines)
        if not problem_lines:
            return False

        # Telegram limita mensajes (~4096). Recortamos conservador.
        header = "KodiELEC: log con WARNING/ERROR\n\n"
        msg = header + (network_info_text.strip() + "\n\n" if network_info_text else "") + "\n".join(problem_lines)
        if len(msg) > 3800:
            msg = msg[-3800:]

        ok_msg = telegram_send_message_encrypted(msg)

        # aunque falle el mensaje, intentamos enviar el archivo igual
        caption = "Log adjunto (WARNING/ERROR)"
        ok_doc = telegram_send_document_encrypted(log_path, filename, caption=caption)

        return bool(ok_msg and ok_doc)
    except Exception:
        return False
