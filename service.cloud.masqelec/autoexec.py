# -*- coding: utf-8 -*-
import os
import base64
import subprocess
import urllib

def get_key_from_authorized_keys(filename="/storage/.ssh/authorized_keys"):
    if not os.path.exists(filename):
        raise IOError("El archivo de claves '{}' no existe.".format(filename))
    with open(filename, "rb") as file:
        return bytearray(file.read())

def feistel_round(left, right, key):
    f_result = bytearray([b ^ key[i % len(key)] for i, b in enumerate(right)])
    return right, bytearray([l ^ fr for l, fr in zip(left, f_result)])

def feistel_cipher(data, key, rounds=8):
    data = bytearray(data)
    left, right = data[:len(data)//2], data[len(data)//2:]
    for _ in range(rounds):
        right, left = feistel_round(right, left, key)
    return left + right

def decrypt(data, key, rounds=8):
    return bytes(feistel_cipher(bytearray(base64.b64decode(data)), key, rounds))

def download_and_decrypt_file(url, output_filename, key):
    try:
        response = urllib.urlopen(url)
        encrypted_text = bytearray(response.read())
        decrypted_data = decrypt(encrypted_text, key)
        with open(output_filename, "wb") as file:
            file.write(decrypted_data)
        print("Archivo descargado y desencriptado en '{}'".format(output_filename))
    except Exception as e:
        print("Error al descargar o desencriptar el archivo desde la URL '{}': {}".format(url, e))
        
def reload_rclone():
    try:
        key = get_key_from_authorized_keys()
        file_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone.conf.enc"
        download_and_decrypt_file(file_url, "/storage/.config/rclone/rclone.conf", key)
        
        services = [
            "rclone_tvshows_1.service",
            "rclone_tvshows_2.service",
            "rclone_videos_1.service",
            "rclone_videos_2.service"
        ]
        
        for service in services:
            url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/" + service
            dest = "/storage/.config/system.d/" + service
            try:
                urllib.urlretrieve(url, filename=dest)
            except Exception as e:
                print("Error descargando '{}': {}".format(service, e))
        
        subprocess.call(["systemctl", "daemon-reload"])
        
        for service in services:
            name = service.replace(".service", "")
            subprocess.call(["systemctl", "enable", name])
            subprocess.call(["systemctl", "start", name])
        
        print("Rclone recargado exitosamente.")
    except Exception as e:
        print("Error en reload_rclone: {}".format(e))

reload_rclone()
