# -*- coding: utf-8 -*-
"""system_utils.py — wrappers de comandos del sistema (solo Py3)"""

import subprocess

from lib import log_utils

def run_cmd(cmd, timeout=10):
    """
    Ejecuta comando con timeout.
    Devuelve (returncode, stdout, stderr) como texto (utf-8 con replacement).
    """
    if not isinstance(cmd, (list, tuple)):
        raise TypeError("cmd debe ser list/tuple, recibido: {}".format(type(cmd).__name__))
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False
        )
        out = (p.stdout or b"").decode("utf-8", "replace")
        err = (p.stderr or b"").decode("utf-8", "replace")
        return p.returncode, out, err
    except subprocess.TimeoutExpired:
        return 124, "", "Timeout expirado ({}s)".format(timeout)
    except OSError as e:
        log_utils.write_log("[ERROR] run_cmd OSError: {} ({})".format(" ".join(cmd) if isinstance(cmd, (list, tuple)) else str(cmd), e))
        return 1, "", str(e)
