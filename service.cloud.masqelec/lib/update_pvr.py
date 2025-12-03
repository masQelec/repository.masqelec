# -*- coding: utf-8 -*-
"""
update_pvr.py — Gestión de PVR:
- Playlist con USER_CODE/PASS_CODE
- Instalación/actualización del addon
- Edición segura de instance-settings-1.xml (siempre con el addon detenido)
- Deshabilitar PVR/servicios conflictivos (opcional por ajuste)
- Limpieza de DB (TV*.db/Epg*.db) si hubo cambios
- Reinicio del PVR y espera hasta estar “listo” (canales/EPG)

Ajustes usados (leer vía utils):
- pvr_disable_conflicts (bool)            -> deshabilitar otros PVR clients
- pvr_disable_conflict_services (bool)    -> deshabilitar servicios conflictivos
"""

import os
import re
import time
import urllib.request
import traceback
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, List

import xbmc
import xbmcvfs
import json

from lib import jsonrpc_utils
from lib import log_utils
from lib import rclone_utils
from lib import utils

# ------------------------------
# Utilidades JSON-RPC “suaves”
# ------------------------------

def _jsonrpc_call_soft(method: str, params: dict | None = None):
    """
    Versión 'suave' de JSON-RPC:
      - No lanza excepción si hay error
      - Devuelve (ok, result, error_dict)
    """
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params is not None:
            payload["params"] = params
        raw = xbmc.executeJSONRPC(json.dumps(payload))
        if not raw:
            return False, None, {"message": "Respuesta vacía"}
        data = json.loads(raw)
        if data.get("error"):
            return False, None, data["error"]
        return True, data.get("result"), None
    except Exception as e:
        return False, None, {"message": str(e)}

def _path_database() -> str:
    try:
        return xbmcvfs.translatePath("special://database")
    except Exception:
        return "/storage/.kodi/userdata/Database/"

def _path_profile() -> str:
    try:
        return xbmcvfs.translatePath("special://profile")
    except Exception:
        return "/storage/.kodi/userdata/"

def _path_addons() -> str:
    try:
        return xbmcvfs.translatePath("special://home/addons")
    except Exception:
        return "/storage/.kodi/addons"

def _ensure_dir(path: str):
    if not xbmcvfs.exists(path):
        xbmcvfs.mkdirs(path)

# ------------------------------
# Descarga robusta (reintentos + atómica)
# ------------------------------

def _download_to(path_dst: str, url: str, retries: int = 2, timeout: int = 20) -> bool:
    tmp = path_dst + ".part"
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Kodi-addon/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
                f.write(r.read())
            os.replace(tmp, path_dst)
            return True
        except Exception as e:
            last_err = e
            time.sleep(1.2 * (attempt + 1))
    log_utils.write_log(f"[pvr] Descarga fallida {url}: {last_err}", level="ERROR")
    try:
        if os.path.exists(tmp):
            os.remove(tmp)
    except Exception:
        pass
    return False

# ------------------------------
# Playlist (m3u) con USER_CODE/PASS_CODE
# ------------------------------

