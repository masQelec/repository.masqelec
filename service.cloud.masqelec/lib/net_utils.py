# -*- coding: utf-8 -*-
"""net_utils.py — utilidades de red (Python 3)

Objetivo:
- Aislar la lógica de red (DNS/online/descargas) fuera de utils.py.
- Mantener API estable re-exportada desde lib/utils.py para compatibilidad.
"""
import os
import shutil
import socket
import time
import traceback
import urllib.request
import urllib.error
import gzip

from lib import log_utils

# Defaults (pueden ser sobreescritos por kwargs desde callers)
NET_TIMEOUT = 30           # segundos
NET_RETRIES = 2            # reintentos adicionales en error de red
UA_HTTP = "KodiELEC-HTTP/1.0"
RETRY_BACKOFF = 2          # segundos entre reintentos


def wait_for_dns(hostname="www.google.com", timeout=NET_TIMEOUT, poll=1.0):
    """Espera hasta que el resolver DNS funcione para 'hostname' o expire."""
    deadline = time.time() + (timeout or NET_TIMEOUT)
    while time.time() < deadline:
        try:
            socket.getaddrinfo(hostname, 80)
            return True
        except (socket.gaierror, OSError):
            time.sleep(poll)
    return False


def _has_network(timeout=2):
    """Comprueba si hay interfaz con salida (muy simple)."""
    try:
        # Un método barato: resolver + socket corto a 1.1.1.1:53
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.connect(("1.1.1.1", 53))
        s.close()
        return True
    except OSError:
        return False


def _has_internet(timeout=5):
    """Comprueba conectividad real a internet (petición HEAD a un endpoint estable)."""
    url = "https://connectivitycheck.gstatic.com/generate_204"
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA_HTTP})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code = getattr(r, "status", None) or r.getcode()
            return int(code) == 204 or int(code) == 200
    except OSError:
        return False


def is_online():
    """Online = red + internet."""
    return _has_network() and _has_internet()


def _net_open(url, data=None, timeout=NET_TIMEOUT, retries=NET_RETRIES, ua=UA_HTTP, backoff=RETRY_BACKOFF):
    """Abre URL con User-Agent y timeout, con reintentos simples."""
    headers = {
    "User-Agent": ua,
    "Accept-Encoding": "identity",
    }
    req = urllib.request.Request(url, data=data, headers=headers)
    last_err = None
    for attempt in range(int(retries) + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            last_err = e
            log_utils.write_log(
                "Intento {}/{} falló para {}: {}".format(attempt + 1, int(retries) + 1, url, getattr(e, "reason", e)),
                "ERROR"
            )
            time.sleep(backoff)
        except Exception as e:
            last_err = e
            log_utils.write_log(
                "Intento {}/{} falló para {}: {}".format(attempt + 1, int(retries) + 1, url, e),
                "ERROR"
            )
            time.sleep(backoff)
    raise last_err


def download_atomic(dst_path, url, retries=NET_RETRIES, timeout=NET_TIMEOUT, tmp_suffix=".part"):
    """
    Descarga 'url' y escribe en 'dst_path' de forma atómica (dst_path + .part + os.replace).
    - Maneja errores de red típicos (URLError/HTTPError/timeout/OSError)
    - Limpia el .part en caso de fallo
    - Evita guardar respuestas gzip “en crudo” (GitHub raw suele comprimir)
    - Si la respuesta sale vacía, falla (para no sobreescribir con 0 bytes)
    """
    tmp_path = dst_path + tmp_suffix
    last_err = None

    for attempt in range(int(retries) + 1):
        try:
            with _net_open(url, timeout=timeout, retries=0) as r:
                data = r.read() or b""

                # Headers pueden fallar según wrapper / impl
                try:
                    enc = (r.headers.get("Content-Encoding") or "").lower()
                except Exception:
                    enc = ""

            # Descompresión según Content-Encoding (y fallback por magic bytes)
            if ("gzip" in enc) or (len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B):
                try:
                    data = gzip.decompress(data)
                except Exception as e:
                    # Si el servidor dice gzip pero no lo era, no corrompemos: seguimos con data original
                    log_utils.write_log(
                        "[WARNING] download_atomic gzip decompress falló: {} -> {} ({})".format(
                            url, dst_path, type(e).__name__
                        )
                    )

            # Validación mínima: evita reemplazar por vacío
            if not data:
                raise ValueError("respuesta vacía")

            dstdir = os.path.dirname(dst_path)
            if dstdir:
                os.makedirs(dstdir, exist_ok=True)

            with open(tmp_path, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())

            os.replace(tmp_path, dst_path)
            return True

        except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout, TimeoutError, OSError, ValueError) as e:
            last_err = e
            # Limpieza del temporal
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

            log_utils.write_log(
                "[WARNING] download_atomic fallo intento {}/{}: {} -> {} ({}: {})".format(
                    attempt + 1,
                    int(retries) + 1,
                    url,
                    dst_path,
                    type(e).__name__,
                    str(e) or "-",
                )
            )
            if attempt < int(retries):
                time.sleep(RETRY_BACKOFF)
                continue
            return False

        except Exception as e:
            # Errores inesperados: log detallado para diagnóstico
            last_err = e
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            log_utils.write_log(
                "[ERROR] download_atomic error inesperado: {} -> {} ({}: {})\n{}".format(
                    url,
                    dst_path,
                    type(e).__name__,
                    str(e) or "-",
                    traceback.format_exc(),
                )
            )
            return False

    if last_err:
        log_utils.write_log("[ERROR] download_atomic agotados reintentos: {}: {}".format(type(last_err).__name__, str(last_err) or "-"))
    return False
