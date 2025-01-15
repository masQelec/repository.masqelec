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

# Funcion para modificar el agente de usuario en el archivo config
def modificar_agente_usuario(ruta_archivo):
    # Verificar si el archivo existe
    if not os.path.isfile(ruta_archivo):
        print('El archivo {} no existe.'.format(ruta_archivo))
        return
    
    try:
        # Leer el contenido del archivo
        with open(ruta_archivo, 'r') as archivo:
            lineas = archivo.readlines()
        
        cambio_realizado = False  # Variable para rastrear si se ha realizado un cambio

        # Abrir el archivo en modo escritura para hacer los cambios
        with open(ruta_archivo, 'w') as archivo:
            for linea in lineas:
                # Buscar la linea que contiene "http_user_agent"
                if '"http_user_agent":' in linea:
                    partes = linea.split('"http_user_agent":')
                    
                    # Obtener el valor actual del agente de usuario
                    usuario_actual = partes[1].split('"')[1].strip()
                    print('Agente de usuario actual: {}'.format(usuario_actual))  # Mensaje de depuracion sin comilla adicional
                    
                    # Si el valor no es "samsung-agent/1.1", actualizarlo
                    if usuario_actual != 'samsung-agent/1.1':
                        nueva_linea = '    "http_user_agent": "{}",\n'.format("samsung-agent/1.1")
                        archivo.write(nueva_linea)
                        cambio_realizado = True
                        print("Se ha realizado un cambio.")  # Mensaje de depuracion

                    else:
                        archivo.write(linea)
                else:
                    archivo.write(linea)
        
        if cambio_realizado:
            # Mensaje de confirmacion
            print("El archivo {} ha sido modificado.".format(ruta_archivo))
            subprocess.call(["systemctl", "restart", "service.tvheadend43"])
        else:
            print("No se realizaron cambios en el archivo {}.".format(ruta_archivo))
    
    except Exception as e:
        print("Ocurrio un error al modificar el archivo: {}".format(e))

# Llamada a la funcion con la ruta especificada
modificar_agente_usuario('/storage/.kodi/userdata/addon_data/service.tvheadend43/config')

reload_rclone()
