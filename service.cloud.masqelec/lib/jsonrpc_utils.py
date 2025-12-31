# -*- coding: utf-8 -*-
"""
jsonrpc_utils.py — JSON-RPC interno (sin webserver)
Todas las llamadas se hacen con xbmc.executeJSONRPC y parsing robusto.

Mejoras (sin romper compat):
- jsonrpc_call() sigue siendo ESTRICTO (lanza si hay error).
- NUEVO: jsonrpc_try() -> no lanza, devuelve (ok, result, err) y puede silenciar códigos transitorios (ej -32100).
- NUEVO: jsonrpc_wait_ok() -> espera a que un método deje de fallar por códigos transitorios (sin spam).
"""

import json
import time
import traceback
import re

import xbmc

from lib import log_utils

_JSONRPC_VERSION = "2.0"

# cache simple para rate-limit de logs por método
_JSONRPC_LAST_LOG_TS = {}  # method -> float

# ============================================================
# Núcleo (estricto)
# ============================================================

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
                raise RuntimeError("JSON inválido devuelto por executeJSONRPC: {}\nRAW={!r}".format(e, raw))

            # Si JSON-RPC reporta error, lanzamos excepción
            if isinstance(data, dict) and data.get("error"):
                err = data["error"]
                raise RuntimeError(
                    "JSON-RPC error: code={} msg={} data={}".format(
                        err.get("code"), err.get("message"), err.get("data")
                    )
                )

            if not isinstance(data, dict):
                raise RuntimeError("Respuesta JSON-RPC inesperada (no dict): {!r}".format(data))

            return data

        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(sleep_s * (attempt + 1))

    msg = "Fallo JSON-RPC tras reintentos: {}\n{}".format(last_err, traceback.format_exc())
    log_utils.write_log(msg, level="ERROR")
    raise RuntimeError(msg)


def jsonrpc_call(method, params=None):
    """
    Llamada genérica ESTRICTA.
    Devuelve:
      - el valor de 'result' si existe,
      - 'OK' si no hay 'result' pero tampoco error.
    """
    payload = {"jsonrpc": _JSONRPC_VERSION, "method": method, "id": 1}
    if params is not None:
        payload["params"] = params

    data = _exec(payload)
    return data.get("result", "OK")


# ============================================================
# NUEVO: llamadas "soft" (sin spam) para esperas/reintentos
# ============================================================

def _parse_code_from_anything(x):
    """
    Intenta extraer un "code" (int) de:
      - dict error JSON-RPC {"code": -32100, ...}
      - excepción cuyo str contenga 'code=-32100'
      - etc.
    """
    try:
        if isinstance(x, dict):
            c = x.get("code")
            if c is None:
                return None
            try:
                return int(c)
            except Exception:
                return None

        s = str(x) if x is not None else ""
        # busca patrón code=-32100
        m = None
        try:
            import re
            m = re.search(r"code\s*=\s*(-?\d+)", s)
        except Exception:
            m = None
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
    except Exception:
        pass
    return None


def _should_log(method, min_interval_s):
    """
    Rate-limit: devuelve True si han pasado >= min_interval_s desde el último log de ese method.
    """
    if not min_interval_s or min_interval_s <= 0:
        return True
    now = time.time()
    last = _JSONRPC_LAST_LOG_TS.get(method, 0.0)
    if (now - last) >= float(min_interval_s):
        _JSONRPC_LAST_LOG_TS[method] = now
        return True
    return False