def update_playlist(reload_if_enabled: bool = True) -> tuple[bool, bool]:
    """
    Descarga la plantilla, sustituye USER_CODE/PASS_CODE y compara con la local.
    - Si falta /storage/.user/user: intenta recuperarlo del remoto masqelec:masqelec/user/<nwid>_<eth0>.
      Para ello usa rclone_utils.copy_remote_to_tmp_then_move(remote, remote_path, final_dir) con final_dir="/tmp",
      valida y, si es correcto, lo instala en /storage/.user/user.
    - Solo escribe la playlist si cambia.
    - Si cambia y reload_if_enabled=True y pvr.hts está habilitado, lo recarga.
    Retorna: (ok, changed)
    """
    user_dir = "/storage/.user"
    playlist_file = os.path.join(user_dir, "playlist.m3u")
    user_file = os.path.join(user_dir, "user")
    base_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/playlist.m3u"

    def _read_text(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _has_valid_creds(txt: str) -> bool:
        m_user = re.search(r'USER_CODE="([^"]+)"', txt)
        m_pass = re.search(r'PASS_CODE="([^"]+)"', txt)
        return bool(m_user and m_pass and m_user.group(1).strip() and m_pass.group(1).strip())

    def _try_fetch_user_from_remote() -> bool:
        """
        Intenta traer masqelec:masqelec/user/<nwid>_<eth0> a /tmp usando
        rclone_utils.copy_remote_to_tmp_then_move(..., final_dir="/tmp").
        Si el archivo es válido, lo instala en /storage/.user/user (atómico).
        """
        try:
            nwid = "nonwid"
            eth0 = "nomac"
            try:
                zt = utils.get_zerotier_ids() or {}
                nwid = (zt.get("nwid") or "").strip() or nwid
            except Exception:
                pass
            try:
                ni = utils.get_net_info() or {}
                eth0 = (ni.get("eth0") or "").strip().replace(":", "").lower() or eth0
            except Exception:
                pass

            remote = "masqelec"
            remote_path = f"masqelec/user/{nwid}_{eth0}"
            tmp_dir = "/tmp"
            tmp_file = os.path.join(tmp_dir, f"{nwid}_{eth0}")

            ok = False
            try:
                ok = rclone_utils.copy_remote_to_tmp_then_move(remote, remote_path, tmp_dir)
            except Exception as e:
                log_utils.write_log(f"[update_playlist] rclone copy failed: {e}\n{traceback.format_exc()}", level="ERROR")
                ok = False

            if not ok or not os.path.exists(tmp_file):
                log_utils.write_log(f"[update_playlist] No se encontró user remoto en {remote}:{remote_path}", level="INFO")
                return False

            txt = _read_text(tmp_file)
            if not _has_valid_creds(txt):
                log_utils.write_log("[update_playlist] Archivo remoto user inválido (faltan USER_CODE/PASS_CODE).", level="WARNING")
                try: os.remove(tmp_file)
                except Exception: pass
                return False

            os.makedirs(user_dir, exist_ok=True)
            tmp_install = user_file + ".part"
            with open(tmp_install, "w", encoding="utf-8") as f:
                f.write(txt)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_install, user_file)
            try: os.remove(tmp_file)
            except Exception: pass

            log_utils.write_log(f"[update_playlist] user recuperado del remoto ({nwid}_{eth0}) e instalado en {user_file}")
            return True
        except Exception as e:
            log_utils.write_log(f"[update_playlist] Error en _try_fetch_user_from_remote: {e}\n{traceback.format_exc()}", level="ERROR")
            return False

    try:
        os.makedirs(user_dir, exist_ok=True)

        # Si no existe user local, intentar recuperarlo del remoto
        if not os.path.exists(user_file):
            if not _try_fetch_user_from_remote():
                log_utils.write_log("Archivo /storage/.user/user no encontrado y no disponible en remoto.", level="ERROR")
                return False, False

        # Descargar plantilla a <file>.remote.part y leerla
        if not _download_to(playlist_file + ".remote.part", base_url):
            log_utils.write_log("Fallo al descargar plantilla de playlist.", level="ERROR")
            try:
                if os.path.exists(playlist_file + ".remote.part"):
                    os.remove(playlist_file + ".remote.part")
            except Exception:
                pass
            return False, False

        try:
            remote_tpl = _read_text(playlist_file + ".remote.part")
        finally:
            try: os.remove(playlist_file + ".remote.part")
            except Exception: pass

        content = _read_text(user_file)
        user_code_m = re.search(r'USER_CODE="([^"]+)"', content)
        pass_code_m = re.search(r'PASS_CODE="([^"]+)"', content)
        if not user_code_m or not pass_code_m or not user_code_m.group(1).strip() or not pass_code_m.group(1).strip():
            log_utils.write_log("USER_CODE o PASS_CODE ausentes o vacíos en /storage/.user/user", level="WARNING")
            return False, False

        new_playlist = remote_tpl.replace("USER_CODE", user_code_m.group(1)).replace("PASS_CODE", pass_code_m.group(1))
        new_playlist_norm = new_playlist.replace("\r\n", "\n").replace("\r", "\n")

        local_exists = os.path.exists(playlist_file)
        if local_exists:
            local_norm = _read_text(playlist_file).replace("\r\n", "\n").replace("\r", "\n")
        else:
            local_norm = None

        if local_exists and local_norm == new_playlist_norm:
            log_utils.write_log(f"Playlist sin cambios: {playlist_file}")
            return True, False

        tmp = playlist_file + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(new_playlist_norm)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, playlist_file)
        log_utils.write_log(f"Playlist {'creada' if not local_exists else 'actualizada'}: {playlist_file}")

        if reload_if_enabled:
            enabled = _get_addon_enabled_state("pvr.hts")
            if enabled:
                log_utils.write_log("Playlist modificada y PVR habilitado → recargando PVR…")
                if restart_pvr_addon("pvr.hts", wait_ready=True):
                    log_utils.write_log("PVR recargado tras cambiar la playlist.")
                else:
                    log_utils.write_log("No se pudo recargar PVR automáticamente.", level="WARNING")

        return True, True

    except Exception as e:
        log_utils.write_log(f"Error en update_playlist: {e}\n{traceback.format_exc()}", level="ERROR")
        try:
            tmp = playlist_file + ".part"
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False, False


