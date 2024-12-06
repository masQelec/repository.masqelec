#!/usr/bin/python
import os
import io
import urllib.request
import zipfile
import subprocess

# Función para verificar si un directorio existe y descomprimir en memoria
def verificar_directorio_y_descargar_en_memoria(url, ruta_directorio):
    ruta_installed = os.path.join("/storage/.kodi/addons/service.libraryautoupdate", "installed")
    # Verificar si el directorio existe
    if not os.path.exists('/storage/.kodi/addons/service.libraryautoupdate'):
        subprocess.run('kodi-send --action="Notification(En mantenimiento,se reiniciara 2 veces,20000)"', shell=True, check=True)
        print(f"El directorio {ruta_directorio} no existe. Procediendo a descargar y descomprimir el archivo en memoria.")
        
        # Descargar el archivo ZIP en memoria
        with urllib.request.urlopen(url) as response:
            zip_data = response.read()
        
        # Crear un buffer en memoria para el archivo ZIP
        zip_buffer = io.BytesIO(zip_data)
        
        # Descomprimir el archivo en memoria
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            zip_ref.extractall(ruta_directorio)
        
        print(f"Archivo descomprimido en {ruta_directorio}")
        subprocess.call(["systemctl", "restart", "kodi"])
    else:
        print(f"El directorio {ruta_directorio} ya existe. No se necesita descargar ni descomprimir nada.")
        if not os.path.exists(ruta_installed):
            subprocess.run('kodi-send --action="Notification(En mantenimiento,se reiniciara 1 vez,20000)"', shell=True, check=True)
            print("El archivo 'installed' no existe. Creándolo ahora...")
            # Crear el archivo 'installed'
            with open(ruta_installed, 'w') as installed_file:
                installed_file.write("Instalación completada.")
            
            print(f"Archivo 'installed' creado en {ruta_directorio}")
            # Ejecutar la consulta SQL para habilitar el addon en Kodi
            habilitar_addon_sqlite()
            subprocess.call(["systemctl", "restart", "kodi"])

# Función para ejecutar la consulta SQL en la base de datos de Kodi
def habilitar_addon_sqlite():
    try:
        # Comando para ejecutar sqlite3
        comando_sql = 'sqlite3 ~/.kodi/userdata/Database/Addons33.db "UPDATE installed SET enabled=1 WHERE addonid=\'service.libraryautoupdate\';"'
        
        # Ejecutar el comando
        subprocess.run(comando_sql, shell=True, check=True)
        
        print("El addon ha sido habilitado exitosamente en la base de datos de Kodi.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando SQL: {e}")
        

def reload_rclone():
    try:
        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone.conf",
                                   filename="/storage/.config/rclone/rclone.conf")

        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone_tvshows_1.service",
                                   filename="/storage/.config/system.d/rclone_tvshows_1.service")

        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone_tvshows_2.service",
                                   filename="/storage/.config/system.d/rclone_tvshows_2.service")

        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone_videos_1.service",
                                   filename="/storage/.config/system.d/rclone_videos_1.service")

        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone_videos_2.service",
                                   filename="/storage/.config/system.d/rclone_videos_2.service")
        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone_update.service",
                                   filename="/storage/.config/system.d/rclone_update.service")


        subprocess.call(["systemctl", "daemon-reload"])
        
        subprocess.call(["systemctl", "enable", "rclone_tvshows_1"])
        subprocess.call(["systemctl", "enable", "rclone_tvshows_2"])
        subprocess.call(["systemctl", "enable", "rclone_videos_1"])
        subprocess.call(["systemctl", "enable", "rclone_videos_2"])
        subprocess.call(["systemctl", "enable", "rclone_update"])
        
        subprocess.call(["systemctl", "start", "rclone_tvshows_1"])
        subprocess.call(["systemctl", "start", "rclone_tvshows_2"])
        subprocess.call(["systemctl", "start", "rclone_videos_1"])
        subprocess.call(["systemctl", "start", "rclone_videos_2"])
        subprocess.call(["systemctl", "start", "rclone_update"])

    except:
        reload_rclone()

# Llamar a la función
reload_rclone()

# Llamar a la función
verificar_directorio_y_descargar_en_memoria('https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/service.libraryautoupdate.zip', '/storage/.kodi/addons/')