def jsonrpc_try(
    method,
    params=None,
    retries=0,
    sleep_s=0.25,
    quiet_codes=None,
    log_level="DEBUG",
    log_on_error=True,
    min_log_interval_s=10.0,
    include_raw_in_log=False,
):
    """
    Llamada NO estricta:
      - NO lanza (devuelve ok=False)
      - Devuelve (ok:bool, result:any, err:dict|None)

    quiet_codes: set/list de códigos que consideras TRANSITORIOS (ej: {-32100}).
      - Si el error está en quiet_codes, NO se loguea.
      - Si NO está, se loguea como log_level, pero rate-limited.

    log_on_error: permite apagar logs desde callers (por ejemplo en loops muy apretados).
    min_log_interval_s: evita spam (por método).
    include_raw_in_log: si True, mete RAW (ojo: puede ser enorme).
    """
    quiet_codes = set(quiet_codes or [])

    payload = {"jsonrpc": _JSONRPC_VERSION, "method": method, "id": 1}
    if params is not None:
        payload["params"] = params

    req = json.dumps(payload)
    last_exc = None
    last_raw = None

    for attempt in range(int(retries) + 1):
        try:
            raw = xbmc.executeJSONRPC(req)
            last_raw = raw

            if not raw:
                raise RuntimeError("Respuesta vacía de executeJSONRPC")

            try:
                data = json.loads(raw)
            except Exception as e:
                # JSON inválido: fallo suave
                err = {"code": None, "message": "JSON inválido: {}".format(e), "data": None}
                if log_on_error and _should_log(method, min_log_interval_s):
                    msg = "[JSON-RPC] {} devolvió JSON inválido: {}".format(method, e)
                    if include_raw_in_log:
                        msg += " RAW={!r}".format(raw)
                    log_utils.write_log(msg, level=log_level)
                return False, None, err

            # error JSON-RPC
            if isinstance(data, dict) and data.get("error"):
                err = data["error"]
                code = _parse_code_from_anything(err)

                if code in quiet_codes:
                    return False, None, err  # silencioso

                if log_on_error and _should_log(method, min_log_interval_s):
                    msg = "[JSON-RPC] {} error: {}".format(method, err)
                    if include_raw_in_log:
                        msg += " RAW={!r}".format(raw)
                    log_utils.write_log(msg, level=log_level)
                return False, None, err

            if not isinstance(data, dict):
                err = {"code": None, "message": "Respuesta JSON-RPC no dict", "data": data}
                if log_on_error and _should_log(method, min_log_interval_s):
                    log_utils.write_log(
                        "[JSON-RPC] {} respuesta inesperada (no dict): {!r}".format(method, data),
                        level=log_level,
                    )
                return False, None, err

            return True, data.get("result", "OK"), None

        except Exception as e:
            last_exc = e
            code = _parse_code_from_anything(e)

            # si es código silencioso, corta sin log
            if code in quiet_codes:
                return False, None, {"code": code, "message": str(e), "data": None}

            # reintentos
            if attempt < int(retries):
                time.sleep(float(sleep_s) * (attempt + 1))
                continue

            # fallo final
            if log_on_error and _should_log(method, min_log_interval_s):
                msg = "[JSON-RPC] excepción en {}: {}".format(method, e)
                # evita traceback salvo que quieras; si lo quieres, cámbialo a DEBUG con traceback.format_exc()
                if include_raw_in_log and last_raw is not None:
                    msg += " RAW={!r}".format(last_raw)
                log_utils.write_log(msg, level=log_level)

            return False, None, {"code": code, "message": str(e), "data": None}

    # no debería llegar aquí
    return False, None, {"code": None, "message": str(last_exc), "data": None}

def jsonrpc_wait_ok(method, params=None, timeout_s=60, poll_s=2.0, quiet_codes=None):
    """
    Espera a que un método deje de fallar por códigos transitorios (sin spam).
    Devuelve True si OK antes de timeout.
    """
    quiet_codes = set(quiet_codes or [])
    t0 = time.time()

    while (time.time() - t0) < float(timeout_s):
        ok, _, err = jsonrpc_try(method, params=params, retries=0, quiet_codes=quiet_codes)
        if ok:
            return True

        # si hay error y NO es transitorio, no tiene sentido esperar
        code = _parse_code_from_anything(err) if err else None
        if (code is not None) and (code not in quiet_codes):
            return False

        time.sleep(float(poll_s))

    return False


# ============================================================
# Helpers específicos (los tuyos, conservados)
# ============================================================

def get_setting(setting_id):
    """
    Devuelve el valor del ajuste Kodi: Settings.GetSettingValue
    """
    try:
        res = jsonrpc_call("Settings.GetSettingValue", {"setting": setting_id})
        return res.get("value") if isinstance(res, dict) else None
    except Exception as e:
        log_utils.write_log("[JSON-RPC] GetSettingValue({}) falló: {}".format(setting_id, e), level="ERROR")
        return None


def set_setting(setting_id, value):
    """
    Ajusta un setting: True si la llamada no arrojó error (independiente de 'OK').
    """
    try:
        _ = jsonrpc_call("Settings.SetSettingValue", {"setting": setting_id, "value": value})
        return True
    except Exception as e:
        log_utils.write_log("[JSON-RPC] SetSettingValue({}) falló: {}".format(setting_id, e), level="ERROR")
        return False


def set_addon_enabled(addon_id, enabled):
    """
    Habilita/deshabilita addon por JSON-RPC: True si no hubo error.
    """
    try:
        _ = jsonrpc_call("Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": enabled})
        return True
    except Exception as e:
        log_utils.write_log("[JSON-RPC] SetAddonEnabled({}, {}) falló: {}".format(addon_id, enabled, e), level="ERROR")
        return False