# ------------------------------
# JSON-RPC helpers (compatibles y silenciosos)
# ------------------------------

def _get_addon_details(addon_id: str) -> Optional[dict]:
    """
    Devuelve detalles mínimos del addon sin generar warnings:
    - Primero intenta Addons.GetAddonDetails con propiedades seguras (soft).
    - Si no está soportado o devuelve error (p.ej. -32602), cae a GetAddons.
    """
    ok, res, _ = _jsonrpc_call_soft(
        "Addons.GetAddonDetails",
        {"addonid": addon_id, "properties": ["enabled", "name"]}
    )
    if ok and isinstance(res, dict) and res.get("addon"):
        return res["addon"]

    ok2, res2, _ = _jsonrpc_call_soft(
        "Addons.GetAddons",
        {"properties": ["enabled", "name"], "enabled": "all"}
    )
    if ok2 and isinstance(res2, dict):
        for a in res2.get("addons", []):
            if a.get("addonid") == addon_id:
                return a

    ok3, res3, _ = _jsonrpc_call_soft("Addons.GetAddons", {"enabled": "all"})
    if ok3 and isinstance(res3, dict):
        for a in res3.get("addons", []):
            if a.get("addonid") == addon_id:
                return a
    return None

def _get_addon_enabled_state(addon_id: str) -> Optional[bool]:
    det = _get_addon_details(addon_id)
    return None if det is None else bool(det.get("enabled"))

def _set_addon_enabled(addon_id: str, enabled: bool) -> bool:
    """
    Intenta con JSON-RPC 'suave' y, si no queda en el estado deseado,
    usa los builtins de Kodi. Evita logs ruidosos.
    """
    ok, _, _ = _jsonrpc_call_soft("Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": enabled})
    if ok:
        state = _get_addon_enabled_state(addon_id)
        if state is not None and state == enabled:
            return True

    # Fallback builtins (no webserver)
    try:
        xbmc.executebuiltin(f'{"EnableAddon" if enabled else "DisableAddon"}("{addon_id}")')
        xbmc.sleep(900)
        state = _get_addon_enabled_state(addon_id)
        return state is not None and state == enabled
    except Exception:
        return False

# ------------------------------
# PVR listados y conflictos
# ------------------------------

def _list_pvr_clients() -> List[dict]:
    """
    Devuelve lista de PVR clients con 'addonid' y 'enabled'.
    - Si 'type=xbmc.pvrclient' no está soportado (-32602), usa fallback.
    """
    ok, res, err = _jsonrpc_call_soft(
        "Addons.GetAddons",
        {"type": "xbmc.pvrclient", "properties": ["enabled"], "enabled": "all"}
    )
    if ok and isinstance(res, dict):
        addons = res.get("addons", [])
        return [a for a in addons if a.get("addonid")]

    if not ok and isinstance(err, dict) and err.get("code") == -32602:
        log_utils.write_log("Addons.GetAddons: filtro 'type=xbmc.pvrclient' no soportado; usando fallback.", level="INFO")

    ok2, res2, _ = _jsonrpc_call_soft(
        "Addons.GetAddons",
        {"properties": ["enabled"], "enabled": "all"}
    )
    if ok2 and isinstance(res2, dict):
        addons = res2.get("addons", [])
        return [a for a in addons if str(a.get("addonid", "")).startswith("pvr.")]
    return []

