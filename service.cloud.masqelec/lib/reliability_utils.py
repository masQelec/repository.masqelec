# -*- coding: utf-8 -*-
"""reliability_utils.py — estado persistente + circuit breaker + métricas"""

import os
import time
import traceback
import json

import xbmcvfs

from lib import log_utils
from lib import constants

def get_addon_data_dir():
    return xbmcvfs.translatePath("special://profile/addon_data/{}".format(constants.ADDON_ID))

# ---------------------------------------------------------
# Estado persistente (state.json) — NO sobreescribir claves
# ---------------------------------------------------------

def _state_path():
    # Estado persistente del addon (circuit breaker / métricas)
    return "/storage/.kodi/userdata/addon_data/service.cloud.masqelec/state.json"

def load_state():
    """Carga state.json del addon_data. Si no existe o está corrupto, devuelve dict vacío."""
    path = _state_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def save_state(state):
    """Guarda state.json de forma atómica."""
    try:
        state_dir = get_addon_data_dir()
        os.makedirs(state_dir, exist_ok=True)
        tmp = os.path.join(state_dir, "state.json.tmp")
        final = os.path.join(state_dir, "state.json")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, final)
        return True
    except Exception:
        return False

def cb_should_run(task):
    st = load_state()
    cb = st.get("circuit_breaker") if isinstance(st.get("circuit_breaker"), dict) else {}
    t = cb.get(task) if isinstance(cb.get(task), dict) else {}
    next_ts = float(t.get("next_ts", 0) or 0)
    return time.time() >= next_ts

def cb_note_success(task):
    st = load_state()
    cb = st.get("circuit_breaker") if isinstance(st.get("circuit_breaker"), dict) else {}
    cb[task] = {"fails": 0, "next_ts": 0}
    st["circuit_breaker"] = cb
    save_state(st)

def cb_note_failure(name, threshold=3, cooldown_sec=3600, max_fails=None):
    if max_fails is not None:
        threshold = int(max_fails)
    try:
        st = load_state()
        cb = st.get("cb", {})

        ent = cb.get(name, {})
        ent["fails"] = int(ent.get("fails", 0)) + 1
        ent["last_fail"] = int(time.time())
        ent["threshold"] = int(threshold)
        ent["cooldown_sec"] = int(cooldown_sec)

        cb[name] = ent
        st["cb"] = cb
        save_state(st)

    except Exception:
        log_utils.log(
            "[cb] fallo en cb_note_failure({}):\n{}".format(name, traceback.format_exc()),
            level="WARNING",
        )

def cb_should_log_cooldown(task, every_sec=600):
    """Evita spam: si está en cooldown, loguea como mucho cada X segundos."""
    try:
        now = time.time()
        st = load_state() or {}
        meta = st.get("cb_meta")
        if not isinstance(meta, dict):
            meta = {}

        last = float(meta.get(task, 0) or 0)
        if (now - last) >= max(60, int(every_sec)):
            meta[task] = now
            st["cb_meta"] = meta
            save_state(st)
            return True

    except Exception:
        # Logging NUNCA debe romper el flujo principal
        pass

    return False


def metrics_note(task, ok, duration_sec, extra=None):
    """Guarda métricas simples por tarea en state.json sin hacer ruido."""
    try:
        now = int(time.time())
        data = {
            "last_run_ts": now,
            "last_duration_sec": float(duration_sec) if duration_sec is not None else None,
            "last_ok_ts": now if ok else None,
            "last_result": "OK" if ok else "FAIL",
        }
        if extra:
            try:
                data.update(extra)
            except Exception:
                pass

        # FIX: update_state ahora soporta merge=True
        update_state({"metrics": {task: data}}, merge=True)
    except Exception:
        return

def metrics_get(task):
    try:
        st = load_state() or {}
        m = st.get("metrics") if isinstance(st.get("metrics"), dict) else {}
        return m.get(task) or {}
    except Exception:
        return {}



# =========================================================
# Re-export select helpers from split modules (safe refactor)
# =========================================================
# NOTE: these imports intentionally override local definitions above,
# keeping backwards-compatible API via lib.utils.*
try:
    from lib.net_utils import wait_for_dns, _net_open, download_atomic, _has_network, _has_internet, is_online  # noqa
except Exception:
    pass

try:
    from lib.fs_utils import _read_bytes, _sha256, _cleanup_dir, _safe_rmtree, atomic_write_bytes, atomic_write_text  # noqa
except Exception:
    pass
