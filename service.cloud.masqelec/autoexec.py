#!/usr/bin/python
import os
import io
import re
import urllib.request
import zipfile
import subprocess

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

def get_ver_file(name_file):
    # Abre el archivo
    with open(name_file, 'r') as archivo:
        # Lee el archivo linea por linea
        for linea in archivo:
            # Busca la palabra "VERSION" en la linea
            if "VERSION" in linea:
                # Si la encuentra, extrae el texto entre comillas
                resultado = re.findall(r'"(.*?)"', linea)
                return resultado

    # Si no encuentra ninguna linea con "VERSION", devuelve None
    return None

def get_ver_txt(txt):
    # Divide el texto en l neas
    lineas = txt.split('\n')

    for linea in lineas:
        # Busca la palabra "VERSION" en la l nea
        if "VERSION" in linea:
            # Si la encuentra, extrae el texto entre comillas
            resultado = re.findall(r'"(.*?)"', linea)
            return resultado

    # Si no encuentra ninguna linea con "VERSION", devuelve Nonee
    return None
    
def get_txt_url(url):
    # Abre la URL
    with urllib.request.urlopen(url) as txt_url:
        # Lee el contenido y lo decodifica a txt
        txt = txt_url.read().decode()
    return txt

# Función para actualizar la verison de kodi
def update_version():
    try:
        name_str_file = get_ver_file('/etc/os-release')
        print(name_str_file[0])
        
        name_str_url = get_ver_txt(get_txt_url("https://docs.google.com/uc?export=download&id=1jYfAGe_peaZJvhhTgXhDWBrQIX8yeAPv"))
        
        if name_str_file[0] != name_str_url[0]:
        	print("Nueva actualizacion " + name_str_url[0])
        	copy("update/" + name_str_url[0] + ".tar")
        	subprocess.call(["kodi-send", "-action='Notification(MANTENIMIENTO,'Kodi va a reiniciar para actualizar, espere..')'"])
        	os.system('reboot')
        	
    except subprocess.CalledProcessError as e:
        print(f"Error during copy: {e}")
    
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


        subprocess.call(["systemctl", "daemon-reload"])
        
        subprocess.call(["systemctl", "start", "rclone_tvshows_1"])
        subprocess.call(["systemctl", "enable", "rclone_tvshows_1"])
        
        subprocess.call(["systemctl", "start", "rclone_tvshows_2"])
        subprocess.call(["systemctl", "enable", "rclone_tvshows_2"])
        
        subprocess.call(["systemctl", "start", "rclone_videos_1"])
        subprocess.call(["systemctl", "enable", "rclone_videos_1"])
        
        subprocess.call(["systemctl", "start", "rclone_videos_2"])
        subprocess.call(["systemctl", "enable", "rclone_videos_2"])
        

    except:
        reload_rclone()

# Función para modificar el agente de usuario en el archivo config
def modificar_agente_usuario(ruta_archivo):
    # Verificar si el archivo existe
    if not os.path.isfile(ruta_archivo):
        print(f"El archivo {ruta_archivo} no existe.")
        return
    
    try:
        # Leer el contenido del archivo
        with open(ruta_archivo, 'r') as archivo:
            lineas = archivo.readlines()
        
        cambio_realizado = False  # Variable para rastrear si se ha realizado un cambio

        # Abrir el archivo en modo escritura para hacer los cambios
        with open(ruta_archivo, 'w') as archivo:
            for linea in lineas:
                # Buscar la línea que contiene "http_user_agent"
                if '"http_user_agent":' in linea:
                    partes = linea.split('"http_user_agent":')
                    
                    # Obtener el valor actual del agente de usuario
                    usuario_actual = partes[1].split('"')[1].strip()
                    print(f'Agente de usuario actual: {usuario_actual}')  # Mensaje de depuración sin comilla adicional
                    
                    # Si el valor no es "samsung-agent/1.1", actualizarlo
                    if usuario_actual != 'samsung-agent/1.1':
                        nueva_linea = f'    "http_user_agent": "samsung-agent/1.1",\n'
                        archivo.write(nueva_linea)
                        cambio_realizado = True
                        print("Se ha realizado un cambio.")  # Mensaje de depuración
                    else:
                        archivo.write(linea)
                else:
                    archivo.write(linea)
        
        if cambio_realizado:
            # Mensaje de confirmación
            print(f"El archivo {ruta_archivo} ha sido modificado.")
            subprocess.call(["systemctl", "restart", "service.tvheadend43"])
        else:
            print(f"No se realizaron cambios en el archivo {ruta_archivo}.")
    
    except Exception as e:
        print(f"Ocurrió un error al modificar el archivo: {e}")
        
# Llamar a la función
verificar_directorio_y_descargar_en_memoria('https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/service.libraryautoupdate.zip', '/storage/.kodi/addons/')

# Llamar a la función
reload_rclone()

# Llamar a la función
update_version()

# Llamada a la función con la ruta especificada
modificar_agente_usuario('/storage/.kodi/userdata/addon_data/service.tvheadend43/config')

