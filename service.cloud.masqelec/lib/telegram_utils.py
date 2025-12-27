# -*- coding: utf-8 -*-
"""
telegram_utils.py — envío de logs a Telegram (igual que ZIP original)

Comportamiento:
- SOLO envía si el log contiene [WARNING] o [ERROR]
- Envía:
  1) Mensaje resumen (red + métricas + cooldown + líneas problema)
  2) Adjunta el log como documento (multipart/form-data)
- Token cifrado TG_TOKEN_B64 (Feistel) → se descifra con clave derivada de authorized_keys
"""

import os
import time
import json
import uuid
import mimetypes
import traceback
import urllib.request
import urllib.parse

from lib import log_utils
from lib import device_utils
from lib import crypto_utils
from lib import reliability_utils


# ------------------------------
# Constantes (preferente: constants.py)
# ------------------------------
try:
    from lib.constants import TG_TOKEN_B64, TG_FEISTEL_ROUNDS, TG_CHATID
except Exception:
    TG_TOKEN_B64 = "rAn4xRtvfVFS9L/8wJIxc/S8D92Zb83zVAAAAC44NTk5NzIxOTMxOkFBR2R0eENrZEY="
    TG_FEISTEL_ROUNDS = 8
    TG_CHATID = "952051424"


# ------------------------------
# Credenciales (token cifrado)
# ------------------------------
def _tg_get_plain_credentials():
    """
    Devuelve (bot_token:str, chat_id:str) o ("","") si no hay credenciales.
    """
    try:
        if not TG_TOKEN_B64 or not TG_CHATID:
            return "", ""

        key = device_utils.get_key_from_authorized_keys()
        if not key:
            return "", ""

        token_bytes = crypto_utils.decrypt(TG_TOKEN_B64, key, rounds=int(TG_FEISTEL_ROUNDS))
        if not token_bytes:
            return "", ""

        if isinstance(token_bytes, str):
            token_bytes = token_bytes.encode("utf-8", "replace")

        token = token_bytes.decode("utf-8", errors="ignore").strip()
        chat_id = str(TG_CHATID).strip()
        if not token or not chat_id:
            return "", ""

        return token, chat_id

    except Exception:
        return "", ""


# ------------------------------
# Multipart helpers (document upload)
# ------------------------------
def _multipart_formdata(fields, files):
    """
    fields: dict[str,str]
    files: list of tuples: (fieldname, filename, content_bytes, content_type)
    """
    boundary = "----KodiELECFormBoundary" + uuid.uuid4().hex
    body = bytearray()

    def add_line(s):
        body.extend(s.encode("utf-8"))

    for k, v in (fields or {}).items():
        add_line("--{}\r\n".format(boundary))
        add_line('Content-Disposition: form-data; name="{}"\r\n\r\n'.format(k))
        add_line(str(v))
        add_line("\r\n")

    for (fieldname, filename, content, content_type) in (files or []):
        add_line("--{}\r\n".format(boundary))
        add_line(
            'Content-Disposition: form-data; name="{}"; filename="{}"\r\n'.format(
                fieldname, filename
            )
        )
        add_line("Content-Type: {}\r\n\r\n".format(content_type or "application/octet-stream"))
        body.extend(content or b"")
        add_line("\r\n")

    add_line("--{}--\r\n".format(boundary))
    return boundary, bytes(body)


