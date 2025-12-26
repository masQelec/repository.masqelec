# -*- coding: utf-8 -*-

import os
import datetime
import xbmc
import xbmcgui
import xbmcvfs

from lib import utils

# Identidad del addon (centralizada en utils.py)
ADDON_ID = utils.ADDON_ID
ADDON_NAME = utils.ADDON_NAME
_addon = utils.addon  # instancia xbmcaddon.Addon

# Ruta de perfil del addon (Omega-safe)
PROFILE_PATH = xbmcvfs.translatePath(_addon.getAddonInfo("profile"))
LOG_FILE = os.path.join(PROFILE_PATH, "service.log")

# Flag de sesión para sobrescribir en la primera escritura
_first_write_done = False

def _ensure_dirs():
    if not xbmcvfs.exists(PROFILE_PATH):
        xbmcvfs.mkdirs(PROFILE_PATH)

def is_enabled() -> bool:
    """Devuelve si el log a archivo está activo vía setting activar_log"""
    try:
        return _addon.getSettingBool("activar_log")
    except Exception:
        return True

def kodi_loglevel(level: str):
    return xbmc.LOGERROR if level.upper() == "ERROR" else xbmc.LOGINFO

def write_log(message: str, level: str = "INFO"):
    """Escribe en el log de Kodi y, si está activado, en el archivo sobrescribiendo en cada arranque."""
    global _first_write_done

    # Log de Kodi
    line_kodi = f"[{ADDON_NAME}] {message}"
    try:
        xbmc.log(line_kodi, kodi_loglevel(level))
    except Exception as e:
        try:
            print(f"[{ADDON_NAME}] log_utils: fallo escribiendo log: {e}")
        except Exception:
            # Último recurso: no hacemos nada
            return

    if not is_enabled():
        return

    try:
        _ensure_dirs()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line_file = f"[{ts}] [{level}] {message}\n"

        mode = "a"
        if not _first_write_done:
            mode = "w"  # sobrescribe en la primera escritura del arranque
            _first_write_done = True

        with open(LOG_FILE, mode, encoding="utf-8") as f:
            f.write(line_file)
    except Exception as e:
        try:
            print(f"[{ADDON_NAME}] log_utils: fallo escribiendo a fichero: {e}")
        except Exception:
            return

def notify(message: str, icon=xbmcgui.NOTIFICATION_INFO, time_ms=4000, also_log=True, level="INFO"):
    """Muestra una notificación y opcionalmente la registra."""
    try:
        xbmcgui.Dialog().notification(ADDON_NAME, message, icon, time_ms)
    finally:
        if also_log:
            write_log(f"Notificación: {message}", level=level)

def get_log_file_path() -> str:
    """Ruta absoluta del archivo de log actual."""
    return LOG_FILE

