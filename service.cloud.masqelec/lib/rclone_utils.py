# -*- coding: utf-8 -*-
"""
rclone_utils.py — utilidades para rclone (safe I/O y progreso sin --stats)

Optimizado para Google Drive:
- Conservador en E/S (transfers=1, checkers=1, tpslimit, pacer).
- Reintentos ×5 con backoff exponencial.
- Cancelación fiable (SIGTERM → SIGKILL, kill a grupo).
- Progreso estable por “pesos” de ficheros (delegado al caller) + avance por bytes local.
- Evita depender de --stats; usa lsjson opcionalmente y sondea tamaño local del archivo.

Notas:
- Si `lsjson` del objeto falla (cuotas/ratelimit), intentamos igualmente la descarga.
- Para evitar cuelgues, no se consume stdout/stderr (redirigidos a DEVNULL).
"""

import os
import time
import shutil
import subprocess
import json
import signal
from typing import List, Dict, Tuple, Callable, Optional

from lib import log_utils

# ---------- Config por defecto ----------
RCLONE_BIN_CANDIDATES = [
    "/storage/.config/rclone/rclone",
    "/storage/.opt/bin/rclone",
    "/usr/bin/rclone",
    "/usr/local/bin/rclone",
]

# Subimos el timeout por intentos para DBs grandes en equipos lentos
RCLONE_TIMEOUT = 900              # seg por intento
RCLONE_RETRIES = 5                # intentos totales
RCLONE_BACKOFF_BASE = 3           # seg, backoff exponencial: 3, 6, 12, 24...

# Flags BASE (prudentes y amistosas con Drive)
RCLONE_ARGS_BASE = [
    "--transfers=1",
    # Limitar ancho de banda y buffers para bajar presión de I/O
    "--bwlimit=8M",
    "--buffer-size=4M",
    # Evitar multi-thread en streams (menos bursts)
    "--multi-thread-streams=0",
    # Ritmo y pacer (Drive)
    "--drive-chunk-size=4M",
]

RCLONE_ARGS_COPY_EXTRA: List[str] = [
    # Aquí puedes añadir flags backend-específicos si los necesitas.
    # Ejemplo (con cuidado): "--disable-http2"
]

# ---------- Helpers ----------
def _which(cmd: str) -> str:
    from shutil import which
    return which(cmd) or ""

def which_rclone() -> str:
    for p in RCLONE_BIN_CANDIDATES:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    p = _which("rclone")
    if p:
        return p
    raise FileNotFoundError("No se encontró rclone en rutas conocidas ni en $PATH")

def _maybe_wrap_ionice_nice(cmd_list: List[str]) -> List[str]:
    ion = _which("ionice")
    nic = _which("nice")
    wrapped = cmd_list
    if ion:
        wrapped = [ion, "-c2", "-n7"] + wrapped
    if nic:
        wrapped = [nic, "-n", "19"] + wrapped
    return wrapped

def _is_drive_quota_error(stderr_text: str) -> bool:
    s = (stderr_text or "").lower()
    return ("ratelimitexceeded" in s) or ("quota exceeded" in s)

def _is_drive_daily_limit(stderr_text: str) -> bool:
    s = (stderr_text or "").lower()
    return ("daily limit" in s) or ("user rate limit exceeded" in s)

def _select_tmp_dir() -> str:
    for d in ("/dev/shm", "/tmp", "/storage/.update"):
        try:
            os.makedirs(d, exist_ok=True)
            if os.access(d, os.W_OK):
                return d
        except Exception:
            pass
    return "/tmp"

def _copy_atomic(src: str, dst_dir: str) -> bool:
    try:
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, os.path.basename(src))
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        log_utils.write_log(f"[rclone_utils] error copiando {src} -> {dst_dir}: {e}", "ERROR")
        return False

def safe_rmtree(path: str):
    try:
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        log_utils.write_log(f"[rmtree] {path}: {e}", "ERROR")

def _terminate_proc_tree(proc: subprocess.Popen, name: str = "rclone"):
    """Termina el proceso con SIGTERM y, si no sale, SIGKILL (grupo si existe)."""
    try:
        if proc.poll() is not None:
            return
        killed_group = False
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGTERM)
            killed_group = True
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                if killed_group:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                else:
                    proc.kill()
            except Exception:
                pass
    except Exception as e:
        log_utils.write_log(f"[terminate] error terminando {name}: {e}", "WARNING")


