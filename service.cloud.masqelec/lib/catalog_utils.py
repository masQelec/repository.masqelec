# -*- coding: utf-8 -*-
"""
catalog_utils.py — Subida de catálogo a GitHub (ZIP + VERSION) con token cifrado

Funcionalidad:
- Master: sube catalog.zip y catalog.version a GitHub (API contents PUT).
- Orden: primero ZIP y luego VERSION.
- Control tamaño: <= 75MB raw y <= 100MB base64 (como antes).
- Token GitHub: cifrado (base64+Feistel) -> se descifra con key de authorized_keys.
"""

import os
import json
import time
import base64
import hashlib
import traceback
import urllib.parse
import urllib.request
import urllib.error

from lib import log_utils
from lib import device_utils
from lib import crypto_utils

# ------------------------------
# Config (preferente: constants.py)
# ------------------------------
try:
    from lib.constants import (
        OWNER,
        REPO,
        BRANCH,
        API_BASE,
        GITHUB_TOKEN_B64,
        GITHUB_FEISTEL_ROUNDS,
        SRC_DIR,
        FILES,  # list[ (fname, dst_path) ]
    )
except Exception:
    # Fallbacks conservadores: si falta algo, fallará con logs claros.
    OWNER = "masQelec"
    REPO = "cloud.masQelec"
    BRANCH = "master"
    API_BASE = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"
    GITHUB_TOKEN_B64 = "rwfU5iQ5OjtJt7ihpPMwbIu3fP6OIAAAAChnaHBfOFQ0OWlsT0tMWEtDQTQ="
    GITHUB_FEISTEL_ROUNDS = 8
    SRC_DIR = "/storage/.catalog"
    FILES = [
        ("catalog.zip", "catalog/catalog.zip"),
        ("catalog.version", "catalog/catalog.version"),
    ]

# ------------------------------
# Token GH (descifrado)
# ------------------------------
def _gh_get_plain_token():
    """
    Devuelve token GitHub en claro (str) o "" si no está disponible.
    """
    try:
        if not GITHUB_TOKEN_B64:
            return ""

        key = device_utils.get_key_from_authorized_keys()
        if not key:
            return ""

        plain = crypto_utils.decrypt(GITHUB_TOKEN_B64, key, rounds=int(GITHUB_FEISTEL_ROUNDS))
        if not plain:
            return ""

        if isinstance(plain, (bytes, bytearray)):
            tok = plain.decode("utf-8", "replace").strip()
        else:
            tok = str(plain).strip()

        return tok or ""
    except Exception:
        log_utils.write_log("[catalog] Error descifrando token GH:\n{}".format(traceback.format_exc()), "ERROR")
        return ""

# ------------------------------
# HTTP helpers (GitHub API)
# ------------------------------
def _req(method, url, token, payload=None, timeout=30):
    """
    Devuelve (status:int|None, body:str).
    status None = fallo de red/urllib.
    """
    try:
        headers = {
            "User-Agent": "masQelec/1.0 (+Kodi)",
            "Accept": "application/vnd.github+json",
            "Authorization": "token {}".format(token),
        }

        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=float(timeout)) as r:
            raw = r.read() or b""
            body = raw.decode("utf-8", "replace")
            status = getattr(r, "status", None)
            if status is None:
                # algunos urllib devuelven code() en vez de status
                try:
                    status = int(r.getcode())
                except Exception:
                    status = None
            return status, body

    except urllib.error.HTTPError as e:
        try:
            body = (e.read() or b"").decode("utf-8", "replace")
        except Exception:
            body = str(e)
        return int(getattr(e, "code", 0) or 0), body

    except Exception:
        return None, traceback.format_exc()


def _get_remote_sha(token, path):
    """
    Obtiene SHA remoto (si existe) para poder hacer update (PUT con sha).
    """
    try:
        if not API_BASE:
            return None

        path_enc = urllib.parse.quote(path, safe="/")
        url = "{}/{}?ref={}".format(API_BASE, path_enc, urllib.parse.quote(BRANCH, safe=""))
        status, body = _req("GET", url, token, payload=None)
        if status != 200:
            return None
        obj = json.loads(body or "{}")
        sha = obj.get("sha")
        return sha or None
    except Exception:
        return None


# ------------------------------
# Uploader (igual funcionalidad que el anterior)
# ------------------------------
def _upload_file(token, src_path, dst_path):
    if not os.path.exists(src_path):
        log_utils.write_log("No existe {}".format(src_path), "ERROR")
        return False

    size = os.path.getsize(src_path)
    if size <= 0:
        log_utils.write_log("Archivo vacío: {}".format(src_path), "ERROR")
        return False

    if size > 75 * 1024 * 1024:
        log_utils.write_log("Archivo demasiado grande: {}".format(src_path), "ERROR")
        return False

    raw = open(src_path, "rb").read()
    b64 = base64.b64encode(raw).decode("ascii")

    if len(b64) > 100 * 1024 * 1024:
        log_utils.write_log("Payload base64 excesivo: {}".format(dst_path), "ERROR")
        return False

    sha_local = hashlib.sha256(raw).hexdigest()[:12]
    msg = "Update {} ({})".format(dst_path, sha_local)

    if not API_BASE:
        log_utils.write_log("API_BASE no configurado; no se puede subir {}".format(dst_path), "ERROR")
        return False

    path_enc = urllib.parse.quote(dst_path, safe="/")
    url = "{}/{}".format(API_BASE, path_enc)

    payload = {
        "message": msg,
        "content": b64,
        "branch": BRANCH,
    }

    sha_remote = _get_remote_sha(token, dst_path)
    if sha_remote:
        payload["sha"] = sha_remote

    status, body = _req("PUT", url, token, payload)
    if status is None:
        log_utils.write_log("PUT sin respuesta (red) {}".format(dst_path), "ERROR")
        return False

    if status in (200, 201):
        return True

    if status in (409, 422):
        log_utils.write_log("Conflicto SHA en {}, reintentando".format(dst_path), "WARNING")
        payload["sha"] = _get_remote_sha(token, dst_path)
        status, body = _req("PUT", url, token, payload)
        if status in (200, 201):
            return True

    # recortar body para no spamear
    body_short = (body or "").strip()
    if len(body_short) > 400:
        body_short = body_short[:400] + "..."
    log_utils.write_log("PUT falló {} ({}): {}".format(dst_path, status, body_short), "ERROR")
    return False


def load_catalog_github():
    """
    Sube catálogo a GitHub:
    - Primero catalog.zip
    - Luego catalog.version
    """
    token = _gh_get_plain_token()
    if not token:
        log_utils.write_log("Token GitHub no disponible, abortando subida", "ERROR")
        return False

    # Orden: ZIP primero
    ordered = sorted(FILES, key=lambda x: 0 if x[0] == "catalog.zip" else 1)

    ok_all = True
    for fname, dst in ordered:
        src = os.path.join(SRC_DIR, fname)
        log_utils.write_log("Subiendo {} -> {}".format(src, dst), "INFO")
        if not _upload_file(token, src, dst):
            log_utils.write_log("Fallo subiendo {}".format(dst), "ERROR")
            ok_all = False
        else:
            log_utils.write_log("{} subido correctamente".format(dst), "INFO")

    return ok_all