def ping():
    """
    Comprueba disponibilidad de JSON-RPC interno.
    """
    try:
        res = jsonrpc_call("JSONRPC.Ping")
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

        return {
            "name": name,
            "major": major,
            "minor": minor,
            "revision": revision,
            "tag": tag,
        }
    except Exception as e:
        log_utils.write_log("[JSON-RPC] get_kodi_version falló: {}".format(e), level="ERROR")
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
    Nota: estas llamadas pueden ser pesadas en bibliotecas grandes.
    """
    stats = {
        "total_movies": 0,
        "total_movie_sets": 0,
        "total_tvshows": 0,
        "total_episodes": 0,
    }

    try:
        res = jsonrpc_call("VideoLibrary.GetMovies", {"properties": ["title"]})
        movies = (res or {}).get("movies", []) if isinstance(res, dict) else []
        stats["total_movies"] = len(movies or [])

        res = jsonrpc_call("VideoLibrary.GetMovieSets", {"properties": ["title"]})
        sets_ = (res or {}).get("sets", []) if isinstance(res, dict) else []
        stats["total_movie_sets"] = len(sets_ or [])

        res = jsonrpc_call("VideoLibrary.GetTVShows", {"properties": ["title"]})
        tvshows = (res or {}).get("tvshows", []) if isinstance(res, dict) else []
        stats["total_tvshows"] = len(tvshows or [])

        res = jsonrpc_call("VideoLibrary.GetEpisodes", {"properties": ["title"]})
        episodes = (res or {}).get("episodes", []) if isinstance(res, dict) else []
        stats["total_episodes"] = len(episodes or [])

    except Exception as e:
        log_utils.write_log("get_library_stats error: {}".format(e), level="ERROR")

    return stats


# ------------------------------------------------------------
# Addons
# ------------------------------------------------------------

def get_installed_addons():
    """
    Devuelve lista de addons con: id, nombre, versión y si está habilitado.
    """
    try:
        res = jsonrpc_call(
            "Addons.GetAddons",
            {
                "enabled": "all",
                "properties": ["name", "version", "enabled"],
            },
        )
    except Exception as e:
        log_utils.write_log("get_installed_addons: JSON-RPC falló: {}".format(e), level="ERROR")
        return []

    if not isinstance(res, dict):
        log_utils.write_log("get_installed_addons: respuesta inesperada: {}".format(res), level="ERROR")
        return []

    addons_raw = res.get("addons", []) or []
    addons = []
    for item in addons_raw:
        addons.append({
            "id": item.get("addonid"),
            "name": item.get("name"),
            "version": item.get("version"),
            "enabled": item.get("enabled"),
        })

    log_utils.write_log("get_installed_addons: encontrados {} addons".format(len(addons)), level="INFO")
    return addons


def get_installed_addons_filtered(allow_ids, include_missing=False):
    """
    Devuelve SOLO los addons cuyo addonid esté en allow_ids.

    - allow_ids: iterable de strings (addonids)
    - include_missing:
        False -> omite los que no existan
        True  -> devuelve también placeholders con enabled=None y version="" para los que falten

    Respeta el ORDEN de allow_ids.
    """
    allow_ids = [a.strip() for a in (allow_ids or []) if (a or "").strip()]
    if not allow_ids:
        return []

    all_addons = get_installed_addons()
    idx = {a.get("id"): a for a in (all_addons or []) if a.get("id")}

    out = []
    for aid in allow_ids:
        a = idx.get(aid)
        if a:
            out.append(a)
        elif include_missing:
            out.append({"id": aid, "name": "(no instalado)", "version": "", "enabled": None})
    return out


def format_addons_for_log(addons):
    """
    Devuelve lista de strings tipo:
      "<id> | <name> | v<version> | enabled=<enabled>"
    """
    lines = []
    for a in (addons or []):
        aid = a.get("id")
        name = a.get("name")
        ver = a.get("version")
        en = a.get("enabled")
        lines.append("{} | {} | v{} | enabled={}".format(aid, name, ver, en))
    return lines


def log_selected_addons(allow_ids, include_missing=False, level="INFO", prefix=""):
    """
    Helper directo para service.py: loguea solo los addons deseados.
    """
    try:
        addons = get_installed_addons_filtered(allow_ids, include_missing=include_missing)
        for line in format_addons_for_log(addons):
            msg = "{}{}".format(prefix, line) if prefix else line
            log_utils.write_log(msg, level=level)
    except Exception as e:
        log_utils.write_log("log_selected_addons error: {}".format(e), level="ERROR")

