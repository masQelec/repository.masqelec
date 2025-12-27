# -*- coding: utf-8 -*-
"""
fix_guisettins.py — Aplicador masivo de ajustes de guisettings.xml con refuerzo XML.

Características:
- Aplica primero por JSON-RPC (rápido/limpio).
- (Opcional) Refuerza/crea nodos en guisettings.xml de forma atómica.
- Permite marcar algunas claves para forzar atributo default="true".
- Incluye solo el lote de cache/buffer (sin tocar videolibrary).
- SIN backup (por directriz).

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
    log_summary: bool = True,
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
        - Escritura atómica (archivo .part + os.replace).
        - SIN backup (por directriz).

    Logging (resumen):
        - INFO: cambios aplicados y/o "sin cambios".
        - INFO: XML "modificado" solo si realmente cambia algo en el archivo.
        - INFO: XML "verificado" si se comprobó pero no hubo cambios reales.
        - WARNING: los que no se pudieron aplicar.

    Returns:
        {
            "changed":      [...],
            "unchanged":    [...],
            "failed":       [...],
            "xml_touched":  [...],  # ids revisados/garantizados en el XML
            "xml_modified": [...],  # ids que realmente provocaron modificación
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
            log_utils.write_log(
                f"[guisettings] No se pudo leer '{sid}' (get_setting): {e}",
                level="WARNING",
            )
            current = None

        try:
            if current == target:
                unchanged.append(sid)
                continue

            ok = jsonrpc_utils.set_setting(sid, target)
            if ok:
                changed.append(sid)
            else:
                failed.append(sid)
        except Exception as e:
            failed.append(sid)
            log_utils.write_log(
                f"[guisettings] Error aplicando '{sid}' (set_setting): {e}\n{traceback.format_exc()}",
                level="WARNING",
            )

    # ----- Paso 2: Refuerzo XML (solo si hace falta y detectando cambios reales) -----
    xml_touched: List[str] = []
    xml_modified: List[str] = []

    try:
        ids_to_patch = set()
        if force_create_missing:
            ids_to_patch |= set(settings_map.keys())
        ids_to_patch |= force_default_ids

        if ids_to_patch:
            xml_path = _guisettings_xml_path()
            os.makedirs(os.path.dirname(xml_path), exist_ok=True)

            root = None
            tree = None

            try:
                if os.path.exists(xml_path) and os.path.getsize(xml_path) > 0:
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
            except Exception:
                log_utils.write_log(
                    "[guisettings] guisettings.xml corrupto, re-creando archivo.",
                    level="WARNING",
                )

            if root is None:
                root = ET.Element("settings")
                tree = ET.ElementTree(root)

            needs_write = False

            for sid in ids_to_patch:
                val = settings_map.get(sid)
                if val is None:
                    # Si force_default_ids tiene un id que no está en settings_map,
                    # no tocamos nada para no dejar un <setting> vacío.
                    continue

                node = root.find(f".//setting[@id='{sid}']")
                created = False
                if node is None:
                    node = ET.Element("setting", id=sid)
                    root.append(node)
                    created = True

                prev_text = node.text or ""
                new_text = str(val)

                prev_default = node.get("default")
                wants_default_true = sid in force_default_ids

                changed_here = False
                if created:
                    changed_here = True
                if prev_text != new_text:
                    changed_here = True
                if wants_default_true and prev_default != "true":
                    changed_here = True

                # Aplicar en memoria
                node.text = new_text
                if wants_default_true:
                    node.set("default", "true")

                xml_touched.append(sid)
                if changed_here:
                    needs_write = True
                    xml_modified.append(sid)

            # Escritura atómica SIN backup, solo si hubo cambios reales
            if needs_write:
                tmp_path = xml_path + ".part"
                try:
                    tree.write(tmp_path, encoding="UTF-8", xml_declaration=True)
                    os.replace(tmp_path, xml_path)
                finally:
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception:
                        pass

    except Exception as e:
        log_utils.write_log(
            f"[guisettings] Error parcheando guisettings.xml: {e}\n{traceback.format_exc()}",
            level="WARNING",
        )

    # ----- Resumen de logs (solo lo que pides) -----
    if log_summary:
        if changed:
            log_utils.write_log(
                "[guisettings] Cambios aplicados: " + ", ".join(changed),
                level="INFO",
            )
        else:
            # Si todo está correcto pero no hubo cambios, también INFO
            log_utils.write_log(
                "[guisettings] Sin cambios: los ajustes ya estaban aplicados.",
                level="INFO",
            )

        if xml_modified:
            log_utils.write_log(
                "[guisettings] XML modificado: " + ", ".join(xml_modified),
                level="INFO",
            )
        elif xml_touched:
            log_utils.write_log(
                "[guisettings] XML verificado: sin cambios necesarios.",
                level="INFO",
            )

        if failed:
            log_utils.write_log(
                "[guisettings] No se pudieron aplicar: " + ", ".join(failed),
                level="WARNING",
            )

    # Notificación opcional
    if notify:
        try:
            import xbmcgui
            msg = (
                f"Cambiados: {len(changed)} | "
                f"Sin cambios: {len(unchanged)} | "
                f"No aplicados: {len(failed)} | "
                f"XML tocados: {len(xml_touched)} | "
                f"XML modificados: {len(xml_modified)}"
            )
            xbmcgui.Dialog().notification(
                "Ajustes aplicados", msg, xbmcgui.NOTIFICATION_INFO, 4000
            )
        except Exception:
            pass

    return {
        "changed": changed,
        "unchanged": unchanged,
        "failed": failed,
        "xml_touched": xml_touched,
        "xml_modified": xml_modified,
    }


# ----------------- Lote único: cache/buffer -----------------

def fix_cache() -> Dict[str, List[str]]:
    """
    Ajustes cache/buffer (VALORES LITERALES):
    """
    settings = {
        "filecache.buffermode": 1,
        "filecache.memorysize": 128,
        "filecache.readfactor": 0,
        "filecache.chunksize": 131072,
    }

    return ensure_guisettings_bulk(
        settings_map=settings,
        force_default_ids={"filecache.chunksize"},
        force_create_missing=True,
        notify=False,
        log_summary=True,
    )
