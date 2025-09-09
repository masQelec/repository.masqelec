# -*- coding: utf-8 -*-
"""
fix_guisettins.py — Aplicador masivo de ajustes de guisettings.xml con refuerzo XML.

Características:
- Aplica primero por JSON-RPC (rápido/limpio).
- (Opcional) Refuerza/crea nodos en guisettings.xml de forma atómica.
- Permite marcar algunas claves para forzar atributo default="true".
- Incluye run_fix() con el lote de ajustes solicitado.

Requisitos:
- lib/jsonrpc_utils.py con get_setting(id) y set_setting(id, value)
- lib/log_utils.py con write_log(msg, level="INFO")
"""

import os
import traceback
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Set, List, Any

import xbmc
import xbmcvfs

from lib import jsonrpc_utils
from lib import log_utils


# ----------------- Paths helpers -----------------

def _profile_path() -> str:
    try:
        return xbmcvfs.translatePath("special://profile")
    except Exception:
        return "/storage/.kodi/userdata/"

def _guisettings_xml_path() -> str:
    return os.path.join(_profile_path(), "guisettings.xml")


# ----------------- Core helper -----------------

def ensure_guisettings_bulk(
    settings_map: Dict[str, Any],
    force_default_ids: Optional[Set[str]] = None,
    notify: bool = False,
    force_create_missing: bool = False,
) -> Dict[str, List[str]]:
    """
    Aplica ajustes de forma masiva y segura.

    Paso 1) JSON-RPC:
        - Lee cada ajuste con jsonrpc_utils.get_setting.
        - Si el valor actual difiere, intenta set_setting.
        - Registra 'changed' / 'unchanged' / 'failed'.

    Paso 2) Refuerzo en guisettings.xml (cuando sea necesario):
        - Si force_create_missing=True: garantiza que existan nodos para TODAS las claves de settings_map.
        - Para claves en 'force_default_ids', también fuerza default="true".
        - Escritura atómica (archivo .part + os.replace). Backup best-effort (.bak).

    Args:
        settings_map: {setting_id: value}
        force_default_ids: ids a las que se les añadirá default="true" en el XML.
        notify: si True, muestra notificación con el resumen.
        force_create_missing: si True, crea nodos XML para claves ausentes.

    Returns:
        {
            "changed":    [...],
            "unchanged":  [...],
            "failed":     [...],
            "xml_patched":[...]
        }
    """
    force_default_ids = set(force_default_ids or [])
    changed: List[str] = []
    unchanged: List[str] = []
    failed: List[str] = []

    # ----- Paso 1: JSON-RPC -----
    for sid, target in settings_map.items():
        try:
            current = jsonrpc_utils.get_setting(sid)
        except Exception as e:
            log_utils.write_log(f"[guisettings] get_setting('{sid}') falló: {e}", level="WARNING")
            current = None

        try:
            if current == target:
                unchanged.append(sid)
                continue

            ok = jsonrpc_utils.set_setting(sid, target)
            if ok:
                changed.append(sid)
                log_utils.write_log(f"[guisettings] {sid}: {current!r} -> {target!r}")
            else:
                failed.append(sid)
                log_utils.write_log(f"[guisettings] No se pudo aplicar '{sid}' vía JSON-RPC", level="ERROR")
        except Exception as e:
            failed.append(sid)
            log_utils.write_log(
                f"[guisettings] set_setting('{sid}') error: {e}\n{traceback.format_exc()}",
                level="ERROR"
            )

    # ----- Paso 2: Refuerzo XML (si hace falta) -----
    xml_patched: List[str] = []
    try:
        ids_to_patch = set()
        if force_create_missing:
            # garantizamos nodo para TODAS las claves del lote
            ids_to_patch |= set(settings_map.keys())
        # además, por si no creamos todo, nos aseguramos de incluir las marcadas para default="true"
        ids_to_patch |= force_default_ids

        if ids_to_patch:
            xml_path = _guisettings_xml_path()
            os.makedirs(os.path.dirname(xml_path), exist_ok=True)

            # Cargar o crear árbol
            root = None
            tree = None
            try:
                if os.path.exists(xml_path) and os.path.getsize(xml_path) > 0:
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
            except Exception:
                log_utils.write_log("[guisettings] guisettings.xml corrupto, re-creando archivo.", level="WARNING")

            if root is None:
                root = ET.Element("settings")
                tree = ET.ElementTree(root)

            for sid in ids_to_patch:
                # ¿Qué valor debemos escribir?
                val = settings_map.get(sid)
                # si no tenemos valor, no hacemos nada (salvo que esté en force_default_ids, entonces
                # solo agregamos el atributo default, pero tiene sentido tener un texto)
                if val is None:
                    continue

                node = root.find(f".//setting[@id='{sid}']")
                if node is None:
                    node = ET.Element("setting", id=sid)
                    root.append(node)

                node.text = str(val)
                if sid in force_default_ids:
                    node.set("default", "true")
                xml_patched.append(sid)

            # Escritura atómica
            tmp_path = xml_path + ".part"
            backup = xml_path + ".bak"
            try:
                # Backup best-effort
                if os.path.exists(xml_path):
                    try:
                        with open(xml_path, "rb") as fr, open(backup, "wb") as fw:
                            fw.write(fr.read())
                    except Exception:
                        pass
                tree.write(tmp_path, encoding="UTF-8", xml_declaration=True)
                os.replace(tmp_path, xml_path)
                log_utils.write_log(
                    "[guisettings] guisettings.xml parcheado: " + (", ".join(xml_patched) or "—")
                )
            finally:
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass

    except Exception as e:
        log_utils.write_log(
            f"[guisettings] Error parcheando guisettings.xml: {e}\n{traceback.format_exc()}",
            level="ERROR"
        )

    # Notificación opcional
    if notify:
        try:
            import xbmcgui
            msg = (
                f"Cambiados: {len(changed)} | Sin cambios: {len(unchanged)} | "
                f"Fallidos: {len(failed)} | XML: {len(xml_patched)}"
            )
            xbmcgui.Dialog().notification("Ajustes aplicados", msg, xbmcgui.NOTIFICATION_INFO, 4000)
        except Exception:
            pass

    return {
        "changed": changed,
        "unchanged": unchanged,
        "failed": failed,
        "xml_patched": xml_patched,
    }


# ----------------- Runner solicitado -----------------

def fix_cache() -> Dict[str, List[str]]:
    """
    Aplica el lote pedido y fuerza la creación de nodos en guisettings.xml
    cuando no existan. Además, marca 'filecache.chunksize' con default="true".
    """
    settings = {
        "filecache.buffermode": 1,
        "filecache.memorysize": 256,
        "filecache.readfactor": 0,
        "filecache.chunksize": 131072,
    }

    result = ensure_guisettings_bulk(
        settings_map=settings,
        force_default_ids={"filecache.chunksize"},
        force_create_missing=True,
    )

    log_utils.write_log(f"[guisettings] run_fix() -> {result}")
    return result

def fix_movieset_folder() -> Dict[str, List[str]]:
    settings = {
        "videolibrary.moviesetsfolder": "",
    }

    result = ensure_guisettings_bulk(
        settings_map=settings,
    )