def _list_service_addons() -> List[dict]:
    """
    Lista servicios con propiedades seguras. Si no soporta 'type',
    se hace fallback sin filtro y, si es necesario, sin 'properties'.
    """
    ok, res, err = _jsonrpc_call_soft(
        "Addons.GetAddons",
        {"type": "xbmc.service", "properties": ["enabled", "name"], "enabled": "all"}
    )
    if ok and isinstance(res, dict):
        return [a for a in res.get("addons", []) if a.get("addonid")]

    if not ok and isinstance(err, dict) and err.get("code") == -32602:
        log_utils.write_log("Addons.GetAddons: filtro 'type=xbmc.service' no soportado; usando fallback.", level="INFO")

    ok2, res2, _ = _jsonrpc_call_soft(
        "Addons.GetAddons",
        {"properties": ["enabled", "name"], "enabled": "all"}
    )
    if ok2 and isinstance(res2, dict):
        return [a for a in res2.get("addons", []) if str(a.get("addonid", "")).startswith("service.")]

    ok3, res3, _ = _jsonrpc_call_soft("Addons.GetAddons", {"enabled": "all"})
    if ok3 and isinstance(res3, dict):
        return [a for a in res3.get("addons", []) if str(a.get("addonid", "")).startswith("service.")]
    return []

def _disable_conflicts_enabled() -> bool:
    try:
        fn = getattr(utils, "get_bool", None)
        if callable(fn):
            return bool(fn("pvr_disable_conflicts", True))
    except Exception:
        pass
    return True  # por defecto activado

def _disable_conflict_services_enabled() -> bool:
    try:
        fn = getattr(utils, "get_bool", None)
        if callable(fn):
            return bool(fn("pvr_disable_conflict_services", True))
    except Exception:
        pass
    return True

def _disable_other_pvr_clients(keep_id: str = "pvr.hts"):
    """Deshabilita todos los PVR clients habilitados excepto 'keep_id'."""
    if not _disable_conflicts_enabled():
        log_utils.write_log("Omitiendo deshabilitar PVR conflictivos (ajuste desactivado).")
        return
    for a in _list_pvr_clients():
        aid = a.get("addonid")
        if not aid or aid == keep_id:
            continue
        if a.get("enabled"):
            log_utils.write_log(f"Deshabilitando PVR conflictivo: {aid}")
            _set_addon_enabled(aid, False)
            xbmc.sleep(300)

def _looks_conflicting_service(a: dict) -> bool:
    """
    Heurística para detectar servicios (service.*) que potencialmente gestionan IPTV/PVR/EPG.
    """
    aid  = str(a.get("addonid", "")).strip().lower()
    name = str(a.get("name", "")).strip().lower()
    if not aid:
        return False
    # Debe parecer service.*
    is_service_like = aid.startswith("service.") or "service" in name
    if not is_service_like:
        return False

    known_conflicts = {
        "service.iptv.manager",
        "service.iptv.merge",
        "service.iptv.recorder",
        "service.iptv.archive",
        "service.waipu",
        "service.zattoo",
        "service.stalker",
        "service.teleboy",
        "service.sledovani",
        "service.nextpvr",
        "service.tvheadend42",
        "service.enigma2",
        "service.pvr.proxy",
    }
    if aid in known_conflicts:
        return True
    return False  # <-- aseguremos bool siempre

def _disable_conflicting_services():
    """Deshabilita servicios detectados como conflictivos mediante heurística."""
    if not _disable_conflict_services_enabled():
        log_utils.write_log("Omitiendo deshabilitar servicios conflictivos (ajuste desactivado).")
        return
    services = _list_service_addons()
    if not services:
        return
    for a in services:
        aid = a.get("addonid")
        if not aid or not a.get("enabled"):
            continue
        if _looks_conflicting_service(a):
            log_utils.write_log(f"Deshabilitando servicio conflictivo: {aid}")
            _set_addon_enabled(aid, False)
            xbmc.sleep(300)

# ------------------------------
# Esperas y reinicio PVR
# ------------------------------

def wait_for_pvr_ready(max_wait: int = 180) -> bool:
    """
    Espera a que el PVR termine de inicializar:
      - PVR.IsInitialising == False
      - PVR.HasTVChannels or PVR.HasRadioChannels == True
    """
    start = time.time()
    mon = xbmc.Monitor()
    while time.time() - start < max_wait and not mon.abortRequested():
        try:
            if not xbmc.getCondVisibility("PVR.IsInitialising") and (
                xbmc.getCondVisibility("PVR.HasTVChannels") or
                xbmc.getCondVisibility("PVR.HasRadioChannels")
            ):
                return True
        except Exception:
            pass
        xbmc.sleep(500)
    return False

