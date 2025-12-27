# -*- coding: utf-8 -*-
"""crypto_utils.py — cifrado/descifrado (Feistel)"""

import base64
import hashlib
import struct
import traceback

from lib import log_utils

def feistel_round(left, right, key):
    f_result = bytearray(b ^ key[i % len(key)] for i, b in enumerate(right))
    return right, bytearray(l ^ fr for l, fr in zip(left, f_result))

def decrypt(data_b64, key, rounds=8):
    """
    Descifra base64 en formato NEW:
      - header 4 bytes (len)
      - padding automático a par (en cifrado)
    Mantiene firma para no romper llamadas existentes.
    """
    try:
        if not key:
            raise ValueError("La clave de descifrado está vacía")
        decoded = base64.b64decode((data_b64 or "").strip())

        if not decoded or (len(decoded) % 2) != 0:
            raise ValueError("cipher inválido")

        half = len(decoded) // 2
        left, right = decoded[:half], decoded[half:]

        for _ in range(int(rounds)):
            right, left = feistel_round(right, left, key)

        data = bytes(left + right)

        if len(data) < 4:
            raise ValueError("cipher sin header")

        orig_len = struct.unpack(">I", data[:4])[0]
        plain = data[4:4 + orig_len]

        if len(plain) != orig_len:
            raise ValueError("longitud descifrada incorrecta")

        return plain

    except Exception as e:
        log_utils.write_log("Error al desencriptar los datos: {}\n{}".format(e, traceback.format_exc()), "ERROR")
        return None
