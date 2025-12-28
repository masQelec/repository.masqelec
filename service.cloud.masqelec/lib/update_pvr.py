# -*- coding: utf-8 -*-
"""
update_pvr.py — Gestión de PVR:
- Playlist con USER_CODE/PASS_CODE (instalación SOLO si cambia el hash final)
- Sincronización de tv_grab_file desde la nube
- Ajuste http_user_agent en Tvheadend
"""

import os
import subprocess
import re
import time
import urllib.request
import traceback
import json
import gzip
import zlib

from lib import log_utils
from lib import rclone_utils
from lib import utils

# ------------------------------
# Descarga robusta (reintentos + atómica)
# ------------------------------

def _restart_tvheadend() -> bool:
    # CoreELEC suele usar systemctl; si falla, devolvemos False
    cmd = ["systemctl", "restart", "service.tvheadend43"]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20, check=True)
        log_utils.write_log("[pvr] Tvheadend reiniciado por cambio de playlist.")
        return True
    except Exception as e:
        log_utils.write_log(f"[pvr] No pude reiniciar Tvheadend: {e}", level="WARNING")
        return False

def _download_to(path_dst: str, url: str, retries: int = 2, timeout: int = 20) -> bool:
    """Compat: descarga atómica reutilizando lib.utils.download_atomic()."""
    return bool(utils.download_atomic(path_dst, url, retries=retries, timeout=timeout))

