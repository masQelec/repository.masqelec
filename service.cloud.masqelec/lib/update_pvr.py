# -*- coding: utf-8 -*-
"""
update_pvr.py — Gestión de PVR:
- Playlist con USER_CODE/PASS_CODE
- Sincronización de tv_grab_file desde la nube
"""

import os
import re
import time
import urllib.request
import traceback
import json

from lib import log_utils
from lib import rclone_utils
from lib import utils

# ------------------------------
# Descarga robusta (reintentos + atómica)
# ------------------------------

def _download_to(path_dst: str, url: str, retries: int = 2, timeout: int = 20) -> bool:
    """
    Descarga URL a path_dst de forma atómica usando path_dst + '.part' como temporal.
    """
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

def update_playlist() -> tuple[bool, bool]:
    """
    Descarga la plantilla, sustituye USER_CODE/PASS_CODE y compara con la local.
    - Si falta /storage/.user/user: intenta recuperarlo del remoto masqelec:masqelec/user/<eth0>.
      Para ello usa rclone_utils.copy_remote_to_tmp_then_move(remote, remote_path, final_dir="/tmp"),
      valida y, si es correcto, lo instala en /storage/.user/user.
    - Solo escribe la playlist si cambia.

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
        return bool(
            m_user and m_pass and
            m_user.group(1).strip() and
            m_pass.group(1).strip()
        )

    def _try_fetch_user_from_remote() -> bool:
        """
        Intenta traer masqelec:masqelec/user/<eth0> a /tmp usando
        rclone_utils.copy_remote_to_tmp_then_move(..., final_dir="/tmp").
        Si el archivo es válido, lo instala en /storage/.user/user (atómico).
        """
        try:
            eth0 = "nomac"
            try:
                ni = utils.get_net_info() or {}
                eth0 = (ni.get("eth0") or "").strip().replace(":", "").lower() or eth0
            except Exception:
                pass

            remote = "masqelec"
            remote_path = f"masqelec/user/{eth0}"
            tmp_dir = "/tmp"
            tmp_file = os.path.join(tmp_dir, eth0)

            ok = False
            try:
                ok = rclone_utils.copy_remote_to_tmp_then_move(remote, remote_path, tmp_dir)
            except Exception as e:
                log_utils.write_log(
                    f"[update_playlist] rclone copy failed: {e}\n{traceback.format_ext()}",
                    level="ERROR",
                )
                ok = False

            if not ok or not os.path.exists(tmp_file):
                log_utils.write_log(
                    f"[update_playlist] No se encontró user remoto en {remote}:{remote_path}",
                    level="INFO",
                )
                return False

            txt = _read_text(tmp_file)
            if not _has_valid_creds(txt):
                log_utils.write_log(
                    "[update_playlist] Archivo remoto user inválido (faltan USER_CODE/PASS_CODE).",
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
                f.write(txt)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_install, user_file)
            try:
                os.remove(tmp_file)
            except Exception:
                pass

            log_utils.write_log(
                f"[update_playlist] user recuperado del remoto ({eth0}) e instalado en {user_file}"
            )
            return True
        except Exception as e:
            log_utils.write_log(
                f"[update_playlist] Error en _try_fetch_user_from_remote: {e}\n{traceback.format_exc()}",
                level="ERROR",
            )
            return False

    try:
        os.makedirs(user_dir, exist_ok=True)

        # Si no existe user local, intentar recuperarlo del remoto
        if not os.path.exists(user_file):
            if not _try_fetch_user_from_remote():
                log_utils.write_log(
                    "Archivo /storage/.user/user no encontrado y no disponible en remoto.",
                    level="ERROR",
                )
                return False, False

        # Descargar plantilla a <file>.remote y leerla
        remote_tpl_path = playlist_file + ".remote"
        if not _download_to(remote_tpl_path, base_url):
            log_utils.write_log("Fallo al descargar plantilla de playlist.", level="ERROR")
            try:
                if os.path.exists(remote_tpl_path):
                    os.remove(remote_tpl_path)
            except Exception:
                pass
            return False, False

        try:
            remote_tpl = _read_text(remote_tpl_path)
        finally:
            try:
                os.remove(remote_tpl_path)
            except Exception:
                pass

        content = _read_text(user_file)
        if not _has_valid_creds(content):
            log_utils.write_log(
                "USER_CODE o PASS_CODE ausentes o vacíos en /storage/.user/user",
                level="WARNING",
            )
            return False, False

        # Extraer credenciales “limpias”
        user_code = re.search(r'USER_CODE="([^"]+)"', content).group(1).strip()
        pass_code = re.search(r'PASS_CODE="([^"]+)"', content).group(1).strip()

        new_playlist = (
            remote_tpl
            .replace("USER_CODE", user_code)
            .replace("PASS_CODE", pass_code)
        )
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

        log_utils.write_log(
            f"Playlist {'creada' if not local_exists else 'actualizada'}: {playlist_file}"
        )

        return True, True

    except Exception as e:
        log_utils.write_log(
            f"Error en update_playlist: {e}\n{traceback.format_exc()}",
            level="ERROR",
        )
        try:
            tmp = playlist_file + ".part"
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False, False

# ------------------------------
# Sincronizar tv_grab_file desde la nube
# ------------------------------

def update_tv_grab_file() -> bool:
    """
    Verifica que /storage/.kodi/addons/service.tvheadend43/bin/tv_grab_file
    es igual que el archivo remoto en:
      https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/tv_grab_file

    - Si no existe el local o es diferente, descarga el remoto y sobrescribe.
    - Operación atómica (usa .part) y deja el fichero con permisos 0o755.
    """
    local_path = "/storage/.kodi/addons/service.tvheadend43/bin/tv_grab_file"
    remote_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/tv_grab_file"
    remote_tmp = local_path + ".remote"

    def _read_bytes(path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    try:
        # Asegurar directorio destino existe (el addon debería crearlo, pero no cuesta nada)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Descargar remoto a local_path + ".remote"
        if not _download_to(remote_tmp, remote_url):
            log_utils.write_log(
                "[tv_grab_file] No se pudo descargar el archivo remoto.",
                level="ERROR",
            )
            return False

        remote_data = _read_bytes(remote_tmp)
        local_exists = os.path.exists(local_path)

        if local_exists:
            try:
                local_data = _read_bytes(local_path)
            except Exception as e:
                log_utils.write_log(
                    f"[tv_grab_file] Error leyendo archivo local: {e}",
                    level="ERROR",
                )
                local_data = None
        else:
            local_data = None

        # Si existe y es idéntico, no hacemos nada
        if local_data is not None and local_data == remote_data:
            log_utils.write_log(
                f"[tv_grab_file] Sin cambios, archivo local ya coincide con el remoto: {local_path}"
            )
            return True

        # Es nuevo o distinto → sobrescribir de forma atómica
        tmp_local = local_path + ".part"
        with open(tmp_local, "wb") as f:
            f.write(remote_data)
            f.flush()
            os.fsync(f.fileno())

        # Aseguramos que sea ejecutable (script grabber)
        try:
            os.chmod(tmp_local, 0o755)
        except Exception as e:
            log_utils.write_log(
                f"[tv_grab_file] No se pudo aplicar permisos 755 al archivo temporal: {e}",
                level="WARNING",
            )

        os.replace(tmp_local, local_path)

        log_utils.write_log(
            f"[tv_grab_file] Archivo {'creado' if not local_exists else 'actualizado'}: {local_path}"
        )
        return True

    except Exception as e:
        log_utils.write_log(
            f"[tv_grab_file] Error en update_tv_grab_file: {e}\n{traceback.format_exc()}",
            level="ERROR",
        )
        try:
            tmp_local = local_path + ".part"
            if os.path.exists(tmp_local):
                os.remove(tmp_local)
        except Exception:
            pass
        return False

    finally:
        try:
            if os.path.exists(remote_tmp):
                os.remove(remote_tmp)
        except Exception:
            pass

# ------------------------------
# Ajustar http_user_agent en config Tvheadend
# ------------------------------

def ensure_tvh_http_user_agent() -> bool:
    """
    Garantiza que en el fichero:
      /storage/.kodi/userdata/addon_data/service.tvheadend43/config

    la clave "http_user_agent" exista y tenga exactamente el valor:
      "samsung-agent/1.1"

    - Si ya tiene ese valor → no toca nada.
    - Si falta o es distinto → lo corrige y reescribe el JSON de forma atómica.
    """
    cfg_path = "/storage/.kodi/userdata/addon_data/service.tvheadend43/config"
    desired_agent = "samsung-agent/1.1"

    if not os.path.exists(cfg_path):
        log_utils.write_log(
            f"[tvh_config] Config no encontrado: {cfg_path}",
            level="ERROR",
        )
        return False

    try:
        with open(cfg_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()

        # Por si acaso han dejado un ';' final tipo JSON "sucio"
        stripped = raw.strip()
        had_trailing_semicolon = False
        if stripped.endswith(";"):
            stripped = stripped[:-1].rstrip()
            had_trailing_semicolon = True

        try:
            data = json.loads(stripped)
        except Exception as e:
            log_utils.write_log(
                f"[tvh_config] Error parseando JSON de config: {e}",
                level="ERROR",
            )
            return False

        current = data.get("http_user_agent")

        if current == desired_agent:
            log_utils.write_log(
                f"[tvh_config] http_user_agent ya está en '{desired_agent}', sin cambios.",
            )
            return True

        # Ajustar valor
        data["http_user_agent"] = desired_agent

        tmp_path = cfg_path + ".part"
        # Reescribimos JSON bonito; Tvheadend no depende del formato
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.write("\n")
            # Si originalmente había ';', podemos optar por reponerlo.
            # Si quieres evitar riesgos, comenta las dos líneas siguientes.
            if had_trailing_semicolon:
                f.write(";\n")
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, cfg_path)

        log_utils.write_log(
            f"[tvh_config] http_user_agent ajustado a '{desired_agent}' en {cfg_path}"
        )
        return True

    except Exception as e:
        log_utils.write_log(
            f"[tvh_config] Error en ensure_tvh_http_user_agent: {e}\n{traceback.format_exc()}",
            level="ERROR",
        )
        try:
            tmp_path = cfg_path + ".part"
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False

# ------------------------------
# Punto de entrada general
# ------------------------------

def update_pvr():
    """
    Punto de entrada para actualizar PVR:
    - Asegura que la playlist existe y es válida.
    - Sincroniza tv_grab_file con la versión en la nube.
    """
    ok_pl = update_playlist()
    if not ok_pl:
        log_utils.write_log("Playlist no válida; se detiene update_pvr.", level="ERROR")

    ok_grab = update_tv_grab_file()
    if not ok_grab:
        log_utils.write_log(
            "No se pudo actualizar tv_grab_file correctamente.",
            level="ERROR",
        )
    
    ok_cfg = ensure_tvh_http_user_agent()
    if not ok_cfg:
        log_utils.write_log(
            "No se pudo asegurar http_user_agent en config de Tvheadend.",
            level="ERROR",
        )

    return

