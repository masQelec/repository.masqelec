# -*- coding: utf-8 -*-
import os
import re
import time
import json
import shutil
import hashlib
import zipfile
import calendar
from datetime import datetime
import urllib.parse
import urllib.request
import urllib.error

from lib import log_utils
import xbmc

# ==========================
# CONFIG
# ==========================
RAW_BASE = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/catalog"

CATALOG_ROOT = "/storage/"
EXPORT_DIR   = "/storage/.catalog"
ZIP_NAME     = "catalog.zip"
VER_NAME     = "catalog.version"

MOVIES_DIR   = os.path.join(CATALOG_ROOT, "videos")
TV_DIR       = os.path.join(CATALOG_ROOT, "tvshows")

LOCAL_STATE_DIR = "/storage/.kodi/userdata/addon_data/service.cloud.masqelec"
LOCAL_VER_PATH  = os.path.join(LOCAL_STATE_DIR, VER_NAME)

TMP_DIR     = "/tmp/catalog_sync"
TMP_ZIP     = os.path.join(TMP_DIR, ZIP_NAME)
STAGING_DIR = os.path.join(TMP_DIR, "staging")

LOCK_PATH   = "/tmp/catalog_sync.lock"

HTTP_TIMEOUT = 30
USER_AGENT = "KodiCatalogClient/1.0"

# Empaquetar y versionar
MAKE_ZIP = True

# Progreso
PROGRESS_MOVIES_EVERY = 500
PROGRESS_EPISODES_EVERY = 1000

# Prefijos reales de TVShows en tu BD
TV_MOUNT_PREFIXES = (
    "/storage/.mnt/tvshows/1/",
    "/storage/.mnt/tvshows/2/",
)

# ==========================
# VERSION PARSE (utc + hash)
# ==========================
_UTC_RE = re.compile(r"\butc=([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)\b")
_HASH64_RE = re.compile(r"\b([0-9a-fA-F]{64})\b")

def _parse_utc(ver_text: str):
    """
    Devuelve epoch UTC (int) si puede extraer utc=... (Z).
    Si no puede, devuelve None.
    """
    if not ver_text:
        return None
    m = _UTC_RE.search(ver_text)
    if not m:
        return None
    try:
        dt = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ")  # naive UTC
        return int(calendar.timegm(dt.timetuple()))
    except Exception:
        return None

def _version_hash(ver_text: str) -> str:
    """
    Primer token (hash sha256 64 hex) si existe.
    """
    if not ver_text:
        return ""
    tok = ver_text.split()[0].strip()
    if re.fullmatch(r"[0-9a-fA-F]{64}", tok):
        return tok.lower()
    m = _HASH64_RE.search(ver_text)
    return (m.group(1).lower() if m else "")

def _is_remote_newer(remote_ver: str, local_ver: str) -> bool:
    """
    Regla principal: comparar utc=...
      - si remote_utc > local_utc => True (sync)
      - si remote_utc <= local_utc => False

    Fallbacks:
      - si local no tiene utc y remoto sí => True
      - si remoto no tiene utc y local sí => False
      - si ninguno tiene utc => compara hash; si cambia => True
    """
    r_utc = _parse_utc(remote_ver)
    l_utc = _parse_utc(local_ver)

    if r_utc is not None and l_utc is not None:
        return r_utc > l_utc

    if r_utc is not None and l_utc is None:
        return True

    if l_utc is not None and r_utc is None:
        return False

    r_hash = _version_hash(remote_ver)
    l_hash = _version_hash(local_ver)
    if r_hash and l_hash:
        return r_hash != l_hash

    return (remote_ver or "").strip() != (local_ver or "").strip()

# ==========================
# RPC / UTIL
# ==========================
def rpc(method, params=None):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        payload["params"] = params
    r = xbmc.executeJSONRPC(json.dumps(payload))
    data = json.loads(r)
    if "error" in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    return data.get("result", {})

def safe_name(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r'[\\/:*?"<>|]+', "_", s)
    s = re.sub(r"\s+", " ", s)
    return s[:180].rstrip()