# ------------------------------
# Telegram API: sendMessage + sendDocument
# ------------------------------
def telegram_send_message_encrypted(text, timeout=10.0):
    """
    Envía un mensaje usando token cifrado (ZIP original style).
    """
    try:
        bot_token, chat_id = _tg_get_plain_credentials()
        if not bot_token or not chat_id:
            return False

        url = "https://api.telegram.org/bot{}/sendMessage".format(bot_token)
        data = urllib.parse.urlencode({
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": "true",
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=float(timeout)) as r:
            status = getattr(r, "status", 0) or 0
            return 200 <= int(status) < 300

    except Exception:
        return False


def telegram_send_document_encrypted(file_path, filename, caption="", timeout=20.0):
    """
    Adjunta un fichero como documento (multipart/form-data) usando token cifrado.
    """
    try:
        bot_token, chat_id = _tg_get_plain_credentials()
        if not bot_token or not chat_id:
            return False

        if not os.path.exists(file_path):
            return False

        with open(file_path, "rb") as f:
            content = f.read() or b""

        ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        url = "https://api.telegram.org/bot{}/sendDocument".format(bot_token)

        fields = {
            "chat_id": str(chat_id),
        }
        if caption:
            fields["caption"] = caption

        boundary, body = _multipart_formdata(
            fields=fields,
            files=[("document", filename, content, ctype)],
        )

        headers = {
            "Content-Type": "multipart/form-data; boundary={}".format(boundary),
            "Content-Length": str(len(body)),
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=float(timeout)) as r:
            status = getattr(r, "status", 0) or 0
            return 200 <= int(status) < 300

    except Exception:
        return False


# ------------------------------
# Log parsing (problemas)
# ------------------------------
def _extract_warn_error_lines(log_path, max_lines=30):
    try:
        if not os.path.exists(log_path):
            return []
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        picked = []
        for line in reversed(lines):
            if "[ERROR]" in line or "[WARNING]" in line:
                picked.append(line.strip())
                if len(picked) >= int(max_lines):
                    break
        picked.reverse()
        return picked
    except Exception:
        return []


# ------------------------------
# Public: igual que ZIP original
# ------------------------------
def telegram_send_log_with_summary_if_problem(
    log_path,
    filename,
    network_info_text,
    max_problem_lines=30,
):
    """
    Si el log contiene WARNING/ERROR, envía:
      1) Mensaje con resumen (red + métricas + cooldown + líneas problema)
      2) Log adjunto como documento
    """
    try:
        if not os.path.exists(log_path):
            return False

        problem_lines = _extract_warn_error_lines(log_path, max_lines=max_problem_lines)
        if not problem_lines:
            return False

        # ---- resumen de métricas/cooldown desde reliability state ----
        summary = ""
        try:
            st = reliability_utils.load_state() or {}
            tasks = st.get("tasks", {}) if isinstance(st.get("tasks"), dict) else {}
            cb = st.get("cb", {}) if isinstance(st.get("cb"), dict) else {}

            metrics_parts = []
            cb_parts = []

            # métricas básicas por tarea (si existen en tu state.json)
            for t, v in sorted(tasks.items()):
                if not isinstance(v, dict):
                    continue
                ok = int(v.get("ok", 0) or 0)
                fail = int(v.get("fail", 0) or 0)
                last_ok = int(v.get("last_ok", 0) or 0)
                if ok or fail or last_ok:
                    ago = int(time.time() - last_ok) if last_ok else -1
                    if ago >= 0:
                        metrics_parts.append("{}: ok={} fail={} last_ok={}s".format(t, ok, fail, ago))
                    else:
                        metrics_parts.append("{}: ok={} fail={} last_ok=?".format(t, ok, fail))

            # cooldown (circuit breaker)
            now = int(time.time())
            for t, v in sorted(cb.items()):
                if not isinstance(v, dict):
                    continue
                fails = int(v.get("fails", 0) or 0)
                thr = int(v.get("threshold", 3) or 3)
                cooldown = int(v.get("cooldown_sec", 3600) or 3600)
                last_fail = int(v.get("last_fail", 0) or 0)
                if fails >= thr and last_fail:
                    next_ts = last_fail + cooldown
                    if next_ts > now:
                        mins = int((next_ts - now) / 60)
                        cb_parts.append("{}:cooldown {}m (fails={})".format(t, mins, fails))

            lines = []
            if metrics_parts:
                lines.append("Tareas: " + " | ".join(metrics_parts))
            if cb_parts:
                lines.append("Cooldown: " + " | ".join(cb_parts))
            if lines:
                summary = "\n".join(lines).strip() + "\n\n"
        except Exception:
            summary = ""

        # ---- construir mensaje (ZIP original style) ----
        header = "KodiELEC: log con WARNING/ERROR\n\n"
        net = (network_info_text or "").strip()
        if net:
            net = net + "\n\n"

        body = summary + "\n".join(problem_lines).strip()
        if not body:
            body = "(sin líneas problema)"

        prefix = header + net
        msg = prefix + body

        # limitar tamaño (Telegram ~4096)
        max_len = 3800
        if len(msg) > max_len:
            allowed = max_len - len(prefix)
            if allowed < 200:
                prefix2 = header + net
                allowed = max_len - len(prefix2)
                body2 = body[-max(0, allowed):]
                msg = prefix2 + body2
            else:
                body2 = body[-max(0, allowed):]
                msg = prefix + body2

        ok_msg = telegram_send_message_encrypted(msg)
        caption = "Log adjunto (WARNING/ERROR)"
        ok_doc = telegram_send_document_encrypted(log_path, filename, caption=caption)

        return bool(ok_msg and ok_doc)

    except Exception:
        # IMPORTANTE: esto no debe romper el servicio
        try:
            log_utils.write_log("[telegram] upload_log fallido:\n{}".format(traceback.format_exc()), "WARNING")
        except Exception:
            pass
        return False

