# -*- coding: utf-8 -*-
"""fs_utils.py — utilidades de filesystem (Python 3)

Objetivo:
- Aislar operaciones atómicas y helpers de IO fuera de utils.py.
- Mantener API estable re-exportada desde lib/utils.py para compatibilidad.
"""

import os
import shutil
import hashlib

from lib import log_utils


def _read_bytes(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def _sha256(b):
    """SHA-256 hex digest de bytes (o b'' si None)."""
    try:
        return hashlib.sha256(b or b"").hexdigest()
    except Exception:
        return ""

def _sha256_bytes(b: bytes) -> str:
    """SHA256 de bytes."""
    h = hashlib.sha256()
    h.update(b or b"")
    return h.hexdigest()

def _cleanup_dir(path):
    """Borra un directorio (si existe) sin lanzar excepción."""
    try:
        if path and os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def _safe_rmtree(path):
    try:
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        log_utils.write_log("safe_rmtree falló para {}: {}".format(path, e), "DEBUG")


def atomic_write_bytes(path, data, mode=0o600):
    """
    Escritura atómica de bytes con .tmp + os.replace + fsync.
    Devuelve True/False y deja log si falla. Limpia el temporal en error.
    """
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "wb") as f:
            f.write(data or b"")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)

        # fsync directorio (best-effort)
        try:
            dfd = os.open(os.path.dirname(path) or ".", os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except Exception:
            pass

        return True

    except OSError as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        log_utils.write_log("[ERROR] atomic_write_bytes: {} ({})".format(path, e))
        return False


def atomic_write_text(path, text, encoding="utf-8", mode=0o644):
    return atomic_write_bytes(path, (text or "").encode(encoding), mode=mode)