def write_text(path, txt):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)

def wipe_strm_only():
    """Borra solo .strm dentro del catálogo."""
    for root in (MOVIES_DIR, TV_DIR):
        if not os.path.isdir(root):
            continue
        for base, dirs, files in os.walk(root):
            for fn in files:
                if fn.endswith(".strm"):
                    try:
                        os.remove(os.path.join(base, fn))
                    except Exception:
                        pass

def _normalize_kodi_path(p: str) -> str:
    """
    Normaliza rutas tipo file:// y separadores.
    """
    p = (p or "").strip()
    if p.startswith("file://"):
        p = urllib.parse.unquote(p[len("file://"):])
    return p.replace("\\", "/")

def _clone_mtime_from_video(video_path: str, strm_path: str):
    """
    Clona el mtime del vídeo real al .strm
    """
    try:
        vp = _normalize_kodi_path(video_path)
        st = os.stat(vp)
        os.utime(strm_path, (st.st_mtime, st.st_mtime))
    except Exception as e:
        log_utils.write_log(f"No se pudo clonar fecha: video={video_path} -> strm={strm_path} ({e})")

def _extract_show_folder_from_db_path(fpath: str):
    """
    Extrae la carpeta de serie desde la ruta real en BD.
    """
    p = _normalize_kodi_path(fpath)
    for pref in TV_MOUNT_PREFIXES:
        if p.startswith(pref):
            rel = p[len(pref):].lstrip("/")
            if not rel:
                return None
            return rel.split("/", 1)[0].strip() or None
    return None

def _read_old_version_hash(ver_path: str):
    """
    Lee el hash viejo desde catalog.version.
    Formato esperado: "<sha256>  strm_files=...  utc=..."
    Devuelve hash (str) o None si no existe/no es válido.
    """
    try:
        if not os.path.isfile(ver_path):
            return None
        with open(ver_path, "r", encoding="utf-8", errors="replace") as f:
            line = (f.readline() or "").strip()
        if not line:
            return None
        old = line.split()[0].strip()
        if re.fullmatch(r"[0-9a-fA-F]{64}", old):
            return old.lower()
        return None
    except Exception:
        return None

# ==========================
# BUILD STRM
# ==========================
def build_movies_strm():
    res = rpc("VideoLibrary.GetMovies", {
        "properties": ["title", "year", "file"],
        "sort": {"method": "title", "order": "ascending"},
        "limits": {"start": 0, "end": 200000},
    })
    movies = res.get("movies", []) or []

    n = 0
    for m in movies:
        fpath = (m.get("file") or "").strip()
        if not fpath:
            continue

        title = safe_name(m.get("title", ""))
        year = m.get("year")
        base = f"{title} ({year})" if year else title
        base = safe_name(base)

        strm = os.path.join(MOVIES_DIR, base + ".strm")
        write_text(strm, fpath + "\n")

        _clone_mtime_from_video(fpath, strm)

        n += 1
        if n % PROGRESS_MOVIES_EVERY == 0:
            log_utils.write_log(f"Películas .strm generadas: {n}")

    log_utils.write_log(f"Películas total .strm: {n}")

def build_tv_strm():
    res = rpc("VideoLibrary.GetEpisodes", {
        "properties": ["title", "file", "showtitle", "season", "episode"],
        "sort": {"method": "title", "order": "ascending"},
        "limits": {"start": 0, "end": 2000000},
    })
    eps = res.get("episodes", []) or []

    total = 0
    fallback = 0

    for e in eps:
        fpath = (e.get("file") or "").strip()
        if not fpath:
            continue

        season = int(e.get("season") or 0)
        epno   = int(e.get("episode") or 0)
        ep_title = safe_name(e.get("title") or f"S{season:02d}E{epno:02d}")

        show_folder = _extract_show_folder_from_db_path(fpath)
        if not show_folder:
            fallback += 1
            show_folder = safe_name(e.get("showtitle") or "Unknown Show")

        show_dir = os.path.join(TV_DIR, safe_name(show_folder))
        season_dir = os.path.join(show_dir, f"Season {season:02d}")
        os.makedirs(season_dir, exist_ok=True)

        base = safe_name(f"S{season:02d}E{epno:02d} - {ep_title}")
        strm = os.path.join(season_dir, base + ".strm")
        write_text(strm, fpath + "\n")

        _clone_mtime_from_video(fpath, strm)

        total += 1
        if total % PROGRESS_EPISODES_EVERY == 0:
            log_utils.write_log(f"Episodios .strm generados: {total} (fallback={fallback})")

    log_utils.write_log(f"Episodios total .strm: {total} (fallback={fallback})")