def restart_pvr_addon(addon_id: str = "pvr.hts", wait_ready: bool = True) -> bool:
    """Recarga el PVR (disable → enable) con verificación y espera opcional a canales/EPG."""
    log_utils.write_log("Recargando PVR…")
    if not _set_addon_enabled(addon_id, False):
        log_utils.write_log("No se pudo deshabilitar PVR", level="ERROR")
        return False
    xbmc.sleep(1200)
    if not _set_addon_enabled(addon_id, True):
        log_utils.write_log("No se pudo habilitar PVR", level="ERROR")
        return False

    if wait_ready:
        log_utils.notify("Cargando PVR (canales/EPG)…")
        ready = wait_for_pvr_ready(180)
        if ready:
            log_utils.notify("PVR listo")
            log_utils.write_log("PVR listo (canales/EPG).")
        else:
            log_utils.write_log("Timeout esperando PVR listo", level="WARNING")
    return True

# ------------------------------
# Settings de pvr.hts
# ------------------------------

def _pvr_settings_dir(addon_id="pvr.hts") -> str:
    return os.path.join(_path_profile(), "addon_data", addon_id)

def _settings_file(addon_id="pvr.hts") -> str:
    return os.path.join(_pvr_settings_dir(addon_id), "instance-settings-1.xml")

def ensure_instance_settings_exists(addon_id: str = "pvr.hts") -> bool:
    """
    Asegura que existe instance-settings-1.xml. Si no existe, crea una plantilla mínima.
    No arranca el addon para generarlo: escribimos un XML válido directamente.
    """
    sdir = _pvr_settings_dir(addon_id)
    sfile = _settings_file(addon_id)
    os.makedirs(sdir, exist_ok=True)

    if os.path.exists(sfile):
        return True

    log_utils.write_log(f"Creando plantilla inicial de settings: {sfile}")
    try:
        root = ET.Element("settings", version="1")
        defaults = {
            "m3uPathType": "0",
            "m3uPath": "/storage/.user/playlist.m3u",
            "epgUrl": "https://raw.githubusercontent.com/masQelec/epg/main/guide.xml",
            "defaultUserAgent": "samsung-agent/1.1",
        }
        for sid, val in defaults.items():
            elem = ET.Element("setting", id=sid, default="true")
            elem.text = val
            root.append(elem)

        tree = ET.ElementTree(root)
        tree.write(sfile, encoding="UTF-8", xml_declaration=True)
        return True
    except Exception as e:
        log_utils.write_log(f"Error creando plantilla de settings: {e}\n{traceback.format_exc()}", level="ERROR")
        return False

def verify_and_correct_pvr_settings(settings_dir: str) -> bool:
    """
    Verifica/corrige instance-settings-1.xml.
    Devuelve True si hubo cambios o faltaba el archivo (forzará reload), False si ya era correcto.
    """
    settings_file = os.path.join(settings_dir, "instance-settings-1.xml")

    if not os.path.exists(settings_dir):
        os.makedirs(settings_dir, exist_ok=True)

    if not os.path.exists(settings_file):
        log_utils.write_log(f"No existe {settings_file}; se creará plantilla.")
        if not ensure_instance_settings_exists():
            return True  # forzamos reload igualmente
        return True

    correct = {
        "m3uPathType": "0",
        "m3uPath": "/storage/.user/playlist.m3u",
        "epgUrl": "https://raw.githubusercontent.com/masQelec/epg/main/guide.xml",
        "defaultUserAgent": "samsung-agent/1.1",
    }

    try:
        tree = ET.parse(settings_file)
        root = tree.getroot()
        changed = False

        for sid, val in correct.items():
            elem = root.find(f"./setting[@id='{sid}']")
            if elem is None:
                new_elem = ET.Element("setting", id=sid, default="true")
                new_elem.text = val
                root.append(new_elem)
                changed = True
            elif (elem.text or "") != val:
                elem.text = val
                changed = True

        if changed:
            tree.write(settings_file, encoding="UTF-8", xml_declaration=True)
            log_utils.write_log("PVR settings actualizados.")
        else:
            log_utils.write_log("PVR settings ya correctos.")
        return changed

    except Exception as e:
        log_utils.write_log(f"Error editando settings PVR: {e}\n{traceback.format_exc()}", level="ERROR")
        return True  # fuerza reload por si el XML está corrupto

# ------------------------------
# DB TV/Epg
# ------------------------------

def remove_old_databases(db_dir: str):
    """Elimina TV*.db y Epg*.db (si existen)."""
    try:
        for name in os.listdir(db_dir):
            if name.endswith(".db") and (name.startswith("TV") or name.startswith("Epg")):
                fp = os.path.join(db_dir, name)
                os.remove(fp)
                log_utils.write_log(f"Eliminado: {name}")
    except Exception as e:
        log_utils.write_log(f"Error eliminando DBs TV/Epg: {e}\n{traceback.format_exc()}", level="ERROR")

