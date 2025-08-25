import os
import subprocess
import urllib.request
import urllib.error
import traceback
import re
import shutil
import io
import zipfile
import time
import xml.etree.ElementTree as ET
from . import db_utils
from . import utils
from . import webserver_check

def update_playlist():
    """Descarga y actualiza la playlist con USER_CODE y PASS_CODE."""
    playlist_file = "/storage/.user/playlist.m3u"
    user_file = "/storage/.user/user"
    base_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/"

    try:
        urllib.request.urlretrieve(base_url + "playlist.m3u", playlist_file)
        
        if not os.path.exists(playlist_file):
            utils.write_log(f"No se encontró el archivo: {playlist_file}", level="ERROR")
            return

        with open(user_file, encoding="utf-8") as f:
            content = f.read()

        user_code = re.search(r'USER_CODE="([^"]+)"', content)
        pass_code = re.search(r'PASS_CODE="([^"]+)"', content)

        if not user_code or not pass_code:
            utils.write_log("No se encontró USER_CODE o PASS_CODE en el archivo de usuario.", level="WARNING")
            return

        with open(playlist_file, encoding="utf-8") as f:
            playlist = f.read()

        playlist = playlist.replace("USER_CODE", user_code.group(1))
        playlist = playlist.replace("PASS_CODE", pass_code.group(1))

        with open(playlist_file, "w", encoding="utf-8") as f:
            f.write(playlist)

        utils.write_log(f"Playlist actualizada en: {playlist_file}")
    except Exception as e:
        utils.write_log(f"Error en update_playlist: {e}\n{traceback.format_exc()}", level="ERROR")


def verify_and_correct_pvr_settings(settings_dir):
    """
    Verifica y corrige la configuración del addon PVR editando directamente el archivo XML.
    Devuelve True si hubo algún problema o cambio, False si la configuración es correcta.
    """
    settings_file = os.path.join(settings_dir, "instance-settings-1.xml")
    if not os.path.exists(settings_file):
        utils.write_log(f"No se encontró el archivo: {settings_file}", level="ERROR")
        return True

    # Valores correctos
    correct_values = {
        "m3uPath": "/storage/.user/playlist.m3u",
        "epgUrl": "https://raw.githubusercontent.com/masQelec/epg/main/guide.xml",
        "defaultUserAgent": "samsung-agent/1.1"
    }

    try:
        tree = ET.parse(settings_file)
        root = tree.getroot()
        updated = False
        
        for setting_id, correct_value in correct_values.items():
            elem = root.find(f"./setting[@id='{setting_id}']")
            if elem is not None:
                if elem.text != correct_value:
                    utils.write_log(f"Valor incorrecto para {setting_id}: '{elem.text}' -> Corrigiendo a: '{correct_value}'")
                    elem.text = correct_value
                    updated = True
                else:
                    utils.write_log(f"'{setting_id}' ya está correcto: {correct_value}")
            else:
                utils.write_log(f"El valor para '{setting_id}' no existe en el XML. Agregando.")
                new_elem = ET.Element("setting", id=setting_id, default="true")
                new_elem.text = correct_value
                root.append(new_elem)
                updated = True

        if updated:
            tree.write(settings_file, encoding="UTF-8", xml_declaration=True)
            utils.write_log("Archivo de configuración actualizado.")
            # Devuelve True para indicar que se requiere una recarga del addon
            return True

    except Exception as e:
        utils.write_log(f"Error al verificar la configuración de PVR: {e}\n{traceback.format_exc()}", level="ERROR")
        return True

    return False

def remove_old_databases(db_dir):
    """
    Elimina bases de datos viejas con prefijos 'TV' o 'Epg' en el directorio dado.
    """
    try:
        for filename in os.listdir(db_dir):
            if any(filename.startswith(prefix) for prefix in ["TV", "Epg"]) and filename.endswith(".db"):
                os.remove(os.path.join(db_dir, filename))
                utils.write_log(f"Eliminado: {filename}")
    except Exception as e:
        utils.write_log(f"Error al eliminar bases de datos antiguas: {e}\n{traceback.format_exc()}", level="ERROR")

