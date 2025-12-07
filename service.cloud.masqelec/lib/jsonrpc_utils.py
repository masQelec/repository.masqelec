# -*- coding: utf-8 -*-
"""
jsonrpc_utils.py — JSON-RPC interno (sin webserver)
Todas las llamadas se hacen con xbmc.executeJSONRPC y parsing robusto.
"""

import json
import time
import traceback

import xbmc

from lib import log_utils

_JSONRPC_VERSION = "2.0"

def _exec(payload, retries=2, sleep_s=0.3):
    """
    Ejecuta una llamada JSON-RPC interna con reintentos.
    Devuelve el dict parseado o lanza excepción si hay error.
    """
    last_err = None
    req = json.dumps(payload)

    for attempt in range(retries + 1):
        try:
            raw = xbmc.executeJSONRPC(req)
            if not raw:
                raise RuntimeError("Respuesta vacía de executeJSONRPC")

            try:
                data = json.loads(raw)
            except Exception as e:
                raise RuntimeError(f"JSON inválido devuelto por executeJSONRPC: {e}\nRAW={raw!r}")

            # Si JSON-RPC reporta error, lanzamos excepción
            if data.get("error"):
                err = data["error"]
                raise RuntimeError(f"JSON-RPC error: code={err.get('code')} msg={err.get('message')} data={err.get('data')}")

            return data

        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(sleep_s * (attempt + 1))

    msg = f"Fallo JSON-RPC tras reintentos: {last_err}\n{traceback.format_exc()}"
    log_utils.write_log(msg, level="ERROR")
    raise RuntimeError(msg)


def jsonrpc_call(method, params=None):
    """import json
import xbmc
from lib import log_utils
    Llamada genérica. Devuelve:
      - el valor de 'result' si existe,
      - 'OK' si no hay 'result' pero tampoco error.
    """
    payload = {"jsonrpc": _JSONRPC_VERSION, "method": method, "id": 1}
    if params is not None:
        payload["params"] = params

    data = _exec(payload)
    return data.get("result", "OK")


# ------------------------------
# Helpers específicos
# ------------------------------

def get_setting(setting_id):
    """
    Devuelve el valor del ajuste Kodi: Settings.GetSettingValue
    """
    try:
        res = jsonrpc_call("Settings.GetSettingValue", {"setting": setting_id})
        return res.get("value") if isinstance(res, dict) else None
    except Exception as e:
        log_utils.write_log(f"[JSON-RPC] GetSettingValue({setting_id}) falló: {e}", level="ERROR")
        return None


def set_setting(setting_id, value):
    """
    Ajusta un setting: True si la llamada no arrojó error (independiente de 'OK').
    """
    try:
        _ = jsonrpc_call("Settings.SetSettingValue", {"setting": setting_id, "value": value})
        return True
    except Exception as e:
        log_utils.write_log(f"[JSON-RPC] SetSettingValue({setting_id}) falló: {e}", level="ERROR")
        return False


def set_addon_enabled(addon_id, enabled):
    """
    Habilita/deshabilita addon por JSON-RPC: True si no hubo error.
    """
    try:
        _ = jsonrpc_call("Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": enabled})
        return True
    except Exception as e:
        log_utils.write_log(f"[JSON-RPC] SetAddonEnabled({addon_id},{enabled}) falló: {e}", level="ERROR")
        return False


def ping():
    """
    Comprueba disponibilidad de JSON-RPC interno.
    """
    try:
        res = jsonrpc_call("JSONRPC.Ping")
        # Respuesta típica: "pong"
        return (isinstance(res, str) and res.lower() == "pong") or (isinstance(res, dict) and res.get("ping") == "pong")
    except Exception:
        return False


def get_kodi_version():
    """
    Obtiene la versión de Kodi (name, major, minor, revision, tag).
    Devuelve un dict o None en error.
    """
    try:
        res = jsonrpc_call("Application.GetProperties", {"properties": ["version", "name"]})
        if not res or "version" not in res:
            log_utils.write_log("[JSON-RPC] No se pudo obtener la versión de Kodi", level="ERROR")
            return None

        version_info = res["version"]
        name = res.get("name", "Kodi")
        major = version_info.get("major")
        minor = version_info.get("minor")
        revision = version_info.get("revision")
        tag = version_info.get("tag")

        info = {
            "name": name,
            "major": major,
            "minor": minor,
            "revision": revision,
            "tag": tag,
        }
        return info
    except Exception as e:
        log_utils.write_log(f"[JSON-RPC] get_kodi_version falló: {e}", level="ERROR")
        return None

# ------------------------------------------------------------
# Estadísticas de biblioteca (películas, sets, series, episodios)
# ------------------------------------------------------------
def get_library_stats():
    """
    Devuelve estadísticas de la videoteca:
      - total_movies
      - total_movie_sets
      - total_tvshows
      - total_episodes
    """
    stats = {
        "total_movies": 0,
        "total_movie_sets": 0,
        "total_tvshows": 0,
        "total_episodes": 0
    }

    try:
        # ---------- Películas ----------
        r = xbmc.executeJSONRPC(json.dumps({
            "jsonrpc": "2.0", "method": "VideoLibrary.GetMovies",
            "params": {"properties": ["title"]}, "id": 1
        }))
        data = json.loads(r)
        stats["total_movies"] = len(data.get("result", {}).get("movies", []) or [])

        # ---------- Sets / Sagas ----------
        r = xbmc.executeJSONRPC(json.dumps({
            "jsonrpc": "2.0", "method": "VideoLibrary.GetMovieSets",
            "params": {"properties": ["title"]}, "id": 2
        }))
        data = json.loads(r)
        stats["total_movie_sets"] = len(data.get("result", {}).get("sets", []) or [])

        # ---------- Series ----------
        r = xbmc.executeJSONRPC(json.dumps({
            "jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows",
            "params": {"properties": ["title"]}, "id": 3
        }))
        data = json.loads(r)
        stats["total_tvshows"] = len(data.get("result", {}).get("tvshows", []) or [])

        # ---------- Episodios ----------
        r = xbmc.executeJSONRPC(json.dumps({
            "jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes",
            "params": {"properties": ["title"]}, "id": 4
        }))
        data = json.loads(r)
        stats["total_episodes"] = len(data.get("result", {}).get("episodes", []) or [])

    except Exception as e:
        log_utils.write_log(f"get_library_stats error: {e}", level="ERROR")

    return stats