# ==========================
# VERSION / ZIP
# ==========================
def compute_version_hash(root):
    h = hashlib.sha256()
    files = []
    for base, dirs, fns in os.walk(root):
        for fn in fns:
            if fn.endswith(".strm"):
                files.append(os.path.join(base, fn))
    files.sort()

    for p in files:
        rel = os.path.relpath(p, root).replace("\\", "/")
        h.update(rel.encode("utf-8"))
        with open(p, "rb") as f:
            h.update(f.read())

    return h.hexdigest(), len(files)

def make_zip(src_root, out_zip):
    os.makedirs(os.path.dirname(out_zip), exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for base, dirs, fns in os.walk(src_root):
            for fn in fns:
                if fn.endswith(".strm"):
                    full = os.path.join(base, fn)
                    arc  = os.path.relpath(full, src_root).replace("\\", "/")
                    z.write(full, arc)

def generate_catalog():
    os.makedirs(MOVIES_DIR, exist_ok=True)
    os.makedirs(TV_DIR, exist_ok=True)
    os.makedirs(EXPORT_DIR, exist_ok=True)

    ver_path = os.path.join(EXPORT_DIR, VER_NAME)
    old_hash = _read_old_version_hash(ver_path)

    if old_hash:
        log_utils.write_log(f"Hash anterior detectado: {old_hash}")
    else:
        log_utils.write_log("No hay hash anterior válido (catalog.version ausente o corrupto).")

    log_utils.write_log("Limpiando catálogo previo (.strm)…")
    wipe_strm_only()

    log_utils.write_log("Generando .strm de películas…")
    build_movies_strm()

    log_utils.write_log("Generando .strm de series…")
    build_tv_strm()

    new_hash, count = compute_version_hash(CATALOG_ROOT)

    if old_hash and old_hash == new_hash.lower():
        log_utils.write_log(f"Hash idéntico al anterior; NO se actualiza {VER_NAME} (hash={new_hash})")
    else:
        stamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        ver_txt = f"{new_hash}  strm_files={count}  utc={stamp}\n"
        write_text(ver_path, ver_txt)
        log_utils.write_log(f"Version actualizada: {ver_path} (hash={new_hash})")

    if MAKE_ZIP:
        zip_path = os.path.join(EXPORT_DIR, ZIP_NAME)
        log_utils.write_log("Creando ZIP (.strm)…")
        make_zip(CATALOG_ROOT, zip_path)
        log_utils.write_log(f"ZIP: {zip_path}")

    log_utils.write_log(f"OK. hash={new_hash} strm_files={count}")

# ==========================
# LOCK
# ==========================
def _pid_alive(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def acquire_lock() -> bool:
    """
    Lock simple por fichero con PID.
    - Si existe y PID vive -> no entra.
    - Si existe y PID muerto -> limpia y entra.
    """
    try:
        if os.path.exists(LOCK_PATH):
            try:
                with open(LOCK_PATH, "r", encoding="utf-8") as f:
                    txt = (f.read() or "").strip()
                old_pid = int(txt) if txt.isdigit() else -1
            except Exception:
                old_pid = -1

            if old_pid > 0 and _pid_alive(old_pid):
                log_utils.write_log(f"Lock activo (PID {old_pid}). No ejecuto para evitar paralelos.", "WARNING")
                return False

            log_utils.write_log("Lock antiguo detectado (muerto o corrupto). Reemplazando…", "WARNING")
            try:
                os.remove(LOCK_PATH)
            except Exception:
                pass

        with open(LOCK_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(str(os.getpid()) + "\n")
        return True
    except Exception as e:
        log_utils.write_log(f"No se pudo crear lock: {e}", "ERROR")
        return False

def release_lock():
    try:
        if os.path.exists(LOCK_PATH):
            os.remove(LOCK_PATH)
    except Exception:
        pass

# ==========================
# HELPERS
# ==========================
def _url(base, name):
    return base.rstrip("/") + "/" + name

def _http_get_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return r.read().decode("utf-8", "replace").strip()

def _http_download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)

def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 256), b""):
            h.update(chunk)
    return h.hexdigest()

