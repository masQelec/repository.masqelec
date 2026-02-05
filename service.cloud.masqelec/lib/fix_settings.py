# -*- coding: utf-8 -*-
"""
fix_settings.py — Fix de “skin booleans” (home menu) de forma robusta.

Objetivo:
- homemenunomoviebutton
- homemenunotvshowbutton
- homemenunotvbutton

Regla:
- Si alguno está activo (Skin.HasSetting == true) -> forzar a false con Skin.Reset()

Notas:
- Estos NO son “Kodi settings” estándar => JSON-RPC NO los puede escribir.
- Usamos builtins del motor de skin, que es lo más estable y no depende del settings.xml del skin.
- Opcional: ReloadSkin si hubo cambios y es seguro (idle + no reproduciendo).
"""

from __future__ import annotations
from typing import List, Tuple

import xbmc

from lib import log_utils
from lib import jsonrpc_utils

TARGET_SKIN_BOOL_IDS = (
    "homemenunomoviebutton",
    "homemenunotvshowbutton",
    "homemenunotvbutton",
)

DEFAULT_SKIN_ID = "skin.estuary"
QUIET_JSONRPC_CODES = {-32100}


def _get_current_skin_id(default: str = DEFAULT_SKIN_ID) -> str:
    """
    Detecta el skin actual por JSON-RPC (solo lectura).
    """
    try:
        ok, res, _err = jsonrpc_utils.jsonrpc_try(
            "Settings.GetSettingValue",
            params={"setting": "lookandfeel.skin"},
            retries=1,
            sleep_s=0.25,
            quiet_codes=QUIET_JSONRPC_CODES,
            log_on_error=False,
            min_log_interval_s=30.0,
        )
        if ok and isinstance(res, dict):
            v = res.get("value")
            if isinstance(v, str) and v.strip():
                return v.strip()
    except Exception:
        pass
    return default


def _is_safe_to_reload_skin(min_idle_secs: int = 30) -> bool:
    try:
        if xbmc.Player().isPlaying():
            return False
    except Exception:
        return False

    try:
        idle = int(xbmc.getGlobalIdleTime() or 0)
        return idle >= int(min_idle_secs)
    except Exception:
        return False


def _skin_has(setting_id: str) -> bool:
    """
    True si el skin setting está activo.
    """
    try:
        return bool(xbmc.getCondVisibility(f"Skin.HasSetting({setting_id})"))
    except Exception:
        return False


def _skin_reset(setting_id: str) -> bool:
    """
    Fuerza el skin setting a false usando Skin.Reset().
    """
    try:
        xbmc.executebuiltin(f"Skin.Reset({setting_id})")
        return True
    except Exception:
        return False


def fix_skin_home_menu_visibility_and_reload(
    *,
    min_idle_secs: int = 30,
    reload_if_changed: bool = True,
    log_summary: bool = True,
) -> Tuple[str, bool, bool, List[str], List[str]]:
    """
    Aplica el fix y opcionalmente recarga el skin.

    Returns:
      (skin_id, changed, reloaded, fixed_ids, failed_ids)
    """
    skin_id = _get_current_skin_id(DEFAULT_SKIN_ID)

    fixed: List[str] = []
    failed: List[str] = []
    changed = False

    # 1) Solo tocamos los que estén activos (true)
    for sid in TARGET_SKIN_BOOL_IDS:
        try:
            if _skin_has(sid):
                ok = _skin_reset(sid)
                if ok:
                    fixed.append(sid)
                    changed = True
                else:
                    failed.append(sid)
        except Exception:
            failed.append(sid)

    # 2) Logs coherentes (sin contradicciones)
    if log_summary:
        if changed:
            log_utils.write_log(
                f"[fix_settings] Skin={skin_id} | Forzados a false (Skin.Reset): " + ", ".join(fixed),
                level="INFO",
            )
        else:
            log_utils.write_log(
                f"[fix_settings] Skin={skin_id} | Sin cambios: ya estaban en false (o no estaban activos).",
                level="INFO",
            )

        if failed:
            log_utils.write_log(
                f"[fix_settings] Skin={skin_id} | Fallo aplicando: " + ", ".join(failed),
                level="WARNING",
            )

    # 3) ReloadSkin solo si hubo cambios y es seguro
    reloaded = False
    if reload_if_changed and changed:
        if _is_safe_to_reload_skin(min_idle_secs=min_idle_secs):
            try:
                xbmc.executebuiltin("ReloadSkin()")
                reloaded = True
                if log_summary:
                    log_utils.write_log(
                        f"[fix_settings] Skin={skin_id} | ReloadSkin ejecutado.",
                        level="INFO",
                    )
            except Exception as e:
                if log_summary:
                    log_utils.write_log(
                        f"[fix_settings] Skin={skin_id} | Error en ReloadSkin: {e}",
                        level="WARNING",
                    )
        else:
            if log_summary:
                log_utils.write_log(
                    f"[fix_settings] Skin={skin_id} | Cambios aplicados pero NO recargo ahora "
                    f"(idle<{min_idle_secs}s o reproduciendo).",
                    level="INFO",
                )

    return skin_id, changed, reloaded, fixed, failed

