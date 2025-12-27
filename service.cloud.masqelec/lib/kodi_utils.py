# -*- coding: utf-8 -*-
"""kodi_utils.py — helpers relacionados con Kodi (idle, reinicios, notificaciones)"""

import xbmc
import xbmcgui
import subprocess

from lib import log_utils

def kodi_is_idle(min_idle_secs=0):
    """
    Heurística PERMISIVA diseñada para:
      - CleanLibrary
      - UpdateLibrary / escaneos
      - Actualización de canales/EPG PVR
    """
    try:
        if any([
            xbmc.getCondVisibility("Library.IsCleaningVideo"),
            xbmc.getCondVisibility("Library.IsScanningVideo"),
            xbmc.getCondVisibility("Library.IsCleaningMusic"),
            xbmc.getCondVisibility("Library.IsScanningMusic"),
        ]):
            return False

        if any([
            xbmc.getCondVisibility("Player.Playing"),
            xbmc.getCondVisibility("Player.Paused"),
            xbmc.getCondVisibility("Player.HasGame"),
        ]):
            return False

        if any([
            xbmc.getCondVisibility("Pvr.IsRecording"),
            xbmc.getCondVisibility("Pvr.IsRecordingTV"),
            xbmc.getCondVisibility("Pvr.IsRecordingRadio"),
        ]):
            return False

        return True

    except Exception as e:
        try:
            log_utils.write_log("[idle] Error comprobando estado: {}".format(e), level="WARNING")
        except Exception:
            pass
        return True


# ----------------- Helpers internos -----------------

def restart_kodi_with_popup(delay_ms=5000):
    """
    Muestra popup INFO con sonido avisando del reinicio y reinicia Kodi tras delay_ms.
    Centralizado para que cualquier módulo lo use.

    Texto NO se cambia (pedido del usuario).
    """
    heading = "Información"
    message = "Kodi se va a reiniciar, espere unos momentos…"

    try:
        xbmcgui.Dialog().notification(
            heading,
            message,
            xbmcgui.NOTIFICATION_INFO,
            delay_ms,
            True,  # sound
        )
    except Exception:
        try:
            log_utils.notify(message, xbmcgui.NOTIFICATION_INFO)
        except Exception:
            pass

    try:
        xbmc.sleep(int(delay_ms))
    except Exception:
        xbmc.sleep(5000)

    try:
        log_utils.write_log("[kodi] Reiniciando Kodi: systemctl restart kodi", "INFO")
        subprocess.run(["systemctl", "restart", "kodi"], check=False)
    except Exception as e:
        log_utils.write_log("[kodi] No se pudo reiniciar Kodi: {}".format(e), "ERROR")
