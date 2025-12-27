# -*- coding: utf-8 -*-
"""catalog_utils.py — acceso a catálogo en GitHub (token cifrado)"""

import traceback

from lib import log_utils
from lib import device_utils
from lib import crypto_utils

# Intentamos tomar constantes del sitio “nuevo” (constants.py). Si no están, fallback seguro.
try:
    from lib.constants import GITHUB_TOKEN_B64, GITHUB_FEISTEL_ROUNDS
except Exception:
    GITHUB_TOKEN_B64 = "rwfU5iQ5OjtJt7ihpPMwbIu3fP6OIAAAAChnaHBfOFQ0OWlsT0tMWEtDQTQ="
    GITHUB_FEISTEL_ROUNDS = 8

def _gh_get_plain_token():
    """
    Devuelve el token GitHub en claro (bytes) descifrado desde GITHUB_TOKEN_B64.
    """
    if not GITHUB_TOKEN_B64:
        return None

    try:
        key = device_utils.get_key_from_authorized_keys()
        if not key:
            return None

        plain = crypto_utils.decrypt(GITHUB_TOKEN_B64, key, rounds=int(GITHUB_FEISTEL_ROUNDS))
        if not plain:
            return None

        # decrypt puede devolver bytes o str según implementación
        if isinstance(plain, str):
            plain = plain.encode("utf-8", "replace")

        return plain

    except Exception:
        log_utils.write_log(
            "[catalog] error obteniendo token GH:\n{}".format(traceback.format_exc()),
            "WARNING",
        )
        return None

def load_catalog_github():
    """
    Wrapper compatible hacia atrás.
    """
    try:
        # Import local para evitar dependencias circulares
        try:
            from lib import core_catalog
        except Exception:
            core_catalog = None

        token = _gh_get_plain_token()
        if isinstance(token, (bytes, bytearray)):
            token = token.decode("utf-8", "replace").strip()

        if not token:
            log_utils.write_log(
                "[catalog] token GH no disponible; se omite load_catalog_github()",
                "WARNING",
            )
            return False

        if core_catalog and hasattr(core_catalog, "load_catalog_github"):
            return bool(core_catalog.load_catalog_github(token))

        log_utils.write_log(
            "[catalog] no hay implementación real de carga de catálogo.",
            "INFO",
        )
        return False

    except Exception:
        log_utils.write_log(
            "[catalog] fallo en load_catalog_github:\n{}".format(traceback.format_exc()),
            "ERROR",
        )
        return False