def update_playlist() -> tuple[bool, bool]:
    user_dir = "/storage/.user"
    playlist_file = os.path.join(user_dir, "playlist.m3u")
    user_file = os.path.join(user_dir, "user")
    BASE_URLS = [
        "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/pvr/playlist.m3u",
    ]

    def _read_text(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _norm_newlines(s: str) -> str:
        return (s or "").replace("\r\n", "\n").replace("\r", "\n")

    def _sha256_text(s: str) -> str:
        return utils._sha256_bytes(_norm_newlines(s).encode("utf-8", errors="replace"))

    def _has_valid_creds(txt: str) -> bool:
        m_user = re.search(r'USER_CODE="([^"]+)"', txt)
        m_pass = re.search(r'PASS_CODE="([^"]+)"', txt)
        return bool(
            m_user and m_pass and
            m_user.group(1).strip() and
            m_pass.group(1).strip()
        )

    def _extract_creds(txt: str) -> tuple[str, str]:
        m_user = re.search(r'USER_CODE="([^"]+)"', txt)
        m_pass = re.search(r'PASS_CODE="([^"]+)"', txt)
        if not (m_user and m_pass):
            return "", ""
        return m_user.group(1).strip(), m_pass.group(1).strip()

    def _try_fetch_user_from_remote() -> bool:
        try:
            eth0 = "nomac"
            try:
                ni = utils.get_net_info() or {}
                eth0 = (ni.get("eth0") or "").strip().replace(":", "").lower() or eth0
            except Exception as e:
                log_utils.write_log(f"Excepción ignorada en update_pvr: {e}", "DEBUG")

            remote = "masqelec"
            remote_path = f"masqelec/user/{eth0}"
            tmp_dir = "/tmp"
            tmp_file = os.path.join(tmp_dir, eth0)

            try:
                ok = rclone_utils.copy_remote_to_tmp_then_move(remote, remote_path, tmp_dir)
            except Exception as e:
                log_utils.write_log(
                    f"[update_playlist] rclone copy failed: {e}\n{traceback.format_exc()}",
                    level="ERROR",
                )
                return False

            if not ok or not os.path.exists(tmp_file):
                log_utils.write_log(
                    f"[update_playlist] user remoto no encontrado: {remote}:{remote_path}",
                    level="INFO",
                )
                return False

            txt = _read_text(tmp_file)
            if not _has_valid_creds(txt):
                log_utils.write_log(
                    "[update_playlist] user remoto inválido (faltan USER_CODE/PASS_CODE)",
                    level="WARNING",
                )
                try:
                    os.remove(tmp_file)
                except Exception:
                    pass
                return False

            os.makedirs(user_dir, exist_ok=True)
            tmp_install = user_file + ".part"
            with open(tmp_install, "w", encoding="utf-8") as f:
                f.write(_norm_newlines(txt))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_install, user_file)

            try:
                os.remove(tmp_file)
            except Exception:
                pass

            log_utils.write_log(f"[update_playlist] user recuperado del remoto ({eth0})")
            return True

        except Exception as e:
            log_utils.write_log(
                f"[update_playlist] Error recuperando user remoto: {e}\n{traceback.format_exc()}",
                level="ERROR",
            )
            return False

    try:
        os.makedirs(user_dir, exist_ok=True)

        if not os.path.exists(user_file):
            if not _try_fetch_user_from_remote():
                log_utils.write_log("Archivo /storage/.user/user no disponible.", level="ERROR")
                return False, False

        # Descarga/validación EN MEMORIA para evitar falsos negativos por escritura truncada.
        # Además, loguea URL real, bytes y primera línea para diagnosticar HTML/403/vacío.
        remote_tpl = None
        used_url = None
        last_candidate = ""
        last_bytes = 0
        last_firstline = ""

        for url in BASE_URLS:
            try:
                with utils._net_open(url, timeout=20) as r:
                    data = r.read()
                last_bytes = len(data or b"")
                # Algunos servidores (GitHub raw) pueden responder comprimido si se anuncia Accept-Encoding.
                try:
                    enc = (getattr(r, "headers", None).get("Content-Encoding") or "").lower()
                except Exception:
                    enc = ""
                try:
                    if ("gzip" in enc) or (data[:3] == b"\x1f\x8b\x08"):
                        data = gzip.decompress(data)
                    elif "deflate" in enc:
                        data = zlib.decompress(data)
                except Exception as _de:
                    # Si no podemos descomprimir, seguimos con bytes crudos (se diagnosticará con first line).
                    pass
                last_bytes = len(data or b"")
                txt = (data or b"").decode("utf-8", "replace")
            except Exception as e:
                log_utils.write_log(f"[update_playlist] Descarga plantilla falló para {url}: {e}", level="DEBUG")
                continue

            candidate_norm = _norm_newlines(txt)
            last_candidate = candidate_norm
            try:
                last_firstline = (candidate_norm.strip().splitlines()[0] if candidate_norm.strip() else "")[:200]
            except Exception:
                last_firstline = ""

            # Filtrado básico de respuestas HTML/errores comunes de GitHub.
            # Si es HTML o demasiado pequeño, lo tratamos como descarga inválida (no como 'faltan tokens').
            low = (candidate_norm.lstrip()[:120] or "").lower()
            if last_bytes < 64 or low.startswith("<!doctype html") or low.startswith("<html") or "rate limit" in low or "access denied" in low:
                continue

            if "USER_CODE" in candidate_norm and "PASS_CODE" in candidate_norm:
                remote_tpl = candidate_norm
                used_url = url
                break

        if not remote_tpl:
            log_utils.write_log(
                "Plantilla playlist remota no contiene tokens USER_CODE/PASS_CODE o llegó inválida. "
                f"URLs probadas={len(BASE_URLS)}; última url bytes={last_bytes}; primera='{last_firstline}'",
                level="ERROR",
            )
            return False, False

        log_utils.write_log(f"[update_playlist] Plantilla cargada desde: {used_url} (bytes={len(remote_tpl.encode('utf-8','replace'))})", level="INFO")

        content = _read_text(user_file)
        if not _has_valid_creds(content):
            log_utils.write_log("USER_CODE o PASS_CODE inválidos en /storage/.user/user", level="ERROR")
            return False, False

        user_code, pass_code = _extract_creds(content)
        if not user_code or not pass_code:
            log_utils.write_log("No se pudieron extraer credenciales válidas del user_file.", level="ERROR")
            return False, False

        tpl = _norm_newlines(remote_tpl)

        # Plantilla: tokens en URL /live/USER_CODE/PASS_CODE/...
        if "USER_CODE" not in tpl or "PASS_CODE" not in tpl:
            log_utils.write_log(
                "Plantilla playlist remota no contiene tokens USER_CODE/PASS_CODE.",
                level="ERROR",
            )
            return False, False

        new_playlist = tpl.replace("USER_CODE", user_code).replace("PASS_CODE", pass_code)

        new_hash = _sha256_text(new_playlist)

        if os.path.exists(playlist_file):
            try:
                local_hash = _sha256_text(_read_text(playlist_file))
            except Exception:
                local_hash = None
        else:
            local_hash = None

        if local_hash is not None and local_hash == new_hash:
            log_utils.write_log("Playlist sin cambios (sha256).")
            return True, False

        tmp = playlist_file + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(new_playlist)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, playlist_file)

        log_utils.write_log("Playlist instalada/actualizada (sha256 distinto).")
        _restart_tvheadend()
        # Opcional: marcar que Kodi debe refrescar PVR tras el reinicio del backend
        try:
            with open("/tmp/pvr_force_resync", "w", encoding="utf-8") as f:
                f.write("1\n")
        except Exception:
            pass

        return True, True

    except Exception as e:
        log_utils.write_log(f"Error en update_playlist: {e}\n{traceback.format_exc()}", level="ERROR")
        return False, False