# ---------- API: inspección remota ----------
def stat_remote(remote: str, remote_path: str) -> dict:
    """
    Comprueba si existe remote:remote_path -> {exists: True/False/None, size:int, error?:str}
    exists=None indica estado indeterminado (p.ej. rate limit).
    """
    try:
        rclone = which_rclone()
        dirname = os.path.dirname(remote_path).rstrip("/")
        basename = os.path.basename(remote_path)
        target = f"{remote}:{dirname}" if dirname else f"{remote}:"

        base = [rclone, "lsjson", target, "--files-only", "--fast-list"] + RCLONE_ARGS_BASE
        cmd = _maybe_wrap_ionice_nice(base)
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=RCLONE_TIMEOUT)

        if proc.returncode == 0 and proc.stdout:
            try:
                items = json.loads(proc.stdout.decode("utf-8", "ignore"))
            except Exception:
                items = []
            for it in items:
                # En lsjson de directorio, el campo fiable para comparar nombre es "Name"
                if it.get("Name") == basename and not it.get("IsDir", False):
                    return {"exists": True, "size": int(it.get("Size", 0))}
            return {"exists": False, "size": 0}
        else:
            stderr = proc.stderr.decode("utf-8", "ignore")
            if _is_drive_quota_error(stderr):
                return {"exists": None, "size": 0, "error": "quota"}
            if _is_drive_daily_limit(stderr):
                return {"exists": None, "size": 0, "error": "daily"}
            return {"exists": None, "size": 0, "error": stderr.strip()}
    except Exception as e:
        log_utils.write_log(f"[rclone stat] fallo: {e}", "ERROR")
        return {"exists": None, "size": 0, "error": "err"}