def disable_conflicting_addons(addons_list):
    """
    Deshabilita addons que están habilitados de la lista proporcionada.
    """
    for addon in addons_list:
        inst, en = db_utils.get_addon_status(addon)
        if inst and en:
            db_utils.set_addon_status(addon, 0)
            utils.write_log(f"Deshabilitado {addon}")

def download_and_extract_zip(url, install_dir):
    """Descarga y extrae un archivo ZIP desde una URL."""
    utils.write_log(f"Descargando y extrayendo {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            zip_buffer = io.BytesIO(response.read())
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        utils.write_log(f"PVR extraído en {install_dir}")
    except Exception as e:
        utils.write_log(f"Error al descargar o extraer el archivo ZIP: {e}\n{traceback.format_exc()}", level="ERROR")

def restart_pvr_addon():
    """Reinicia el addon PVR deshabilitándolo y habilitándolo de nuevo con la API."""
    utils.write_log("Reiniciando el addon PVR con comandos de la API...")
    # Deshabilitar
    subprocess.run(['curl', '-H', 'Content-Type: application/json', '--data', '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":false},"id":1}', 'http://localhost:8080/jsonrpc'], check=True)
    time.sleep(2)  # Esperar a que se detenga
    # Habilitar
    subprocess.run(['curl', '-H', 'Content-Type: application/json', '--data', '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":true},"id":1}', 'http://localhost:8080/jsonrpc'], check=True)

# ------------------------------
# INSTALADOR/ACTUALIZADOR DE PVR
# ------------------------------
def update_pvr(url='https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/pvr.zip', install_dir='/storage/'):
    """
    Descarga, instala y configura el addon pvr.iptvsimple desde una URL ZIP.
    """
    user_file = "/storage/.user/user"
    db_dir = "/storage/.kodi/userdata/Database/"
    pvr_addon_id = "pvr.iptvsimple"
    pvr_addon_dir = "/storage/.kodi/addons/pvr.iptvsimple"
    addon_data_dir = os.path.join("/storage/.kodi/userdata/addon_data/", pvr_addon_id)
    conflict_addons = ["pvr.hts", "service.tvheadend43"]

    if not os.path.exists(user_file):
        utils.write_log("Archivo de usuario no encontrado. Abortando instalación de PVR.", level="ERROR")
        return False
        
    update_playlist()

    installed, enabled = db_utils.get_addon_status(pvr_addon_id)
    needs_pvr_reload = False

    if not installed or not os.path.exists(pvr_addon_dir):
        # Caso 1: Instalación completa
        utils.write_log("Addon no instalado o directorio no encontrado. Iniciando instalación completa.")
        utils.notify_user("instalando addon pvr.iptvsimple")
        if utils.install_addon_from_repo("pvr.iptvsimple", "https://raw.githubusercontent.com/masQelec/repository.masqelec/masqelec_21/addons/1.0/Amlogic/arm/addons.xml"):
        	remove_old_databases(db_dir)
        	disable_conflicting_addons(conflict_addons)
        	db_utils.register_addon(pvr_addon_id, 1, "repository.xbmc.org")
        	needs_pvr_reload = True
        	verify_and_correct_pvr_settings(addon_data_dir)
        else:
        	 return False
    elif not enabled:
        # Caso 2: Addon deshabilitado, solo se habilita y verifica
        utils.write_log("Addon instalado pero deshabilitado. Habilitando y verificando configuración.")
        db_utils.set_addon_status(pvr_addon_id, 1)
        needs_pvr_reload = verify_and_correct_pvr_settings(addon_data_dir)
    else:
        # Caso 3: Addon instalado y habilitado, solo se verifica configuración
        utils.write_log("pvr.iptvsimple ya estaba habilitado. Verificando configuración...")
        mismatch_found = verify_and_correct_pvr_settings(addon_data_dir)
        if mismatch_found:
            utils.write_log("Configuración del addon incorrecta, se requiere reiniciar.")
            needs_pvr_reload = True
        else:
            utils.write_log("Configuración del addon correcta.")
    
    if needs_pvr_reload:
        if webserver_check.is_webserver_enabled():
            restart_pvr_addon()
        else:
            utils.write_log("Servidor web de Kodi deshabilitado, reiniciando Kodi completo.")
            os.system('systemctl restart kodi')

    return True           
