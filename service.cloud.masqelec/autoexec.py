#!/usr/bin/python
import os
import subprocess
import urllib

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
                    print(f'Partes: {partes}')  # Mensaje de depuración
                    
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
            subprocess.call(["systemctl", "restart", "service.tvheadend42"])
        else:
            print(f"No se realizaron cambios en el archivo {ruta_archivo}.")
    
    except Exception as e:
        print(f"Ocurrió un error al modificar el archivo: {e}")

# Llamada a la función con la ruta especificada
modificar_agente_usuario('/storage/.kodi/userdata/addon_data/service.tvheadend42/config')

reload_rclone()