# ---------- API: progreso “por lista” (Drive-friendly) ----------
def copy_selected_remote_files_with_progress(
    remote: str,
    remote_dir: str,
    rel_paths: List[str],
    staging_dir: str,
    *,
    on_progress_per_file: Optional[Callable[[str, float, str], None]] = None,  # (rel, pct0..100, msg)
    on_file_done: Optional[Callable[[str], None]] = None,
    is_canceled: Optional[Callable[[], bool]] = None,
) -> bool:
    """
    Descarga secuencialmente archivos concretos a 'staging_dir'.
    Estrategia conservadora para Google Drive:
      - Para cada archivo:
          * 5 reintentos con backoff.
          * Sondeo del tamaño local para reportar % de ese archivo (si se conoce su tamaño remoto).
          * Si no se conoce tamaño remoto, reporta “indeterminado” pero mantiene la barra estable
            gracias a la capa de pesos en el caller (update_library.py).
      - MyVideos*.db es OBLIGATORIO (si falla, aborta).
      - Textures*.db y Thumbnails.zip son OPCIONALES (si fallan, se omiten).
      - Cancelación inmediata y limpieza de parciales.

    Devuelve False si hubo cancelación o falló un obligatorio.
    """
    if on_progress_per_file is None:
        on_progress_per_file = lambda rel, pct, msg="": None
    if on_file_done is None:
        on_file_done = lambda rel: None
    if is_canceled is None:
        is_canceled = lambda: False

    try:
        rclone = which_rclone()
    except FileNotFoundError as e:
        log_utils.write_log(str(e), "ERROR")
        return False

    os.makedirs(staging_dir, exist_ok=True)

    def _classify(rp: str) -> Tuple[int, bool]:
        rp_l = f"/{rp}".lower()
        if "/myvideos" in rp_l:
            return (0, True)   # prioridad 0, obligatorio
        if rp_l.endswith("/thumbnails.zip") or rp_l == "thumbnails.zip":
            return (2, False)  # prioridad 2, opcional
        if "/textures" in rp_l:
            return (1, False)  # prioridad 1, opcional
        return (3, False)

    rel_paths_sorted = sorted(rel_paths, key=lambda p: _classify(p)[0])

    # Pre-stat (mejor esfuerzo). Si falla (rate limit), seguimos con tamaños desconocidos.
    sizes: Dict[str, int] = {}
    for rp in rel_paths_sorted:
        full_remote = f"{remote_dir.rstrip('/')}/{rp}"
        st = stat_remote(remote, full_remote)
        if st.get("exists") is True:
            sizes[rp] = int(st.get("size") or 0)
        else:
            sizes[rp] = 0  # tamaño indeterminado o ausente

    for rp in rel_paths_sorted:
        prio, required = _classify(rp)
        remote_spec = f"{remote}:{remote_dir.rstrip('/')}/{rp}"
        local_path = os.path.join(staging_dir, rp)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        target_size = max(0, int(sizes.get(rp, 0)))

        # Si pre-stat dice ausente y es opcional → omitir
        if target_size == 0 and not required and sizes.get(rp, 0) == 0:
            log_utils.write_log(f"[rclone copy list] Omitiendo opcional (stat ausente): {rp}")
            continue

        attempts = RCLONE_RETRIES
        backoff = RCLONE_BACKOFF_BASE
        success = False

        for attempt in range(1, attempts + 1):
            if is_canceled():
                log_utils.write_log("[rclone copy list] cancelado por usuario (antes de iniciar intento).", "INFO")
                return False

            # limpiar parcial anterior
            try:
                if os.path.exists(local_path):
                    os.remove(local_path)
            except Exception:
                pass

            cmd = [rclone, "copyto", remote_spec, local_path] + RCLONE_ARGS_BASE + ["--no-traverse"]
            cmd = _maybe_wrap_ionice_nice(cmd)
            log_utils.write_log(f"[rclone copy list] ({attempt}/{attempts}) {remote_spec} -> {local_path}")

            try:
                # Iniciar como grupo propio para poder matar a todo el árbol
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            except Exception as e:
                log_utils.write_log(f"[rclone copy list] error lanzando rclone: {e}", "ERROR")
                break

            last_local = 0
            started = time.time()

            # Bucle de sondeo del archivo local
            while True:
                if is_canceled():
                    _terminate_proc_tree(proc, name="rclone(copyto)")
                    log_utils.write_log("[rclone copy list] cancelado durante copyto.", "INFO")
                    return False

                rc = proc.poll()
                try:
                    cur = os.path.getsize(local_path) if os.path.exists(local_path) else 0
                except Exception:
                    cur = last_local
                if cur < last_local:
                    cur = last_local
                last_local = cur

                # Progreso por archivo (si conocemos el tamaño)
                if target_size > 0:
                    pct_file = min(100.0, (cur * 100.0) / float(target_size)) if target_size else 0.0
                    on_progress_per_file(rp, pct_file, f"Descargando {os.path.basename(rp)}… {cur/1_000_000:.1f}/{target_size/1_000_000:.1f} MB")
                else:
                    # Tamaño desconocido: reporta “indeterminado”. La barra global se estabiliza con pesos.
                    on_progress_per_file(rp, 50.0, f"Descargando {os.path.basename(rp)}…")

                if rc is not None:
                    # Proceso terminó
                    if rc == 0 and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                        # Si tamaño remoto era desconocido, ya no nos importa: damos el archivo por OK
                        on_progress_per_file(rp, 100.0, f"Completado {os.path.basename(rp)}")
                        on_file_done(rp)
                        success = True
                    else:
                        level = "WARNING" if not required else "ERROR"
                        log_utils.write_log(f"[rclone copy list] rc={rc} al copiar {rp}", level)
                    break

                time.sleep(0.35)

            if success:
                break

            # Backoff antes del siguiente intento
            time.sleep(backoff)
            backoff *= 2

        if not success:
            if required:
                log_utils.write_log(f"[rclone copy list] FALLO definitivo en obligatorio: {rp}", "ERROR")
                return False
            else:
                # opcional: limpiar parcial si quedó algo
                try:
                    if os.path.exists(local_path):
                        os.remove(local_path)
                except Exception:
                    pass
                log_utils.write_log(f"[rclone copy list] omitido (opcional, fallo persistente): {rp}", "WARNING")

    return True

