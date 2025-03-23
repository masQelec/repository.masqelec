#!/usr/bin/python
import os
import io
import re
import base64
import urllib.request
import subprocess

def get_key_from_authorized_keys(filename="/storage/.ssh/authorized_keys"):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"El archivo de claves '{filename}' no existe.")
    with open(filename, "rb") as file:
        return file.read()

def feistel_round(left, right, key):
    f_result = bytearray(b ^ key[i % len(key)] for i, b in enumerate(right))
    return right, bytearray(l ^ fr for l, fr in zip(left, f_result))

def feistel_cipher(data, key, rounds=8):
    left, right = data[:len(data)//2], data[len(data)//2:]
    for _ in range(rounds):
    	right, left = feistel_round(right, left, key)
    return left + right

def decrypt(data, key, rounds=8):
    return feistel_cipher(base64.b64decode(data), key, rounds)

def download_and_decrypt_file(url, output_filename, key):
    try:
        with urllib.request.urlopen(url) as response:
            encrypted_text = response.read().decode("utf-8")
            decrypted_data = decrypt(encrypted_text, key)
            with open(output_filename, "wb") as file:
                file.write(decrypted_data)
            print(f"Archivo descargado y desencriptado en '{output_filename}'")
    except Exception as e:
        print(f"Error al descargar o desencriptar el archivo desde la URL '{url}': {e}")
        
def copy_file_with_rclone(remote, remote_path, local_path):
    command = [
        '/storage/.config/rclone/rclone', 'copy', f'{remote}:{remote_path}', local_path
    ]
    try:
        subprocess.run(command, check=True)
        print(f"Copy complete: {local_path}/{remote_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during copy: {e}")

def copy(name_file):
    remote = "update"  # Nombre del remote configurado en rclone
    remote_path = name_file  # Ruta del archivo en Google Drive
    local_path = "/storage/.update"  # Ruta local donde quieres guardar el archivo
    print(f"Copying {remote}:{remote_path} to {local_path} using rclone")
    copy_file_with_rclone(remote, remote_path, local_path)

def get_ver_file(name_file, ide):
    """ Obtiene la versión desde un archivo local buscando 'VERSION' """
    try:
        with open(name_file, 'r') as archivo:
            for linea in archivo:
                if ide in linea:
                    resultado = re.findall(r'"(.*?)"', linea)
                    return resultado[0] if resultado else None
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {name_file}")
    return None

def get_ver_txt(txt, ide):
    """ Obtiene la versión desde un texto en memoria """
    for linea in txt.split('\n'):
        if ide in linea:
            resultado = re.findall(r'"(.*?)"', linea)
            return resultado[0] if resultado else None
    return None

def get_txt_url(url):
    """ Descarga el contenido de un archivo de texto desde una URL """
    try:
        with urllib.request.urlopen(url) as txt_url:
            return txt_url.read().decode()
    except Exception as e:
        print(f"Error al obtener datos de la URL: {e}")
        return None

def update_version():
    """ Verifica si hay una actualización y notifica si hay una nueva versión disponible """
    try:
        # Obtener versión local
        #name_str_file = get_ver_file('/etc/os-release')
        name_str_file = get_ver_file('/etc/os-release', 'VERSION_ID')
        if not name_str_file:
            print("No se pudo obtener la versión local.")
            return
        
        # Obtener versión remota desde la URL
        url_content = get_txt_url('https://docs.google.com/uc?export=download&id=1jYfAGe_peaZJvhhTgXhDWBrQIX8yeAPv')
        if not url_content:
            print("No se pudo obtener la versión remota.")
            return
        
        name_str_url = get_ver_txt(url_content, 'VERSION_ID')
        if not name_str_url:
            print("No se encontró la versión en el archivo remoto.")
            return
        else:
        	ver_url = get_ver_txt(url_content, 'VERSION')
        	
        # Comparar versiones
        if name_str_file < name_str_url:
            print(f"Nueva actualización disponible: {name_str_url} VS {name_str_file}")
            copy("update/" + ver_url + ".tar")
            subprocess.run('kodi-send --action="Notification(Kodi va a reiniciar para actualizar, espere.."', shell=True, check=True)
            os.system('reboot')
        else:
            print("No hay nuevas actualizaciones")
    
    except Exception as e:
        print(f"Error durante la verificación de actualización: {e}")        

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
                urllib.request.urlretrieve(url, filename=dest)
            except Exception as e:
                print("Error descargando: {e}")
        
        subprocess.call(["systemctl", "daemon-reload"])
        
        for service in services:
            name = service.replace(".service", "")
            subprocess.call(["systemctl", "enable", name])
            subprocess.call(["systemctl", "start", name])
        
        print("rclone recargado exitosamente.")
    except Exception as e:
        print(f"Error en reload_rclone: {e}")
        
# Llamar a la función
reload_rclone()

# Llamar a la función
update_version()
