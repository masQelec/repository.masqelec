import os
import re
import urllib.request
import urllib.error
import xbmc
import xbmcgui
import traceback
import sys
import subprocess
from . import utils

# ------------------------------
# ACTUALIZACIÓN DEL SISTEMA
# ------------------------------
def get_version_from_file(filename: str, identifier: str):
    """Obtiene la versión desde un archivo local buscando un identificador."""
    try:
        with open(filename, 'r') as f:
            for line in f:
                if identifier in line:
                    result = re.findall(r'"(.*?)"', line)
                    return result[0] if result else None
    except FileNotFoundError:
        utils.write_log(f"No se encontró el archivo {filename}", level="ERROR")
    return None


def get_version_from_text(text: str, identifier: str):
    """Obtiene la versión desde un texto en memoria."""
    for line in text.splitlines():
        if identifier in line:
            result = re.findall(r'"(.*?)"', line)
            return result[0] if result else None
    return None


def get_text_from_url(url: str):
    """Descarga el contenido de texto desde una URL."""
    try:
        with urllib.request.urlopen(url) as txt_url:
            return txt_url.read().decode()
    except Exception as e:
        utils.write_log(f"Error al obtener datos de la URL: {e}", level="ERROR")
        return None

def copy_file_with_rclone(remote: str, remote_path: str, local_path: str) -> bool:
    """Copia archivos usando rclone."""
    command = [
        '/storage/.config/rclone/rclone', 'copy', f'{remote}:{remote_path}', local_path
    ]
    try:
        utils.write_log(f"Ejecutando rclone: {' '.join(command)}")
        subprocess.run(command, check=True)
        utils.write_log(f"Copia completada: {local_path}/{os.path.basename(remote_path)}")
        return True
    except subprocess.CalledProcessError as e:
        utils.write_log(f"Error durante la copia: {e}", level="ERROR")
        return False
    except FileNotFoundError:
        utils.write_log("Comando rclone no encontrado. Asegúrate de que la ruta sea correcta.", level="ERROR")
        return False


def copy(name_file: str) -> bool:
    """
    Copia un archivo desde el remote configurado.
    Retorna True si la copia fue exitosa, False en caso contrario.
    """
    remote = "update"
    remote_path = name_file
    local_path = "/storage/.update"
    
    return copy_file_with_rclone(remote, remote_path, local_path)


def update_system():
    """Verifica si hay una actualización disponible e inicia el proceso."""
    try:
        utils.write_log("Iniciando verificación de sistema para actualización.")
        
        # Versión local
        local_version = get_version_from_file('/etc/os-release', 'VERSION_ID')
        if not local_version:
            utils.write_log("No se pudo obtener la versión local.", level="WARNING")
            return

        # Versión remota
        url_content = get_text_from_url(
            'https://docs.google.com/uc?export=download&id=1jYfAGe_peaZJvhhTgXhDWBrQIX8yeAPv'
        )
        if not url_content:
            utils.write_log("No se pudo obtener la versión remota.", level="WARNING")
            return

        remote_version = get_version_from_text(url_content, 'VERSION_ID')
        if not remote_version:
            utils.write_log("No se encontró VERSION_ID en el archivo remoto.", level="WARNING")
            return

        version_file = get_version_from_text(url_content, 'VERSION')

        # Comparar
        if local_version < remote_version:
            utils.write_log(f"Nueva actualización disponible: {remote_version} VS {local_version}")
            
            # Aseguramos que version_file exista
            if version_file:
                # Se llama a la función copy() y se verifica su retorno
                if copy("update/" + version_file + ".tar"):
                    utils.write_log("Archivo de actualización copiado con éxito. Procediendo con el diálogo.")
                    # Usamos el diálogo de Kodi
                    dialog = xbmcgui.Dialog()
                    ret = dialog.yesno(
                        "Hay una actualizacion de sitema disponible",
                        "¿Desea actualizar ahora o en el proximo reinicio?",
                        nolabel="Posponer", 
                        yeslabel="Actualizar"
                    )

                    if ret:
                        utils.notify_user("Iniciando proceso...", xbmcgui.NOTIFICATION_INFO)
                        # Ejecutamos el comando de reinicio
                        utils.write_log("Reiniciando para actualizar")
                        time.sleep(3)  # Pausa de 3 segundos
                        os.system('reboot')                        
                    else:
                        utils.notify_user("Se actualizara en el proximo reinicio.", xbmcgui.NOTIFICATION_INFO)
                else:
                    utils.write_log("La copia del archivo falló. No se mostrará el diálogo de actualización.", level="ERROR")
            
        else:
            utils.write_log("No hay nuevas actualizaciones.")

    except Exception as e:
        utils.write_log(f"Error en update_system: {e}\n{traceback.format_exc()}", level="ERROR")
        utils.notify_user("Error en el proceso de actualización", xbmcgui.NOTIFICATION_ERROR)