# ---------- API básicos (por compatibilidad con otras partes del addon) ----------
def sync_remote_dir(remote: str,
                    remote_dir: str,
                    local_dir: str,
                    includes: List[str] | None = None,
                    excludes: List[str] | None = None,
                    dry_run: bool = False,
                    delete_excluded: bool = False) -> bool:
    """
    Sincroniza un directorio remoto -> local usando `rclone sync`.
    Usa --filter para evitar warnings de include/exclude.
    (Este método no se usa en el flujo principal de update_library, pero lo dejamos por compatibilidad)
    """
    try:
        rclone = which_rclone()
    except FileNotFoundError as e:
        log_utils.write_log(str(e), "ERROR")
        return False

    try:
        os.makedirs(local_dir, exist_ok=True)
    except Exception as e:
        log_utils.write_log(f"[rclone sync] no se pudo crear destino {local_dir}: {e}", "ERROR")
        return False

    src_spec = f"{remote}:{remote_dir.rstrip('/')}"
    dst_spec = local_dir

    cmd = [rclone, "sync", src_spec, dst_spec] + RCLONE_ARGS_BASE + [
        "--fast-list",
        "--use-server-modtime",
        "--modify-window=2s",
        "--track-renames",
        "--delete-after",
    ]

    # Filtros con --filter (evita warning)
    if includes:
        for pat in includes:
            cmd += ["--filter", f"+ {pat}"]
    if excludes:
        for pat in excludes:
            cmd += ["--filter", f"- {pat}"]
    if includes and not excludes:
        cmd += ["--filter", "- **"]
    if delete_excluded:
        cmd.append("--delete-excluded")
    if dry_run:
        cmd.append("--dry-run")

    cmd = _maybe_wrap_ionice_nice(cmd)

    last_err = ""
    for attempt in range(1, RCLONE_RETRIES + 1):
        if attempt > 1:
            time.sleep(RCLONE_BACKOFF_BASE * (2 ** (attempt - 2)))
        try:
            log_utils.write_log(f"[rclone sync] intento {attempt}/{RCLONE_RETRIES}: {' '.join(cmd)}")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=RCLONE_TIMEOUT)
            rc = proc.returncode
            out = proc.stdout.decode("utf-8", "ignore")
            err = proc.stderr.decode("utf-8", "ignore")

            if rc == 0:
                log_utils.write_log("[rclone sync] sincronización completada")
                return True

            if _is_drive_quota_error(err):
                last_err = "quota exceeded"
            elif _is_drive_daily_limit(err):
                last_err = "daily limit exceeded"
            else:
                last_err = err.strip() or out.strip()
            log_utils.write_log(f"[rclone sync] rc={rc} stderr={last_err}", "ERROR")

        except subprocess.TimeoutExpired:
            last_err = f"timeout {RCLONE_TIMEOUT}s"
            log_utils.write_log(f"[rclone sync] timeout en intento {attempt}", "ERROR")
        except Exception as e:
            last_err = f"excepción: {e}"
            log_utils.write_log(f"[rclone sync] excepción: {e}", "ERROR")

    log_utils.write_log(f"[rclone sync] falló tras reintentos: {last_err}", "ERROR")
    return False

def copy_remote_to_tmp_then_move(remote: str, remote_path: str, final_dir: str) -> bool:
    """
    Copia remote:remote_path → tmp_dir → final_dir (con validación mínima).
    Dejado por compatibilidad (no se usa en el nuevo flujo principal).
    """
    tmp_dir = _select_tmp_dir()
    os.makedirs(final_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        rclone = which_rclone()
    except FileNotFoundError as e:
        log_utils.write_log(str(e), "ERROR")
        return False

    tmp_file = os.path.join(tmp_dir, os.path.basename(remote_path))
    final_file = os.path.join(final_dir, os.path.basename(remote_path))

    base = [rclone, "copy", f"{remote}:{remote_path}", tmp_dir,
            "--no-traverse"] + RCLONE_ARGS_BASE + RCLONE_ARGS_COPY_EXTRA

    last_err = ""
    try:
        for attempt in range(1, RCLONE_RETRIES + 1):
            if attempt > 1:
                time.sleep(RCLONE_BACKOFF_BASE * (2 ** (attempt - 2)))
            try:
                cmd = _maybe_wrap_ionice_nice(base)
                log_utils.write_log(f"[rclone copy] intento {attempt}/{RCLONE_RETRIES}: {' '.join(cmd)}")
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=RCLONE_TIMEOUT)
                if proc.returncode == 0:
                    if os.path.exists(tmp_file) and os.path.getsize(tmp_file) > 0:
                        if _copy_atomic(tmp_file, final_dir):
                            if os.path.exists(final_file) and os.path.getsize(final_file) > 0:
                                try: os.remove(tmp_file)
                                except Exception: pass
                                log_utils.write_log(f"[rclone copy] OK -> {final_file}")
                                return True
                        last_err = "archivo final inválido"
                    else:
                        last_err = "tmp vacío"
                else:
                    stderr = proc.stderr.decode("utf-8", "ignore")
                    if _is_drive_quota_error(stderr):
                        last_err = "quota exceeded"
                    elif _is_drive_daily_limit(stderr):
                        last_err = "daily limit exceeded"
                    else:
                        last_err = stderr.strip()
                    log_utils.write_log(f"[rclone copy] rc={proc.returncode} stderr={last_err}", "ERROR")
            except subprocess.TimeoutExpired:
                last_err = f"timeout {RCLONE_TIMEOUT}s"
                log_utils.write_log(last_err, "ERROR")
            except Exception as e:
                last_err = f"excepción: {e}"
                log_utils.write_log(last_err, "ERROR")
        log_utils.write_log(f"[rclone copy] falló tras reintentos: {last_err}", "ERROR")
        return False
    finally:
        try:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
        except Exception:
            pass