# ------------------------------
# Sincronizar tv_grab_file desde la nube
# ------------------------------

def update_tv_grab_file() -> bool:
    local_path = "/storage/.kodi/addons/service.tvheadend43/bin/tv_grab_file"
    remote_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/pvr/tv_grab_file"
    remote_tmp = local_path + ".remote"


    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if not _download_to(remote_tmp, remote_url):
            log_utils.write_log("[tv_grab_file] Descarga fallida.", level="ERROR")
            return False

        remote_data = utils._read_bytes(remote_tmp)
        local_data = utils._read_bytes(local_path) if os.path.exists(local_path) else None

        if local_data == remote_data:
            log_utils.write_log("[tv_grab_file] Sin cambios.")
            return True

        tmp_local = local_path + ".part"
        with open(tmp_local, "wb") as f:
            f.write(remote_data)
            f.flush()
            os.fsync(f.fileno())

        os.chmod(tmp_local, 0o755)
        os.replace(tmp_local, local_path)

        log_utils.write_log("[tv_grab_file] Actualizado.")
        return True

    except Exception as e:
        log_utils.write_log(
            f"[tv_grab_file] Error: {e}\n{traceback.format_exc()}",
            level="ERROR",
        )
        return False

    finally:
        try:
            if os.path.exists(remote_tmp):
                os.remove(remote_tmp)
        except Exception:
            pass

# ------------------------------
# Ajustar http_user_agent en Tvheadend
# ------------------------------

def ensure_tvh_http_user_agent() -> bool:
    cfg_path = "/storage/.kodi/userdata/addon_data/service.tvheadend43/config"
    desired_agent = "samsung-agent/1.1"

    if not os.path.exists(cfg_path):
        log_utils.write_log("[tvh_config] Config no encontrado.", level="ERROR")
        return False

    try:
        with open(cfg_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read().strip()

        if raw.endswith(";"):
            raw = raw[:-1].rstrip()

        data = json.loads(raw)

        if data.get("http_user_agent") == desired_agent:
            return True

        data["http_user_agent"] = desired_agent

        tmp = cfg_path + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp, cfg_path)
        log_utils.write_log("[tvh_config] http_user_agent ajustado.")
        return True

    except Exception as e:
        log_utils.write_log(
            f"[tvh_config] Error: {e}\n{traceback.format_exc()}",
            level="ERROR",
        )
        return False

# ------------------------------
# Punto de entrada general
# ------------------------------

def update_pvr():
    """
    Punto de entrada PVR (mínimo):
      - Actualiza tv_grab_file (si cambia)
      - Asegura http_user_agent en Tvheadend
    NOTA: update_playlist() se gestiona fuera de aquí (o se llama desde otro flujo).
    """
    start_ts = time.time()

    # 1) bin tv_grab_file
    try:
        update_tv_grab_file()
    except Exception as e:
        try:
            log_utils.write_log("[pvr] update_tv_grab_file error: {}".format(e), level="WARNING")
        except Exception:
            pass

    # 2) user-agent tvheadend
    try:
        ensure_tvh_http_user_agent()
    except Exception as e:
        try:
            log_utils.write_log("[pvr] ensure_tvh_http_user_agent error: {}".format(e), level="WARNING")
        except Exception:
            pass

    # 3) log final
    try:
        dt = time.time() - start_ts
        log_utils.write_log("[pvr] update_pvr terminado en {:.1f}s".format(dt), level="INFO")
    except Exception:
        pass