# ------------------------------
# Detección robusta de instalación
# ------------------------------

def _is_pvr_installed(addon_id: str) -> Tuple[bool, bool, str]:
    """
    (instalado, habilitado, ruta_addon)
    Instalado = (Kodi conoce el addon: GetAddonDetails/GetAddons) Y (existe special://home/addons/addon_id).
    """
    addons_dir = _path_addons()
    addon_dir = os.path.join(addons_dir, addon_id)

    details = _get_addon_details(addon_id)
    installed = details is not None
    enabled = bool(details.get("enabled")) if details else False

    if not os.path.exists(addon_dir):
        installed = False

    return installed, enabled, addon_dir

# ------------------------------
# Instalación / actualización PVR (flujo principal)
# ------------------------------

def update_pvr() -> bool:
    addon_id = "pvr.hts"
    db_dir = _path_database()
    addon_data_dir = _pvr_settings_dir(addon_id)

    # 0) playlist primero (sin recargar aquí)
    ok_pl, playlist_changed = update_playlist(reload_if_enabled=False)
    if not ok_pl:
        log_utils.write_log("Playlist no válida; se detiene update_pvr.", level="ERROR")
        return False

    # 1) detección
    installed, enabled, _ = _is_pvr_installed(addon_id)

    # 2) instalar si falta
    if not installed:
        log_utils.write_log("PVR no instalado completamente. Instalando…")
        log_utils.notify("Instalando PVR")

        ok = utils.install_addon_from_repo(
            addon_id,
            "https://raw.githubusercontent.com/masQelec/repository.masqelec/masqelec_21/addons/1.0/Amlogic/arm/addons.xml"
        )
        if not ok:
            log_utils.write_log("Fallo instalando PVR desde repositorio.", level="ERROR")
            return False

        _disable_other_pvr_clients(keep_id=addon_id)
        _disable_conflicting_services()

        _set_addon_enabled(addon_id, False)
        xbmc.sleep(500)

        ensure_instance_settings_exists(addon_id)
        settings_changed = verify_and_correct_pvr_settings(addon_data_dir)
        if settings_changed:
            remove_old_databases(db_dir)

        # Un único reinicio: playlist_changed o settings_changed o instalación nueva
        if restart_pvr_addon(addon_id, wait_ready=True):
            log_utils.notify("PVR instalado y listo.")
        else:
            log_utils.notify("Instalado, pero no se pudo reiniciar PVR automáticamente.")
        return True

    # 3) instalado pero deshabilitado
    if not enabled:
        log_utils.write_log("PVR instalado pero deshabilitado. Ajustando configuración…")

        _disable_other_pvr_clients(keep_id=addon_id)
        _disable_conflicting_services()

        ensure_instance_settings_exists(addon_id)
        settings_changed = verify_and_correct_pvr_settings(addon_data_dir)
        if settings_changed:
            remove_old_databases(db_dir)

        # Un único reinicio: playlist_changed o settings_changed
        if playlist_changed or settings_changed:
            if restart_pvr_addon(addon_id, wait_ready=True):
                log_utils.notify("PVR habilitado y listo.")
            else:
                log_utils.notify("No se pudo reiniciar PVR automáticamente.")
        else:
            # Si no hay cambios, basta con habilitarlo y esperar listo.
            _set_addon_enabled(addon_id, True)
            wait_for_pvr_ready(180)
        return True

    # 4) instalado y habilitado
    log_utils.write_log("PVR habilitado. Verificando configuración…")

    _disable_other_pvr_clients(keep_id=addon_id)
    _disable_conflicting_services()

    ensure_instance_settings_exists(addon_id)
    settings_changed = verify_and_correct_pvr_settings(addon_data_dir)
    if settings_changed:
        remove_old_databases(db_dir)
        restart_pvr_addon(addon_id, wait_ready=True)

    # Un único reinicio según cambios
    if playlist_changed or settings_changed:
        if restart_pvr_addon(addon_id, wait_ready=True):
            log_utils.notify("PVR actualizado y listo.")
        else:
            log_utils.notify("No se pudo reiniciar PVR automáticamente.")
    else:
        # Sin cambios reales: asegurar habilitado y listo
        _set_addon_enabled(addon_id, True)
        wait_for_pvr_ready(180)
        log_utils.write_log("PVR se re-habilitó sin cambios en configuración.")

    return True