def copy_to_tmp_then_move_remote(src_path: str, remote: str, remote_path: str,
                                 keep_tmp: bool = False, restore_on_fail: bool = True) -> bool:
    """
    Copia src_path → tmp_dir → remote:remote_path (copyto).
    Retorna True si el objeto remoto final existe y tiene tamaño > 0.
    """
    if not os.path.exists(src_path) or os.path.getsize(src_path) <= 0:
        log_utils.write_log(f"[rclone up] origen inválido: {src_path}", "ERROR")
        return False

    src_name = os.path.basename(src_path)
    tmp_dir = _select_tmp_dir()
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        rclone = which_rclone()
    except FileNotFoundError as e:
        log_utils.write_log(str(e), "ERROR")
        return False

    tmp_file = os.path.join(tmp_dir, src_name)
    dest_spec = f"{remote}:{remote_path}"

    if not _copy_atomic(src_path, tmp_dir):
        log_utils.write_log(f"[rclone up] no se pudo copiar a tmp: {src_path}", "ERROR")
        return False

    base = [rclone, "copyto", tmp_file, dest_spec,
            "--no-traverse"] + RCLONE_ARGS_BASE + RCLONE_ARGS_COPY_EXTRA

    uploaded = False
    last_err = ""

    for attempt in range(1, RCLONE_RETRIES + 1):
        if attempt > 1:
            time.sleep(RCLONE_BACKOFF_BASE * (2 ** (attempt - 2)))

        try:
            cmd = _maybe_wrap_ionice_nice(base)
            log_utils.write_log(f"[rclone up] intento {attempt}/{RCLONE_RETRIES}: {' '.join(cmd)}")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=RCLONE_TIMEOUT)

            if proc.returncode == 0:
                st = stat_remote(remote, remote_path)
                if st.get("exists") and st.get("size", 0) > 0:
                    uploaded = True
                    break
                else:
                    last_err = f"verificación remota fallida: {st}"
                    log_utils.write_log(last_err, "ERROR")
            else:
                stderr = proc.stderr.decode("utf-8", "ignore")
                if _is_drive_quota_error(stderr):
                    last_err = "quota exceeded"
                elif _is_drive_daily_limit(stderr):
                    last_err = "daily limit exceeded"
                else:
                    last_err = stderr.strip()
                log_utils.write_log(f"[rclone up] rc={proc.returncode} stderr={last_err}", "ERROR")

        except subprocess.TimeoutExpired:
            last_err = f"timeout {RCLONE_TIMEOUT}s"
            log_utils.write_log(last_err, "ERROR")
        except Exception as e:
            last_err = f"excepción: {e}"
            log_utils.write_log(last_err, "ERROR")

    if uploaded:
        log_utils.write_log(f"[rclone up] OK -> {dest_spec}")
        if not keep_tmp and os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except Exception:
                pass
        return True

    if restore_on_fail:
        try:
            if not os.path.exists(src_path) and os.path.exists(tmp_file):
                _copy_atomic(tmp_file, os.path.dirname(src_path))
        except Exception as e:
            log_utils.write_log(f"[rclone up] error restaurando origen: {e}", "ERROR")

    try:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
    except Exception:
        pass

    log_utils.write_log(f"[rclone up] falló tras reintentos: {last_err}", "ERROR")
    return False