def _collect_strm(root):
    """
    Devuelve dict: relpath -> sha256
    relpath relativo a root
    """
    out = {}
    if not os.path.isdir(root):
        return out
    for base, _, files in os.walk(root):
        for fn in files:
            if fn.endswith(".strm"):
                full = os.path.join(base, fn)
                rel = os.path.relpath(full, root).replace("\\", "/")
                out[rel] = _sha256(full)
    return out

def _safe_zip_members(zf):
    """
    Seguridad ZIP:
    - sin rutas absolutas
    - sin ..
    - solo .strm
    - solo videos/ y tvshows/
    """
    members = []
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        n = name.replace("\\", "/").lstrip("/")
        if ".." in n.split("/"):
            raise RuntimeError(f"ZIP inseguro: {name}")
        if not n.endswith(".strm"):
            continue
        if not (n.startswith("videos/") or n.startswith("tvshows/")):
            continue
        members.append(n)
    return members

def _atomic_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    try:
        st = os.stat(src)
        src_mtime = st.st_mtime
    except Exception:
        src_mtime = None

    tmp = dst + ".tmp"
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)

    if src_mtime is not None:
        try:
            os.utime(dst, (src_mtime, src_mtime))
        except Exception:
            pass

def _extract_zip_with_mtime(zip_path: str, dest_dir: str) -> int:
    """
    Extrae el ZIP en dest_dir (solo .strm seguros) y fija el mtime de cada .strm
    según la fecha almacenada en el ZIP (ZipInfo.date_time).

    Devuelve SIEMPRE un int: número de .strm extraídos (0 si ninguno).
    """
    extracted = 0

    os.makedirs(dest_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = _safe_zip_members(zf) or []
        if not members:
            return 0

        for m in members:
            zf.extract(m, dest_dir)
            try:
                zi = zf.getinfo(m)
                epoch = time.mktime(zi.date_time + (0, 0, -1))
                p = os.path.join(dest_dir, m.replace("/", os.sep))
                os.utime(p, (epoch, epoch))
            except Exception:
                pass

            extracted += 1

    return extracted

def _cleanup_empty_dirs(root):
    if not os.path.isdir(root):
        return
    for base, dirs, files in os.walk(root, topdown=False):
        if not dirs and not files:
            try:
                os.rmdir(base)
            except Exception:
                pass

def _read_local_version():
    try:
        with open(LOCAL_VER_PATH, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except Exception:
        return ""

def _write_local_version(txt):
    """
    Escritura ATÓMICA (evita catalog.version corrupto a medias).
    """
    try:
        os.makedirs(os.path.dirname(LOCAL_VER_PATH), exist_ok=True)
        tmp = LOCAL_VER_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write((txt or "").rstrip("\n") + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, LOCAL_VER_PATH)
    except Exception as e:
        log_utils.write_log(f"No se pudo escribir catalog.version local (atómico): {e}", "ERROR")

def _cleanup_tmp_best_effort():
    try:
        if os.path.exists(TMP_ZIP):
            os.remove(TMP_ZIP)
    except Exception:
        pass
    try:
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
    except Exception:
        pass

# ==========================
# VERIFY: DB (Kodi) vs FS (.strm)
# ==========================
def verify_catalog_db_vs_fs(sample_limit: int = 50) -> dict:
    """
    Compara:
      - FS: .strm en MOVIES_DIR y TV_DIR
      - DB: entries de Kodi cuyo "file" apunta a esos .strm

    Retorna:
      {
        "total": {"missing": int, "extra": int, "fs": int, "db": int},
        "missing_samples": [...],  # FS - DB
        "extra_samples":   [...],  # DB - FS
      }
    """
    # FS
    fs_movies = _collect_strm(MOVIES_DIR)
    fs_tv     = _collect_strm(TV_DIR)

    fs_keys = set()
    for rel in fs_movies.keys():
        fs_keys.add("videos/" + rel)
    for rel in fs_tv.keys():
        fs_keys.add("tvshows/" + rel)

    # DB (solo "file")
    db_keys = set()

    try:
        res = rpc("VideoLibrary.GetMovies", {
            "properties": ["file"],
            "limits": {"start": 0, "end": 300000},
        })
        for m in (res.get("movies", []) or []):
            p = _normalize_kodi_path(m.get("file") or "")
            if not p:
                continue
            if p.startswith(_normalize_kodi_path(MOVIES_DIR) + "/") and p.endswith(".strm"):
                rel = p[len(_normalize_kodi_path(MOVIES_DIR) + "/"):]
                db_keys.add("videos/" + rel)
    except Exception as e:
        log_utils.write_log(f"verify_catalog_db_vs_fs: GetMovies falló: {e}", "ERROR")

    try:
        res = rpc("VideoLibrary.GetEpisodes", {
            "properties": ["file"],
            "limits": {"start": 0, "end": 3000000},
        })
        for ep in (res.get("episodes", []) or []):
            p = _normalize_kodi_path(ep.get("file") or "")
            if not p:
                continue
            if p.startswith(_normalize_kodi_path(TV_DIR) + "/") and p.endswith(".strm"):
                rel = p[len(_normalize_kodi_path(TV_DIR) + "/"):]
                db_keys.add("tvshows/" + rel)
    except Exception as e:
        log_utils.write_log(f"verify_catalog_db_vs_fs: GetEpisodes falló: {e}", "ERROR")

    missing = sorted(fs_keys - db_keys)
    extra   = sorted(db_keys - fs_keys)

    return {
        "total": {
            "missing": int(len(missing)),
            "extra": int(len(extra)),
            "fs": int(len(fs_keys)),
            "db": int(len(db_keys)),
        },
        "missing_samples": missing[:max(0, int(sample_limit))],
        "extra_samples": extra[:max(0, int(sample_limit))],
    }

# ==========================
# SYNC (CAMBIO: compara por utc)
# ==========================
def sync_catalog_https() -> bool:
    """
    Sincroniza catálogo desde RAW_BASE si remoto es más nuevo.
    Devuelve:
      - True  => se aplicaron cambios en disco (copias y/o borrados) y se guardó version local
      - False => no se aplicó nada (al día / error / lock / remoto inválido)
    """
    if not acquire_lock():
        return False

    try:
        ver_url = _url(RAW_BASE, VER_NAME)
        zip_url = _url(RAW_BASE, ZIP_NAME)

        log_utils.write_log("Comprobando versión remota…")

        try:
            remote_ver = _http_get_text(ver_url)
        except urllib.error.HTTPError as e:
            log_utils.write_log(f"HTTP error leyendo version: {e}", "ERROR")
            return False
        except Exception as e:
            log_utils.write_log(f"Error leyendo version remota: {e}", "ERROR")
            return False

        local_ver = _read_local_version()

        if not _is_remote_newer(remote_ver, local_ver):
            log_utils.write_log(
                f"Catálogo al día. local_utc={_parse_utc(local_ver)} remoto_utc={_parse_utc(remote_ver)}"
            )
            return False

        remote_hash = _version_hash(remote_ver)
        if not remote_hash:
            log_utils.write_log("catalog.version remoto inválido (sin hash64). No aplico nada.", "ERROR")
            return False

        log_utils.write_log(
            f"Versión remota MÁS NUEVA detectada -> sincronizando. "
            f"local_utc={_parse_utc(local_ver)} remoto_utc={_parse_utc(remote_ver)}"
        )

        # Preparar TMP/staging
        try:
            os.makedirs(TMP_DIR, exist_ok=True)
            shutil.rmtree(STAGING_DIR, ignore_errors=True)
            os.makedirs(STAGING_DIR, exist_ok=True)
        except Exception as e:
            log_utils.write_log(f"No se pudo preparar staging: {e}", "ERROR")
            return False

        # Descargar ZIP
        try:
            log_utils.write_log("Descargando catalog.zip…")
            _http_download(zip_url, TMP_ZIP)
        except Exception as e:
            log_utils.write_log(f"Error descargando ZIP: {e}", "ERROR")
            return False

        # Extraer ZIP en staging + fijar mtime desde ZipInfo
        try:
            log_utils.write_log("Extrayendo ZIP en staging (preservando fechas)…")
            n = _extract_zip_with_mtime(TMP_ZIP, STAGING_DIR)
            if not n:
                log_utils.write_log("ZIP no contiene .strm válidos (videos/ o tvshows/).", "ERROR")
                return False
            log_utils.write_log(f"ZIP extraído: {n} archivos .strm")
        except Exception as e:
            log_utils.write_log(f"Error extrayendo ZIP: {e}", "ERROR")
            return False

        # Calcular estado staging
        staged = _collect_strm(STAGING_DIR)
        if not staged:
            log_utils.write_log("Staging vacío tras extraer. No aplico.", "ERROR")
            return False

        # Estado local
        local_movies = _collect_strm(MOVIES_DIR)
        local_tv     = _collect_strm(TV_DIR)

        local_all = {}
        for rel, h in local_movies.items():
            local_all["videos/" + rel] = h
        for rel, h in local_tv.items():
            local_all["tvshows/" + rel] = h

        staged_keys = set(staged.keys())
        local_keys  = set(local_all.keys())

        to_delete = sorted(local_keys - staged_keys)
        to_apply  = sorted(staged_keys)

        # Asegurar carpetas base
        try:
            os.makedirs(MOVIES_DIR, exist_ok=True)
            os.makedirs(TV_DIR, exist_ok=True)
        except Exception as e:
            log_utils.write_log(f"No se pudieron crear carpetas base del catálogo: {e}", "ERROR")
            return False

        # Eliminar sobrantes
        deleted = 0
        if to_delete:
            log_utils.write_log(f"Eliminando {len(to_delete)} .strm obsoletos…")
        for rel in to_delete:
            if rel.startswith("videos/"):
                dst = os.path.join(MOVIES_DIR, rel[len("videos/"):])
            elif rel.startswith("tvshows/"):
                dst = os.path.join(TV_DIR, rel[len("tvshows/"):])
            else:
                continue

            if os.path.isfile(dst):
                try:
                    os.remove(dst)
                    deleted += 1
                except Exception as e:
                    log_utils.write_log(f"No se pudo borrar {dst}: {e}", "WARNING")

        # Añadir / actualizar
        changed = 0
        for rel in to_apply:
            src = os.path.join(STAGING_DIR, rel.replace("/", os.sep))
            if rel.startswith("videos/"):
                dst = os.path.join(MOVIES_DIR, rel[len("videos/"):])
            elif rel.startswith("tvshows/"):
                dst = os.path.join(TV_DIR, rel[len("tvshows/"):])
            else:
                continue

            old_hash = local_all.get(rel)
            new_hash = staged.get(rel)

            if old_hash == new_hash and os.path.isfile(dst):
                continue

            try:
                _atomic_copy(src, dst)
                changed += 1
            except Exception as e:
                log_utils.write_log(f"Error copiando {rel} -> {dst}: {e}", "ERROR")

        _cleanup_empty_dirs(MOVIES_DIR)
        _cleanup_empty_dirs(TV_DIR)

        # Guardar version local (atómico)
        _write_local_version(remote_ver)

        applied_any = (changed > 0) or (deleted > 0)

        log_utils.write_log(
            f"Sincronización completada: aplicados={changed}, eliminados={deleted}, total_remoto={len(staged)}"
        )

        return applied_any

    finally:
        _cleanup_tmp_best_effort()
        release_lock()

