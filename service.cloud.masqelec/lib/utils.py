import os
import datetime
import traceback
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import io
import zipfile
import shutil

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

# Inicialización de variables para el addon
ADDON_ID = "service.cloud.masqelec"
addon = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = addon.getAddonInfo("name")
PROFILE_PATH = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
LOG_FILE = os.path.join(PROFILE_PATH, "service.log")

# Crear profile si no existe
if not xbmcvfs.exists(PROFILE_PATH):
    xbmcvfs.mkdirs(PROFILE_PATH)

def write_log(message: str, level="INFO"):
    """Escribe un mensaje en el log del addon."""
    if addon.getSettingBool("activar_log"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")
        except Exception:
            pass

def notify_user(message: str, type_=xbmcgui.NOTIFICATION_INFO, time_ms=4000):
    """Muestra una notificación en la pantalla de Kodi."""
    xbmcgui.Dialog().notification(ADDON_NAME, message, type_, time_ms)
    write_log(f"Notificación mostrada: {message}")

def get_addon_download_url(addon_id, addons_xml_url):
    """
    Obtiene la URL de descarga de un addon a partir de un archivo addons.xml remoto.
    """
    write_log(f"Buscando URL de descarga para el addon '{addon_id}' en '{addons_xml_url}'")
    try:
        response = urllib.request.urlopen(addons_xml_url)
        xml_content = response.read()
        root = ET.fromstring(xml_content)
        addon_elem = root.find(f"./addon[@id='{addon_id}']")
        
        if addon_elem is not None:
            version = addon_elem.get('version')
            write_log(f"Versión de '{addon_id}' encontrada: {version}")
            
            base_url = addons_xml_url.rsplit('/', 1)[0]
            download_url = f"{base_url}/{addon_id}/{addon_id}-{version}.zip"
            write_log(f"URL de descarga construida: {download_url}")
            return download_url
        else:
            write_log(f"El addon '{addon_id}' no se encontró en el archivo XML.", level="ERROR")
            return None

    except urllib.error.URLError as e:
        write_log(f"Error de red al acceder a {addons_xml_url}: {e.reason}", level="ERROR")
        return None
    except ET.ParseError as e:
        write_log(f"Error al analizar el archivo XML: {e}", level="ERROR")
        return None
    except Exception as e:
        write_log(f"Error inesperado: {e}", level="ERROR")
        return None

def install_addon_silent(addon_id, addon_url):
    """
    Descarga un addon a la memoria, lo extrae a una carpeta temporal y lo mueve al directorio de addons.
    """
    write_log(f"Iniciando instalación silenciosa para el addon {addon_id} desde: {addon_url}")
    
    # Usamos xbmcvfs.translatePath solo para obtener la ruta del sistema operativo
    # Las operaciones de archivos se hacen con os y shutil para mayor estabilidad
    temp_dir_kodi = 'special://temp/addons_temp/'
    temp_dir_os = xbmcvfs.translatePath(temp_dir_kodi)
    destination_dir_os = xbmcvfs.translatePath('special://home/addons/')
    
    try:
        # 1. Asegurarse de que el directorio temporal existe
        if not os.path.exists(temp_dir_os):
            os.makedirs(temp_dir_os)
        
        # 2. Descargar el archivo ZIP a la memoria
        with urllib.request.urlopen(addon_url) as response:
            zip_content = io.BytesIO(response.read())

        # 3. Descomprimir el archivo en la carpeta temporal (usando la ruta del sistema)
        with zipfile.ZipFile(zip_content, 'r') as zf:
            zf.extractall(temp_dir_os)
        
        write_log(f"Addon descargado y descomprimido en: {temp_dir_os}")
        
        # 4. Mover la carpeta del addon a su ubicación final (usando shutil)
        addon_extracted_path = os.path.join(temp_dir_os, addon_id)
        addon_final_path = os.path.join(destination_dir_os, addon_id)
        
        if os.path.exists(addon_final_path):
            shutil.rmtree(addon_final_path)
            write_log(f"Versión anterior de {addon_id} eliminada.")

        shutil.move(addon_extracted_path, addon_final_path)

        write_log(f"Addon {addon_id} instalado correctamente en {addon_final_path}.")
        
        return True

    except urllib.error.URLError as e:
        write_log(f"Error de red al descargar el addon: {e.reason}", level="ERROR")
        return False
    except zipfile.BadZipFile:
        write_log("El archivo descargado no es un archivo ZIP válido.", level="ERROR")
        return False
    except Exception:
        write_log(f"Error inesperado durante la instalación de {addon_id}.", level="ERROR")
        traceback.print_exc()
        return False
    finally:
        # 5. Limpiar la carpeta temporal
        if os.path.exists(temp_dir_os):
            shutil.rmtree(temp_dir_os, ignore_errors=True)
            write_log(f"Directorio temporal {temp_dir_os} eliminado.")

def install_addon_from_repo(addon_id, addons_xml_url):
    """
    Función principal para obtener la URL e instalar un addon de forma automática y silenciosa.
    """
    addon_url = get_addon_download_url(addon_id, addons_xml_url)
    if addon_url:
        return install_addon_silent(addon_id, addon_url)
    else:
        write_log(f"No se pudo obtener la URL de descarga para {addon_id}.", level="ERROR")
        return False
